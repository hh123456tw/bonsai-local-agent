"""Local OpenAI/Anthropic bridge with bounded thinking and repeated-tool recovery."""
import copy, hashlib, json, pathlib, threading, time, urllib.request, urllib.error,urllib.parse,uuid
import anthropic_bridge as anthropic
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT=pathlib.Path(__file__).resolve().parent
UPSTREAM='http://127.0.0.1:8080'
LOCK=threading.Lock()

def tool_limit():
    path=ROOT/'guard-config.json'
    limit=json.loads(path.read_text(encoding='utf-8')).get('max_tool_calls') if path.exists() else None
    if limit is None:return None
    if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=1000:
        raise ValueError('guard-config.json: max_tool_calls must be null (unlimited) or an integer from 1 to 1000')
    return limit
def signature(call):
    f=call.get('function',{})
    try: args=json.loads(f.get('arguments','{}'))
    except (ValueError,TypeError): args=f.get('arguments','')
    if isinstance(args,dict):args={k:v for k,v in args.items() if k not in ('description','timeout')}
    return f.get('name','')+':'+json.dumps(args,sort_keys=True,ensure_ascii=False)
def recent_calls(messages):
    last_user=max((i for i,m in enumerate(messages) if m.get('role')=='user'),default=0)
    return [c for m in messages[last_user:] for c in m.get('tool_calls',[])]
def prepare(body):
    b=copy.deepcopy(body)
    for m in b.get('messages',[]):
        for field in ('reasoning_content','reasoning','reasoning_text'):m.pop(field,None)
    b['preserve_thinking']=False
    b['enable_thinking']=True
    b['thinking_budget']=1536
    b['max_tokens']=min(max(int(b.get('max_tokens') or b.get('max_completion_tokens') or 16384),2048),32768)
    b.pop('max_completion_tokens',None)
    b['stream']=False;b.pop('stream_options',None)
    b.setdefault('temperature',0.3)
    return b
