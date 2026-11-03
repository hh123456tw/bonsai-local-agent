import json
from lab import LAB,dump
records=[]
for p in sorted((LAB/'raw').glob('*.claude.jsonl')):
 sample=None;compact=[]
 for line in p.read_text(encoding='utf-8',errors='replace').splitlines():
  try:e=json.loads(line)
  except ValueError:continue
  if e.get('type')=='assistant':
   u=e.get('message',{}).get('usage',{})
   if u.get('cache_read_input_tokens') and sample is None:sample=u
  if e.get('subtype')=='compact_boundary':
   meta=e.get('compact_metadata',{});compact.append({k:meta.get(k) for k in ('trigger','pre_tokens','post_tokens','cumulative_dropped_tokens','duration_ms')})
 if compact or p.name.endswith('bug-0.claude.jsonl'):
  item={'run':p.name,'first_cached_assistant_usage':sample,'compactions':compact};records.append(item);print(json.dumps(item))
dump(LAB/'compaction-analysis.json',records)
