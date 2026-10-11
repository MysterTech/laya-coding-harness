import concurrent.futures
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys

import pytest

from laya_harness import launchd as probe


@pytest.fixture
def home(tmp_path, monkeypatch):
    path = tmp_path / 'state with spaces'
    path.mkdir(mode=0o700)
    (path / 'config.json').write_text(json.dumps({'model_mode': 'fake', 'port': 43127}))
    monkeypatch.setenv('LAYA_HARNESS_TEST', '1')
    monkeypatch.setenv('LAYA_HARNESS_HOME', str(path))
    (path / 'launchd').mkdir(mode=0o700)
    return path


class Shim:
    def __init__(self):
        self.calls = []
        self.path = None

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        if argv[1] == 'print':
            return subprocess.CompletedProcess(argv, 0 if self.path else 113,
                self.loaded_output() if self.path else '', '')
        if argv[1] == 'bootstrap':
            self.path = argv[3]
        if argv[1] == 'bootout':
            self.path = None
        return subprocess.CompletedProcess(argv, 0, '', '')

    def loaded_output(self):
        job = plistlib.loads(Path(self.path).read_bytes())
        return ('path = ' + str(self.path) + '\nprogram = ' + job['ProgramArguments'][0] +
                '\nworking directory = ' + job['WorkingDirectory'] + '\narguments = {\n' +
                '\n'.join(job['ProgramArguments']) + '\n}\n')


def test_exact_definition_and_privacy(home):
    path, job = probe.definition(home, sys.executable)
    assert job['ProgramArguments'] == [sys.executable, '-I', '-m', 'laya_harness.service']
    assert job['KeepAlive'] is False and job['RunAtLoad'] is False
    assert job['ThrottleInterval'] == 0
    assert job['WorkingDirectory'] == str(home)
    assert job['EnvironmentVariables'] == {'LAYA_HARNESS_TEST': '1', 'LAYA_HARNESS_HOME': str(home), 'CODEX_HOME': str(home / 'codex'), 'HF_HUB_OFFLINE': '1'}
    assert set(job) == {'Label','ProgramArguments','WorkingDirectory','EnvironmentVariables','KeepAlive','RunAtLoad','ThrottleInterval','StandardInPath','StandardOutPath','StandardErrorPath'}
    assert job['StandardInPath'] == job['StandardOutPath'] == '/dev/null'
    assert job['StandardErrorPath'] == str(home / 'service.log')
    assert path.parent == home/'launchd'
    assert job['Label'].startswith('local.laya-harness.service.')
    assert probe.definition(home, sys.executable) == (path, job)


def test_launch_and_exact_cleanup(home):
    shim = Shim()
    assert probe.launch(home, sys.executable, shim) is True
    path, job = probe.definition(home, sys.executable)
    assert plistlib.loads(path.read_bytes()) == job
    assert path.stat().st_mode & 0o777 == 0o600
    assert home.stat().st_mode & 0o777 == 0o700
    assert (home / 'service.log').stat().st_mode & 0o777 == 0o600
    assert [a[1] for a, k in shim.calls] == ['print','bootstrap','print','kickstart']
    assert all(a[0] == '/bin/launchctl' and k['timeout'] <= 1 for a,k in shim.calls)
    assert all(k['stdin'] == subprocess.DEVNULL for a,k in shim.calls)
    assert '-k' not in shim.calls[-1][0]
    assert probe.cleanup(home, sys.executable, shim) is True
    assert shim.calls[-1][0] == ['/bin/launchctl', 'bootout', f'gui/{os.getuid()}/{job["Label"]}']


def test_concurrent_same_definition(home):
    shim = Shim()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        assert all(pool.map(lambda _: probe.launch(home, sys.executable, shim), range(4)))
    assert sum(a[1]=='bootstrap' for a,k in shim.calls) == 1
    assert sum(a[1]=='kickstart' for a,k in shim.calls) == 4




@pytest.mark.parametrize('target', ['definition','log','lock'])
def test_symlink_files_refused(home, target):
    path, job = probe.definition(home, sys.executable)
    victim = home.parent / 'victim'
    victim.write_text('unchanged')
    actual = {'definition':path, 'log':home/'service.log', 'lock':home/'launchd'/'launch.lock'}[target]
    actual.symlink_to(victim)
    shim = Shim()
    assert probe.launch(home, sys.executable, shim) is False
    assert victim.read_text() == 'unchanged'
    assert shim.calls == []


