"""Apply only a measured guidance winner; never switch stable engine profiles."""
import argparse,ast,datetime,json,os,pathlib,tempfile,time
import requests
from lab import LAB,ROOT,REPO,existing,dump,sha
from report import rows,summary
from guidance_versions import GENERIC_GUIDANCE,WINDOWS_GUIDANCE

def run(apply=False):
 baseline=list({x['key']:x for x in rows(LAB/'baseline/coding.jsonl')+rows(LAB/'baseline/coding-audit.jsonl')}.values());baseline=[x for x in baseline if x['profile']=='dflash144']
 current=list({x['key']:x for x in existing('coding')+existing('coding-audit')}.values())
 groups={'baseline':baseline,'generic':[x for x in current if x['profile']=='dflash144'],'windows':[x for x in current if x['profile']=='dflash144windows']}
 stats={k:summary(v) for k,v in groups.items()};best='baseline'
 for name in ('generic','windows'):
  s=stats[name];b=stats[best]
  assert len(groups[name])==9,f'Incomplete guidance records: {name}'
  if s['measured']!=9 or s['not_tested']:continue
  if s['passes']>b['passes'] or (s['passes']==b['passes'] and s['passes'] and s['seconds_per_success']<=.9*b['seconds_per_success']):best=name
 decision={'decided_at':datetime.datetime.now().astimezone().isoformat(),'selected':best,'criterion':'Completion count first; tied variants need >=10% lower failure-inclusive seconds/success to replace current selection','statistics':stats,'small_sample_and_adaptive_guidance_not_heldout_certification':True,'engine_profile':'dflash144 unchanged','applied':False}
 if apply:
  previous=LAB/'guidance-decision.json'
  if previous.exists() and json.loads(previous.read_text(encoding='utf-8')).get('applied'):raise RuntimeError('Guidance was already applied; do not mutate a finalized study')
  for _ in range(3):
   assert not requests.get('http://127.0.0.1:8081/health',timeout=5).json().get('busy')
   assert not any(s.get('is_processing') for s in requests.get('http://127.0.0.1:8080/slots',timeout=5).json());time.sleep(.25)
  snapshot=LAB/'tested-runtime';snapshot.mkdir(exist_ok=True)
  for name in ('bonsai_proxy.py','claude_launch.py','anthropic_bridge.py'):
   p=snapshot/name
   if not p.exists():p.write_bytes((ROOT/name).read_bytes())
  source=REPO/'runtime/claude_launch.py';text=source.read_text(encoding='utf-8')
  guidance=WINDOWS_GUIDANCE if best=='windows' else GENERIC_GUIDANCE
  node=next(n for n in ast.parse(text).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CODING_GUIDANCE' for t in n.targets))
  if ast.literal_eval(node.value)!=guidance:
   lines=text.splitlines(keepends=True);lines[node.lineno-1:node.end_lineno]=['CODING_GUIDANCE='+repr(guidance)+'\n'];text=''.join(lines)
  if best=='baseline':
   text=text.replace("parser=argparse.ArgumentParser();parser.add_argument('--profile'","parser=argparse.ArgumentParser();parser.add_argument('--edit-first',action='store_true');parser.add_argument('--profile'",1)
   text=text.replace(" if not any(x=='--append-system-prompt'"," if args.edit_first and not any(x=='--append-system-prompt'",1)
  source.write_text(text,encoding='utf-8')
  fd,tmp=tempfile.mkstemp(prefix='claude-launch-',suffix='.tmp',dir=ROOT)
  try:
   with os.fdopen(fd,'wb') as stream:stream.write(source.read_bytes())
   os.replace(tmp,ROOT/'claude_launch.py')
  finally:
   if pathlib.Path(tmp).exists():pathlib.Path(tmp).unlink()
  decision.update(applied=True,launcher_sha256=sha(ROOT/'claude_launch.py'),default_guidance=best!='baseline',bridge_unchanged=True)
 dump(LAB/'guidance-decision.json',decision);print(json.dumps(decision,ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');run(p.parse_args().apply)
