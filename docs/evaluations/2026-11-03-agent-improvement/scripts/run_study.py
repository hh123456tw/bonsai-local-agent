"""One serial controller: daily regression, then gated experimental Draft5."""
import datetime,json,pathlib,subprocess,sys
from lab import LAB,ROOT,REPO,dump,sha,existing
HERE=pathlib.Path(__file__).resolve().parent
OLD=LAB.parent/'bonsai-evaluation-20261103'

def phase(name,args):
 print(json.dumps({'phase':name,'status':'start'}),flush=True)
 with (LAB/'logs'/f'{name}.stdout').open('w',encoding='utf-8') as out,(LAB/'logs'/f'{name}.stderr').open('w',encoding='utf-8') as err:
  r=subprocess.run([sys.executable,*map(str,args)],stdout=out,stderr=err)
 item={'phase':name,'exit':r.returncode,'time':datetime.datetime.now().astimezone().isoformat()}
 with (LAB/'raw/phases.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(item)+'\n')
 print(json.dumps(item),flush=True)
 if r.returncode:raise RuntimeError('Phase failed; do not continue: '+name)

def run():
 matched={}
 reference_path=LAB/'baseline/fixture-reference.json';reference=json.loads(reference_path.read_text(encoding='utf-8')) if reference_path.exists() else {}
 for task in ('bug','feature','refactor'):
  for name in ('manifest.json','prompt.txt','acceptance.py'):
   if reference:assert sha(LAB/'fixtures'/task/name)==reference[f'{task}/{name}'],(task,name)
   else:assert (LAB/'fixtures'/task/name).read_bytes()==(OLD/'fixtures'/task/name).read_bytes(),(task,name)
   matched[f'{task}/{name}']=sha(LAB/'fixtures'/task/name)
 dump(LAB/'fixture-comparison.json',matched)
 dump(LAB/'tested-source.json',{'repo_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),'runtime_sha256':{n:sha(ROOT/n) for n in ('bonsai_proxy.py','claude_launch.py','anthropic_bridge.py')},'guidance_scope':'Claude Code only; OpenCode stable config unchanged','stable_profiles':json.loads((LAB/'inventory.json').read_text(encoding='utf-8'))['stable_profile_hashes']})
 phase('daily-coding',[HERE/'coding.py','--profiles','dflash144','--reps','3'])
 phase('daily-audit',[HERE/'audit_coding.py'])
 daily=[x for x in existing('coding') if x['profile']=='dflash144']
 passes=sum(bool(x.get('passed')) for x in daily)
 if len(daily)==9 and passes>=8 and not any(x.get('not_tested') for x in daily):
  dump(LAB/'draft5-gate.json',{'allowed':True,'daily_passes':passes,'daily_runs':len(daily),'experimental_only':True})
  phase('draft5-coding',[HERE/'coding.py','--profiles','graph128draft5','--reps','3'])
  phase('draft5-audit',[HERE/'audit_coding.py'])
 else:dump(LAB/'draft5-gate.json',{'allowed':False,'daily_passes':passes,'daily_runs':len(daily),'status':'未測試','reason':'New daily policy did not meet historical8/9 completion gate; do not promote throughput candidate'})
 print(json.dumps({'phase':'study_finished'}),flush=True)
if __name__=='__main__':run()
