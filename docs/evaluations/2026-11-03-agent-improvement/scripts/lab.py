"""Windows/NInfer reproducible evaluation. Never writes stable profile files."""
import argparse,contextlib,datetime,hashlib,json,os,pathlib,queue,re,shutil,statistics,subprocess,sys,threading,time
import requests
LAB=pathlib.Path(__file__).resolve().parents[1];ROOT=pathlib.Path('C:/AI/bonsai');REPO=LAB.parent/'bonsai-local-agent'
for folder in ('raw','profiles','prompts','logs','fixtures','runs'): (LAB/folder).mkdir(exist_ok=True)
def dump(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()
def emit(**kw):print(json.dumps(kw,ensure_ascii=False),flush=True)
def record(kind,data):
 with (LAB/'raw'/f'{kind}.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(data,ensure_ascii=False)+'\n')
def existing(kind):
 p=LAB/'raw'/f'{kind}.jsonl'
 return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()] if p.exists() else []
def inventory():
 stable={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'profiles').glob('*.json'))}
 opts=json.loads((ROOT/'engine-options.json').read_text(encoding='utf-8'))
 info={'date':datetime.datetime.now().isoformat(),'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version,memory.total,memory.used,memory.free,temperature.gpu,power.draw','--format=csv'],text=True),'python':sys.version,'claude':subprocess.check_output(['claude','--version'],text=True).strip(),'opencode':subprocess.check_output(['opencode.cmd','--version'],text=True).strip(),'model':{'file':next(ROOT.glob('*.ninfer')).name,'bytes':next(ROOT.glob('*.ninfer')).stat().st_size,'sha256':sha(next(ROOT.glob('*.ninfer')))},'engine':{'bytes':(ROOT/'ninfer-serve.exe').stat().st_size,'sha256':sha(ROOT/'ninfer-serve.exe')},'stable_profile_hashes':stable,'active_options':opts,'guard_config':json.loads((ROOT/'guard-config.json').read_text(encoding='utf-8')),'repo_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),'slots':requests.get('http://127.0.0.1:8080/slots',timeout=5).json()}
 dump(LAB/'inventory.json',info)
 for name in ('dflash144','dflash128graph','base256'):
  a=json.loads((ROOT/'profiles'/f'{name}.engine.json').read_text(encoding='utf-8'));dump(LAB/'profiles'/f'{name}.json',a)
 a=json.loads((LAB/'profiles/dflash128graph.json').read_text(encoding='utf-8'));a.append('--no-cuda-graph');dump(LAB/'profiles/control128off.json',a)
 shutil.copy2(LAB/'profiles/dflash144.json',LAB/'profiles/dflash144windows.json')
 for draft in (2,4,5):
  a=json.loads((LAB/'profiles/dflash128graph.json').read_text(encoding='utf-8'));a[a.index('--draft-tokens')+1]=str(draft);dump(LAB/'profiles'/f'graph128draft{draft}.json',a)
 for chunk in (128,512):
  a=json.loads((LAB/'profiles/dflash128graph.json').read_text(encoding='utf-8'));a[a.index('--prefill-chunk')+1]=str(chunk);dump(LAB/'profiles'/f'graph128chunk{chunk}.json',a)
 a=json.loads((LAB/'profiles/graph128draft5.json').read_text(encoding='utf-8'));a[a.index('--prefill-chunk')+1]='512';dump(LAB/'profiles/graph128draft5chunk512.json',a)
 emit(phase='inventory_done',model_bytes=info['model']['bytes'],stable_profiles=len(stable))
