"""Explicit historical-shape regression with real assistant/user history."""
import hashlib,json,time
from lab import LAB,Engine,GPU,chat,count,record,existing,emit,dump
def value(i):return hashlib.sha256(f'public-bonsai-context-fixture-v1:{i}'.encode()).hexdigest()[:16]
FACTS={'SECRET_ALPHA':'VIOLET-582731','SECRET_BETA':'COPPER-294865','SECRET_GAMMA':'ORBIT-716943'}
def make(n):
 lines=[f'item_{i:06d}: {value(i)}' for i in range(n)]
 for pos,(k,v) in zip((n//20,n//2,n*19//20),FACTS.items()):lines.insert(pos,f'{k} = {v}')
 return 'Read these reference records. Preserve exact facts for later questions.\n'+'\n'.join(lines)+'\nReturn only a JSON object with the exact values of SECRET_ALPHA, SECRET_BETA, and SECRET_GAMMA.'
def run():
 n=1000
 for _ in range(3):n=int(n*(122880-64)/count(make(n)))
 engine=Engine();done={r['key'] for r in existing('multiturn')}
 # Count while the original service is available. A failed experimental launch
 # must not prevent later independent profiles from being recorded.
 fixtures={}
 for records,label in ((n,'120k'),(5238,'historical130k')):
  text=make(records);tokens=count(text);fixtures[label]=(text,tokens)
  dump(LAB/'prompts'/f'multiturn-{label}.json',{'records':records,'tokens':tokens,'text':text,'middle_id':records//2-10,'expected_middle':value(records//2-10)})
 with GPU() as gpu:
  try:
   for profile,records,label in [('dflash128graph',n,'120k'),('dflash144',n,'120k'),('base256',n,'120k'),('dflash144',5238,'historical130k')]:
    key=f'{profile}-{label}'
    if key in done:continue
    text,tokens=fixtures[label]
    row={'key':key,'profile':profile,'records':records,'counted_tokens':tokens,'rounds':[],'historical_results_not_reused':True};emit(phase='multiturn_start',key=key,tokens=tokens)
    try:
     engine.launch(profile,'multiturn-'+key);chat('Warmup only: say OK.',16,ignore_eos=False);messages=[{'role':'user','content':text}]
     for step in range(3):
      if step:messages.append({'role':'user','content':f'Return the exact value of item_{(10 if step==1 else records//2-10):06d}. No explanation.'})
      t=time.monotonic();r,body,wire=chat('',2048,thinking=True,ignore_eos=False,messages=messages);r['gpu']=gpu.window(t,time.monotonic());want=list(FACTS.values()) if step==0 else [value(10 if step==1 else records//2-10)];r['expected']=want;r['correct']=all(v in r['text'] for v in want);r['step']=step;row['rounds'].append(r);messages.append({'role':'assistant','content':r['text']});dump(LAB/'raw'/f'multiturn-{key}-{step}.json',r);emit(phase='multiturn_round',key=key,step=step,correct=r['correct'],seconds=r['latency_s'],cached=r['timings'].get('cache_n'))
     row['api_ok']=True
    except Exception as e:row['api_ok']=False;row['error']=str(e)
    record('multiturn',row)
  finally:engine.restore()
if __name__=='__main__':run()
