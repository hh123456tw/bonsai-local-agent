"""Shared paths and GPU sampling for the synthetic vision checks only."""
import json,pathlib,statistics,subprocess,threading,time
LAB=pathlib.Path(__file__).resolve().parents[1]
ROOT=pathlib.Path('C:/AI/bonsai')
for folder in ('raw','logs','runs'):(LAB/folder).mkdir(exist_ok=True)
def dump(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
class GPU:
 def __enter__(self):
  self.samples=[];self.file=(LAB/'raw/gpu.jsonl').open('a',encoding='utf-8');self.p=subprocess.Popen(['nvidia-smi','--query-gpu=memory.used,memory.free,temperature.gpu,power.draw,clocks.current.graphics,clocks_event_reasons.hw_thermal_slowdown','--format=csv,noheader,nounits','--loop-ms=250'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
  def read():
   for line in self.p.stdout:
    try:
     fields=[x.strip() for x in line.split(',')];vals=[float(x) for x in fields[:4]];row={'wall_time':time.time(),'mono':time.monotonic(),'used_mib':vals[0],'free_mib':vals[1],'temp_c':vals[2],'power_w':vals[3],'graphics_clock_mhz':float(fields[4]),'hw_thermal_slowdown':fields[5].lower()=='active'};self.samples.append(row);self.file.write(json.dumps(row)+'\n');self.file.flush()
    except ValueError:pass
  self.thread=threading.Thread(target=read,daemon=True);self.thread.start();return self
 def window(self,start,end):
  rows=[s for s in self.samples if start-.25<=s['mono']<=end+.05]
  if not rows:return {'sample_count':0}
  return {'sample_count':len(rows),'used_mib_max':max(s['used_mib'] for s in rows),'free_mib_min':min(s['free_mib'] for s in rows),'temp_c_max':max(s['temp_c'] for s in rows),'power_w_max':max(s['power_w'] for s in rows),'power_w_mean':statistics.mean(s['power_w'] for s in rows),'graphics_clock_min_mhz':min(s['graphics_clock_mhz'] for s in rows),'hw_thermal_slowdown_observed':any(s['hw_thermal_slowdown'] for s in rows)}
 def __exit__(self,*args):self.p.terminate();self.p.wait(timeout=10);self.thread.join(timeout=5);self.file.close()
