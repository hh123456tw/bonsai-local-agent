"""A queued/preparing guarded request also prevents an engine restart."""
import json,pathlib,sys,tempfile,unittest
from unittest.mock import patch,Mock
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'runtime'))
import bonsai_ensure as e
class Tests(unittest.TestCase):
 def test_busy_bridge_refuses_switch_before_stopping_or_writing(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp)
   (root/'profiles.json').write_text(json.dumps({'vision':{'engine_options':'vision.json'}}))
   (root/'vision.json').write_text('["--vision"]')
   (root/'engine-options.json').write_text('["old"]')
   with patch.object(e,'ROOT',root),patch.object(e,'ready',return_value=True),patch.object(e,'process_options',return_value=['old']),patch.object(e.requests,'get',return_value=Mock(json=lambda:{'busy':True})),patch.object(e.subprocess,'run') as stop:
    with self.assertRaisesRegex(RuntimeError,'bridge is busy'):e.ensure('vision')
   stop.assert_not_called();self.assertEqual((root/'engine-options.json').read_text(),'["old"]')
