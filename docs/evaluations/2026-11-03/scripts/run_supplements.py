"""After main controller exits: replace the pilot and confirm extreme candidate."""
import ctypes,sys,json
from run_remaining import execute,HERE,LAB
if __name__=='__main__':
 pid=int(sys.argv[1]);k=ctypes.windll.kernel32;k.OpenProcess.restype=ctypes.c_void_p;k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32];k.CloseHandle.argtypes=[ctypes.c_void_p]
 h=k.OpenProcess(0x100000,False,pid)
 if h:k.WaitForSingleObject(h,0xffffffff);k.CloseHandle(h)
 execute('refactor-pilot-replacement',[HERE/'coding.py','--profiles','dflash128graph','--reps','1','--tasks','refactor','--rep-offset','3'])
 execute('draft5-confirm',[HERE/'lab.py','benchmark','--profiles','graph128draft5','--cases','short:256','short:1024','32768:256'])
 execute('combined-confirm',[HERE/'lab.py','benchmark','--profiles','graph128draft5chunk512','--cases','short:512','8192:256','32768:256'])
 execute('coding-audit',[HERE/'audit_coding.py'])
 print(json.dumps({'phase':'supplements_finished'}),flush=True)
