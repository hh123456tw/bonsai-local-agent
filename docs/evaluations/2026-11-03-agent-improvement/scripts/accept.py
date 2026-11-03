import pathlib,sys,unittest,importlib.util,json
project=pathlib.Path(sys.argv[1]).resolve();acceptance=pathlib.Path(sys.argv[2]).resolve()
sys.path.insert(0,str(project))
spec=importlib.util.spec_from_file_location('external_acceptance',acceptance);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
suite=unittest.defaultTestLoader.loadTestsFromModule(module);result=unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful()}));sys.exit(0 if result.wasSuccessful() else 1)
