# macOS launch ownership preflight plan

Execution: required project two-agent workflow, with Codex implementer and separate Codex contract reviewer under the existing Claude-limit routing exception. No production promotion in this preflight.

Spec: `docs/superpowers/specs/2026-10-10-laya-harness-macos-service-launch-design.md`, approved by user. Goal: verify a minimal on-demand macOS launchd service before writing the production literal plan. Standard library only; configured repo venv interpreter; no Fable/downloads/realmodel/realhome/port47913/userLaunchAgents/enable-disable/login-startup/KeepAlive/kickstart-k/domain-widebootout. No UI/copy changes, visualN/A.

## Task 1 — workbench-only launch probe and tests

Create `.workbench/macos-launch/probe.py` and `test_probe.py`. The probe builds private definitions for explicitly isolated temporary homes and app-specific temporary labels, invokes bootstrap/kickstart under finite command budgets, and supports exact-job cleanup. It supports synthetic hook/spawn routing without modifying shipping modules on disk. Unit/subprocess tests use a fake launchctl shim and requirement-derived actual RED/GREEN for argv/definition/privacy, off/refused-only routing, command failures/timeouts, concurrent launcher behavior, immutable identity and no service-killing flags. No real launchd mutation by implementer/reviewer; only controller may run the authorized native gate.

Controller snapshots only these tool files with an isolated index, replays tests and commissions a fresh independent review against the on-disk spec. Generate literal file blocks from executed files, commit before native tool use. No guessed executable plan blocks.

## Task 2 — controller-only isolated native gate

After independent approval, controller creates a uniquely labeled gui/uid job with a fake predictor in temporary private state/freeport and exact reviewed definition. Observe ready/decided row, hook-exit continuation, idle exit/no restart, failure/no restart, explicit stop/no restart, refused-only restart and concurrent startups. Job registration does not constitute proof of app-exit survival. Always exact-label bootout in finally and verify absent; never touch realhome or unrelatedjobs. Capture readable commands, outcomes, ownership and limits in QA. User authorized this temporary gate, not live service replacement.

## Task 3 — evidence-driven production design

Finalize lifecycle/identity/cleanup requirements from observed behavior. Update parent docs first and generate a literal production plan from verified workbench code. Any production promotion follows separate contract review/controller gates and exact live-change approval. No implementation commit/push here; existing Stage0/1 product tree remains untouched.

## Independent review round 1

Initial shim suite40GREEN (controller2.33s/reviewer2.38s), actualstub18RED. Reviewer CHANGES REQUESTED: same-path registered-job mismatch can pass source-path-only ownership; nonzero launchctl rejects lacked required private diagnostics. Updated spec now pins loaded argv/cwd/path identity and fixed-stage/code diagnostics. Implementer adds deliberate RED cases for same-path loaded-program/arguments/cwd mismatches and print/bootstrap/kickstart/ownership rejections before GREEN. Exact native print identity format remains a controller empirical gate; unsupported output must fail closed, never assume ownership. No native job or production change yet.

## Verified workbench blocks

Initial actualstubRED18failed0.12s. Initial controller40GREEN2.33s, independent40GREEN2.38s/CHANGES REQUESTED for loadedidentity/rejectiondiagnostics. Updatedspecbb1f8c8 preceded correctionRED8failed40passed2.53s. Corrected controller48GREEN2.38s; independent48GREEN2.38s **APPROVED for controller isolated native gate only**. Command `.venv/bin/python -m pytest -q .workbench/macos-launch/test_probe.py`; shims/tempstate/freeports only, localhostsandboxescalation required. No nativejobs or shippingchanges. WIP refs `refs/laywip/macos-launch/task-1` and `.r2`. VisualN/A. Native missing-jobprint113 observed read-only; existingappjob supplied read-only identitygrammar. Nativejobownership/lifecycle still unverified.

## Verified file: .workbench/macos-launch/probe.py

