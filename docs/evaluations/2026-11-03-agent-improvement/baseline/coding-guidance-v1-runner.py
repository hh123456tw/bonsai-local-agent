import pathlib,sys,os,json,subprocess,shutil,time,collections
from lab import LAB,ROOT,Engine,GPU,dump,sha,record,existing,emit
sys.path.insert(0,str(ROOT));from claude_launch import environment,CODING_GUIDANCE
def run(profiles,reps,tasks=('bug','feature','refactor'),offset=0):
 engine=Engine();done={r['key'] for r in existing('coding')};order=[];failed_profiles=set()
 # Interleave arms, alternating their order to reduce thermal/order bias.
 for rep in range(offset,offset+reps):
  for profile in (profiles if rep%2==0 else list(reversed(profiles))):order.append((rep,profile))
 with GPU() as gpu:
  try:
   for rep,profile in order:
    pending=[task for task in tasks if f'{profile}-{task}-{rep}' not in done]
    if not pending:continue
    if profile in failed_profiles:
     for task in pending:record('coding',{'key':f'{profile}-{task}-{rep}','profile':profile,'task':task,'rep':rep,'passed':False,'not_tested':True,'error':'Profile previously failed startup; no repeated attempt'})
     continue
    try:engine.launch(profile,f'coding-{profile}-{rep}')
    except Exception as e:
     failed_profiles.add(profile)
     for task in pending:record('coding',{'key':f'{profile}-{task}-{rep}','profile':profile,'task':task,'rep':rep,'passed':False,'not_tested':True,'error':str(e)})
     continue
    for task in pending:
     key=f'{profile}-{task}-{rep}';project=LAB/'runs'/key;start=LAB/'fixtures'/task/'start'
     if project.exists():raise RuntimeError('Refuse to reuse dirty fixture: '+str(project))
     shutil.copytree(start,project,ignore=shutil.ignore_patterns('__pycache__'));prompt=(LAB/'fixtures'/task/'prompt.txt').read_text(encoding='utf-8');guard_before=len((ROOT/'guard-events.jsonl').read_text().splitlines())
     env=environment('dflash128graph' if profile=='graph128draft5' else profile);env['CLAUDE_CONFIG_DIR']=str(LAB/'claude-home');env['PYTHONDONTWRITEBYTECODE']='1'
     args=[shutil.which('claude'),'--bare','--setting-sources','','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--model','bonsai2-27b','--tools','Read,Write,Edit,Bash,Glob,Grep','--allowedTools','Read,Write,Edit,Glob,Grep,Bash(python *)','--no-session-persistence','--output-format','stream-json','--verbose','-p',prompt]
     args[1:1]=['--append-system-prompt',CODING_GUIDANCE]
     row={'key':key,'profile':profile,'task':task,'rep':rep,'prompt_sha256':sha(LAB/'fixtures'/task/'prompt.txt'),'guidance':CODING_GUIDANCE,'guidance_sha256':__import__('hashlib').sha256(CODING_GUIDANCE.encode()).hexdigest(),'input_manifest':json.loads((LAB/'fixtures'/task/'manifest.json').read_text()),'passed':False};emit(phase='coding_start',key=key);t=time.monotonic();stage='agent';child=None
     try:
      with (LAB/'raw'/f'{key}.claude.jsonl').open('w',encoding='utf-8') as out,(LAB/'raw'/f'{key}.stderr').open('w',encoding='utf-8') as err:
       child=subprocess.Popen(args,cwd=project,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW);row['cli_exit']=child.wait(timeout=480)
      row['agent_latency_s']=time.monotonic()-t
      events=[json.loads(s) for s in (LAB/'raw'/f'{key}.claude.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
      calls=[b for e in events if e.get('type')=='assistant' for b in e.get('message',{}).get('content',[]) if b.get('type')=='tool_use'];results=[b for e in events if e.get('type')=='user' for b in e.get('message',{}).get('content',[]) if b.get('type')=='tool_result']
      sigs=[c['name']+json.dumps({k:v for k,v in c.get('input',{}).items() if k not in ('description','timeout')},sort_keys=True) for c in calls]
      terminal=next((e for e in events if e.get('type')=='result'),{})
      row.update(tool_calls=len(calls),consecutive_repeat_count=sum(a==b for a,b in zip(sigs,sigs[1:])),nonconsecutive_duplicate_count=sum(n-1 for n in collections.Counter(sigs).values() if n>1),tool_errors=sum(bool(b.get('is_error')) for b in results),permission_denials=len(terminal.get('permission_denials',[])),usage=terminal.get('usage',{}),modelUsage=terminal.get('modelUsage',{}),client_success=not terminal.get('is_error',True),agent_ran_tests=any(c['name']=='Bash' and ('unittest' in c.get('input',{}).get('command','') or 'pytest' in c.get('input',{}).get('command','')) for c in calls),acceptance_sha256=sha(LAB/'fixtures'/task/'acceptance.py'))
      guard=[json.loads(s) for s in (ROOT/'guard-events.jsonl').read_text().splitlines()[guard_before:]];row['guard_recoveries']=sum(e['kind']=='recovery' for e in guard);row['guard_stops']=sum(e['kind'].endswith('stop') for e in guard)
      stage='external_acceptance';external=subprocess.run([sys.executable,str(LAB/'scripts/accept.py'),str(project),str(LAB/'fixtures'/task/'acceptance.py')],cwd=project,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},timeout=30)
      (LAB/'raw'/f'{key}.acceptance.txt').write_text(external.stdout+external.stderr,encoding='utf-8');row['acceptance']=json.loads(external.stdout.strip().splitlines()[-1]) if external.stdout.strip() else {'passed':False,'error':external.stderr[:300]}
      stage='public_tests';public=subprocess.run([sys.executable,'-m','unittest','discover'],cwd=project,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},timeout=30);(LAB/'raw'/f'{key}.public-tests.txt').write_text(public.stdout+public.stderr,encoding='utf-8');row['public_tests_passed']=public.returncode==0
      row['protected_files_changed']=[name for name in ('test_existing.py','README.md') if not (project/name).exists() or sha(project/name)!=row['input_manifest'][name]]
      row['changed_files']=[str(p.relative_to(project)) for p in project.rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.claude' not in p.parts and (str(p.relative_to(project)).replace('\\','/') not in row['input_manifest'] or sha(p)!=row['input_manifest'].get(str(p.relative_to(project)).replace('\\','/')))]
      row['passed']=external.returncode==0 and public.returncode==0 and not row['protected_files_changed'] and row['cli_exit']==0 and row['agent_ran_tests']
     except subprocess.TimeoutExpired:
      if child is not None and child.poll() is None:subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True)
      row['error']=f'Supervised timeout during {stage}; no completed/unowned CLI PID terminated'
      if stage=='agent':row['agent_latency_s']=time.monotonic()-t
      # The engine may finish an in-flight request after client disconnects.
      for _ in range(60):
       try:engine.idle();break
       except RuntimeError:time.sleep(1)
     except Exception as e:row['error']=str(e)
     row['gpu']=gpu.window(t,time.monotonic());row['evaluation_total_s']=time.monotonic()-t;record('coding',row);dump(LAB/'raw'/f'{key}.summary.json',row);emit(phase='coding_done',key=key,passed=row['passed'],seconds=row.get('agent_latency_s'),tools=row.get('tool_calls'),errors=row.get('tool_errors'));done.add(key)
  finally:engine.restore()
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--profiles',nargs='+',default=['dflash128graph','dflash144']);p.add_argument('--reps',type=int,default=3);p.add_argument('--tasks',nargs='+',default=['bug','feature','refactor']);p.add_argument('--rep-offset',type=int,default=0);a=p.parse_args();run(a.profiles,a.reps,a.tasks,a.rep_offset)
