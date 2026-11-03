"""Real 8081 client budgets, thought toggles, tools and UTF-8 SSE."""
import json,time,requests
from lab import LAB,dump
BASE='http://127.0.0.1:8081';results=[]
def post(body,path='/v1/chat/completions'):
 t=time.monotonic();r=requests.post(BASE+path,json=body,timeout=120);return r.status_code,r.json(),time.monotonic()-t
def req(**fields):return {'model':'bonsai2-27b','messages':[{'role':'user','content':'Explain Python unit testing in detail.'}],'temperature':0,**fields}
def run():
 for rep in range(3):
  s,b,w=post(req(max_tokens=16,enable_thinking=False));assert s==200 and b['usage']['completion_tokens']<=16 and b['usage']['completion_tokens_details']['reasoning_tokens']==0
  results.append({'case':'cap16_disabled','rep':rep,'status':s,'seconds':w,'usage':b['usage']})
 for fields in ({'max_completion_tokens':16},{'max_tokens':2048,'enable_thinking':True,'thinking_budget':1024}):
  s,b,w=post(req(**fields))
  if s!=200:
   dump(LAB/'raw/explicit-budget-rejected.json',{'requested':fields,'status':s,'response':b});raise RuntimeError(f'Explicit budget returned {s}: {b}')
  assert b['usage']['completion_tokens']<=fields.get('max_tokens',fields.get('max_completion_tokens'))
  results.append({'case':'alias_or_explicit_thought','requested':fields,'status':s,'seconds':w,'usage':b['usage']})
 for fields in ({'max_tokens':16,'enable_thinking':True},{'max_tokens':16,'max_completion_tokens':32},{'max_tokens':0},{'max_tokens':32769}):
  s,b,w=post(req(**fields));assert s==400 and 'message' in b['error'];results.append({'case':'invalid_budget','requested':fields,'status':s,'error':b['error']})
 tools=[{'type':'function','function':{'name':'lookup','description':'Look up a test value','parameters':{'type':'object','properties':{'key':{'type':'string'}},'required':['key']}}}]
 b=req(max_tokens=256,enable_thinking=False,tools=tools);b['messages']=[{'role':'user','content':'Use lookup with key answer, then report its exact value.'}]
 s,r,w=post(b);assert s==200;msg=r['choices'][0]['message'];calls=msg.get('tool_calls') or [];assert calls and all(c['function']['name']=='lookup' and json.loads(c['function']['arguments'])=={'key':'answer'} for c in calls)
 results.append({'case':'tool_call','status':s,'seconds':w,'usage':r['usage']});b['messages'].append(msg)
 for c in calls:b['messages'].append({'role':'tool','tool_call_id':c['id'],'content':'{"answer":"TEAL-573921"}'})
 s,r,w=post(b);assert s==200 and 'TEAL-573921' in r['choices'][0]['message']['content'];results.append({'case':'tool_result','status':s,'seconds':w,'usage':r['usage']})
 tiny=req(max_tokens=1,enable_thinking=False,tools=tools);tiny['messages']=[{'role':'user','content':'Use lookup with key answer.'}]
 s,r,w=post(tiny)
 if s==200:assert not r['choices'][0]['message'].get('tool_calls') and r['choices'][0]['finish_reason']=='length'
 else:assert s in (400,502)
 results.append({'case':'too_small_for_tool_no_partial_delivery','status':s,'response':r})
 b=req(max_tokens=16,enable_thinking=False,stream=True);b['messages']=[{'role':'user','content':'請只回答：測試完成'}]
 t=time.monotonic();lines=[]
 with requests.post(BASE+'/v1/chat/completions',json=b,stream=True,timeout=120) as r:
  r.raise_for_status()
  for raw in r.iter_lines():
   if raw:lines.append(raw.decode('utf-8'))
 assert lines[-1]=='data: [DONE]';data=[json.loads(s[6:]) for s in lines if s.startswith('data: ') and s!='data: [DONE]'];assert data[-1]['usage']['completion_tokens']<=16
 assert '測試完成' in ''.join(c.get('delta',{}).get('content','') for row in data for c in row.get('choices',[]))
 results.append({'case':'utf8_sse','status':200,'seconds':time.monotonic()-t,'usage':data[-1]['usage']})
 (LAB/'raw/budget-stream.sse').write_text('\n'.join(lines),encoding='utf-8')
 s,b,w=post({'model':'bonsai2-27b','max_tokens':16,'messages':[{'role':'user','content':'Explain Python unit testing in detail.'}]},'/v1/messages')
 assert s==200 and b['usage']['output_tokens']<=16;results.append({'case':'anthropic_cap16','status':s,'seconds':w,'usage':b['usage']})
 dump(LAB/'api-validation.json',{'passed':True,'cases':results});print(json.dumps({'passed':True,'cases':len(results)}))
if __name__=='__main__':
 try:run()
 except Exception as e:dump(LAB/'api-validation.json',{'passed':False,'error':str(e),'cases':results});raise
