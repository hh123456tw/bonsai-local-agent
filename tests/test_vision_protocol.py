import copy,json,pathlib,sys,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'runtime'))
import anthropic_bridge as a
import bonsai_proxy as p
from test_anthropic import Reply,answer,use,repeated_history

PNG='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jH1EAAAAASUVORK5CYII='
def image():return {'type':'image','source':{'type':'base64','media_type':'image/png','data':PNG}}
class Tests(unittest.TestCase):
 def test_user_image_reaches_native_anthropic_generation(self):
  body={'model':a.MODEL,'max_tokens':512,'messages':[{'role':'user','content':[image(),{'type':'text','text':'Describe it.'}]}]};original=copy.deepcopy(body);seen=[]
  def upstream(req,**kw):seen.append(json.loads(req.data));return Reply(answer({'type':'text','text':'An image.'}))
  with patch.object(p.urllib.request,'urlopen',side_effect=upstream),patch.object(p,'event'):
   result=p.generate(body,anthropic_mode=True)
  self.assertEqual(seen[0]['messages'][0]['content'][0],image());self.assertEqual(body,original);self.assertEqual(result['content'][0]['text'],'An image.')
  converted=a.to_openai(body);self.assertEqual(converted['messages'][0]['content'][0]['image_url']['url'],'data:image/png;base64,'+PNG)
 def test_read_image_tool_result_preserves_image_and_turn_guard(self):
  body=repeated_history();body['messages'][-1]['content'][0]['content']=[{'type':'text','text':'Read result'},image()]
  converted=a.to_openai(body);self.assertEqual(len(p.recent_calls(converted['messages'])),2)
  self.assertEqual(converted['messages'][-1]['role'],'tool');parts=converted['messages'][-1]['content'];self.assertTrue(any(x['type']=='image_url' for x in parts))
  self.assertIn('client reminder',' '.join(x.get('text','') for x in parts))
  self.assertEqual(a.prepare_request(body)['messages'][-1]['content'][0]['content'][1],image())
 def test_outer_image_after_tool_results_does_not_reset_tool_counter(self):
  body=repeated_history();body['messages'][-1]['content'].append(image());converted=a.to_openai(body)
  self.assertEqual(len(p.recent_calls(converted['messages'])),2);self.assertEqual(converted['messages'][-1]['role'],'tool')
  self.assertTrue(any(x['type']=='image_url' for x in converted['messages'][-1]['content']))
 def test_count_route_preserves_images_without_replaying_thought(self):
  body={'messages':[{'role':'user','content':[image(),{'type':'text','text':'What is it?'}]}]}
  self.assertEqual(a.count_request(body)['messages'],body['messages'])
 def test_url_source_converts_without_fetching_in_bridge(self):
  body={'messages':[{'role':'user','content':[{'type':'image','source':{'type':'url','url':'https://example.com/test.png'}}]}]}
  self.assertEqual(a.to_openai(body)['messages'][0]['content'][0]['image_url']['url'],'https://example.com/test.png')
 def test_invalid_images_and_other_media_still_fail_visibly(self):
  bad=[{'type':'document','source':{}},{'type':'image','source':{'type':'url','url':'file:///C:/secret.png'}},{'type':'image','source':{'type':'base64','media_type':'image/png','data':'???'}},{'type':'image','source':{'type':'base64','media_type':'image/svg+xml','data':PNG}}]
  for block in bad:
   with self.subTest(block=block),self.assertRaises(a.ProtocolError):a.to_openai({'messages':[{'role':'user','content':[block]}]})
  with self.assertRaises(a.ProtocolError):a.to_openai({'messages':[{'role':'assistant','content':[image()]}]})
 def test_openai_images_remain_intact(self):
  parts=[{'type':'text','text':'Describe'},{'type':'image_url','image_url':{'url':'data:image/png;base64,'+PNG}}]
  body={'messages':[{'role':'user','content':parts}],'max_tokens':256,'enable_thinking':False};self.assertEqual(p.prepare(body)['messages'][0]['content'],parts)
 def test_image_size_limit_is_enforced_without_a_large_fixture(self):
  with patch.object(a,'MAX_IMAGE_BYTES',4),self.assertRaises(a.ProtocolError):a.to_openai({'messages':[{'role':'user','content':[image()]}]})

if __name__=='__main__':unittest.main()
