import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'runtime'))
import claude_launch as c
from unittest.mock import patch
class Tests(unittest.TestCase):
 def test_environment_is_local_scoped_and_uses_profile_context(self):
  with patch.object(c,'ROOT',pathlib.Path(__file__).resolve().parents[1]/'config'),patch.dict(c.os.environ,{'ANTHROPIC_API_KEY':'test-secret','CLAUDE_CODE_USE_BEDROCK':'1','DISABLE_COMPACT':'1'}):
   fast=c.environment('dflash144');large=c.environment('base256')
  self.assertNotIn('ANTHROPIC_API_KEY',fast);self.assertNotIn('CLAUDE_CODE_USE_BEDROCK',fast);self.assertNotIn('DISABLE_COMPACT',fast)
  self.assertEqual(fast['ANTHROPIC_BASE_URL'],'http://127.0.0.1:8081')
  self.assertEqual(fast['CLAUDE_CODE_MAX_CONTEXT_TOKENS'],'147456');self.assertEqual(large['CLAUDE_CODE_MAX_CONTEXT_TOKENS'],'262144')
  self.assertEqual(fast['CLAUDE_CODE_AUTO_COMPACT_WINDOW'],'122880')
  self.assertEqual(large['CLAUDE_CODE_AUTO_COMPACT_WINDOW'],'229376')
  self.assertEqual(fast['ANTHROPIC_DEFAULT_HAIKU_MODEL'],'bonsai2-27b')
if __name__=='__main__':unittest.main()
