import json,re
from lab import LAB,dump
attempts=[]
for p in (LAB/'raw').glob('*.claude.jsonl'):
 events=[]
 for line in p.read_text(encoding='utf-8',errors='replace').splitlines():
  try:e=json.loads(line)
  except ValueError:continue
  events.append(e)
  if e.get('type')!='assistant' or not isinstance(e.get('message'),dict):continue
  for b in e['message'].get('content',[]):
   if b.get('type')!='tool_use' or b.get('name')!='Bash':continue
   command=b.get('input',{}).get('command','')
   if isinstance(command,str) and re.search(r'\bpip(?:3)?\s+install\b|\b(?:curl|wget)\s',command):attempts.append({'run':p.name,'tool_id':b['id'],'command':command})
 for attempt in [a for a in attempts if a['run']==p.name]:
  for e in events:
   if e.get('type')!='user' or not isinstance(e.get('message'),dict):continue
   for b in e['message'].get('content',[]):
    if b.get('type')=='tool_result' and b.get('tool_use_id')==attempt['tool_id']:attempt.update(is_error=b.get('is_error'),result=b.get('content'))
dump(LAB/'dependency-review.json',{'attempts':attempts,'scope':'Recorded agent Bash commands; no installer/model download was invoked by the study controller'});print(json.dumps({'dependency_or_download_command_attempts':len(attempts),'results':[{'run':x['run'],'is_error':x.get('is_error'),'result':str(x.get('result',''))[:800]} for x in attempts]}))
