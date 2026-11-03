"""Text/tool subset of Anthropic Messages, normalized through the shared loop guard."""
import copy,json,uuid

MODEL='bonsai2-27b'
class ProtocolError(ValueError):pass

def text_blocks(value):
 if isinstance(value,str):return value
 if value is None:return ''
 if not isinstance(value,list):raise ProtocolError('content must be text or a content-block array')
 texts=[]
 for block in value:
  if not isinstance(block,dict):raise ProtocolError('content blocks must be objects')
  kind=block.get('type')
  if kind=='text':texts.append(block.get('text',''))
  elif kind in ('thinking','redacted_thinking'):continue
  else:raise ProtocolError(f'Unsupported content block {kind!r}; this deployment supports text and tools, not images/documents/server tools')
 return '\n'.join(texts)

def to_openai(body):
 if not isinstance(body,dict) or not isinstance(body.get('messages'),list):raise ProtocolError('messages must be an array')
 messages=[]
 if body.get('system'):messages.append({'role':'system','content':text_blocks(body['system'])})
 for msg in body.get('messages',[]):
  role=msg.get('role');content=msg.get('content',[])
  if role not in ('user','assistant'):raise ProtocolError('Messages roles must be user or assistant')
  if isinstance(content,str):messages.append({'role':role,'content':content});continue
  if not isinstance(content,list):raise ProtocolError('message content must be text or an array')
  texts=[];calls=[];results=[]
  for block in content:
   kind=block.get('type')
   if kind=='text':texts.append(block.get('text',''))
   elif kind in ('thinking','redacted_thinking'):continue
   elif kind=='tool_use' and role=='assistant':
    if not isinstance(block.get('input',{}),dict):raise ProtocolError('tool_use.input must be an object')
    calls.append({'id':block['id'],'type':'function','function':{'name':block['name'],'arguments':json.dumps(block.get('input',{}),ensure_ascii=False)}})
   elif kind=='tool_result' and role=='user':
    result=text_blocks(block.get('content',''))
    if block.get('is_error'):result='Tool error:\n'+result
    results.append({'role':'tool','tool_call_id':block['tool_use_id'],'content':result})
   else:raise ProtocolError(f'Unsupported {role} content block {kind!r}')
  if role=='assistant':
   if texts or calls:
    out={'role':role,'content':'\n'.join(texts) or None}
    if calls:out['tool_calls']=calls
    messages.append(out)
  elif results:
   # Tool-result wrappers are not new human turns: preserve the guard's per-turn budget.
   if texts:results[-1]['content']+='\n\nClient note:\n'+'\n'.join(texts)
   messages.extend(results)
  elif texts:messages.append({'role':'user','content':'\n'.join(texts)})
 if not messages:raise ProtocolError('messages must contain text or tools')
 out={'model':MODEL,'messages':messages,'max_tokens':body.get('max_tokens',16384)}
 for key in ('temperature','top_p','top_k'): 
  if key in body:out[key]=body[key]
 if body.get('stop_sequences'):out['stop']=body['stop_sequences']
 if body.get('tools'):
  out['tools']=[]
  for tool in body['tools']:
   if tool.get('type') not in (None,'custom') or not tool.get('name'):raise ProtocolError('Only client-defined tools are supported')
   out['tools'].append({'type':'function','function':{'name':tool['name'],'description':tool.get('description',''),'parameters':tool.get('input_schema',{'type':'object'})}})
 choice=body.get('tool_choice',{})
 kind=choice.get('type') if isinstance(choice,dict) else None
 if kind in ('auto','none'):out['tool_choice']=kind
 elif kind=='any':out['tool_choice']='required'
 elif kind=='tool':out['tool_choice']={'type':'function','function':{'name':choice['name']}}
 elif kind is not None:raise ProtocolError('Unsupported tool_choice type')
 if isinstance(choice,dict) and choice.get('disable_parallel_tool_use'):out['parallel_tool_calls']=False
 return out

def count_request(body):
 # Native tokenizer route; keep Anthropic tool/result structure, never replay thinking.
 to_openai(body) # Validate the same supported subset as generation.
 out={k:copy.deepcopy(body[k]) for k in ('system','messages','tools','tool_choice') if k in body}
 out['model']=MODEL;out['thinking']={'type':'enabled','budget_tokens':1536}
 for msg in out['messages']:
  if isinstance(msg.get('content'),list):msg['content']=[b for b in msg['content'] if b.get('type') not in ('thinking','redacted_thinking')]
 return out

