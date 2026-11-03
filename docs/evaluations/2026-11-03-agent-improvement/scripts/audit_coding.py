"""Recover measured diagnostics for timed-out clients; never turn a timeout into success."""
import json,pathlib,re,datetime,collections,subprocess,sys,os
from lab import LAB,ROOT,existing,record,sha,dump
def audit():
 done={x['key'] for x in existing('coding-audit') if x.get('audit_version',0)>=3};guards=[json.loads(s) for s in (ROOT/'guard-events.jsonl').read_text(encoding='utf-8').splitlines()]
 for original in existing('coding'):
  if original['key'] in done:continue
  row=dict(original);key=row['key'];path=LAB/'raw'/f'{key}.claude.jsonl'
  if not path.exists():continue
  events=[]
  for line in path.read_text(encoding='utf-8',errors='replace').splitlines():
   try:events.append(json.loads(line))
   except json.JSONDecodeError:pass
  calls={}
  for e in events:
   if e.get('type')=='assistant':
    for b in e.get('message',{}).get('content',[]):
     if b.get('type')=='tool_use':calls[b['id']]=b
  calls=list(calls.values());sigs=[b['name']+json.dumps({k:v for k,v in b.get('input',{}).items() if k not in ('description','timeout')},sort_keys=True) for b in calls]
  results=[b for e in events if e.get('type')=='user' for b in e.get('message',{}).get('content',[]) if b.get('type')=='tool_result']
  row.update(tool_calls=len(calls),consecutive_repeat_count=sum(a==b for a,b in zip(sigs,sigs[1:])),nonconsecutive_duplicate_count=sum(n-1 for n in collections.Counter(sigs).values() if n>1),tool_errors=sum(bool(x.get('is_error')) for x in results),agent_ran_tests=any(b['name']=='Bash' and any(word in b.get('input',{}).get('command','') for word in ('unittest','pytest')) for b in calls))
  start=path.stat().st_ctime;end=start+row.get('evaluation_total_s',row.get('agent_latency_s',0));window=[e for e in guards if start-.05<=e['time']<=end+.05];row['guard_recoveries']=sum(e['kind']=='recovery' for e in window);row['guard_stops']=sum(e['kind'].endswith('stop') for e in window);row['guard_audit_window']='Windows file creation time plus measured evaluation duration; serial test jobs, 50ms boundary tolerance'
  engine_log=LAB/'logs'/f'coding-{row["profile"]}-{row["rep"]}.engine.log';totals={'completed_requests':0,'input_tokens_total':0,'cached_input_tokens':0,'output_tokens':0,'max_request_prompt_tokens':0,'max_request_output_tokens':0}
  if engine_log.exists():
   for line in engine_log.read_text(encoding='utf-8',errors='replace').splitlines():
    if ' done | anthropic |' not in line:continue
    try:stamp=datetime.datetime.strptime(line[:23],'%Y-%m-%d %H:%M:%S.%f').timestamp()
    except ValueError:continue
    if not start-.05<=stamp<=end+.05:continue
    m=re.search(r'prompt ([\d,]+) \| output ([\d,]+) \| cache ([\d,]+)',line)
    if m:
     p,o,c=(int(v.replace(',','')) for v in m.groups());totals['completed_requests']+=1;totals['input_tokens_total']+=p;totals['cached_input_tokens']+=c;totals['output_tokens']+=o;totals['max_request_prompt_tokens']=max(totals['max_request_prompt_tokens'],p);totals['max_request_output_tokens']=max(totals['max_request_output_tokens'],o)
  row['engine_usage']=totals
  row['guard_tool_rejections']=sum(e['kind']=='tool_output_rejected' for e in window);row['guard_output_truncations']=sum(e['kind']=='output_truncated' for e in window)
  row['client_api_retry_events']=sum(e.get('type')=='system' and e.get('subtype')=='api_retry' for e in events)
  if not row.get('usage'):
   row['usage']={'input_tokens':totals['input_tokens_total']-totals['cached_input_tokens'],'cache_read_input_tokens':totals['cached_input_tokens'],'output_tokens':totals['output_tokens']};row['usage_source']='engine completed-request logs; includes retries and post-disconnect drain, not an invented CLI terminal summary'
  project=LAB/'runs'/key;row['protected_files_changed']=[n for n in ('README.md','test_existing.py') if not (project/n).exists() or sha(project/n)!=row['input_manifest'][n]]
  if 'acceptance' not in row:
   env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
   try:
    p=subprocess.run([sys.executable,str(LAB/'scripts/accept.py'),str(project),str(LAB/'fixtures'/row['task']/'acceptance.py')],cwd=project,capture_output=True,text=True,env=env,timeout=30);(LAB/'raw'/f'{key}.post-timeout-acceptance.txt').write_text(p.stdout+p.stderr,encoding='utf-8');row['acceptance']=json.loads(p.stdout.strip().splitlines()[-1]) if p.stdout.strip() else {'passed':False,'error':p.stderr[:200]}
    p=subprocess.run([sys.executable,'-m','unittest','discover'],cwd=project,capture_output=True,text=True,env=env,timeout=30);row['public_tests_passed']=p.returncode==0;(LAB/'raw'/f'{key}.post-timeout-public-tests.txt').write_text(p.stdout+p.stderr,encoding='utf-8');row['post_timeout_grade']=True
   except subprocess.TimeoutExpired:row['acceptance']={'passed':False,'error':'post-timeout validation exceeded30s'}
  row['audit_version']=3;record('coding-audit',row);dump(LAB/'raw'/f'{key}.audited.json',row)
 print('Audited',len(existing('coding-audit')),'completed coding runs, including timeout diagnostics.')
if __name__=='__main__':audit()
