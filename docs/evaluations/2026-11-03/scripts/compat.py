"""Live tests through port8081 only; no additional harness installation."""
import concurrent.futures,json,os,pathlib,shutil,subprocess,sys,time
import requests
from lab import LAB,ROOT,Engine,GPU,dump,emit
RESULT={}
def post(path,body):
 t=time.monotonic();r=requests.post('http://127.0.0.1:8081'+path,json=body,timeout=900);return r.status_code,r.json(),time.monotonic()-t
def run():
 out=RESULT;out.update(date='2026-11-03',new_harness_installed=False);out['bridge_health']=requests.get('http://127.0.0.1:8081/health',timeout=5).json();assert out['bridge_health']['max_tool_calls'] is None
 out['opencode_steps']={p.name:json.loads(p.read_text())['agents']['build'].get('steps') for p in (ROOT/'profiles').glob('*.opencode.json')};out['models_status']=requests.get('http://127.0.0.1:8081/v1/models',timeout=5).status_code
 count_status,count_body,_=post('/v1/messages/count_tokens',{'model':'bonsai2-27b','messages':[{'role':'user','content':'Test token count.'}]});out['count_tokens']={'status':count_status,'result':count_body};assert count_status==200 and count_body['input_tokens']>0
 tools=[{'type':'function','function':{'name':'lookup','description':'Read a key from a test dictionary','parameters':{'type':'object','properties':{'key':{'type':'string'}},'required':['key']}}}]
 body={'model':'bonsai2-27b','messages':[{'role':'user','content':'Use lookup with key answer, then report its exact value.'}],'tools':tools,'max_tokens':2048,'temperature':0}
 status,reply,wall=post('/v1/chat/completions',body);msg=reply['choices'][0]['message'];calls=msg.get('tool_calls') or [];assert status==200 and calls
 for c in calls:assert c['function']['name']=='lookup' and json.loads(c['function']['arguments'])=={'key':'answer'}
 body['messages'].append(msg)
 for c in calls:body['messages'].append({'role':'tool','tool_call_id':c['id'],'content':'{"answer":"TEAL-573921"}'})
 s2,r2,w2=post('/v1/chat/completions',body);assert 'TEAL-573921' in (r2['choices'][0]['message'].get('content') or '')
 out['openai_tool_roundtrip']={'ok':True,'seconds':[wall,w2]};dump(LAB/'raw/compat-openai.json',{'first':reply,'second':r2})
 bodya={'model':'bonsai2-27b','max_tokens':2048,'messages':[{'role':'user','content':'Use lookup with key answer, then report its exact value.'}],'tools':[{'name':'lookup','description':'Read a key from a test dictionary','input_schema':tools[0]['function']['parameters']}],'temperature':0}
 s,a,w=post('/v1/messages?beta=true',bodya);uses=[b for b in a['content'] if b['type']=='tool_use'];assert s==200 and uses
 assert all(c['name']=='lookup' and c['input']=={'key':'answer'} for c in uses)
 bodya['messages'].append({'role':'assistant','content':a['content']});bodya['messages'].append({'role':'user','content':[{'type':'tool_result','tool_use_id':c['id'],'content':'{"answer":"TEAL-573921"}'} for c in uses]});s,a2,w2=post('/v1/messages',bodya);assert 'TEAL-573921' in ''.join(b.get('text','') for b in a2['content'])
 out['anthropic_tool_roundtrip']={'ok':True,'seconds':[w,w2]};dump(LAB/'raw/compat-anthropic.json',{'first':a,'second':a2})
 streams={}
 for protocol,path,b in [('openai','/v1/chat/completions',{'model':'bonsai2-27b','max_tokens':2048,'messages':[{'role':'user','content':'請只回答這四個繁體中文字：測試完成'}],'stream':True}),('anthropic','/v1/messages',{'model':'bonsai2-27b','max_tokens':2048,'messages':[{'role':'user','content':'請只回答這四個繁體中文字：測試完成'}],'stream':True})]:
  t=time.monotonic();first=None;lines=[]
  with requests.post('http://127.0.0.1:8081'+path,json=b,stream=True,timeout=900) as r:
   r.raise_for_status()
   for line in r.iter_lines(chunk_size=1):
    if line:
     if first is None:first=time.monotonic()-t
     lines.append(line.decode('utf-8'))
  text='\n'.join(lines);assert ('[DONE]' in text if protocol=='openai' else 'event: message_stop' in text)
  parsed=[json.loads(line[6:]) for line in lines if line.startswith('data: ') and line!='data: [DONE]'];pieces=[]
  for item in parsed:
   if protocol=='openai':pieces.extend(c.get('delta',{}).get('content','') for c in item.get('choices',[]))
   elif item.get('type')=='content_block_delta' and item.get('delta',{}).get('type')=='text_delta':pieces.append(item['delta']['text'])
  (LAB/'raw'/f'compat-{protocol}.sse').write_text(text,encoding='utf-8');streams[protocol]={'complete':True,'first_sse_line_s':first,'total_s':time.monotonic()-t,'buffered_by_bridge':True,'utf8_json_parsed':True,'expected_chinese_text_present':'測試完成' in ''.join(pieces)}
 out['streaming']=streams
 s,small,_=post('/v1/chat/completions',{'model':'bonsai2-27b','max_tokens':16,'enable_thinking':False,'messages':[{'role':'user','content':'Explain Python unit testing in detail.'}]});out['openai_small_output_cap']={'status':s,'requested_max_tokens':16,'requested_thinking':False,'actual_usage':small.get('usage',{}),'cap_honored':small.get('usage',{}).get('completion_tokens',0)<=16};dump(LAB/'raw/compat-openai-small-cap.json',small)
 s,small,_=post('/v1/messages',{'model':'bonsai2-27b','max_tokens':16,'messages':[{'role':'user','content':'Explain Python unit testing in detail.'}]});out['anthropic_small_output_cap']={'status':s,'requested_max_tokens':16,'actual_usage':small.get('usage',{}),'cap_honored':small.get('usage',{}).get('output_tokens',0)<=16};dump(LAB/'raw/compat-anthropic-small-cap.json',small)
 t=time.monotonic()
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
  futures=[executor.submit(post,'/v1/messages',{'model':'bonsai2-27b','max_tokens':1024,'messages':[{'role':'user','content':f'Explain Python testing briefly. Request {i}.'}]}) for i in range(2)]
  values=[f.result() for f in futures]
 out['concurrency']={'requests':2,'statuses':[v[0] for v in values],'client_latencies':[v[2] for v in values],'total_s':time.monotonic()-t,'implementation':'bridge LOCK serializes generation, native max-concurrency1; not a fair/cancelable scheduler'}
 r=requests.post('http://127.0.0.1:8081/v1/responses',json={'model':'bonsai2-27b','input':'Hello'},timeout=5);out['responses_endpoint_status']=r.status_code
 # Actual OpenCode task in an independent fresh fixture, with private server.
 project=LAB/'runs/opencode-compat-bug';shutil.copytree(LAB/'fixtures/bug/start',project,ignore=shutil.ignore_patterns('__pycache__'));env=os.environ.copy();env.update(OPENCODE_CONFIG=str(ROOT/'profiles/dflash144.opencode.json'),XDG_CONFIG_HOME=str(ROOT/'config'));env.pop('OPENCODE_CONFIG_CONTENT',None)
 agents=subprocess.run(['opencode.cmd','api','--standalone','agent.list'],cwd=project,env=env,capture_output=True,text=True,encoding='utf-8',timeout=30);agents.check_returncode();build=next(x for x in json.loads(agents.stdout)['data'] if x['id']=='build');out['opencode_effective_build']={'steps_present':'steps' in build,'steps':build.get('steps')};assert 'steps' not in build
 t=time.monotonic()
 with (LAB/'raw/opencode-compat.jsonl').open('w',encoding='utf-8') as stdout,(LAB/'raw/opencode-compat.stderr').open('w',encoding='utf-8') as stderr:
  p=subprocess.run(['opencode.cmd','run','--standalone','--model','bonsai/bonsai2-27b','--agent','build','--format','json','--auto',(LAB/'fixtures/bug/prompt.txt').read_text(encoding='utf-8')],cwd=project,env=env,stdout=stdout,stderr=stderr,timeout=240)
 wall=time.monotonic()-t;accept=subprocess.run([sys.executable,str(LAB/'scripts/accept.py'),str(project),str(LAB/'fixtures/bug/acceptance.py')],cwd=project,capture_output=True,text=True,timeout=30);(LAB/'raw/opencode-compat.acceptance.txt').write_text(accept.stdout+accept.stderr,encoding='utf-8')
 out['opencode_actual_task']={'seconds':wall,'exit_code':p.returncode,'external_pass':accept.returncode==0,'protected_tests_unchanged':(project/'test_existing.py').read_bytes()==(LAB/'fixtures/bug/start/test_existing.py').read_bytes()}
 dump(LAB/'compatibility.json',out);emit(phase='compatibility_done',**out)
if __name__=='__main__':
 try:run()
 except Exception as e:
  RESULT['failed']=True;RESULT['error']=str(e);dump(LAB/'compatibility.json',RESULT);raise