def test_changed_definition_not_replaced(home):
    path, _ = probe.definition(home, sys.executable)
    path.write_bytes(b'other job')
    shim = Shim()
    assert probe.launch(home, sys.executable, shim) is False
    assert path.read_bytes() == b'other job' and not shim.calls


def test_foreign_registered_job_never_started_or_removed(home):
    shim = Shim()
    shim.path = '/other.plist'
    shim.loaded_output = lambda: 'path = /other.plist\n'
    assert probe.launch(home, sys.executable, shim) is False
    assert probe.cleanup(home, sys.executable, shim) is False
    assert all(a[1]=='print' for a,k in shim.calls)


@pytest.mark.parametrize('error', [OSError('private secret'), subprocess.TimeoutExpired(['fake'],1)])
def test_launch_errors_bounded_and_no_fallback(home, error, capsys):
    def fail(*a, **k):
        raise error
    assert probe.launch(home, sys.executable, fail) is False
    assert capsys.readouterr().out == ''
    assert 'private secret' not in (home/'launcher.log').read_text()


@pytest.mark.parametrize('args', [[],['bad'],['hook','missing'],['launch']])
def test_invalid_cli_silent_zero(args, capsys):
    assert probe.main(args) == (1 if not args else 0)
    assert capsys.readouterr() == ('','')




def test_failed_print_does_not_bootstrap(home):
    calls = []
    def fail(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 1, '', 'failure')
    assert probe.launch(home, sys.executable, fail) is False
    assert [a[1] for a in calls] == ['print']


def test_preexisting_log_append_preserved(home):
    log = home/'service.log'
    log.write_text('private diagnostic\n')
    log.chmod(0o644)
    assert probe.launch(home, sys.executable, Shim()) is True
    assert log.read_text() == 'private diagnostic\n'
    assert log.stat().st_mode & 0o777 == 0o600


def test_lock_timeout_prevents_commands(home):
    import fcntl
    fd = probe.private_file(home/'launchd'/'launch.lock')
    fcntl.flock(fd, fcntl.LOCK_EX)
    shim = Shim()
    try:
        import time
        start = time.monotonic()
        assert probe.launch(home, sys.executable, shim) is False
        assert time.monotonic()-start < 1
        assert shim.calls == []
    finally:
        os.close(fd)


@pytest.mark.parametrize('target',['definition','log','lock'])
def test_fifo_files_refused_without_hang(home, target):
    path, _ = probe.definition(home, sys.executable)
    actual = {'definition':path, 'log':home/'service.log', 'lock':home/'launchd'/'launch.lock'}[target]
    os.mkfifo(actual)
    shim = Shim()
    assert probe.launch(home, sys.executable, shim) is False
    assert shim.calls == []




def test_identity_scoped_to_interpreter_and_home(home, monkeypatch):
    _, job = probe.definition(home, sys.executable)
    other = home.parent/'other'
    other.mkdir()
    (other/'config.json').write_bytes((home/'config.json').read_bytes())
    monkeypatch.setenv('LAYA_HARNESS_HOME', str(other))
    _, second = probe.definition(other, sys.executable)
    assert job['Label'] != second['Label']


@pytest.mark.parametrize('value',['path = /foreign.plist','path = /wanted.plist-extra','otherpath = /wanted.plist'])
def test_exact_registered_path_validation(value):
    result = subprocess.CompletedProcess([],0,value,'')
    assert probe.owned(result,Path('/wanted.plist'),{'ProgramArguments':[sys.executable], 'WorkingDirectory':'/'}) is False




def test_off_hook_never_calls_launch(home, monkeypatch):
    from laya_harness import codex_client
    import time
    monkeypatch.setenv('LAYA_HARNESS_TEST','1')
    monkeypatch.setenv('LAYA_HARNESS_HOME',str(home))
    (home/'config.json').write_text(json.dumps({'mode':'off','model_mode':'fake','port':43127}))
    monkeypatch.setattr(codex_client.service_client,'profile',lambda *a:pytest.fail('network'))
    assert codex_client.run('UserPromptSubmit',b'garbage',time.monotonic()) is None
    assert not (home/'decisions.jsonl').exists()






