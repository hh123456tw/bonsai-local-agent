"""Request-to-upstream regression tests for client budgets and tool safety."""
import json,pathlib,sys,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'runtime'))
import bonsai_proxy as p
import anthropic_bridge as a

class Reply:
 def __init__(self,body):self.body=body
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def read(self,*args):return json.dumps(self.body).encode()

def answer(content='OK',finish='stop',calls=None):
 return {'choices':[{'message':{'role':'assistant','content':content,'tool_calls':calls or []},'finish_reason':finish}]}

def request(**kwargs):return {'messages':[{'role':'user','content':'Explain Python unit testing in detail.'}],**kwargs}

class BudgetTests(unittest.TestCase):
 def forward(self,body,replies=None):
  seen=[];replies=iter(replies or [answer()])
  def upstream(req,**kw):seen.append(json.loads(req.data));return Reply(next(replies))
  with patch.object(p.urllib.request,'urlopen',side_effect=upstream),patch.object(p,'event'),patch.object(p,'tool_limit',return_value=None):result=p.generate(body)
  return seen,result
 def test_exact_small_cap_and_disabled_thinking_reach_upstream(self):
  seen,_=self.forward(request(max_tokens=16,enable_thinking=False))
  self.assertEqual(seen[0]['max_tokens'],16)
  self.assertFalse(seen[0]['enable_thinking'])
  self.assertEqual(seen[0]['thinking_budget'],0)
 def test_max_completion_tokens_alias_and_small_auto_budget(self):
  seen,_=self.forward(request(max_completion_tokens=16))
  self.assertEqual(seen[0]['max_tokens'],16);self.assertNotIn('max_completion_tokens',seen[0]);self.assertFalse(seen[0]['enable_thinking'])
 def test_explicit_thinking_budget_is_preserved(self):
  seen,_=self.forward(request(max_tokens=2048,enable_thinking=True,thinking_budget=1024))
  self.assertTrue(seen[0]['enable_thinking']);self.assertEqual(seen[0]['thinking_budget'],1024)
 def test_default_daily_policy_is_unchanged(self):
  seen,_=self.forward(request())
  self.assertEqual(seen[0]['max_tokens'],16384);self.assertTrue(seen[0]['enable_thinking']);self.assertEqual(seen[0]['thinking_budget'],1536)
 def test_invalid_or_contradictory_budgets_fail_before_upstream(self):
  bad=[{'max_tokens':x} for x in (0,-1,True,1.5,'16',None,32769)]
  bad += [{'max_tokens':16,'max_completion_tokens':32},{'max_tokens':16,'enable_thinking':True},{'max_tokens':512,'enable_thinking':True,'thinking_budget':400},{'max_tokens':512,'thinking_budget':64},{'enable_thinking':'false'},{'thinking_budget':-1},{'thinking_budget':True},{'thinking_budget':1537}]
  for fields in bad:
   with self.subTest(fields=fields),patch.object(p.urllib.request,'urlopen') as upstream:
    with self.assertRaises(a.ProtocolError):p.generate(request(**fields))
    upstream.assert_not_called()
 def test_equal_aliases_are_allowed(self):
  seen,_=self.forward(request(max_tokens=512,max_completion_tokens=512,enable_thinking=False))
  self.assertEqual(seen[0]['max_tokens'],512)
 def test_zero_budget_means_disabled(self):
  seen,_=self.forward(request(thinking_budget=0))
  self.assertFalse(seen[0]['enable_thinking']);self.assertEqual(seen[0]['thinking_budget'],0)
 def test_empty_truncation_is_returned_without_recovery_or_budget_growth(self):
  seen,result=self.forward(request(max_tokens=8,enable_thinking=False),[answer('',finish='length')])
  self.assertEqual(len(seen),1);self.assertEqual(result['choices'][0]['finish_reason'],'length')
 def test_empty_answer_recovery_never_reenables_thinking_or_inflates_cap(self):
  seen,_=self.forward(request(max_tokens=16,enable_thinking=False),[answer(''),answer()])
  self.assertEqual(len(seen),2)
  self.assertTrue(all(x['max_tokens']==16 and not x['enable_thinking'] and x['thinking_budget']==0 for x in seen))
 def test_tool_arguments_cannot_be_delivered_when_incomplete(self):
  call={'id':'tool1','type':'function','function':{'name':'Edit','arguments':'{"file_path":'}}
  with self.assertRaises(RuntimeError):self.forward(request(max_tokens=64),[answer(None,'tool_calls',[call])])
 def test_truncated_tool_batch_cannot_be_executed_even_with_parseable_json(self):
  call={'id':'tool1','type':'function','function':{'name':'Edit','arguments':'{"file_path":"x.py"}'}}
  with self.assertRaises(RuntimeError):self.forward(request(max_tokens=64),[answer(None,'length',[call])])

if __name__=='__main__':unittest.main()
