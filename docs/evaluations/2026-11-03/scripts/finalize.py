"""Read-only final integrity audit. Run only after every GPU controller exits."""
import collections,ctypes,datetime,json,pathlib,subprocess
import requests
from lab import LAB,ROOT,REPO,sha,dump,existing
from fixtures import TASKS

def main():
 inv=json.loads((LAB/'inventory.json').read_text(encoding='utf-8'))
 slots=requests.get('http://127.0.0.1:8080/slots',timeout=5).json()
 assert slots and not any(x.get('is_processing') for x in slots),'An active task exists; cannot finalize.'
 stable={n:sha(ROOT/n) for n in inv['stable_profile_hashes']};assert stable==inv['stable_profile_hashes']
 opts=json.loads((ROOT/'engine-options.json').read_text(encoding='utf-8'));assert opts==inv['active_options']
 model=next(ROOT.glob('*.ninfer'));model_sha=sha(model);engine_sha=sha(ROOT/'ninfer-serve.exe')
 assert model_sha==inv['model']['sha256'];assert engine_sha==inv['engine']['sha256']
 assert json.loads((ROOT/'guard-config.json').read_text(encoding='utf-8'))==inv['guard_config']
 status=subprocess.check_output(['git','status','--porcelain'],cwd=REPO,text=True);assert not status,status
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==inv['repo_commit']
 for task,t in TASKS.items():
  base=LAB/'fixtures'/task;manifest=json.loads((base/'manifest.json').read_text())
  assert {n:sha(base/'start'/n) for n in manifest}==manifest
  assert (base/'acceptance.py').read_text(encoding='utf-8')==t['acceptance']
  assert (base/'prompt.txt').read_text(encoding='utf-8')==t['prompt']
 health=requests.get('http://127.0.0.1:8081/health',timeout=5).json();assert health.get('max_tool_calls','MISSING') is None
 steps={p.name:json.loads(p.read_text())['agents']['build'].get('steps') for p in (ROOT/'profiles').glob('*.opencode.json')};assert all(v is None for v in steps.values())
 pid=int((ROOT/'engine.pid').read_text());cmd=f'Get-CimInstance Win32_Process -Filter "ProcessId={pid}" | Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress'
 process=json.loads(subprocess.check_output(['powershell.exe','-NoProfile','-Command',cmd],text=True,encoding='utf-8'))
 assert pathlib.Path(process['ExecutablePath'])==ROOT/'ninfer-serve.exe'
 shell=ctypes.windll.shell32;shell.CommandLineToArgvW.restype=ctypes.POINTER(ctypes.c_wchar_p);n=ctypes.c_int();argv=shell.CommandLineToArgvW(process['CommandLine'],ctypes.byref(n));actual=[argv[i] for i in range(n.value)]
 assert actual[2:]==opts,(actual[2:],opts)
 assert slots[0]['n_ctx']==147456 and slots[0]['speculative'] is True
 coding={x['key']:x for x in existing('coding')+existing('coding-audit')};formal=[x for x in coding.values() if x['task']!='refactor' or x['prompt_sha256']==sha(LAB/'fixtures/refactor/prompt.txt')]
 groups=collections.Counter((x['profile'],x['task']) for x in formal);assert len(groups)==6 and all(n==3 for n in groups.values()),groups
 assert len({x['key'] for x in existing('context')})==12
 mt={x['key']:x for x in existing('multiturn')};assert len(mt)==4,'Multiturn cells missing'
 def parse(a):
  result={};i=0
  while i<len(a):
   k=a[i];i+=1
   if i<len(a) and not a[i].startswith('--'):result[k]=a[i];i+=1
   else:result[k]=True
  return result
 reference=parse(json.loads((LAB/'profiles/dflash128graph.json').read_text()));diffs={}
 for path in sorted((LAB/'profiles').glob('*.json')):
  values=parse(json.loads(path.read_text()));diffs[path.stem]={k:{'reference':reference.get(k),'value':values.get(k)} for k in sorted(reference.keys()|values.keys()) if reference.get(k)!=values.get(k)}
 dump(LAB/'profile-differences.json',diffs)
 dump(LAB/'script-manifest.json',{p.name:sha(p) for p in sorted((LAB/'scripts').glob('*.py'))})
 final={'finished_at':datetime.datetime.now().astimezone().isoformat(),'stable_profile_hashes_match':True,'original_options_unchanged':True,'actual_running_options_match':True,'model_sha256':model_sha,'engine_sha256':engine_sha,'guard_config_unchanged':True,'bridge_health':health,'opencode_steps':steps,'original_repo_clean':True,'original_repo_commit':inv['repo_commit'],'fixtures_and_graders_intact':True,'formal_coding_runs':len(formal),'context_cells':12,'multiturn_cells':len(mt),'multiturn_failed_cells':[k for k,v in mt.items() if not v.get('api_ok')],'slots':slots,'engine_pid':pid,'engine_log':str(ROOT/'engine.log'),'engine_log_bytes':(ROOT/'engine.log').stat().st_size,'no_new_harness_installed':True,'no_publishing':True}
 dump(LAB/'FINALIZED.json',final);print(json.dumps(final,ensure_ascii=False))
if __name__=='__main__':main()
