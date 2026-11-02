import requests,pathlib,time,json,hashlib,sys,threading,subprocess
context=int(sys.argv[1]);label=sys.argv[2];base='http://127.0.0.1:8080';thinking='--thinking' in sys.argv
out=pathlib.Path('reports');out.mkdir(exist_ok=True)
def value(i):return hashlib.sha256(f'public-bonsai-context-fixture-v1:{i}'.encode()).hexdigest()[:16]
expected={'SECRET_ALPHA':'VIOLET-582731','SECRET_BETA':'COPPER-294865','SECRET_GAMMA':'ORBIT-716943'}
def make(n):
 lines=[f'item_{i:06d}: {value(i)}' for i in range(n)]
 for pos,(k,v) in zip((n//20,n//2,n*19//20),expected.items()):lines.insert(pos,f'{k} = {v}')
 return 'Read these reference records. Preserve exact facts for later questions.\n'+'\n'.join(lines)+'\nReturn only a JSON object with the exact values of SECRET_ALPHA, SECRET_BETA, and SECRET_GAMMA.'
def count(text):
 r=requests.post(base+'/v1/messages/count_tokens',json={'model':'bonsai2-27b','messages':[{'role':'user','content':text}],'thinking':{'type':'disabled'}},timeout=60);r.raise_for_status();return r.json()['input_tokens']
n=1000;t=count(make(n));target=context-16384;n=int(n*target/t)
text=make(n);tokens=count(text)
if abs(tokens-target)>1500:n=int(n*target/tokens);text=make(n);tokens=count(text)
print(json.dumps({'label':label,'records':n,'prompt_tokens':tokens,'context':context}),flush=True)
result={'label':label,'context':context,'counted_prompt_tokens':tokens,'records':n,'rounds':[]}
messages=[{'role':'user','content':text}]
questions=[None,'Return the exact value of item_000010. No explanation.',f'Return the exact value of item_{n//2-10:06d}. No explanation.']
answers=[list(expected.values()),[value(10)],[value(n//2-10)]]
for i,(question,want) in enumerate(zip(questions,answers)):
 if question:messages.append({'role':'user','content':question})
 start=time.monotonic();r=requests.post(base+'/v1/chat/completions',json={'model':'bonsai2-27b','messages':messages,'max_tokens':2048 if thinking else 256,'thinking_budget':1536,'enable_thinking':thinking,'temperature':0,'stream':False},timeout=720)
 row={'round':i+1,'status':r.status_code,'wall_seconds':round(time.monotonic()-start,2)}
 if r.status_code==200:
  d=r.json();m=d['choices'][0]['message'];answer=m.get('content') or ''
  row.update(answer=answer,expected=want,correct=all(v.lower() in answer.lower() for v in want),usage=d.get('usage'),timings=d.get('timings'),finish=d['choices'][0].get('finish_reason'))
  messages.append({'role':'assistant','content':answer})
 else:row.update(correct=False,error=r.text[:1000])
 result['rounds'].append(row);(out/(label+'-long.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps(row),flush=True)
 if r.status_code!=200:break
result['passed']=len(result['rounds'])==3 and all(x['correct'] for x in result['rounds'])
(out/(label+'-long.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
sys.exit(0 if result['passed'] else 2)
