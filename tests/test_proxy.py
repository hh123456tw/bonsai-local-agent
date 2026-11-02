import unittest,sys,json
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parents[1]/'runtime'))
import bonsai_proxy as p
from unittest.mock import patch
class Reply:
 def __init__(self,d):self.d=d
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def read(self,*a):return json.dumps(self.d).encode()
def call(command):return {'id':'c1','type':'function','function':{'name':'bash','arguments':json.dumps({'command':command})}}
def response(c=None,text=None):return {'choices':[{'message':{'role':'assistant','content':text,'tool_calls':c or []},'finish_reason':'tool_calls' if c else 'stop'}]}
class Tests(unittest.TestCase):
 def test_thinking_is_bounded_and_not_replayed(self):
  b=p.prepare({'messages':[{'role':'assistant','content':'ok','reasoning_content':'old'}],'max_tokens':8192,'stream':True})
  self.assertNotIn('reasoning_content',b['messages'][0]);self.assertFalse(b['preserve_thinking']);self.assertEqual(b['thinking_budget'],1536)
 def test_large_output_request_is_not_silently_reduced_to_8k(self):
  b=p.prepare({'messages':[{'role':'user','content':'summarize'}],'max_tokens':24000})
  self.assertEqual(b['max_tokens'],24000)
 def test_repeated_tool_is_recovered_with_different_action(self):
  c=call('broken');b={'messages':[{'role':'user','content':'fix'}, {'role':'assistant','tool_calls':[c]},{'role':'tool','content':'error'},{'role':'assistant','tool_calls':[c]},{'role':'tool','content':'error'}]}
  with patch.object(p.urllib.request,'urlopen',side_effect=[Reply(response([c])),Reply(response([call('different')]))]),patch.object(p,'event'):
   result=p.generate(b)
  self.assertEqual(p.signature(result['choices'][0]['message']['tool_calls'][0]),p.signature(call('different')))
 def test_failed_recovery_is_not_reported_as_success(self):
  with patch.object(p.urllib.request,'urlopen',side_effect=[Reply(response())]*3),patch.object(p,'event'):
   result=p.generate({'messages':[{'role':'user','content':'fix'}]})
  self.assertIn('未完成任務',result['choices'][0]['message']['content'])
if __name__=='__main__':unittest.main()