```python
"""Isolated fake-model launchd preflight; never a production launcher."""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import plistlib
import stat
import subprocess
import sys
import tempfile
import time

SCRIPT = str(Path(__file__).absolute())
BUDGET = 0.6


def read_config(home):
    fd = os.open(Path(home) / 'config.json', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_size > 65536:
            raise ValueError('bounded owned regular config required')
        return json.loads(os.read(fd, 65537))
    finally:
        os.close(fd)


def isolated(home, interpreter):
    home = Path(home)
    resolved = home.resolve()
    roots = (Path(tempfile.gettempdir()).resolve(), Path('/private/tmp'))
    if not home.is_absolute() or home != resolved or not any(root in home.parents for root in roots):
        raise ValueError('temporary absolute home required')
    if not stat.S_ISDIR(home.lstat().st_mode) or home.stat().st_uid != os.getuid():
        raise ValueError('owned directory required')
    if not os.path.isabs(interpreter) or not os.access(interpreter, os.X_OK):
        raise ValueError('absolute executable interpreter required')
    cfg = read_config(home)
    if cfg.get('model_mode') != 'fake' or not 1 <= int(cfg.get('port', 0)) <= 65535 or int(cfg['port']) == 47913:
        raise ValueError('isolated fake configuration required')
    return home


def definition(home, interpreter):
    home = isolated(home, interpreter)
    digest = hashlib.sha256(f'{os.getuid()}\0{home}\0{interpreter}'.encode()).hexdigest()[:24]
    label = 'local.laya-harness.preflight.' + digest
    job = {'Label': label, 'ProgramArguments': [interpreter, '-I', '-m', 'laya_harness.service'],
           'WorkingDirectory': str(home), 'EnvironmentVariables': {
               'LAYA_HARNESS_TEST': '1', 'LAYA_HARNESS_HOME': str(home),
               'CODEX_HOME': str(home / 'codex'), 'HF_HUB_OFFLINE': '1'},
           'KeepAlive': False, 'RunAtLoad': False,
           'StandardInPath': '/dev/null', 'StandardOutPath': '/dev/null',
           'StandardErrorPath': str(home / 'service.log')}
    return home / (label + '.plist'), job


def private_file(path):
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    if not stat.S_ISREG(os.fstat(fd).st_mode) or os.fstat(fd).st_uid != os.getuid():
        os.close(fd)
        raise ValueError('owned regular file required')
    os.fchmod(fd, 0o600)
    return fd


@contextlib.contextmanager
def locked(home):
    fd = private_file(home / 'launch.lock')
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
                fd, temp = tempfile.mkstemp(dir=home, suffix='.plist.tmp')
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


def hook(home, event):
    # Validate the explicit temporary configuration before importing any
    # ordinary hook module or consulting ambient state.
    isolated(home, sys.executable)
    cfg = read_config(home)
    interpreter = cfg.get('interpreter') or sys.executable
    isolated(home, interpreter)
    os.environ.update({'LAYA_HARNESS_TEST':'1', 'LAYA_HARNESS_HOME':str(home), 'CODEX_HOME':str(Path(home)/'codex'), 'HF_HUB_OFFLINE':'1'})
    from laya_harness import __main__, spawn
    spawn.service_argv = lambda configured: [configured, '-I', SCRIPT, 'launch', str(home), configured]
    return __main__.main(['hook','codex',event])


def main(argv=None):
    args = sys.argv[1:] if argv is None else list(argv)
    if len(args) == 3 and args[0] in ('launch','cleanup'):
        result = (launch if args[0] == 'launch' else cleanup)(args[1], args[2])
        return 0 if result else 1
    if len(args) == 3 and args[0] == 'hook' and args[2] in ('SessionStart','UserPromptSubmit'):
        try:
            return hook(args[1], args[2])
        except Exception:
            return 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

## Verified file: .workbench/macos-launch/test_probe.py

```python
import concurrent.futures
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile

