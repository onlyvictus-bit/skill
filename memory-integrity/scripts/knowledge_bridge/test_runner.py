"""Explicit local unittest observer. This executes tests, unlike source extraction."""
import contextlib,inspect,io,json,os,socket,sys,unittest
from pathlib import Path

def main():
    config=json.loads(Path(sys.argv[1]).read_text());root=Path(config['root']).resolve();sys.path.insert(0,str(root));os.chdir(root)
    def blocked(*args,**kwargs):raise RuntimeError('E_TEST_NETWORK_FORBIDDEN')
    socket.socket.connect=blocked;socket.socket.connect_ex=blocked;socket.create_connection=blocked
    cases=[]
    class Result(unittest.TextTestResult):
        def observe(self,test,status):
            method=getattr(test,test._testMethodName,None)
            try:
                path=Path(inspect.getsourcefile(method)).resolve();lines,start=inspect.getsourcelines(method)
                relative=path.relative_to(root).as_posix();end=start+len(lines)-1
            except (TypeError,OSError,ValueError):relative=None;start=None;end=None
            cases.append({'id':test.id(),'status':status,'path':relative,'lines':[start,end]})
        def addSuccess(self,t):super().addSuccess(t);self.observe(t,'pass')
        def addFailure(self,t,e):super().addFailure(t,e);self.observe(t,'fail')
        def addError(self,t,e):super().addError(t,e);self.observe(t,'error')
        def addSkip(self,t,r):super().addSkip(t,r);self.observe(t,'skipped')
        def addExpectedFailure(self,t,e):super().addExpectedFailure(t,e);self.observe(t,'expected_failure')
        def addUnexpectedSuccess(self,t):super().addUnexpectedSuccess(t);self.observe(t,'unexpected_success')
        def addSubTest(self,t,sub,err):
            super().addSubTest(t,sub,err)
            if err is not None:self.observe(t,'fail' if issubclass(err[0],t.failureException) else 'error')
    # Tests can print arbitrary data; discard it rather than exposing it in a receipt.
    with open(os.devnull,'w') as sink,contextlib.redirect_stdout(sink),contextlib.redirect_stderr(sink):
        loader=unittest.TestLoader();suite=unittest.TestSuite()
        for relative in config['test_paths']:
            path=root/relative
            suite.addTests(loader.discover(str(path.parent),pattern=path.name,top_level_dir=str(root)))
        result=unittest.TextTestRunner(stream=sink,resultclass=Result,verbosity=0).run(suite)
    payload={'cases':cases,'tests_run':result.testsRun,'ok':bool(cases) and result.wasSuccessful() and all(c['status']=='pass' for c in cases)}
    Path(config['output']).write_text(json.dumps(payload))
if __name__=='__main__':main()