def event(kind,**fields):
    with (ROOT/'guard-events.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps({'time':time.time(),'kind':kind,**fields})+'\n')
def stopped(message):
    return {'id':'guard-'+str(time.time_ns()),'object':'chat.completion','created':int(time.time()),'model':'bonsai2-27b','choices':[{'index':0,'message':{'role':'assistant','content':message},'finish_reason':'stop'}],'usage':{'prompt_tokens':0,'completion_tokens':0,'total_tokens':0}}
def generate(body,anthropic_mode=False):
    b=anthropic.prepare_request(body) if anthropic_mode else prepare(body)
    canonical=anthropic.to_openai(b) if anthropic_mode else b
    calls=recent_calls(canonical['messages']);history=[signature(c) for c in calls]
    def finish_stopped(message):
        result=stopped(message)
        return anthropic.from_openai(result) if anthropic_mode else result
    limit=tool_limit()
    if limit is not None and len(calls)>=limit:
        event('tool_budget_stop',protocol='anthropic' if anthropic_mode else 'openai',calls=len(calls),limit=limit)
        return finish_stopped(f'已暫停：本輪已記錄 {len(calls)} 次工具呼叫（包含失敗或遭拒的呼叫），達橋接設定上限 {limit} 次。此步未再請求模型，目前回報未完成，請檢查實際進度；不代表已確認陷入循環。若要接續，請輸入「繼續，先檢查目前進度，再處理剩餘工作」。新使用者輪次會重新計數；這次任務不能算成功。')
    for attempt in range(3):
        route='/v1/messages' if anthropic_mode else '/v1/chat/completions'
        req=urllib.request.Request(UPSTREAM+route,data=json.dumps(b).encode(),headers={'Content-Type':'application/json','anthropic-version':'2023-06-01'})
        with urllib.request.urlopen(req,timeout=900) as r:result=json.load(r)
        view=anthropic.openai_view(result) if anthropic_mode else result
        choice=view['choices'][0];msg=choice['message'];new=msg.get('tool_calls') or []
        if limit is not None and len(calls)+len(new)>limit:
            event('tool_budget_batch_stop',calls=len(calls),proposed=len(new),limit=limit)
            return finish_stopped(f'已暫停：本輪已記錄 {len(calls)} 次工具呼叫，模型一次提出 {len(new)} 次，將超過橋接上限 {limit} 次；這批工具未放行。任務未完成。請輸入「繼續，先檢查目前進度，再處理剩餘工作」後接續。')
        if choice.get('finish_reason')=='length':
            event('output_truncated',limit=b['max_tokens'],tool_calls=len(new))
        repeated=bool(new) and any(history[-2:]==[signature(c)]*2 for c in new)
        empty=not new and not (msg.get('content') or '').strip()
        if not repeated and not empty:
            event('delivered',protocol='anthropic' if anthropic_mode else 'openai',attempt=attempt,prior_tool_calls=len(calls),tool_limit=limit,tool_calls=len(new),finish=choice.get('finish_reason'),reasoning_tokens=view.get('usage',{}).get('completion_tokens_details',{}).get('reasoning_tokens'))
            return result
        event('recovery',attempt=attempt,reason='repeated_tool' if repeated else 'empty_answer')
        if attempt==2:
            return finish_stopped('已停止：模型在糾正後仍重複同一工具或沒有有效回答。未完成任務，請勿視為成功。')
        b['messages'].append({'role':'user','content':('The identical tool call already ran twice and returned no progress. Do not repeat it. Inspect the prior tool outputs, change your diagnosis and use a DIFFERENT concrete action to solve the task. If you cannot proceed, explain the actual blocker honestly.' if repeated else 'Your previous attempt produced no usable answer. Stop extended reasoning and deliver the requested answer or one concrete tool action now.')})
        if anthropic_mode:
            if b['thinking']['type']=='enabled':b['thinking']['budget_tokens']=1024
        else:b['thinking_budget']=1024
        b['temperature']=0.5
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send_json(self,status,body):
        data=json.dumps(body,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)))
        if getattr(self,'request_id',None):self.send_header('request-id',self.request_id)
        self.end_headers();self.wfile.write(data)
    def do_GET(self):
        if self.path in ('/health','/healthz'):return self.send_json(200,{'status':'ok','service':'bonsai-guard','max_tool_calls':tool_limit()})
        try:
            with urllib.request.urlopen(UPSTREAM+self.path,timeout=5) as r:self.send_json(r.status,json.load(r))
        except Exception as e:self.send_json(503,{'error':{'message':str(e)}})
    def do_POST(self):
        self.request_id='req_bonsai_'+uuid.uuid4().hex
        path=urllib.parse.urlsplit(self.path).path
        is_anthropic=path in ('/v1/messages','/v1/messages/count_tokens')
        if path!='/v1/chat/completions' and not is_anthropic:return self.send_json(404,{'error':{'message':'Unsupported endpoint'}})
        try:
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            if path=='/v1/messages/count_tokens':
                req=urllib.request.Request(UPSTREAM+path,data=json.dumps(anthropic.count_request(body)).encode(),headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(req,timeout=60) as r:return self.send_json(200,json.load(r))
            with LOCK:result=generate(body,anthropic_mode=is_anthropic)
            if is_anthropic:
                message=result
                if not body.get('stream'):return self.send_json(200,message)
                self.send_response(200);self.send_header('Content-Type','text/event-stream; charset=utf-8');self.send_header('request-id',message['id']);self.send_header('Cache-Control','no-cache');self.end_headers()
                for name,data in anthropic.stream_events(message):self.wfile.write(('event: '+name+'\ndata: '+json.dumps(data,ensure_ascii=False)+'\n\n').encode())
                self.wfile.flush();return
            if not body.get('stream'):return self.send_json(200,result)
            self.send_response(200);self.send_header('Content-Type','text/event-stream; charset=utf-8');self.send_header('Cache-Control','no-cache');self.end_headers()
            c=result['choices'][0];m=c['message'];delta={'role':'assistant'}
            if m.get('content') is not None:delta['content']=m['content']
            if m.get('reasoning_content'):delta['reasoning_content']=m['reasoning_content']
            if m.get('tool_calls'):delta['tool_calls']=[dict(call,index=i) for i,call in enumerate(m['tool_calls'])]
            chunk={k:v for k,v in result.items() if k not in ('choices','usage')};chunk['object']='chat.completion.chunk'
            for d,finish in ((delta,None),({},c.get('finish_reason','stop'))):
                out=dict(chunk,choices=[{'index':0,'delta':d,'finish_reason':finish}])
                if finish:out['usage']=result.get('usage',{})
                self.wfile.write(('data: '+json.dumps(out,ensure_ascii=False)+'\n\n').encode())
            self.wfile.write(b'data: [DONE]\n\n');self.wfile.flush()
        except urllib.error.HTTPError as e:
            if is_anthropic:
                try:detail=json.loads(e.read()).get('error',{}).get('message',str(e))
                except Exception:detail=str(e)
                if e.code==400 and ('max_context' in detail or 'context_length_exceeded' in detail):detail='prompt is too long: '+detail
                kind='rate_limit_error' if e.code==429 else 'overloaded_error' if e.code in (503,529) else 'invalid_request_error' if e.code<500 else 'api_error'
                self.send_json(e.code,{'type':'error','error':{'type':kind,'message':detail}})
            else:
                try:self.send_json(e.code,json.loads(e.read()))
                except Exception:self.send_json(502,{'error':{'message':str(e)}})
        except (anthropic.ProtocolError,json.JSONDecodeError) as e:
            self.send_json(400,{'type':'error','error':{'type':'invalid_request_error','message':str(e)}} if is_anthropic else {'error':{'message':str(e)}})
        except (BrokenPipeError,ConnectionResetError):pass
        except Exception as e:self.send_json(502,{'type':'error','error':{'type':'api_error','message':str(e)}} if is_anthropic else {'error':{'message':str(e)}})
if __name__=='__main__':ThreadingHTTPServer(('127.0.0.1',8081),Handler).serve_forever()