@pytest.mark.parametrize('change',['program','argv','cwd','missing','ambiguous'])
def test_registered_full_identity_refuses_foreign(home,change):
    path,job = probe.definition(home,sys.executable)
    class Foreign(Shim):
        def __call__(self,argv,**kwargs):
            result = super().__call__(argv,**kwargs)
            if argv[1]=='print' and self.path:
                output = f'path = {path}\nprogram = {sys.executable}\nworking directory = {home}\narguments = {{\n{sys.executable}\n-I\n-m\nlaya_harness.service\n}}\n'
                if change=='program': output=output.replace('program = '+sys.executable,'program = /foreign/python')
                if change=='argv': output=output.replace('\n-m\n','\n-c\n')
                if change=='cwd': output=output.replace('working directory = '+str(home),'working directory = /foreign')
                if change=='missing': output=f'path = {path}\n'
                if change=='ambiguous': output+='program = /foreign/python\n'
                result.stdout=output
            return result
    shim=Foreign();shim.path=str(path)
    assert probe.launch(home,sys.executable,shim) is False
    assert probe.cleanup(home,sys.executable,shim) is False
    assert [a[1] for a,k in shim.calls] == ['print','print']
    assert 'ownership' in (home/'launcher.log').read_text()


@pytest.mark.parametrize('stage',['print','bootstrap','kickstart'])
def test_rejected_commands_private_diagnostics(home,stage,capsys):
    class Rejected(Shim):
        def __call__(self,argv,**kwargs):
            result=super().__call__(argv,**kwargs)
            if argv[1]==stage:
                result.returncode=5
                result.stderr='sensitive raw stderr'
            return result
    shim=Rejected()
    assert probe.launch(home,sys.executable,shim) is False
    rows=[json.loads(line) for line in (home/'launcher.log').read_text().splitlines()]
    assert rows[-1] == {'stage':stage,'returncode':5}
    assert 'sensitive' not in (home/'launcher.log').read_text()
    assert (home/'launcher.log').stat().st_mode & 0o777 == 0o600
    assert capsys.readouterr() == ('','')

@pytest.mark.parametrize('platform,testing,broker', [('darwin',False,True),('darwin',True,False),('linux',False,False)])
def test_spawn_selects_broker_without_wait(home, monkeypatch, platform, testing, broker):
    from laya_harness import spawn
    monkeypatch.setattr(sys, 'platform', platform)
    monkeypatch.setattr(spawn.paths, 'testing', lambda: testing)
    monkeypatch.setattr(spawn.paths, 'ensure_home', lambda: home)
    monkeypatch.setattr(spawn.paths, 'service_log', lambda: home/'service.log')
    calls=[]
    monkeypatch.setattr(spawn.subprocess, 'Popen', lambda argv, **kw: calls.append((argv,kw)))
    spawn.spawn_service({'interpreter':sys.executable})
    argv,kw=calls[0]
    assert argv == [sys.executable,'-I','-m','laya_harness.launchd' if broker else 'laya_harness.service']
    assert kw['stdin'] == kw['stdout'] == subprocess.DEVNULL
    assert kw['start_new_session'] is True and kw['close_fds'] is True
    assert kw['cwd'] == str(home)
    assert (home/'service.log').stat().st_mode & 0o777 == 0o600


def test_production_definition_drops_ambient_environment(home, monkeypatch):
    monkeypatch.setattr(probe.paths, 'testing', lambda: False)
    monkeypatch.setenv('SECRET_PROMPT','private text')
    path, job=probe.definition(home,sys.executable)
    assert job['EnvironmentVariables'] == {'HF_HUB_OFFLINE':'1'}
    import hashlib
    assert job['Label'] == 'local.laya-harness.service.'+hashlib.sha256(f'{os.getuid()}\0{home}\0{sys.executable}'.encode()).hexdigest()[:24]
    assert path == home/'launchd'/(job['Label']+'.plist')


