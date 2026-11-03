"""Inspect only non-secret routing/MCP metadata; never persist full merged config."""
import os,subprocess,json,pathlib
from lab import ROOT,LAB,dump
env=os.environ.copy();env.update(OPENCODE_CONFIG=str(ROOT/'profiles/dflash144.opencode.json'),XDG_CONFIG_HOME=str(ROOT/'config'));env.pop('OPENCODE_CONFIG_CONTENT',None)
p=subprocess.run(['opencode.cmd','api','--standalone','config.get'],env=env,cwd=LAB/'fixtures/bug/start',capture_output=True,text=True,encoding='utf-8',timeout=45)
if p.returncode:raise RuntimeError('OpenCode config.get failed; full output intentionally not printed')
payload=json.loads(p.stdout);sources=payload if isinstance(payload,list) else payload.get('data',payload)
if isinstance(sources,dict):sources=[sources]
data={}
def merge(a,b):
 for k,v in b.items():
  if isinstance(v,dict) and isinstance(a.get(k),dict):merge(a[k],v)
  elif isinstance(v,list) and isinstance(a.get(k),list):a[k]+=v
  else:a[k]=v
for source in sources:merge(data,source.get('info',source))
mcp=data.get('mcp',{});servers=mcp.get('servers',{})
result={'source_merged_mcp_servers':{k:{'disabled':v.get('disabled',False)} for k,v in servers.items() if isinstance(v,dict)},'plugin_ids':[v.split('@')[0] if isinstance(v,str) else '<object>' for v in data.get('plugins',[])],'build_steps':data.get('agents',{}).get('build',{}).get('steps'),'model':data.get('model'),'has_bonsai': 'bonsai' in data.get('providers',{})}
dump(LAB/'opencode-effective-routing.json',result);print(json.dumps(result,ensure_ascii=False))
