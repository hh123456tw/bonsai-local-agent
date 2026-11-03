"""Read-only final audit after both controllers and client smoke tests finish."""
import ast,collections,ctypes,datetime,json,pathlib,re,subprocess,sys
import requests
from lab import LAB,ROOT,REPO,sha,dump,existing
from fixtures import TASKS
from guidance_versions import GENERIC_GUIDANCE,WINDOWS_GUIDANCE

def main():
 inv=json.loads((LAB/'inventory.json').read_text(encoding='utf-8'));decision=json.loads((LAB/'guidance-decision.json').read_text(encoding='utf-8'));assert decision['applied']
 h=requests.get('http://127.0.0.1:8081/health',timeout=5).json();assert h['max_tool_calls'] is None and h.get('busy') is False
 slots=requests.get('http://127.0.0.1:8080/slots',timeout=5).json();assert slots and not any(x['is_processing'] for x in slots);assert slots[0]['n_ctx']==147456 and slots[0]['speculative']
 assert {n:sha(ROOT/n) for n in inv['stable_profile_hashes']}==inv['stable_profile_hashes']
 assert json.loads((ROOT/'engine-options.json').read_text(encoding='utf-8'))==inv['active_options']
 assert json.loads((ROOT/'guard-config.json').read_text(encoding='utf-8'))==inv['guard_config']
 model=next(ROOT.glob('*.ninfer'));model_sha=sha(model);engine_sha=sha(ROOT/'ninfer-serve.exe');assert model_sha==inv['model']['sha256'] and engine_sha==inv['engine']['sha256']
 for name in ('bonsai_proxy.py','claude_launch.py','anthropic_bridge.py'):assert (ROOT/name).read_bytes()==(REPO/'runtime'/name).read_bytes(),name
 for task,t in TASKS.items():
  base=LAB/'fixtures'/task;manifest=json.loads((base/'manifest.json').read_text(encoding='utf-8'));assert {n:sha(base/'start'/n) for n in manifest}==manifest
  assert (base/'acceptance.py').read_text(encoding='utf-8')==t['acceptance'];assert (base/'prompt.txt').read_text(encoding='utf-8')==t['prompt']
 current=list({x['key']:x for x in existing('coding')+existing('coding-audit')}.values());counts=collections.Counter((x['profile'],x['task']) for x in current)
 gate=json.loads((LAB/'draft5-gate.json').read_text(encoding='utf-8'))
 for profile in ('dflash144','dflash144windows')+(('graph128draft5',) if gate['allowed'] else ()):
  for task in ('bug','feature','refactor'):assert counts[profile,task]==3,(profile,task)
 for x in current:
  if x.get('not_tested'):continue
  assert x['prompt_sha256']==sha(LAB/'fixtures'/x['task']/'prompt.txt');assert not x['protected_files_changed']
  expected=WINDOWS_GUIDANCE if x['profile']=='dflash144windows' else GENERIC_GUIDANCE;assert x['guidance']==expected
  if x['passed']:assert x['acceptance']['passed'] and x['public_tests_passed'] and x['agent_ran_tests'] and not x.get('guard_stops')
 assert (LAB/'profiles/dflash144windows.json').read_bytes()==(LAB/'profiles/dflash144.json').read_bytes()
 clients=json.loads((LAB/'client-validation.json').read_text(encoding='utf-8'));assert len(clients)==2 and all(x['client_exit']==0 and x['external_pass'] and x['protected_files_unchanged'] for x in clients.values())
 assert json.loads((LAB/'api-validation.json').read_text(encoding='utf-8'))['passed']
 dependency=json.loads((LAB/'dependency-review.json').read_text(encoding='utf-8'))
 assert all(a.get('is_error') and "can't be checked before it runs" in str(a.get('result','')) for a in dependency['attempts']),'Review a potentially executed dependency command before finalizing'
 pid=int((ROOT/'engine.pid').read_text(encoding='utf-8'));info=json.loads(subprocess.check_output(['powershell.exe','-NoProfile','-Command',f'Get-CimInstance Win32_Process -Filter "ProcessId={pid}" | Select-Object ExecutablePath,CommandLine | ConvertTo-Json -Compress'],text=True));assert pathlib.Path(info['ExecutablePath'])==ROOT/'ninfer-serve.exe'
 parse=ctypes.windll.shell32.CommandLineToArgvW;parse.argtypes=[ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_int)];parse.restype=ctypes.POINTER(ctypes.c_wchar_p);n=ctypes.c_int();ptr=parse(info['CommandLine'],ctypes.byref(n));argv=[ptr[i] for i in range(n.value)];assert argv[2:]==inv['active_options']
 checks={}
 for label,cmd in [('unit-tests',[sys.executable,'-m','unittest','discover','-s','tests']),('installer-dry-run',[sys.executable,'install.py','--dry-run'])]:
  r=subprocess.run(cmd,cwd=REPO,capture_output=True,text=True,encoding='utf-8');(LAB/'logs'/f'{label}.txt').write_text(r.stdout+r.stderr,encoding='utf-8');assert r.returncode==0,label;checks[label]='passed'
 snapshot=LAB/'deployed-runtime';snapshot.mkdir(exist_ok=True)
 for name in ('bonsai_proxy.py','claude_launch.py','anthropic_bridge.py'):(snapshot/name).write_bytes((ROOT/name).read_bytes())
 dump(LAB/'script-manifest.json',{p.relative_to(LAB).as_posix():sha(p) for p in sorted((LAB/'scripts').glob('*.py'))})
 final={'finished_at':datetime.datetime.now().astimezone().isoformat(),'implementation_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),'model_sha256':model_sha,'engine_sha256':engine_sha,'stable_profiles_unchanged':True,'guard_config_unchanged':True,'original_engine_options_restored':True,'actual_running_options_match':True,'engine_pid':pid,'engine_log':str(ROOT/'engine.log'),'health':h,'guidance_selection':decision['selected'],'runtime_sha256':{n:sha(ROOT/n) for n in ('bonsai_proxy.py','claude_launch.py','anthropic_bridge.py')},'fixture_graders_and_prompts_intact':True,'measured_coding_runs':sum(not x.get('not_tested') for x in current),'not_tested_coding_runs':sum(bool(x.get('not_tested')) for x in current),'group_counts':{p+':'+t:n for (p,t),n in counts.items()},'checks':checks,'client_validation':clients,'no_model_or_dependency_download':True,'dependency_attempts_blocked_before_execution':len(dependency['attempts']),'no_new_harness_installed':True,'no_web_publication':True}
 dump(LAB/'FINALIZED.json',final);print(json.dumps(final,ensure_ascii=False))
if __name__=='__main__':main()
