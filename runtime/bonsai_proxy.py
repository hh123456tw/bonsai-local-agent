"""Local OpenAI bridge: bounded thinking, no reasoning replay, and recovery from repeated tools."""
import copy, hashlib, json, pathlib, threading, time, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT=pathlib.Path(__file__).resolve().parent
UPSTREAM='http://127.0.0.1:8080'
LOCK=threading.Lock()
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
def generate(body):
    b=prepare(body);calls=recent_calls(b['messages']);history=[signature(c) for c in calls]
    if len(calls)>=24:
        event('tool_budget_stop',calls=len(calls))
        return stopped('已停止：本輪已執行 24 次工具，仍未完成。請檢查目前結果；這次任務不能算成功。')
    for attempt in range(3):
        req=urllib.request.Request(UPSTREAM+'/v1/chat/completions',data=json.dumps(b).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=240) as r:result=json.load(r)
        choice=result['choices'][0];msg=choice['message'];new=msg.get('tool_calls') or []
        if choice.get('finish_reason')=='length':
            event('output_truncated',limit=b['max_tokens'],tool_calls=len(new))
        repeated=bool(new) and any(history[-2:]==[signature(c)]*2 for c in new)
        empty=not new and not (msg.get('content') or '').strip()
        if not repeated and not empty:
            event('delivered',attempt=attempt,tool_calls=len(new),finish=choice.get('finish_reason'),reasoning_tokens=result.get('usage',{}).get('completion_tokens_details',{}).get('reasoning_tokens'))
            return result
        event('recovery',attempt=attempt,reason='repeated_tool' if repeated else 'empty_answer')
        if attempt==2:
            return stopped('已停止：模型在糾正後仍重複同一工具或沒有有效回答。未完成任務，請勿視為成功。')
        b['messages'].append({'role':'user','content':('The identical tool call already ran twice and returned no progress. Do not repeat it. Inspect the prior tool outputs, change your diagnosis and use a DIFFERENT concrete action to solve the task. If you cannot proceed, explain the actual blocker honestly.' if repeated else 'Your previous attempt produced no usable answer. Stop extended reasoning and deliver the requested answer or one concrete tool action now.')})
        b['thinking_budget']=1024;b['temperature']=0.5
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send_json(self,status,body):
        data=json.dumps(body,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_GET(self):
        if self.path in ('/health','/healthz'):return self.send_json(200,{'status':'ok','service':'bonsai-guard'})
        try:
            with urllib.request.urlopen(UPSTREAM+self.path,timeout=5) as r:self.send_json(r.status,json.load(r))
        except Exception as e:self.send_json(503,{'error':{'message':str(e)}})
    def do_POST(self):
        if self.path!='/v1/chat/completions':return self.send_json(404,{'error':{'message':'Unsupported endpoint'}})
        try:
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            with LOCK:result=generate(body)
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
            try:self.send_json(e.code,json.loads(e.read()))
            except Exception:self.send_json(502,{'error':{'message':str(e)}})
        except (BrokenPipeError,ConnectionResetError):pass
        except Exception as e:self.send_json(502,{'error':{'message':str(e)}})
if __name__=='__main__':ThreadingHTTPServer(('127.0.0.1',8081),Handler).serve_forever()
