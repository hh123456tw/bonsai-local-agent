"""Exercise real HTTP status/SSE boundaries with a deterministic upstream."""
import http.client,json,pathlib,sys,threading,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'runtime'))
import bonsai_proxy as p
from test_request_budget import Reply,answer

class HTTPTests(unittest.TestCase):
 def setUp(self):
  self.server=p.ThreadingHTTPServer(('127.0.0.1',0),p.Handler)
  self.thread=threading.Thread(target=lambda:self.server.serve_forever(poll_interval=.01),daemon=True);self.thread.start()
 def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join(timeout=2)
 def post(self,path,body):
  c=http.client.HTTPConnection('127.0.0.1',self.server.server_address[1],timeout=3)
  try:
   c.request('POST',path,body=json.dumps(body),headers={'Content-Type':'application/json'});r=c.getresponse();return r.status,r.read().decode('utf-8')
  finally:c.close()
 def test_conflicting_budget_is_400_and_never_contacts_model(self):
  with patch.object(p.urllib.request,'urlopen') as upstream:
   status,text=self.post('/v1/chat/completions',{'messages':[{'role':'user','content':'OK'}],'max_tokens':16,'max_completion_tokens':32})
  self.assertEqual(status,400);self.assertIn('must agree',json.loads(text)['error']['message']);upstream.assert_not_called()
 def test_oversized_image_body_is_rejected_before_model_or_decode(self):
  with patch.object(p,'MAX_REQUEST_BYTES',32),patch.object(p.urllib.request,'urlopen') as upstream:
   status,text=self.post('/v1/messages',{'messages':[{'role':'user','content':'Long image payload placeholder'}],'max_tokens':256})
  self.assertEqual(status,413);self.assertEqual(json.loads(text)['error']['type'],'request_too_large');upstream.assert_not_called()
 def test_malformed_tool_is_502_and_never_a_delivered_tool(self):
  call={'id':'c1','type':'function','function':{'name':'Edit','arguments':'{"file_path":'}}
  with patch.object(p.urllib.request,'urlopen',return_value=Reply(answer(None,'tool_calls',[call]))),patch.object(p,'event'):
   status,text=self.post('/v1/chat/completions',{'messages':[{'role':'user','content':'Edit'}],'max_tokens':64,'stream':True})
  self.assertEqual(status,502);self.assertEqual(json.loads(text)['error']['code'],'invalid_tool_arguments');self.assertNotIn('choices',json.loads(text))
 def test_small_stream_preserves_length_and_final_usage(self):
  result=answer('測試','length');result.update(id='test',model='bonsai2-27b',object='chat.completion',usage={'prompt_tokens':10,'completion_tokens':4,'total_tokens':14})
  with patch.object(p.urllib.request,'urlopen',return_value=Reply(result)),patch.object(p,'event'):
   status,text=self.post('/v1/chat/completions',{'messages':[{'role':'user','content':'OK'}],'max_tokens':4,'enable_thinking':False,'stream':True})
  self.assertEqual(status,200);self.assertIn('[DONE]',text)
  events=[json.loads(s[6:]) for s in text.splitlines() if s.startswith('data: ') and s!='data: [DONE]']
  self.assertEqual(events[-1]['choices'][0]['finish_reason'],'length');self.assertEqual(events[-1]['usage']['completion_tokens'],4)
 def test_mixed_tool_batch_is_rejected_atomically_before_sse_headers(self):
  valid={'id':'c1','type':'function','function':{'name':'Edit','arguments':'{"file_path":"x.py"}'}}
  invalid={'id':'c2','type':'function','function':{'name':'Write','arguments':'{"file_path":'}}
  with patch.object(p.urllib.request,'urlopen',return_value=Reply(answer(None,'tool_calls',[valid,invalid]))),patch.object(p,'event'):
   status,text=self.post('/v1/chat/completions',{'messages':[{'role':'user','content':'Edit'}],'max_tokens':2048,'stream':True})
  self.assertEqual(status,502);self.assertEqual(json.loads(text)['error']['code'],'invalid_tool_arguments');self.assertNotIn('data:',text);self.assertNotIn('choices',json.loads(text))
 def test_anthropic_truncated_batch_also_fails_closed(self):
  result={'id':'m1','type':'message','role':'assistant','model':'bonsai2-27b','content':[{'type':'tool_use','id':'c1','name':'Edit','input':{'file_path':'x.py'}}],'stop_reason':'max_tokens','usage':{'input_tokens':10,'output_tokens':16}}
  with patch.object(p.urllib.request,'urlopen',return_value=Reply(result)),patch.object(p,'event'):
   status,text=self.post('/v1/messages',{'messages':[{'role':'user','content':'Edit'}],'max_tokens':16})
  self.assertEqual(status,502);self.assertEqual(json.loads(text)['type'],'error');self.assertIn('no tool',json.loads(text)['error']['message'])

if __name__=='__main__':unittest.main()
