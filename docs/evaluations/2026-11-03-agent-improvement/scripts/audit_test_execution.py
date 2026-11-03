import json,pathlib,re
from lab import LAB
lab=LAB;old=LAB.parent/'bonsai-evaluation-20261103'
if not old.exists():old=LAB.parent/'2026-11-03'
def read(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()]
new={x['key']:x for x in read(lab/'raw/coding.jsonl')+read(lab/'raw/coding-audit.jsonl')};baseline={x['key']:x for x in read(lab/'baseline/coding.jsonl')+read(lab/'baseline/coding-audit.jsonl')}
proof=[]
for cohort,records,root in [('new',new,lab),('baseline',{k:v for k,v in baseline.items() if v['profile']=='dflash144'},old)]:
 for key,row in records.items():
  calls={};results={}
  for line in (root/'raw'/f'{key}.claude.jsonl').read_text(encoding='utf-8',errors='replace').splitlines():
   try:e=json.loads(line)
   except ValueError:continue
   if e.get('type') not in ('assistant','user') or not isinstance(e.get('message'),dict):continue
   for b in e['message'].get('content',[]):
    if b.get('type')=='tool_use':calls[b['id']]=b
    if b.get('type')=='tool_result':results[b.get('tool_use_id')]=b
  found=[]
  for id,c in calls.items():
   if c['name']!='Bash':continue
   command=c.get('input',{}).get('command','');r=results.get(id,{})
   text=r.get('content','');text=text if isinstance(text,str) else json.dumps(text,ensure_ascii=False)
   ran=re.search(r'Ran (\d+) tests?',text);passed=re.search(r'(\d+) passed',text)
   count=int(ran.group(1)) if ran and re.search(r'\bOK\b',text) else int(passed.group(1)) if passed else 0
   if re.search(r'unittest|pytest|test_.*\.py',command) and not r.get('is_error') and count>0:
    found.append({'tool_id':id,'command':command,'test_count':count,'successful_test_output_present':True})
  proof.append({'cohort':cohort,'run':key,'graded_passed':row.get('passed',False),'successful_test_tool_results':found})
bad=[x['run'] for x in proof if x['graded_passed'] and not x['successful_test_tool_results']]
(lab/'test-execution-audit.json').write_text(json.dumps({'passed_cases_missing_successful_test_output':bad,'runs':proof},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'runs':len(proof),'passed_cases_missing_successful_test_output':bad}));assert not bad
