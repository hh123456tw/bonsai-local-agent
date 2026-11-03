"""Continue after the initial native benchmark process, then run all remaining phases."""
import ctypes,sys,subprocess,pathlib,json,datetime
HERE=pathlib.Path(__file__).resolve().parent;LAB=HERE.parent
def execute(label,args):
 print(json.dumps({'phase':label,'status':'starting','time':datetime.datetime.now().isoformat()}),flush=True)
 with (LAB/'logs'/f'{label}.stdout').open('w',encoding='utf-8') as out,(LAB/'logs'/f'{label}.stderr').open('w',encoding='utf-8') as err:
  p=subprocess.run([sys.executable,*map(str,args)],stdout=out,stderr=err)
 record={'phase':label,'exit':p.returncode,'time':datetime.datetime.now().isoformat()}
 with (LAB/'raw/phases.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
 print(json.dumps(record),flush=True)
 return p.returncode
if __name__=='__main__':
 pid=int(sys.argv[1]);k=ctypes.windll.kernel32;k.OpenProcess.restype=ctypes.c_void_p;k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32];k.CloseHandle.argtypes=[ctypes.c_void_p]
 handle=k.OpenProcess(0x100000,False,pid)
 if handle:k.WaitForSingleObject(handle,0xffffffff);k.CloseHandle(handle)
 execute('short-recheck',[HERE/'lab.py','benchmark','--profiles','dflash128graph','--short-only'])
 execute('draft-scan',[HERE/'lab.py','benchmark','--profiles','graph128draft2','graph128draft4','graph128draft5','--cases','short:512'])
 execute('chunk-scan',[HERE/'lab.py','benchmark','--profiles','graph128chunk128','graph128chunk512','--cases','8192:256'])
 execute('coding',[HERE/'coding.py','--reps','3'])
 execute('context-prep',[HERE/'context.py','prep'])
 execute('context',[HERE/'context.py','run'])
 execute('compatibility',[HERE/'compat.py'])
 print(json.dumps({'phase':'all_experiments_finished'}),flush=True)
