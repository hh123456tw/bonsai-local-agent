"""Final real launcher/OpenCode checks in fresh disposable bug fixtures."""
import json,os,pathlib,shutil,subprocess,sys,time
import requests
from lab import LAB,ROOT,dump,sha

def grade(project):
 r=subprocess.run([sys.executable,str(LAB/'scripts/accept.py'),str(project),str(LAB/'fixtures/bug/acceptance.py')],cwd=project,capture_output=True,text=True,timeout=30)
 protected=all((project/n).read_bytes()==(LAB/'fixtures/bug/start'/n).read_bytes() for n in ('README.md','test_existing.py'))
 return {'external_pass':r.returncode==0,'protected_files_unchanged':protected,'output':r.stdout+r.stderr}

def run():
 assert not requests.get('http://127.0.0.1:8081/health',timeout=5).json().get('busy')
 prompt=(LAB/'fixtures/bug/prompt.txt').read_text(encoding='utf-8');out={}
 for client in ('claude-launcher','opencode'):
  project=LAB/'runs'/f'{client}-smoke-bug';assert not project.exists(),'Refusing to reuse a changed fixture'
  shutil.copytree(LAB/'fixtures/bug/start',project,ignore=shutil.ignore_patterns('__pycache__'))
  env=os.environ.copy()
  if client=='claude-launcher':
   cmd=[sys.executable,str(ROOT/'claude_launch.py'),'--profile','dflash144','--project',str(project),'--','--no-session-persistence','--output-format','stream-json','--verbose','--allowedTools','Read,Write,Edit,Glob,Grep,Bash(python *)','-p',prompt]
  else:
   env.update(OPENCODE_CONFIG=str(ROOT/'profiles/dflash144.opencode.json'),XDG_CONFIG_HOME=str(ROOT/'config'));env.pop('OPENCODE_CONFIG_CONTENT',None)
   cmd=['opencode.cmd','run','--standalone','--model','bonsai/bonsai2-27b','--agent','build','--format','json','--auto',prompt]
  t=time.monotonic()
  with (LAB/'raw'/f'{client}-smoke.stdout').open('w',encoding='utf-8') as stdout,(LAB/'raw'/f'{client}-smoke.stderr').open('w',encoding='utf-8') as stderr:
   child=subprocess.Popen(cmd,cwd=project,env=env,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
   try:code=child.wait(timeout=240)
   except subprocess.TimeoutExpired:
    subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True);raise RuntimeError(client+' smoke timed out; not a production tool limit')
  item={'client_exit':code,'seconds':time.monotonic()-t,**grade(project)}
  (LAB/'raw'/f'{client}-smoke.acceptance.txt').write_text(item.pop('output'),encoding='utf-8');out[client]=item;dump(LAB/'client-validation.json',out)
  assert code==0 and item['external_pass'] and item['protected_files_unchanged'],client+' failed external smoke acceptance'
 print(json.dumps(out))
if __name__=='__main__':run()
