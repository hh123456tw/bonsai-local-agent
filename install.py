"""Install the tested Windows deployment; large third-party assets stay outside Git."""
import argparse,concurrent.futures,hashlib,json,os,pathlib,shutil,subprocess,sys,time,zipfile
import requests

HERE=pathlib.Path(__file__).resolve().parent
ASSETS=[
 ('ninfer-serve.exe','https://github.com/1314521gjy/ninfer-fusion-kvmem/releases/download/engine-v0.11.0-kvmem-20261008/ninfer-serve-86.exe',820153856,'cd6be5e8ca872a1044aaab4c219be38d2787ee852429e2dd9b073e635dcf5d3f'),
 ('Ternary-Bonsai-2-27B-ninfer-v3.ninfer','https://huggingface.co/WaveCut/Ternary-Bonsai-2-27B-NInfer-v3/resolve/main/Ternary-Bonsai-2-27B-ninfer-v3.ninfer',9520051456,'cdc4810b0ff17c40d0f62cf214b6e0bcd08346e9eb05ca53371507037793c14a'),
]
def digest(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def download(root,name,url,size,sha=None):
 dest=root/name
 if dest.exists() and dest.stat().st_size==size and (not sha or digest(dest)==sha):
  print('Verified existing '+name,flush=True);return dest
 if dest.exists():raise RuntimeError(f'{dest} exists but does not match the expected asset; preserve/rename it before retrying')
 chunks=root/'downloads'/name;chunks.mkdir(parents=True,exist_ok=True)
 step=1024*1024 if name.endswith('.exe') else 16*1024*1024
 ranges=[(a,min(size,a+step)-1) for a in range(0,size,step)]
 def block(pair):
  a,b=pair;p=chunks/str(a)
  if p.exists() and p.stat().st_size==b-a+1:return
  for attempt in range(5):
   try:
    with requests.get(url,headers={'Range':f'bytes={a}-{b}'},stream=True,timeout=120) as r:
     r.raise_for_status()
     if r.status_code!=206 or not r.headers.get('Content-Range','').startswith(f'bytes {a}-'):raise RuntimeError('Server did not honor byte range')
     data=r.content
     if len(data)!=b-a+1:raise RuntimeError('Incomplete download block')
    p.write_bytes(data);return
   except (requests.RequestException,RuntimeError):
    if attempt==4:raise
    time.sleep(1+attempt)
 with concurrent.futures.ThreadPoolExecutor(24 if name.endswith('.exe') else 12) as pool:
  for i,_ in enumerate(pool.map(block,ranges)):
   if i%40==0:print(f'{name}: {i+1}/{len(ranges)} blocks',flush=True)
 part=root/(name+'.partial')
 with part.open('wb') as out:
  for a,b in ranges:
   with (chunks/str(a)).open('rb') as src:shutil.copyfileobj(src,out)
 if part.stat().st_size!=size or (sha and digest(part)!=sha):raise RuntimeError('Checksum/size mismatch: '+name)
 part.rename(dest)
 # Remove only this installer's verified, resolved block files.
 assert chunks.resolve().parent==(root/'downloads').resolve()
 for a,b in ranges:(chunks/str(a)).unlink()
 chunks.rmdir()
 print('Installed '+name,flush=True);return dest
def small_zip(root,name,url):
 p=root/'downloads'/name;p.parent.mkdir(exist_ok=True)
 if not p.exists():
  with requests.get(url,stream=True,timeout=120) as r:
   r.raise_for_status()
   with p.open('wb') as f:
    for c in r.iter_content(1024*1024):f.write(c)
 return p
def install_dlls(root):
 local=pathlib.Path(os.environ.get('LOCALAPPDATA',''))
 for name in ('cublas64_13.dll','cublasLt64_13.dll','cudart64_13.dll'):
  if (root/name).exists():continue
  candidates=[]
  for base in (local/'Strata/components/engine',local/'Programs/Ollama/lib/ollama/cuda_v13'):
   if base.exists():candidates+=list(base.rglob(name))
  if candidates:shutil.copy2(sorted(candidates)[-1],root/name)
 if any(not (root/n).exists() for n in ('cublas64_13.dll','cublasLt64_13.dll','cudart64_13.dll')):
  vendor=root/'vendor'
  subprocess.run([sys.executable,'-m','pip','install','--no-deps','--target',str(vendor),'nvidia-cublas-cu13','nvidia-cuda-runtime-cu13'],check=True)
  for name in ('cublas64_13.dll','cublasLt64_13.dll','cudart64_13.dll'):
   if not (root/name).exists():shutil.copy2(next(vendor.rglob(name)),root/name)
 if not (root/'avcodec-63.dll').exists():
  p=small_zip(root,'ffmpeg9.zip','https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n9.0-latest-win64-gpl-shared-9.0.zip')
  with zipfile.ZipFile(p) as z:
   for n in z.namelist():
    if '/bin/' in n and n.endswith('.dll'):(root/pathlib.PurePosixPath(n).name).write_bytes(z.read(n))
 if not (root/'libcurl-x64.dll').exists():
  p=small_zip(root,'curl.zip','https://curl.se/windows/dl-8.23.0_8/curl-8.23.0_8-win64-mingw.zip')
  with zipfile.ZipFile(p) as z:
   n=next(n for n in z.namelist() if n.endswith('/bin/libcurl-x64.dll'))
   (root/'libcurl-x64.dll').write_bytes(z.read(n))
def shortcuts(root):
 script=root/'create-shortcuts.ps1'
 script.write_text('''$root=$PSScriptRoot
$ws=New-Object -ComObject WScript.Shell
$desktop=$ws.SpecialFolders.Item('Desktop')
foreach($entry in @(@('Bonsai OpenCode 修正版','start.ps1',''),@('Bonsai OpenCode DFlash 144K','start.ps1',' -Profile dflash144'),@('Bonsai OpenCode 基本版256K','start.ps1',' -Profile base256'),@('Bonsai Claude Code','start-claude.ps1',''),@('Bonsai Claude Code 加速128K','start-claude.ps1',' -Profile dflash128graph'),@('Bonsai Claude Code 基本版256K','start-claude.ps1',' -Profile base256'),@('Bonsai Claude Code 看圖96K','start-claude.ps1',' -Profile dflash96vision'),@('Bonsai OpenCode 看圖96K','start.ps1',' -Profile dflash96vision'),@('Bonsai 看圖96K 服務','start-server.ps1',' -Profile dflash96vision'),@('停止 Bonsai','stop.ps1',''))) {
 $s=$ws.CreateShortcut((Join-Path $desktop ($entry[0]+'.lnk')))
 $s.TargetPath="$env:WINDIR\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
 $s.Arguments='-NoProfile -ExecutionPolicy Bypass -File "'+(Join-Path $root $entry[1])+'"'+$entry[2]
 $s.WorkingDirectory=$root
 $s.Save()
}
''',encoding='utf-8-sig')
 subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script)],check=True)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=pathlib.Path,default=pathlib.Path('C:/AI/bonsai'));ap.add_argument('--dry-run',action='store_true');ap.add_argument('--verify-only',action='store_true');a=ap.parse_args()
 root=a.root.resolve()
 if a.dry_run:
  print(json.dumps({'root':str(root),'assets':[{'name':n,'bytes':s,'sha256':h,'url':u} for n,u,s,h in ASSETS]},indent=2));return
 if a.verify_only:
  for n,u,s,h in ASSETS:
   p=root/n
   if not p.exists() or p.stat().st_size!=s or digest(p)!=h:raise RuntimeError('Verification failed: '+str(p))
   print('Verified '+n)
  return
 if os.name!='nt':raise RuntimeError('Installation requires Windows x64')
 root.mkdir(parents=True,exist_ok=True)
 for n,u,s,h in ASSETS:download(root,n,u,s,h)
 install_dlls(root)
 for p in (HERE/'runtime').iterdir():
  if p.name=='guard-config.json' and (root/p.name).exists():continue
  if p.is_file():shutil.copy2(p,root/p.name)
 opts=json.loads((HERE/'config/engine-options.json').read_text())
 opts=[v.replace('${ROOT}',root.as_posix()) for v in opts]
 (root/'engine-options.json').write_text(json.dumps(opts,indent=2),encoding='utf-8')
 shutil.copy2(HERE/'config/opencode.json',root/'opencode.json');(root/'config').mkdir(exist_ok=True)
 shutil.copy2(HERE/'config/profiles.json',root/'profiles.json')
 shutil.copytree(HERE/'profiles',root/'profiles',dirs_exist_ok=True)
 shortcuts(root);print('Installed. Start with the Bonsai desktop shortcut.')
if __name__=='__main__':main()
