# macOS service launch production fix

Contract: `docs/superpowers/specs/2026-10-10-laya-harness-macos-service-launch-design.md`, umbrella §4.3 and Codex C10. This literal plan is generated from executed, reviewed workbench files.

## Scope and verification

Only the three files below change. Production remains unpromoted until the user approves the exact private three-file diff, production job definition, and one real-service stop. Hook commands, real configuration and model weights stay unchanged. Final implementation commit and push remain gated on acceptance.

Two-agent workflow under the user-approved temporary Codex routing exception: implementer workbench RED/GREEN, independent reviewer APPROVED with no findings. Initial behavioral stub: 32 failed, 1 passed; Darwin routing, configuration diagnostics and blocked-config watchdog each had an actual RED before GREEN. Focused controller 47 passed in 4.36 s, reviewer 47 passed in 4.35 s. Existing process regressions plus launcher tests: 195 passed in 21.18 s.

Controller full fake gate: 534 passed, 1 deselected in 99.52s. Cached offline controller real-model gate: 1 passed, 534 deselected in 5.43 s. Initial sandbox run could not bind free ports; rerun with temporary localhost access passed.

Actual production module native replay used an isolated fake home/free port. Broker startup 52.403 ms, exact loaded ownership and private modes verified, quiet idle exit/no restart, on-demand restart 44.682 ms, SIGTERM stop/no restart. Exact temporary job cleanup returned true and job absent (113). Desktop quit/reopen survival remains pending and is not inferred. Earlier preflight additionally proved concurrent launch, crash/no restart and bound model-failure behavior. UI/copy unchanged; visual review N/A.

## Promotion and acceptance

After exact user approval: stop the current health-verified real service once; copy these exact blocks to the repo; verify literal bytes and rerun fake gates; start through the ordinary production hook to register only the reviewed on-demand job. KeepAlive and RunAtLoad are false, ThrottleInterval is zero. Capture ready PID and launchd coalition, then user quits/reopens Codex within the idle interval; compare the same PID and readiness. Do not claim survival until observed. No additional stop, hook replacement, download or push is authorized by this plan.

## Verified files

### `laya_harness/launchd.py`

