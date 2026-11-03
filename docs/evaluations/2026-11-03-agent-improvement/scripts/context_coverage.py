import collections,json
from lab import LAB,existing,dump
from error_analysis import analyze
data=list({x['key']:x for x in existing('coding')+existing('coding-audit')}.values());summary={}
for profile in sorted(set(x['profile'] for x in data)):
 g=[x for x in data if x['profile']==profile and not x.get('not_tested')];usage=[x.get('engine_usage',{}) for x in g];p=sum(x.get('input_tokens_total',0) for x in usage);c=sum(x.get('cached_input_tokens',0) for x in usage)
 events=collections.Counter()
 for x in g:
  path=LAB/'raw'/f'{x["key"]}.claude.jsonl'
  if path.exists():events.update(analyze(path).get('event_kinds',{}))
 summary[profile]={'max_single_input_tokens':max((x.get('max_request_prompt_tokens',0) for x in usage),default=0),'cached_input_fraction':c/p if p else None,'compaction_events':{k:v for k,v in events.items() if 'compact' in k},'api_retry_events':events.get('system:api_retry',0)}
dump(LAB/'context-coverage.json',summary);print(json.dumps(summary))
