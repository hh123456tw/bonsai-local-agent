import pathlib,subprocess,time,requests,json,sys,os,argparse,ctypes
ROOT=pathlib.Path(__file__).resolve().parent
def ready(port):
 try:
  r=requests.get(f'http://127.0.0.1:{port}/v1/models',timeout=2)
  return r.status_code==200 and any(m.get('id')=='bonsai2-27b' for m in r.json().get('data',[]))
 except requests.RequestException:return False
def process_options():
 """Read only our recorded engine process, avoiding reuse of another profile."""
 pidfile=ROOT/'engine.pid'
 if not pidfile.exists():return None
 try:pid=int(pidfile.read_text().strip())
 except ValueError:return None
 command=f"Get-CimInstance Win32_Process -Filter 'ProcessId = {pid}' | Select-Object ExecutablePath,CommandLine | ConvertTo-Json -Compress"
 raw=subprocess.check_output(['powershell.exe','-NoProfile','-Command',command],text=True,creationflags=subprocess.CREATE_NO_WINDOW).strip()
 if not raw:return None
 info=json.loads(raw)
 if pathlib.Path(info.get('ExecutablePath') or '').resolve()!= (ROOT/'ninfer-serve.exe').resolve():return None
 count=ctypes.c_int();parse=ctypes.windll.shell32.CommandLineToArgvW
 parse.argtypes=[ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_int)];parse.restype=ctypes.POINTER(ctypes.c_wchar_p)
 args=parse(info['CommandLine'],ctypes.byref(count))
 try:return [args[i] for i in range(count.value)][2:]
 finally:ctypes.windll.kernel32.LocalFree(args)

def ensure(profile=None):
 if profile:
  profiles=json.loads((ROOT/'profiles.json').read_text(encoding='utf-8'))
  if profile not in profiles:raise RuntimeError('Unknown Bonsai profile: '+profile)
  opts=json.loads((ROOT/profiles[profile]['engine_options']).read_text(encoding='utf-8'))
  opts=[v.replace('${ROOT}',ROOT.as_posix()) for v in opts]
  if ready(8080) and process_options()!=opts:
   try:
    if requests.get('http://127.0.0.1:8081/health',timeout=5).json().get('busy'):raise RuntimeError('Bonsai bridge is busy. Finish the current task before switching profiles.')
   except requests.ConnectionError:pass
   slots=requests.get('http://127.0.0.1:8080/slots',timeout=5).json()
   if any(s.get('is_processing') for s in slots):raise RuntimeError('Bonsai is busy. Finish or stop the current task before switching profiles.')
   if process_options() is None:raise RuntimeError('Port 8080 is owned by another server; it will not be stopped automatically.')
   subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'stop.ps1')],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
  (ROOT/'engine-options.json').write_text(json.dumps(opts),encoding='utf-8')
 if not ready(8080):
  opts=json.loads((ROOT/'engine-options.json').read_text())
  log=(ROOT/'engine.log').open('a',encoding='utf-8')
  p=subprocess.Popen([str(ROOT/'ninfer-serve.exe'),str(ROOT/'Ternary-Bonsai-2-27B-ninfer-v3.ninfer')]+opts,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
  (ROOT/'engine.pid').write_text(str(p.pid))
  for i in range(600):
   if p.poll() is not None:raise RuntimeError('NInfer failed to start. See C:/AI/bonsai/engine.log')
   if ready(8080):break
   time.sleep(1)
  else:raise RuntimeError('NInfer startup timed out')
 if not ready(8081):
  log=(ROOT/'proxy.log').open('a',encoding='utf-8')
  p=subprocess.Popen([sys.executable,str(ROOT/'bonsai_proxy.py')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
  (ROOT/'proxy.pid').write_text(str(p.pid))
  for i in range(20):
   if ready(8081):break
   if p.poll() is not None:raise RuntimeError('Bonsai bridge failed to start')
   time.sleep(.5)
  else:raise RuntimeError('Bonsai bridge startup timed out')
 # A model-list response alone is insufficient if an inference worker has failed.
 r=requests.post('http://127.0.0.1:8080/v1/chat/completions',json={'model':'bonsai2-27b','messages':[{'role':'user','content':'Reply OK.'}],'enable_thinking':False,'max_tokens':1,'stream':False},timeout=120)
 r.raise_for_status()
 if not r.json().get('choices'):raise RuntimeError('Inference health check failed')
 print('Bonsai ready: http://127.0.0.1:8081/v1',flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--profile');args=parser.parse_args();ensure(args.profile)
