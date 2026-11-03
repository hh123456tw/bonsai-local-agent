import pathlib,sys,json,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'runtime'))
import anthropic_bridge as a
import bonsai_proxy as p
from unittest.mock import patch

class Reply:
 def __init__(self,d):self.d=d
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def read(self,*args):return json.dumps(self.d).encode()
def use(command,id='toolu_1'):
 return {'type':'tool_use','id':id,'name':'Bash','input':{'command':command}}
def answer(block):
 return {'id':'msg_local','type':'message','role':'assistant','model':a.MODEL,'content':[block],'stop_reason':'tool_use' if block['type']=='tool_use' else 'end_turn','stop_sequence':None,'usage':{'input_tokens':20,'output_tokens':10}}
def repeated_history():
 return {'model':a.MODEL,'max_tokens':4096,'messages':[{'role':'user','content':'Fix it'}, {'role':'assistant','content':[use('broken','a')]},{'role':'user','content':[{'type':'tool_result','tool_use_id':'a','content':'same error'}]}, {'role':'assistant','content':[use('broken','b')]},{'role':'user','content':[{'type':'tool_result','tool_use_id':'b','content':[{'type':'text','text':'same error'}],'is_error':True},{'type':'text','text':'client reminder'}]}]}
class Tests(unittest.TestCase):
 def test_tool_result_wrappers_do_not_reset_turn_counter(self):
  converted=a.to_openai(repeated_history())
  self.assertEqual(len(p.recent_calls(converted['messages'])),2)
  self.assertEqual(converted['messages'][-1]['role'],'tool')
  self.assertIn('client reminder',converted['messages'][-1]['content'])
 def test_native_requests_strip_old_thinking_and_keep_tools(self):
  b=repeated_history();b['messages'][1]['content'].insert(0,{'type':'thinking','thinking':'old','signature':'opaque'})
  prepared=a.prepare_request(b)
  self.assertEqual(prepared['thinking']['budget_tokens'],1536)
  self.assertFalse(prepared['preserve_thinking'])
  self.assertNotIn('thinking',[x['type'] for x in prepared['messages'][1]['content']])
  self.assertIn('thinking',[x['type'] for x in b['messages'][1]['content']])
  self.assertEqual(a.count_request(b)['messages'][1]['content'][0]['type'],'tool_use')
 def test_small_output_caps_are_respected_and_invalid_caps_rejected(self):
  b=a.prepare_request({'messages':[{'role':'user','content':'OK'}],'max_tokens':8})
  self.assertEqual(b['max_tokens'],8);self.assertEqual(b['thinking']['type'],'disabled')
  with self.assertRaises(a.ProtocolError):a.prepare_request({'messages':[{'role':'user','content':'OK'}],'max_tokens':-1})
 def test_anthropic_repeated_tool_uses_same_recovery_guard(self):
  seen=[]
  def upstream(request,**kwargs):
   seen.append((request.full_url,json.loads(request.data)))
   return Reply(answer(use('broken' if len(seen)==1 else 'inspect-file')))
  with patch.object(p.urllib.request,'urlopen',side_effect=upstream),patch.object(p,'event'):
   result=p.generate(repeated_history(),anthropic_mode=True)
  self.assertEqual(result['content'][0]['input']['command'],'inspect-file')
  self.assertTrue(all(url.endswith('/v1/messages') for url,b in seen))
  self.assertEqual(seen[1][1]['thinking']['budget_tokens'],1024)
 def test_tool_budget_applies_across_anthropic_user_wrappers(self):
  b=repeated_history();base=b['messages'][1:3];b['messages']=b['messages'][:1]+base*24
  with patch.object(p,'tool_limit',return_value=24),patch.object(p.urllib.request,'urlopen') as upstream,patch.object(p,'event'):
   result=p.generate(b,anthropic_mode=True)
  upstream.assert_not_called();self.assertIn('未完成',result['content'][0]['text']);self.assertEqual(result['stop_reason'],'end_turn')
 def test_anthropic_exhausted_recovery_stops_honestly(self):
  with patch.object(p.urllib.request,'urlopen',return_value=Reply(answer(use('broken')))) as upstream,patch.object(p,'event'):
   result=p.generate(repeated_history(),anthropic_mode=True)
  self.assertEqual(upstream.call_count,3)
  self.assertEqual(result['stop_reason'],'end_turn')
  self.assertIn('未完成',result['content'][0]['text'])
  self.assertFalse(any(b['type']=='tool_use' for b in result['content']))
 def test_native_stream_thinking_text_tool_and_final_usage(self):
  msg=answer(use('echo 你好'))
  msg['content']=[{'type':'thinking','thinking':'consider','signature':'native-local-marker'},{'type':'text','text':'Checking'},use('echo 你好')]
  events=list(a.stream_events(msg))
  self.assertEqual(events[0][0],'message_start');self.assertEqual(events[-1][0],'message_stop')
  self.assertEqual([d['index'] for n,d in events if n=='content_block_start'],[0,1,2])
  tool=next(d['delta']['partial_json'] for n,d in events if n=='content_block_delta' and d['delta']['type']=='input_json_delta')
  self.assertEqual(json.loads(tool),{'command':'echo 你好'})
  self.assertEqual(events[-2][1]['delta']['stop_reason'],'tool_use')
  self.assertEqual(events[-2][1]['usage']['output_tokens'],10)
 def test_unsupported_media_fails_visibly(self):
  with self.assertRaises(a.ProtocolError):a.to_openai({'messages':[{'role':'user','content':[{'type':'image','source':{}}]}]})
if __name__=='__main__':unittest.main()
