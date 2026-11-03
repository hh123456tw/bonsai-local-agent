import collections,json,time
from lab import LAB
paths=sorted((LAB/'raw').glob('*.claude.jsonl'),key=lambda p:p.stat().st_mtime)
if paths:
 p=paths[-1];events=[]
 for line in p.read_text(encoding='utf-8',errors='replace').splitlines():
  try:events.append(json.loads(line))
  except ValueError:pass
 calls={b['id']:b for e in events if e.get('type')=='assistant' for b in e.get('message',{}).get('content',[]) if b.get('type')=='tool_use'}
 errors=[b for e in events if e.get('type')=='user' for b in e.get('message',{}).get('content',[]) if b.get('type')=='tool_result' and b.get('is_error')]
 print(json.dumps({'run':p.stem,'elapsed_s':round(time.time()-p.stat().st_ctime),'tool_calls':len(calls),'tools':dict(collections.Counter(x['name'] for x in calls.values())),'tool_errors':len(errors),'last_tools':[x['name'] for x in list(calls.values())[-5:]]}))