def prepare_request(body):
 to_openai(body)
 out=copy.deepcopy(body);out['model']=MODEL;out['stream']=False
 limit=body.get('max_tokens',16384)
 if not isinstance(limit,int) or isinstance(limit,bool) or limit<=0:raise ProtocolError('max_tokens must be a positive integer')
 out['max_tokens']=min(limit,32768)
 budget=min(1536,out['max_tokens']-256)
 out['thinking']={'type':'enabled','budget_tokens':budget} if budget>=1024 else {'type':'disabled'}
 out['preserve_thinking']=False;out['enable_thinking']=budget>=1024
 out.setdefault('temperature',0.3)
 for msg in out['messages']:
  if isinstance(msg.get('content'),list):msg['content']=[b for b in msg['content'] if b.get('type') not in ('thinking','redacted_thinking')]
 return out

def openai_view(message):
 blocks=message.get('content',[])
 content='\n'.join(b['text'] for b in blocks if b.get('type')=='text')
 calls=[{'id':b['id'],'type':'function','function':{'name':b['name'],'arguments':json.dumps(b['input'],ensure_ascii=False)}} for b in blocks if b.get('type')=='tool_use']
 usage=message.get('usage',{})
 return {'choices':[{'message':{'role':'assistant','content':content,'tool_calls':calls},'finish_reason':{'tool_use':'tool_calls','max_tokens':'length'}.get(message.get('stop_reason'),'stop')}],'usage':{'prompt_tokens':usage.get('input_tokens',0),'completion_tokens':usage.get('output_tokens',0),'completion_tokens_details':{'reasoning_tokens':(usage.get('output_tokens_details') or {}).get('thinking_tokens')}}}

def from_openai(result):
 choice=result['choices'][0];msg=choice['message'];content=[];identity='msg_bonsai_'+uuid.uuid4().hex
 if msg.get('content'):content.append({'type':'text','text':msg['content']})
 for call in msg.get('tool_calls') or []:
  try:args=json.loads(call['function'].get('arguments','{}'))
  except (ValueError,TypeError) as e:raise RuntimeError('Upstream produced malformed tool JSON') from e
  if not isinstance(args,dict):raise RuntimeError('Upstream tool arguments must be an object')
  content.append({'type':'tool_use','id':call.get('id') or 'toolu_'+uuid.uuid4().hex,'name':call['function']['name'],'input':args})
 usage=result.get('usage',{})
 return {'id':identity,'type':'message','role':'assistant','model':MODEL,'content':content,'stop_reason':{'tool_calls':'tool_use','length':'max_tokens','stop':'end_turn'}.get(choice.get('finish_reason'),'end_turn'),'stop_sequence':None,'usage':{'input_tokens':usage.get('prompt_tokens',0),'output_tokens':usage.get('completion_tokens',0)}}

def stream_events(message):
 initial={**message,'content':[],'stop_reason':None,'stop_sequence':None,'usage':{**message['usage'],'output_tokens':0}}
 yield 'message_start',{'type':'message_start','message':initial}
 for i,block in enumerate(message['content']):
  kind=block['type']
  start={'type':kind,**({'text':''} if kind=='text' else {'thinking':'','signature':''} if kind=='thinking' else {'id':block['id'],'name':block['name'],'input':{}})}
  yield 'content_block_start',{'type':'content_block_start','index':i,'content_block':start}
  delta={'type':'text_delta','text':block['text']} if kind=='text' else {'type':'thinking_delta','thinking':block['thinking']} if kind=='thinking' else {'type':'input_json_delta','partial_json':json.dumps(block['input'],ensure_ascii=False)}
  yield 'content_block_delta',{'type':'content_block_delta','index':i,'delta':delta}
  if kind=='thinking':yield 'content_block_delta',{'type':'content_block_delta','index':i,'delta':{'type':'signature_delta','signature':block['signature']}}
  yield 'content_block_stop',{'type':'content_block_stop','index':i}
 yield 'message_delta',{'type':'message_delta','delta':{'stop_reason':message['stop_reason'],'stop_sequence':message['stop_sequence']},'usage':{'output_tokens':message['usage']['output_tokens']}}
 yield 'message_stop',{'type':'message_stop'}
