"""Wait for the first serial study, then isolate Windows-specific guidance."""
import ctypes,datetime,json,sys
from lab import LAB,dump
from run_study import phase,HERE
from guidance_versions import WINDOWS_GUIDANCE

def run():
 dump(LAB/'windows-protocol.json',{'registered_at':datetime.datetime.now().astimezone().isoformat(),'change':'Only the appended system guidance adds concrete Windows/python/project-CWD rules; user task, permissions, tests and engine settings unchanged','guidance':WINDOWS_GUIDANCE,'profile':'dflash144windows is a byte-identical experimental copy of dflash144','repeats':3,'promotion_rule':'Prefer higher verified completion count; if tied require >=10% lower failure-inclusive seconds/success to replace current choice. If no guidance variant improves historical completion or >=10% task time, retain the original launcher behavior. Small n is not statistical certification.'})
 pid=int(sys.argv[1]) if len(sys.argv)>1 else 0;k=ctypes.windll.kernel32;k.OpenProcess.restype=ctypes.c_void_p;k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32];k.CloseHandle.argtypes=[ctypes.c_void_p]
 h=k.OpenProcess(0x100000,False,pid) if pid else None
 print(json.dumps({'phase':'windows_guidance_waiting','controller_pid':pid}),flush=True)
 if h:k.WaitForSingleObject(h,0xffffffff);k.CloseHandle(h)
 assert (LAB/'profiles/dflash144windows.json').read_bytes()==(LAB/'profiles/dflash144.json').read_bytes()
 phase('windows-coding',[HERE/'coding.py','--profiles','dflash144windows','--reps','3'])
 phase('windows-audit',[HERE/'audit_coding.py'])
 print(json.dumps({'phase':'windows_study_finished'}),flush=True)
if __name__=='__main__':run()
