"""Classify actual tool-result errors without changing any agent workspace."""
import collections,json
from lab import LAB,dump
def analyze(path):
 calls={};errors=[];event_kinds=collections.Counter()
 for line in path.read_text(encoding='utf-8',errors='replace').splitlines():
  try:e=json.loads(line)
  except ValueError:continue
  event_kinds[str(e.get('type'))+':'+str(e.get('subtype',''))]+=1
  if e.get('type') not in ('assistant','user') or not isinstance(e.get('message'),dict):continue
  for block in e.get('message',{}).get('content',[]):
   if not isinstance(block,dict):continue
   if block.get('type')=='tool_use':calls[block['id']]=block
   if block.get('type')=='tool_result' and block.get('is_error'):
    v=block.get('content','');text=v if isinstance(v,str) else '\n'.join(b.get('text','') for b in v if isinstance(b,dict));low=text.lower()
    category='permission' if any(s in low for s in ('permission','not allowed','denied','not authorized','requires approval','require approval')) else 'python_syntax' if 'syntaxerror' in low else 'missing_tool' if 'no such tool' in low or 'tool is not available' in low else 'import' if 'importerror' in low or 'modulenotfounderror' in low else 'missing_file' if 'no such file' in low or 'does not exist' in low else 'test_or_other_command'
    c=calls.get(block.get('tool_use_id'),{});errors.append({'category':category,'tool':c.get('name'),'first_line':text[:240]})
 return {'counts':dict(collections.Counter(e['category'] for e in errors)),'examples':errors[:8],'event_kinds':dict(event_kinds),'client_api_retry_events':sum(v for k,v in event_kinds.items() if k=='system:api_retry'),'client_api_error_events':sum(v for k,v in event_kinds.items() if k in ('system:api_error','api_error:'))}
def main():
 out={}
 for p in sorted((LAB/'raw').glob('*.claude.jsonl')):out[p.stem]=analyze(p)
 dump(LAB/'error-analysis.json',out);print(json.dumps({k:v['counts'] for k,v in out.items()}))
if __name__=='__main__':main()
