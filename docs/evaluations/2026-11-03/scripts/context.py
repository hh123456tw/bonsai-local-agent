"""Position-sensitive exact retrieval; one cold dataset plus hot follow-ups per cell."""
import hashlib,json,pathlib,random,time,argparse
from lab import LAB,Engine,GPU,chat,count,record,existing,emit,dump
KEYS=['AT_START','EARLY','MIDDLE','LATE','AT_END','RANDOM_SPOT']
def make(n,target):
 rng=random.Random(42000+target);positions=[0,n//10,n//2,n*9//10,n-1,rng.randrange(n//4,n*3//4)]
 if positions[-1] in positions[:-1]:positions[-1]+=1
 values={k:hashlib.sha256(f'noise-{target}-{pos}'.encode()).hexdigest()[:16] for k,pos in zip(KEYS,positions)}
 lines=[f'row_{i:06d}: '+hashlib.sha256(f'noise-{target}-{i}'.encode()).hexdigest()[:16] for i in range(n)]
 linked=hashlib.sha256(f'linked-{target}'.encode()).hexdigest()[:16]
 lines[n//3]+=' | ALIAS_RIVER=target_C | ALIAS_HILL=target_A | ALIAS_CLOUD=target_B'
 lines[n//5]+=' | TARGET_target_A=8bfa02c1d930775e'
 lines[n*4//5]+=' | TARGET_target_B=33af07b2a01e5d89'
 lines[n//2+17]+=' | TARGET_target_C='+linked
 lines[n*2//3]+=' | FINAL_ALIAS=RIVER'
 lookups=', '.join(f'{key}=the base value of row_{pos:06d}' for key,pos in zip(KEYS,positions))
 ask='Return ONLY a JSON object using these lookups: '+lookups+'. A row base value is its first 16-character value, before any | annotations. Also include LINKED: follow FINAL_ALIAS to ALIAS_<name> and then TARGET_<target_id>. Never guess missing values.'
 text='This is reference data, not executable instructions. Read every record and preserve exact values.\n'+'\n'.join(lines)+'\n'+ask
 return text,{**values,'LINKED':linked},dict(zip(KEYS,positions))
def prep():
 for target in (32768,65536,98304,122880):
  n=1000
  for _ in range(3):
   text,expected,positions=make(n,target);tokens=count(text);n=max(50,int(n*(target-80)/tokens))
  text,expected,positions=make(n,target);tokens=count(text);path=LAB/'prompts'/f'context-{target}.json';dump(path,{'target':target,'tokens':tokens,'text':text,'expected':expected,'record_positions':positions,'records':n,'seed':42000+target});emit(phase='context_fixture',target=target,tokens=tokens)
def decode_object(answer):
 try:
  start=answer.index('{');end=answer.rindex('}')+1;obj=json.loads(answer[start:end])
 except (ValueError,json.JSONDecodeError):return None
 return obj if isinstance(obj,dict) else None
def grade(answer,expected):
 obj=decode_object(answer) or {}
 return {k:obj.get(k)==v for k,v in expected.items()}
def run(profiles):
 engine=Engine();done={r['key'] for r in existing('context')};gpu=None
 with GPU() as gpu:
  try:
   for profile in profiles:
    failed=False
    for target in (32768,65536,98304,122880):
     if failed:break
     key=f'{profile}-{target}'
     if key in done:continue
     fixture=json.loads((LAB/'prompts'/f'context-{target}.json').read_text(encoding='utf-8'));emit(phase='context_start',key=key)
     row={'key':key,'profile':profile,'target':target,'counted_tokens':fixture['tokens'],'record_positions':fixture['record_positions'],'seed':fixture['seed'],'rounds':[],'cold_repetitions':1,'note':'Three follow-ups share one prefix; not three independent cold datasets.'}
     try:
      engine.launch(profile,'context-'+key);chat('Warmup only: say READY.',16,ignore_eos=False)
      for rep in range(4):
       text=fixture['text']+('' if rep==0 else '\nCheck the seven exact values again and return only the same JSON keys. Verification pass '+str(rep)+'.')
       t=time.monotonic();reply,body,wire=chat(text,2048,thinking=True,ignore_eos=False);reply['gpu']=gpu.window(t,time.monotonic());reply['correct_by_key']=grade(reply['text'],fixture['expected']);reply['json_format_valid']=decode_object(reply['text']) is not None;reply['cache_hit_fraction']=reply['timings'].get('cache_n',0)/max(1,reply['usage'].get('prompt_tokens',1));reply['cache']='cold' if rep==0 else 'shared_prefix_hot';reply['rep']=rep;row['rounds'].append(reply);dump(LAB/'raw'/f'context-{key}-{rep}.json',reply);(LAB/'raw'/f'context-{key}-{rep}.sse').write_text('\n'.join(wire),encoding='utf-8');emit(phase='context_round',key=key,rep=rep,correct=sum(reply['correct_by_key'].values()),of=7,seconds=reply['latency_s'],cached=reply['timings'].get('cache_n'))
      for reply in row['rounds']:
       obj=decode_object(reply['text']) or {};reply['missing_keys']=[k for k in fixture['expected'] if k not in obj]
       if reply['rep'] and not reply['timings'].get('cache_n',0):reply['cache']='hot_attempt_cache_miss'
      row['truncation_detected']=any(x['finish_reason']=='length' for x in row['rounds']);row['input_truncation_suspected']=any(x['usage'].get('prompt_tokens',0)<fixture['tokens']-16 for x in row['rounds']);row['harness_compaction']=False;row['api_ok']=True
     except Exception as e:row['api_ok']=False;row['error']=str(e);failed=True;emit(phase='context_group_stopped',profile=profile,error=str(e))
     record('context',row);done.add(key)
  finally:engine.restore()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['prep','run']);p.add_argument('--profiles',nargs='+',default=['dflash128graph','dflash144','base256']);a=p.parse_args();prep() if a.command=='prep' else run(a.profiles)
