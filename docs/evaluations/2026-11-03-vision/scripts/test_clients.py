"""Actual installed harnesses, synthetic files, guarded endpoints only."""
import json,os,shutil,subprocess,sys,time
from lab import LAB,ROOT,GPU,dump
sys.path.insert(0,str(ROOT))
from claude_launch import environment
def execute(name,cmd,cwd,env,gpu):
 start=time.monotonic()
 with (LAB/'logs'/f'{name}.stdout.jsonl').open('w',encoding='utf-8') as out,(LAB/'logs'/f'{name}.stderr.log').open('w',encoding='utf-8') as err:
  p=subprocess.Popen(cmd,cwd=cwd,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
  try:code=p.wait(timeout=360)
  except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=15);code='timeout'
 text=(LAB/'logs'/f'{name}.stdout.jsonl').read_text(encoding='utf-8')
 row={'name':name,'exit_code':code,'seconds':time.monotonic()-start,'gpu':gpu.window(start,time.monotonic()),'stdout':f'logs/{name}.stdout.jsonl'}
 dump(LAB/f'{name}.json',row);print(json.dumps(row),flush=True)
 return text
with GPU() as gpu:
 project=LAB/'runs/claude-image';project.mkdir(exist_ok=True);shutil.copy2(LAB/'fixtures/fixture-b.png',project/'scene.png')
 prompt='Use the Read tool to inspect scene.png. Do not use Bash or OCR programs. Report the PIN digits, top-left shape and color, and bottom-right shape and color from the image. Do not infer from the filename.'
 cmd=[sys.executable,str(ROOT/'claude_launch.py'),'--profile','dflash96vision','--project',str(project),'--','-p',prompt,'--output-format','stream-json','--verbose','--allowedTools','Read','--max-turns','6']
 execute('claude-image',cmd,project,environment('dflash96vision'),gpu)
 project=LAB/'runs/opencode-image';project.mkdir(exist_ok=True);shutil.copy2(LAB/'fixtures/fixture-ui.png',project/'scene.png')
 env=os.environ.copy();env['OPENCODE_CONFIG']=str(ROOT/'profiles/dflash96vision.opencode.json');env['XDG_CONFIG_HOME']=str(ROOT/'config')
 cmd=[shutil.which('opencode.cmd'),'--standalone','run','--model','bonsai/bonsai2-27b','--format','json','--file',str(project/'scene.png'),'Inspect this attached dashboard image. Report its build status, error code, missing field, and invoice total. Do not use Bash or OCR.']
 execute('opencode-image',cmd,project,env,gpu)