```python
"""Bounded on-demand macOS service registration; never loads the predictor."""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import plistlib
import signal
import stat
import subprocess
import sys
import tempfile
import time

from . import config, paths, spawn

BUDGET = 0.6
WALL_BUDGET = 3.5


def definition(home, interpreter):
    home = Path(home)
    if not home.is_absolute() or home != home.resolve():
        raise ValueError("canonical absolute state home required")
    info = home.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise ValueError("owned directory required")
    if not os.path.isabs(interpreter) or not os.access(interpreter, os.X_OK):
        raise ValueError("absolute executable interpreter required")
    digest = hashlib.sha256(f"{os.getuid()}\0{home}\0{interpreter}".encode()).hexdigest()[:24]
    label = "local.laya-harness.service." + digest
    environment = {"HF_HUB_OFFLINE": "1"}
    if paths.testing():
        if home != paths.home().resolve():
            raise paths.StateDirError("test home mismatch")
        environment.update({"LAYA_HARNESS_TEST": "1", "LAYA_HARNESS_HOME": str(home),
                            "CODEX_HOME": str(home / "codex")})
    job = {"Label": label, "ProgramArguments": spawn.service_argv(interpreter),
           "WorkingDirectory": str(home), "EnvironmentVariables": environment,
           "KeepAlive": False, "RunAtLoad": False, "ThrottleInterval": 0,
           "StandardInPath": "/dev/null", "StandardOutPath": "/dev/null",
           "StandardErrorPath": str(home / "service.log")}
    return home / "launchd" / (label + ".plist"), job


def directory(home):
    path = home / "launchd"
    path.mkdir(mode=0o700, exist_ok=True)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise ValueError("owned launch directory required")
    path.chmod(0o700)
    return path


def private_file(path):
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    if not stat.S_ISREG(os.fstat(fd).st_mode) or os.fstat(fd).st_uid != os.getuid():
        os.close(fd)
        raise ValueError('owned regular file required')
    os.fchmod(fd, 0o600)
    return fd


@contextlib.contextmanager
def locked(home):
    fd = private_file(home / 'launchd' / 'launch.lock')
    end = time.monotonic() + BUDGET
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= end:
                    raise TimeoutError('lock budget')
                time.sleep(0.01)
        yield
    finally:
        os.close(fd)


class LaunchFailure(Exception):
    def __init__(self, stage, returncode=None, exception_class=None):
        self.stage = stage
        self.returncode = returncode
        self.exception_class = exception_class


def command(run, *args):
    try:
        return run(['/bin/launchctl', *args], stdin=subprocess.DEVNULL,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=BUDGET)
    except Exception as exc:
        raise LaunchFailure(args[0], exception_class=type(exc).__name__) from None


def owned(result, path, job):
    if result.returncode != 0:
        return False
    lines = [line.strip() for line in result.stdout.splitlines()]
    for name, expected in (('path', str(path)),
                           ('program', job['ProgramArguments'][0]),
                           ('working directory', job['WorkingDirectory'])):
        found = [line[len(name) + 3:] for line in lines if line.startswith(name + ' = ')]
        if found != [expected]:
            return False
    starts = [index for index, line in enumerate(lines) if line == 'arguments = {']
    if len(starts) != 1:
        return False
    start = starts[0] + 1
    try:
        end = lines.index('}', start)
    except ValueError:
        return False
    return lines[start:end] == job['ProgramArguments']


def diagnostic(home, exc):
    try:
        fd = private_file(home / 'launcher.log')
        try:
            os.lseek(fd, 0, os.SEEK_END)
            row = {'stage': exc.stage} if isinstance(exc, LaunchFailure) else {'stage': 'validation'}
            if isinstance(exc, LaunchFailure) and exc.returncode is not None:
                row['returncode'] = exc.returncode
            else:
                row['exception_class'] = exc.exception_class if isinstance(exc, LaunchFailure) else type(exc).__name__
            os.write(fd, (json.dumps(row, sort_keys=True) + '\n').encode())
        finally:
            os.close(fd)
    except Exception:
        pass


def launch(home, interpreter, run=None):
    run = subprocess.run if run is None else run
    safe_home = None
    try:
        path, job = definition(home, interpreter)
        safe_home = Path(home)
        home = Path(home)
        home.chmod(0o700)
        directory(home)
        with locked(home):
            # Validate every file before issuing an OS command.
            fd = private_file(home / 'service.log')
            os.close(fd)
            encoded = plistlib.dumps(job, sort_keys=True)
            if path.exists() or path.is_symlink():
                fd = private_file(path)
                try:
                    if os.read(fd, len(encoded)+1) != encoded:
                        raise ValueError('immutable definition mismatch')
                finally:
                    os.close(fd)
            else:
                fd, temp = tempfile.mkstemp(dir=path.parent, suffix='.plist.tmp')
                try:
                    with os.fdopen(fd, 'wb') as stream:
                        stream.write(encoded)
                    os.replace(temp, path)
                finally:
                    if os.path.exists(temp):
                        os.unlink(temp)
            target = f'gui/{os.getuid()}/{job["Label"]}'
            result = command(run, 'print', target)
            if result.returncode != 0:
                # Missing-job code must be established by native preflight;
                # arbitrary launchctl failure must never trigger registration.
                if result.returncode != 113:
                    raise LaunchFailure('print', result.returncode)
                registered = command(run, 'bootstrap', f'gui/{os.getuid()}', str(path))
                if registered.returncode != 0:
                    raise LaunchFailure('bootstrap', registered.returncode)
                result = command(run, 'print', target)
            if result.returncode != 0:
                raise LaunchFailure('print', result.returncode)
            if not owned(result, path, job):
                raise LaunchFailure('ownership', result.returncode)
            started = command(run, 'kickstart', target)
            if started.returncode != 0:
                raise LaunchFailure('kickstart', started.returncode)
            return True
    except Exception as exc:
        if safe_home is not None:
            diagnostic(safe_home, exc)
        return False


def cleanup(home, interpreter, run=None):
    run = subprocess.run if run is None else run
    safe_home = None
    try:
        path, job = definition(home, interpreter)
        safe_home = Path(home)
        directory(Path(home))
        with locked(Path(home)):
            fd = private_file(path)
            try:
                encoded = plistlib.dumps(job, sort_keys=True)
                if os.read(fd, len(encoded)+1) != encoded:
                    return False
            finally:
                os.close(fd)
            target = f'gui/{os.getuid()}/{job["Label"]}'
            result = command(run, 'print', target)
            if result.returncode == 113:
                return True
            if result.returncode != 0:
                raise LaunchFailure('print', result.returncode)
            if not owned(result, path, job):
                raise LaunchFailure('ownership', result.returncode)
            removed = command(run, 'bootout', target)
            if removed.returncode != 0:
                raise LaunchFailure('bootout', removed.returncode)
            return True
    except Exception as exc:
        if safe_home is not None:
            diagnostic(safe_home, exc)
        return False


def main(argv=None):
    args = sys.argv[1:] if argv is None else list(argv)
    if args:
        return 0
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    started = time.monotonic()
    signal.signal(signal.SIGALRM, lambda *unused: os._exit(1))
    signal.setitimer(signal.ITIMER_REAL, WALL_BUDGET)
    home = None
    try:
        home = paths.ensure_home().resolve()
        cfg = config.load()
        config.port(cfg)  # enforce isolated test-port guard before any OS command
        return 0 if launch(home, config.interpreter(cfg)) else 1
    except Exception as exc:
        if home is not None:
            diagnostic(home, exc)
        return 1
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0]:
            remaining = max(0.000001, previous_timer[0] - (time.monotonic() - started))
            signal.setitimer(signal.ITIMER_REAL, remaining, previous_timer[1])


if __name__ == "__main__":
    sys.exit(main())
```

### `laya_harness/spawn.py`

```python
"""Request the service asynchronously (spec §4.3).

Darwin production uses the bounded launchd broker; other platforms and ordinary tests
start the service directly. Both paths isolate stdio and never wait in the hook.
"""

import os
import subprocess
import sys

from . import config, paths


def service_argv(interpreter: str) -> list:
    return [interpreter, "-I", "-m", "laya_harness.service"]


def spawn_service(cfg: dict) -> None:
    home = paths.ensure_home()
    fd = os.open(paths.service_log(), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "ab") as log:
        subprocess.Popen(
            ([config.interpreter(cfg), "-I", "-m", "laya_harness.launchd"]
             if sys.platform == "darwin" and not paths.testing()
             else service_argv(config.interpreter(cfg))),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=log,
            start_new_session=True,
            close_fds=True,
            cwd=str(home),
        )
```

### `tests/test_launchd.py`

```python
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
```