import pytest

SPEC = importlib.util.spec_from_file_location('launch_probe', Path(__file__).with_name('probe.py'))
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


@pytest.fixture
def home(tmp_path):
    path = tmp_path / 'state with spaces'
    path.mkdir(mode=0o700)
    (path / 'config.json').write_text(json.dumps({'model_mode': 'fake', 'port': 43127}))
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
    assert job['WorkingDirectory'] == str(home)
    assert job['EnvironmentVariables'] == {'LAYA_HARNESS_TEST': '1', 'LAYA_HARNESS_HOME': str(home), 'CODEX_HOME': str(home / 'codex'), 'HF_HUB_OFFLINE': '1'}
    assert set(job) == {'Label','ProgramArguments','WorkingDirectory','EnvironmentVariables','KeepAlive','RunAtLoad','StandardInPath','StandardOutPath','StandardErrorPath'}
    assert job['StandardInPath'] == job['StandardOutPath'] == '/dev/null'
    assert job['StandardErrorPath'] == str(home / 'service.log')
    assert str(path).startswith(str(home))
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


@pytest.mark.parametrize('change', ['real','port','relative','symlink'])
def test_unsafe_environment_refused(home, change):
    interpreter = sys.executable
    if change == 'real':
        (home / 'config.json').write_text('{"model_mode":"real","port":43127}')
    elif change == 'port':
        (home / 'config.json').write_text('{"model_mode":"fake","port":47913}')
    elif change == 'relative':
        interpreter = 'python'
    else:
        link = home.parent / 'link'
        link.symlink_to(home, target_is_directory=True)
        home = link
    shim = Shim()
    assert probe.launch(home, interpreter, shim) is False
    assert shim.calls == []


@pytest.mark.parametrize('target', ['definition','log','lock'])
def test_symlink_files_refused(home, target):
    path, job = probe.definition(home, sys.executable)
    victim = home.parent / 'victim'
    victim.write_text('unchanged')
    actual = {'definition':path, 'log':home/'service.log', 'lock':home/'launch.lock'}[target]
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
    assert probe.main(args) == 0
    assert capsys.readouterr() == ('','')


def test_hook_routes_exact_broker_argv_and_output(home, monkeypatch, capsys):
    from laya_harness import __main__, spawn
    def ordinary(argv):
        assert argv == ['hook','codex','UserPromptSubmit']
        assert spawn.service_argv(sys.executable) == [sys.executable,'-I',probe.SCRIPT,'launch',str(home),sys.executable]
        assert os.environ['LAYA_HARNESS_HOME'] == str(home)
        print('{"systemMessage":"exact unchanged output"}')
        return 0
    monkeypatch.setattr(__main__, 'main', ordinary)
    monkeypatch.setattr(spawn, 'service_argv', spawn.service_argv)
    monkeypatch.setenv('LAYA_HARNESS_HOME', str(home))
    assert probe.main(['hook',str(home),'UserPromptSubmit']) == 0
    assert capsys.readouterr().out == '{"systemMessage":"exact unchanged output"}\n'


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
    fd = probe.private_file(home/'launch.lock')
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
    actual = {'definition':path, 'log':home/'service.log', 'lock':home/'launch.lock'}[target]
    os.mkfifo(actual)
    shim = Shim()
    assert probe.launch(home, sys.executable, shim) is False
    assert shim.calls == []


def test_invalid_config_has_no_write_or_call(home):
    (home/'config.json').write_text('{"model_mode":"real","port":47913}')
    before = set(home.iterdir())
    assert probe.launch(home, sys.executable, Shim()) is False
    assert set(home.iterdir()) == before


def test_identity_scoped_to_interpreter_and_home(home):
    _, job = probe.definition(home, sys.executable)
    other = home.parent/'other'
    other.mkdir()
    (other/'config.json').write_bytes((home/'config.json').read_bytes())
    _, second = probe.definition(other, sys.executable)
    assert job['Label'] != second['Label']


