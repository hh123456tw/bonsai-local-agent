import pathlib,subprocess,time,requests,json,sys,os
ROOT=pathlib.Path(__file__).resolve().parent
def ready(port):
 try:
  r=requests.get(f'http://127.0.0.1:{port}/v1/models',timeout=2)
  return r.status_code==200 and any(m.get('id')=='bonsai2-27b' for m in r.json().get('data',[]))
 except requests.RequestException:return False
def ensure():
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
if __name__=='__main__':ensure()