@pytest.mark.parametrize('kind', ['symlink','file'])
def test_launch_directory_refuses_foreign(home,kind):
    directory=home/'launchd';directory.rmdir()
    if kind=='symlink':
        victim=home.parent/'outside';victim.mkdir();directory.symlink_to(victim)
    else:
        directory.write_text('keep')
    shim=Shim()
    assert probe.launch(home,sys.executable,shim) is False
    assert shim.calls == []


def test_interpreter_identity_never_replaces_old_registration(home, monkeypatch):
    shim=Shim()
    assert probe.launch(home,sys.executable,shim)
    oldpath=shim.path;oldbytes=Path(oldpath).read_bytes()
    other=home.parent/'python alternate';other.symlink_to(sys.executable)
    newpath,newjob=probe.definition(home,str(other))
    assert newpath != Path(oldpath)
    # A foreign/old definition reported for the new label must not be killed.
    before=len(shim.calls)
    assert probe.launch(home,str(other),shim) is False
    assert [a[1] for a,k in shim.calls[before:]] == ['print']
    assert Path(oldpath).read_bytes() == oldbytes


def test_main_uses_shared_config_and_state(home,monkeypatch):
    monkeypatch.setattr(probe.config,'load',lambda:{'port':43127,'interpreter':sys.executable})
    calls=[]
    monkeypatch.setattr(probe,'launch',lambda h,i:calls.append((h,i)) or True)
    assert probe.main([]) == 0
    assert calls == [(home,sys.executable)]


def test_main_rejects_test_standard_port_before_launch(home,monkeypatch):
    monkeypatch.setattr(probe.config,'load',lambda:{'port':47913})
    monkeypatch.setattr(probe,'launch',lambda *a:pytest.fail('must not launch'))
    assert probe.main([]) == 1


def test_all_commands_have_exact_budget(home):
    shim=Shim();assert probe.launch(home,sys.executable,shim)
    assert all(kwargs['timeout'] == 0.6 for argv,kwargs in shim.calls)
    assert all(kwargs['stdout']==kwargs['stderr']==subprocess.PIPE for argv,kwargs in shim.calls)


def test_config_error_records_class_only(home,monkeypatch,capsys):
    def broken():
        raise ValueError('secret config content')
    monkeypatch.setattr(probe.config,'load',broken)
    assert probe.main([]) == 1
    assert json.loads((home/'launcher.log').read_text()) == {'stage':'validation','exception_class':'ValueError'}
    assert capsys.readouterr() == ('','')


def test_commands_target_only_expected_identity(home):
    shim=Shim();assert probe.launch(home,sys.executable,shim)
    path,job=probe.definition(home,sys.executable)
    target=f'gui/{os.getuid()}/{job["Label"]}'
    assert [argv for argv,kwargs in shim.calls] == [
        ['/bin/launchctl','print',target],
        ['/bin/launchctl','bootstrap',f'gui/{os.getuid()}',str(path)],
        ['/bin/launchctl','print',target],
        ['/bin/launchctl','kickstart',target]]
    assert (home/'launchd').stat().st_mode & 0o777 == 0o700


def test_broker_watchdog_bounds_blocked_config_without_os_calls(home):
    import time
    code = ('import time; from laya_harness import launchd; '
            'launchd.config.load=lambda: time.sleep(30); '
            'launchd.launch=lambda *a: (_ for _ in ()).throw(AssertionError("OS job")); '
            'raise SystemExit(launchd.main([]))')
    started=time.monotonic()
    child=subprocess.Popen([sys.executable,'-I','-c',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        out,err=child.communicate(timeout=4.2)
        assert child.returncode == 1
        assert out == err == b''
        assert 3.3 <= time.monotonic()-started < 4.2
    finally:
        if child.poll() is None:
            child.kill();child.wait()


def test_broker_restores_alarm_after_return(home,monkeypatch):
    import signal
    previous=signal.getsignal(signal.SIGALRM)
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0,0.0)
    monkeypatch.setattr(probe.config,'load',lambda:{'port':43127})
    monkeypatch.setattr(probe,'launch',lambda *a:True)
    assert probe.main([]) == 0
    assert signal.getsignal(signal.SIGALRM) == previous
    assert signal.getitimer(signal.ITIMER_REAL) == (0.0,0.0)