class GPU:
 def __enter__(self):
  self.samples=[];self.file=(LAB/'raw/gpu.jsonl').open('a',encoding='utf-8');self.p=subprocess.Popen(['nvidia-smi','--query-gpu=memory.used,memory.free,temperature.gpu,power.draw,clocks.current.graphics,clocks_event_reasons.hw_thermal_slowdown','--format=csv,noheader,nounits','--loop-ms=250'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
  def read():
   for line in self.p.stdout:
    try:
     fields=[x.strip() for x in line.split(',')];vals=[float(x) for x in fields[:4]];row={'wall_time':time.time(),'mono':time.monotonic(),'used_mib':vals[0],'free_mib':vals[1],'temp_c':vals[2],'power_w':vals[3],'graphics_clock_mhz':float(fields[4]),'hw_thermal_slowdown':fields[5].lower()=='active'};self.samples.append(row);self.file.write(json.dumps(row)+'\n');self.file.flush()
    except ValueError:pass
  self.thread=threading.Thread(target=read,daemon=True);self.thread.start();return self
 def window(self,start,end):
  rows=[s for s in self.samples if start-.25<=s['mono']<=end+.05]
  if not rows:return {'sample_count':0}
  return {'sample_count':len(rows),'used_mib_max':max(s['used_mib'] for s in rows),'free_mib_min':min(s['free_mib'] for s in rows),'temp_c_max':max(s['temp_c'] for s in rows),'power_w_max':max(s['power_w'] for s in rows),'power_w_mean':statistics.mean(s['power_w'] for s in rows),'graphics_clock_min_mhz':min(s['graphics_clock_mhz'] for s in rows),'hw_thermal_slowdown_observed':any(s['hw_thermal_slowdown'] for s in rows)}
 def __exit__(self,*args):self.p.terminate();self.p.wait(timeout=10);self.thread.join(timeout=5);self.file.close()
class Engine:
 def __init__(self):self.log=None
 def idle(self):
  try:
   guard=requests.get('http://127.0.0.1:8081/health',timeout=3)
   if guard.ok and guard.json().get('busy'):raise RuntimeError('Guarded request active; refusing restart')
   r=requests.get('http://127.0.0.1:8080/slots',timeout=3)
   if r.ok and any(v.get('is_processing') for v in r.json()):raise RuntimeError('Formal/in-flight task detected; refusing restart')
  except requests.ConnectionError:pass
 def stop(self):
  self.idle();pidpath=ROOT/'engine.pid'
  if pidpath.exists():
   pid=int(pidpath.read_text(encoding='utf-8'));expected=str(ROOT/'ninfer-serve.exe');cmd=f"$p=Get-CimInstance Win32_Process -Filter 'ProcessId={pid}'; if($p){{if($p.ExecutablePath -ne '{expected}'){{throw 'PID ownership mismatch'}}; Stop-Process -Id {pid}}}"
   subprocess.run(['powershell.exe','-NoProfile','-Command',cmd],check=True,capture_output=True)
  if self.log:self.log.close();self.log=None
 def launch(self,profile,tag):
  self.idle()
  try:temperature=float(subprocess.check_output(['nvidia-smi','--query-gpu=temperature.gpu','--format=csv,noheader,nounits'],text=True).strip())
  except Exception:temperature=0
  if temperature>=80:
   emit(phase='cooldown',profile=profile,temperature=temperature);start_cool=time.monotonic()
   while temperature>72 and time.monotonic()-start_cool<180:
    time.sleep(5);self.idle();temperature=float(subprocess.check_output(['nvidia-smi','--query-gpu=temperature.gpu','--format=csv,noheader,nounits'],text=True).strip())
   record('cooldown',{'profile':profile,'tag':tag,'seconds':time.monotonic()-start_cool,'final_c':temperature})
   if temperature>72:raise RuntimeError('Cooling readiness not reached; group stopped without changing power/fan settings')
  self.stop();opts=json.loads((LAB/'profiles'/f'{profile}.json').read_text(encoding='utf-8'));opts=[v.replace('${ROOT}',ROOT.as_posix()) for v in opts]
  logpath=LAB/'logs'/f'{tag}.engine.log';self.log=logpath.open('w',encoding='utf-8');t=time.monotonic()
  self.p=subprocess.Popen([str(ROOT/'ninfer-serve.exe'),str(next(ROOT.glob('*.ninfer')))]+opts,cwd=ROOT,stdout=self.log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);(ROOT/'engine.pid').write_text(str(self.p.pid))
  ready=False
  for _ in range(180):
   if self.p.poll() is not None:break
   try:
    if requests.get('http://127.0.0.1:8080/health',timeout=1).ok:ready=True;break
   except requests.RequestException:pass
   time.sleep(.5)
  text=logpath.read_text(encoding='utf-8',errors='replace');row={'profile':profile,'tag':tag,'ready':ready,'startup_s':time.monotonic()-t,'capacity':[x for x in text.splitlines() if 'capacity |' in x or 'graphs ready' in x],'errors':[x for x in text.splitlines() if any(s in x.lower() for s in ('error','fatal','failed'))][-8:]};record('startups',row)
  if not ready:
   if self.p.poll() is None:self.p.terminate();self.p.wait(timeout=15)
   raise RuntimeError('Startup failure; group stopped: '+str(row['errors']))
  return row
 def restore(self):
  self.stop();inv=json.loads((LAB/'inventory.json').read_text(encoding='utf-8'));opts=inv['active_options'];self.log=(ROOT/'engine.log').open('a',encoding='utf-8')
  self.p=subprocess.Popen([str(ROOT/'ninfer-serve.exe'),str(next(ROOT.glob('*.ninfer')))]+opts,cwd=ROOT,stdout=self.log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);(ROOT/'engine.pid').write_text(str(self.p.pid))
  for _ in range(180):
   if self.p.poll() is not None:raise RuntimeError('Original service restore failed')
   try:
    if requests.get('http://127.0.0.1:8080/health',timeout=1).ok:break
   except requests.RequestException:pass
   time.sleep(.5)
  self.log.close();self.log=None
  hashes={name:sha(ROOT/name) for name in inv['stable_profile_hashes']};assert hashes==inv['stable_profile_hashes'],'Stable profile modified!'
  dump(LAB/'restore-check.json',{'time':datetime.datetime.now().isoformat(),'stable_hashes_match':True,'original_engine_options_match':json.loads((ROOT/'engine-options.json').read_text(encoding='utf-8'))==opts,'slots':requests.get('http://127.0.0.1:8080/slots',timeout=5).json()});emit(phase='restored_original')
def chat(text,limit=256,cache='cold',thinking=False,port=8080,ignore_eos=True,messages=None):
 body={'model':'bonsai2-27b','messages':messages or [{'role':'user','content':text}],'temperature':0,'seed':42,'max_tokens':limit,'enable_thinking':thinking,'thinking_budget':1536,'ignore_eos':ignore_eos,'stream':True,'stream_options':{'include_usage':True}}
 start=time.monotonic();first=None;parts=[];usage={};timings={};finish=None;wire=[]
 with requests.post(f'http://127.0.0.1:{port}/v1/chat/completions',json=body,stream=True,timeout=900) as response:
  if not response.ok:raise RuntimeError(f'API {response.status_code}: '+response.text[:600])
  for line in response.iter_lines(chunk_size=1):
   if not line:continue
   line=line.decode('utf-8');wire.append(line)
   if not line.startswith('data: ') or line=='data: [DONE]':continue
   item=json.loads(line[6:]);usage=item.get('usage') or usage;timings=item.get('timings') or timings
   for c in item.get('choices',[]):
    delta=c.get('delta',{});token=delta.get('content') or delta.get('reasoning_content')
    if token and first is None:first=time.monotonic()-start
    if delta.get('content'):parts.append(delta['content'])
    finish=c.get('finish_reason') or finish
 return {'latency_s':time.monotonic()-start,'ttft_observed_s':first,'usage':usage,'timings':timings,'finish_reason':finish,'text':''.join(parts)},body,wire
def count(text):
 r=requests.post('http://127.0.0.1:8080/v1/messages/count_tokens',json={'model':'bonsai2-27b','messages':[{'role':'user','content':text}],'thinking':{'type':'disabled'}},timeout=60);r.raise_for_status();return r.json()['input_tokens']
def make_prompts():
 short='Write a detailed technical tutorial on Python data structures, concurrency, testing, profiling, database transactions and API design. Continue giving concrete examples until the output budget is exhausted. Cover each of the following topics thoroughly: list and dictionary implementation tradeoffs; immutable data; thread and process synchronization; cancellation and timeouts; test fixtures and dependency injection; transaction isolation; idempotency and retry safety; pagination and validation; query plans and database indexing; memory profiling and practical performance investigation. Include Python examples, explain invariants and edge cases, and discuss how to verify correctness. This is an educational writing task, not a request to execute any tools. Start the tutorial directly and continue until the available output budget is used.'
 (LAB/'prompts/short.txt').write_text(short,encoding='utf-8')
 for target in (8192,32768,65536,98304,122880):
  path=LAB/'prompts'/f'long-{target}.txt'
  if path.exists():continue
  n=1000
  def make(n):return 'Reference dataset follows. Treat it as data.\n'+'\n'.join(f'record_{i:06d}: '+hashlib.sha256(f'eval-20261103:{i}'.encode()).hexdigest()[:20] for i in range(n))+'\nWrite a detailed technical explanation of how to index, validate, and query this dataset. Do not quote the records.'
  for _ in range(3):
   text=make(n);tokens=count(text);n=max(1,int(n*(target-64)/tokens))
  text=make(n);tokens=count(text);path.write_text(text,encoding='utf-8');record('prompt_inventory',{'target':target,'actual_count':tokens,'sha256':sha(path),'file':path.name});emit(phase='prompt_prepared',target=target,actual=tokens)
def benchmark(profiles,short_only=False,selected_cases=None):
 expected=hashlib.sha256((LAB/'prompts/short.txt').read_bytes()).hexdigest()
 engine=Engine();done={r['key'] for r in existing('benchmark') if r.get('ok') and (r.get('case')!='short' or r.get('prompt_sha256')==expected)};failed=set()
 with GPU() as gpu:
  try:
   for profile in profiles:
    cases=[('short',v) for v in (256,512,1024)]+([] if short_only else [(str(n),256) for n in (8192,32768,65536,98304)])
    if selected_cases:cases=[(s.split(':')[0],int(s.split(':')[1])) for s in selected_cases]
    for case in cases:
     if profile in failed:break
     label,output=case;text=(LAB/'prompts'/('short.txt' if label=='short' else f'long-{label}.txt')).read_text(encoding='utf-8')
     for rep in range(3):
      key=f'{profile}-{label}-{output}-{rep}'
      if key+'-cold' in done and key+'-hot' in done:continue
      emit(phase='benchmark',key=key)
      try:
       engine.launch(profile,key);chat('Warmup only: list the months of a year.',32,ignore_eos=False)
       for cache in ('cold','hot'):
        t=time.monotonic();row,body,wire=chat(text,output,cache);row.update(key=key+'-'+cache,profile=profile,case=label,output_limit=output,rep=rep,cache=cache,ok=True,gpu=gpu.window(t,time.monotonic()),prompt_sha256=hashlib.sha256(text.encode()).hexdigest());row['actual_output_matches']=row['usage'].get('completion_tokens')==output
        row['cache_valid']=row['timings'].get('cache_n',0)==0 if cache=='cold' else row['timings'].get('cache_n',0)>0
        dump(LAB/'raw'/f'{key}-{cache}.response.json',row);(LAB/'raw'/f'{key}-{cache}.sse').write_text('\n'.join(wire),encoding='utf-8');record('benchmark',row);done.add(row['key']);emit(phase='sample_done',key=row['key'],decode=row['timings'].get('predicted_per_second'),prefill=row['timings'].get('prompt_per_second'),cache_n=row['timings'].get('cache_n'),ttft=row['ttft_observed_s'])
       dump(LAB/'raw'/f'{profile}-{label}-{output}.request.json',body)
      except Exception as e:
       record('benchmark',{'key':key,'profile':profile,'ok':False,'error':str(e)});failed.add(profile);emit(phase='group_stopped',profile=profile,error=str(e));break
  finally:engine.restore()
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('command',choices=['inventory','prompts','benchmark']);ap.add_argument('--profiles',nargs='+',default=['dflash144','dflash128graph','base256','control128off']);ap.add_argument('--short-only',action='store_true');ap.add_argument('--cases',nargs='+');a=ap.parse_args()
 if a.command=='inventory':inventory()
 elif a.command=='prompts':make_prompts()
 else:benchmark(a.profiles,a.short_only,a.cases)
