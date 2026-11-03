import json,pathlib,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'runtime'))
import bonsai_proxy as p
from test_anthropic import Reply,answer,use

def history(n):
 messages=[{'role':'user','content':'Finish a multi-step project'}]
 for i in range(n):
  messages.extend([{'role':'assistant','content':[use('inspect-'+str(i),str(i))]}, {'role':'user','content':[{'type':'tool_result','tool_use_id':str(i),'content':'Completed step '+str(i)}]}])
 return {'messages':messages,'max_tokens':2048}

class Tests(unittest.TestCase):
 def test_24_calls_can_continue_under_64_limit(self):
  with patch.object(p,'tool_limit',return_value=64),patch.object(p.urllib.request,'urlopen',return_value=Reply(answer({'type':'text','text':'Next verified step'}))) as upstream,patch.object(p,'event'):
   result=p.generate(history(24),anthropic_mode=True)
  upstream.assert_called_once();self.assertEqual(result['content'][0]['text'],'Next verified step')
 def test_64_calls_stop_without_upstream_and_explain_resume(self):
  with patch.object(p,'tool_limit',return_value=64),patch.object(p.urllib.request,'urlopen') as upstream,patch.object(p,'event'):
   result=p.generate(history(64),anthropic_mode=True)
  upstream.assert_not_called();text=result['content'][0]['text'];self.assertIn('64',text);self.assertIn('繼續',text);self.assertIn('未完成',text)
 def test_real_user_continuation_starts_new_budget(self):
  b=history(64);b['messages'].append({'role':'assistant','content':'Budget stopped; unfinished'});b['messages'].append({'role':'user','content':'繼續，先檢查目前進度，再處理剩餘工作。'})
  with patch.object(p,'tool_limit',return_value=64),patch.object(p.urllib.request,'urlopen',return_value=Reply(answer(use('inspect-remaining')))) as upstream,patch.object(p,'event'):
   result=p.generate(b,anthropic_mode=True)
  upstream.assert_called_once();self.assertEqual(result['stop_reason'],'tool_use')
 def test_policy_hot_reload_and_reject_unbounded_or_invalid_values(self):
  with tempfile.TemporaryDirectory() as d,patch.object(p,'ROOT',pathlib.Path(d)):
   self.assertIsNone(p.tool_limit())
   policy=pathlib.Path(d)/'guard-config.json'
   for limit in (24,64,96):
    policy.write_text(json.dumps({'max_tool_calls':limit}),encoding='utf-8');self.assertEqual(p.tool_limit(),limit)
   policy.write_text('{"max_tool_calls":null}',encoding='utf-8');self.assertIsNone(p.tool_limit())
   for bad in (0,-1,True,'64',1001):
    policy.write_text(json.dumps({'max_tool_calls':bad}),encoding='utf-8')
    with self.assertRaises(ValueError):p.tool_limit()
 def test_unlimited_policy_allows_more_than_64_calls(self):
  with patch.object(p,'tool_limit',return_value=None),patch.object(p.urllib.request,'urlopen',return_value=Reply(answer({'type':'text','text':'Verified next step'}))) as upstream,patch.object(p,'event'):
   result=p.generate(history(128),anthropic_mode=True)
  upstream.assert_called_once();self.assertEqual(result['content'][0]['text'],'Verified next step')
 def test_parallel_batch_cannot_exceed_remaining_budget(self):
  result=answer(use('next-63'));result['content'].append(use('next-64','extra'))
  with patch.object(p,'tool_limit',return_value=64),patch.object(p.urllib.request,'urlopen',return_value=Reply(result)),patch.object(p,'event'):
   out=p.generate(history(63),anthropic_mode=True)
  self.assertEqual(out['stop_reason'],'end_turn');self.assertFalse(any(b['type']=='tool_use' for b in out['content']))
if __name__=='__main__':unittest.main()
