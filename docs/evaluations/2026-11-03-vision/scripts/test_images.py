"""Synthetic known-answer images through guarded APIs, no OCR helpers."""
import base64,json,time,requests
from lab import LAB,GPU,dump
BASE='http://127.0.0.1:8081'
PROMPT='Inspect the attached image. Return only JSON with keys top_left_color, top_left_shape, bottom_right_color, bottom_right_shape, code. Use lowercase English colors and shapes; code is a string of digits.'
UI='Read the dashboard image. Return only JSON with keys status, error_code, missing_field, total (all strings).'
expected=json.loads((LAB/'fixtures/expected.json').read_text())
results=[]
def image(name):return base64.b64encode((LAB/'fixtures'/f'{name}.png').read_bytes()).decode()
def check(text,want):
 try:
  obj=json.loads(text[text.index('{'):text.rindex('}')+1]);return all(str(obj.get(k,'')).lower()==v.lower() for k,v in want.items())
 except (ValueError,TypeError):return False
with GPU() as gpu:
 for index,(api,name,kind) in enumerate([('openai','fixture-a','user'),('openai','fixture-b','user'),('openai','fixture-a','user'),('anthropic','fixture-ui','user'),('anthropic','fixture-b','tool'),('anthropic','fixture-a','stream')]):
  prompt=UI if name=='fixture-ui' else PROMPT
  data=image(name)
  block={'type':'image','source':{'type':'base64','media_type':'image/png','data':data}}
  body={'model':'bonsai2-27b','max_tokens':512,'temperature':0,'stream':kind=='stream'}
  if api=='openai':
   body.update(enable_thinking=False,messages=[{'role':'user','content':[{'type':'text','text':prompt},{'type':'image_url','image_url':{'url':'data:image/png;base64,'+data}}]}]);path='/v1/chat/completions'
  else:
   body['messages']=[{'role':'user','content':[{'type':'text','text':prompt},block]}];path='/v1/messages'
   if kind=='tool':
    body['tools']=[{'name':'Read','description':'Read an image file','input_schema':{'type':'object','properties':{'file_path':{'type':'string'}},'required':['file_path']}}]
    body['messages']=[{'role':'user','content':prompt+' Read scene.png.'},{'role':'assistant','content':[{'type':'tool_use','id':'toolu_image_test','name':'Read','input':{'file_path':'scene.png'}}]},{'role':'user','content':[{'type':'tool_result','tool_use_id':'toolu_image_test','content':[block]}]}]
  start=time.monotonic();r=requests.post(BASE+path,json=body,timeout=480);end=time.monotonic()
  (LAB/'raw'/f'image-{index}.response.txt').write_text(r.text,encoding='utf-8')
  row={'index':index,'api':api,'fixture':name,'kind':kind,'status':r.status_code,'seconds':end-start,'gpu':gpu.window(start,end)}
  if r.ok:
   if kind=='stream':
    events=[json.loads(line[6:]) for line in r.text.splitlines() if line.startswith('data: ')];text=''.join(e.get('delta',{}).get('text','') for e in events);row['message_stop']=any(e['type']=='message_stop' for e in events)
   else:
    obj=r.json();text=obj['choices'][0]['message']['content'] if api=='openai' else ''.join(b.get('text','') for b in obj['content']);row['usage']=obj.get('usage')
   row.update(text=text,passed=check(text,expected[name]))
  else:row.update(passed=False,error=r.text)
  results.append(row);dump(LAB/'image-results.json',results);print(json.dumps(row),flush=True)
  if not r.ok:raise RuntimeError('Image request failed; no repeated retries')
 # Token count includes the same native media preparation route.
 body={'model':'bonsai2-27b','messages':[{'role':'user','content':[{'type':'text','text':PROMPT},{'type':'image','source':{'type':'base64','media_type':'image/png','data':image('fixture-a')}}]}]}
 r=requests.post(BASE+'/v1/messages/count_tokens',json=body,timeout=180);dump(LAB/'count-tokens.json',{'status':r.status_code,'body':r.json()});r.raise_for_status()