@pytest.mark.parametrize('value',['path = /foreign.plist','path = /wanted.plist-extra','otherpath = /wanted.plist'])
def test_exact_registered_path_validation(value):
    result = subprocess.CompletedProcess([],0,value,'')
    assert probe.owned(result,Path('/wanted.plist'),{'ProgramArguments':[sys.executable], 'WorkingDirectory':'/'}) is False


@pytest.mark.parametrize('outcome', ['refused','loading','not_ready','timeout','foreign','error'])
def test_real_client_routing_starts_only_refused(home, monkeypatch, outcome):
    from laya_harness import codex_client, spawn
    import time
    for name, value in {'LAYA_HARNESS_TEST':'1','LAYA_HARNESS_HOME':str(home),'CODEX_HOME':str(home/'codex')}.items():
        monkeypatch.setenv(name,value)
    (home/'config.json').write_text(json.dumps({'mode':'show','model_mode':'fake','port':43127}))
    calls = []
    monkeypatch.setattr(spawn,'service_argv',lambda interpreter:[interpreter,'-I',probe.SCRIPT,'launch',str(home),interpreter])
    monkeypatch.setattr(subprocess,'Popen',lambda argv,**kw:calls.append((argv,kw)))
    monkeypatch.setattr(codex_client.service_client,'profile',lambda *a:(outcome,None))
    payload = dict(hook_event_name='UserPromptSubmit',session_id='native',model='gpt-6.1-sol',cwd='/project',permission_mode='default',turn_id='turn',prompt='private prompt')
    assert codex_client.run('UserPromptSubmit',json.dumps(payload).encode(),time.monotonic()) is None
    assert len(calls) == (outcome == 'refused')
    if calls:
        argv, kw = calls[0]
        assert argv == [sys.executable,'-I',probe.SCRIPT,'launch',str(home),sys.executable]
        assert kw['stdin'] == kw['stdout'] == subprocess.DEVNULL
        assert kw['start_new_session'] is True
        assert 'private prompt' not in str(argv)
    row=json.loads((home/'decisions.jsonl').read_text())
    assert row['prompt'] == 'private prompt'
    assert row['status'] == {'refused':'started_service','foreign':'error'}.get(outcome,outcome)


def test_off_hook_never_calls_launch(home, monkeypatch):
    from laya_harness import codex_client
    import time
    monkeypatch.setenv('LAYA_HARNESS_TEST','1')
    monkeypatch.setenv('LAYA_HARNESS_HOME',str(home))
    (home/'config.json').write_text(json.dumps({'mode':'off','model_mode':'fake','port':43127}))
    monkeypatch.setattr(codex_client.service_client,'profile',lambda *a:pytest.fail('network'))
    assert codex_client.run('UserPromptSubmit',b'garbage',time.monotonic()) is None
    assert not (home/'decisions.jsonl').exists()


def test_hook_open_stdin_deadline_and_silent_zero(home):
    import time
    started = time.monotonic()
    child = subprocess.Popen([sys.executable,'-I',probe.SCRIPT,'hook',str(home),'UserPromptSubmit'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        assert child.wait(timeout=2.1) == 0
        assert time.monotonic()-started < 2.1
        assert child.stdout.read() == b''
        assert child.stderr.read() == b''
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()
        child.stdin.close()
        child.stdout.close()
        child.stderr.close()


@pytest.mark.parametrize('kind',['fifo','symlink'])
def test_unsafe_config_refused(home,kind):
    config = home/'config.json'
    config.unlink()
    if kind == 'fifo':
        os.mkfifo(config)
    else:
        victim=home.parent/'external-config'
        victim.write_text('{"model_mode":"fake","port":43127}')
        config.symlink_to(victim)
    assert probe.launch(home,sys.executable,Shim()) is False
    assert probe.main(['hook',str(home),'UserPromptSubmit']) == 0


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
```
