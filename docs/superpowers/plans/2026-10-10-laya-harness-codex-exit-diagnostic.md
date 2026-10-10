# Codex service-exit diagnostic preflight

Contract: Stage1 design C9; shipping source/config unchanged. User authorized targeted diagnostics, not a speculative fix.

1. Implement only local workbench bootstrap.py and requirement-derived tests under `.workbench/codex-exit-diagnostic/`. RED then GREEN with temporary homes/free ports and fake predictors; no real model/service/home changes.
2. Controller replays focused tests, generates literal blocks from verified files, snapshots isolated tooling, and commissions independent contract review. No UI/copy changes; visual review N/A.
3. Commit verified plan before preparing exact project-hook diff. Show concrete reviewed result for approval of installation and one live service stop. Native trust/reload remains user-controlled.
4. One instrumented real startup and quit/reopen, then analyze metadata and restore production definitions. Any production fix requires root-cause evidence and a separate docs-first workbench pass.

No unexecuted code blocks are included. Verified files/results will be generated after preflight.

## Review round 1 requirements

Independent review identified a C9 test gap: pin the exact systemMessage, fake answers, suggestion and checkpoint provenance in the refused-launch/predict scenario, and exact routing for both SS and UPS. These assertions implement the existing unchanged-output requirement; no advisor contract change. Execute behavioral mutation RED and corrected GREEN before generating final literal blocks.

## Verified preflight

Actual stub RED: 19 failed in 16.00 s. Initial controller GREEN: 24 passed in 7.21 s. Independent first review: CHANGES REQUESTED for exact-output test coverage (24 passed in 7.15 s). Corrected tests caught five separate scratch mutations: wrong copy, answers, suggestion and fake checkpoint each failed one focused test; wrong UPS routing failed UPS while SS still passed. Corrected implementer GREEN: 25 passed in 7.24 s. Corrected controller GREEN: 25 passed in 7.20 s. Command: `.venv/bin/python -m pytest -q .workbench/codex-exit-diagnostic/test_bootstrap.py`. All fixtures use temporary homes/free ports and fake predictors; sandbox-localhost escalation was required. No live service, config or hook changes. Visual review N/A: copy/UI unchanged.

Behavioral RED logs: `/private/tmp/laya-exit-red.txt` and `/private/tmp/laya-exit-mutations/<case>/red.txt` (regenerable scratch). WIP refs: `refs/laywip/codex-exit-diagnostic/task-1` and `.r2`; only the two local tool files, isolated temporary index, no shipping code. SIGKILL/native abort remains unobservable; a missing receipt identifies neither signal nor killer.

Independent correction review: **APPROVED**, 25 passed in 7.29 s; all five mutation logs inspected. No remaining findings.

## Verified file: .workbench/codex-exit-diagnostic/bootstrap.py

```python
"""Temporary C9 metadata instrument, not an advisor fix.

SIGKILL and native aborts cannot be captured. A missing termination receipt does
not identify a killer; a normal return does not establish an idle-exit cause.
"""
import os
import stat
import sys

SCRIPT = os.path.abspath(__file__)
DIRECTORY = os.path.dirname(SCRIPT)
RECEIPTS = os.path.join(DIRECTORY, 'receipts.jsonl')


def receipt(event, **fields):
    """Best effort, bounded private regular-file writes; no exception messages."""
    fd = None
    try:
        import datetime
        import json

        directory = os.lstat(DIRECTORY)
        if not stat.S_ISDIR(directory.st_mode):
            return
        os.chmod(DIRECTORY, 0o700)
        fd = os.open(RECEIPTS, os.O_WRONLY | os.O_CREAT | os.O_APPEND |
                     os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return
        os.fchmod(fd, 0o600)
        row = {'ts': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'event': event, 'pid': os.getpid()}
        row.update(fields)
        os.write(fd, (json.dumps(row, sort_keys=True) + '\n').encode())
    except BaseException:
        pass
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except BaseException:
                pass


def service_mode():
    import signal
    from laya_harness import service

    receipt('start', ppid=os.getppid(), pgid=os.getpgrp(), sid=os.getsid(0))
    for signum in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
        original = signal.getsignal(signum)

        def caught(number, frame, original=original):
            receipt('signal', signal=signal.Signals(number).name)
            if original == signal.SIG_IGN:
                return
            if callable(original):
                original(number, frame)
                return
            signal.signal(number, signal.SIG_DFL)
            os.kill(os.getpid(), number)

        signal.signal(signum, caught)
    try:
        result = service.main()
    except BaseException as exc:
        receipt('exception', exception_class=type(exc).__name__)
        raise
    receipt('normal_exit', returned_normally=True)
    return result


def main(argv=None):
    args = sys.argv[1:] if argv is None else list(argv)
    if args == ['service']:
        return service_mode()
    if len(args) != 2 or args[0] != 'hook' or args[1] not in ('SessionStart', 'UserPromptSubmit'):
        return 0
    # Import the ordinary entry point first: its own start clock/watchdog remains
    # authoritative. Patch only its refused-connection spawn command.
    from laya_harness import __main__, spawn

    spawn.service_argv = lambda interpreter: [interpreter, '-I', SCRIPT, 'service']
    return __main__.main(['hook', 'codex', args[1]])


if __name__ == '__main__':
    sys.exit(main())
```

## Verified file: .workbench/codex-exit-diagnostic/test_bootstrap.py

```python
"""Isolated C9 contract checks; never loads a real checkpoint."""
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import stat
import subprocess
import sys
import time

import pytest

SOURCE = Path(__file__).with_name('bootstrap.py')

@pytest.fixture
def box(tmp_path):
    directory = tmp_path / 'instrument with spaces'
    directory.mkdir()
    script = directory / 'bootstrap.py'
    script.write_bytes(SOURCE.read_bytes())
    home = tmp_path / 'home'
    home.mkdir(mode=0o700)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    cfg = dict(port=port, mode='show', model_mode='fake', idle_seconds=0.3,
               interpreter=sys.executable, fake_answers={
        'difficulty': {'type':'choice','choice':'quick','probabilities': {'quick':0.6,'routine':0.26,'multi_file':0.08,'architecture':0.06}},
        'plan_first': {'type':'noul','noul':0.2}, 'parallel': {'type':'noul','noul':0.1}})
    (home / 'config.json').write_text(json.dumps(cfg))
    env = dict(os.environ, LAYA_HARNESS_HOME=str(home), LAYA_HARNESS_TEST='1', HF_HUB_OFFLINE='1', CODEX_HOME=str(tmp_path/'codex'))
    return script, home, cfg, env


def rows(script):
    path = script.with_name('receipts.jsonl')
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


def run(box, args, value=b''):
    script, home, cfg, env = box
    return subprocess.run([sys.executable,'-I',str(script),*args], input=value, capture_output=True,env=env,timeout=7)


def payload(event):
    return json.dumps(dict(hook_event_name=event,session_id='synthetic',model='gpt-6.1-sol',cwd='/synthetic',permission_mode='default',source='startup',turn_id='1',prompt='PRIVATE PROMPT')).encode()

@pytest.mark.parametrize('args',[[],['junk'],['hook'],['hook','Stop'],['service','extra'],['hook','SessionStart','extra']])
def test_invalid_cli_no_launch(box,args):
    result=run(box,args)
    assert result.returncode == 0 and result.stdout == result.stderr == b''
    assert rows(box[0]) == []
    assert not (box[1]/'service.log').exists()


def test_refused_launch_and_unchanged_predict(box):
    result=run(box,['hook','SessionStart'],payload('SessionStart'))
    assert result.returncode == 0 and result.stdout == result.stderr == b''
    result=run(box,['hook','UserPromptSubmit'],payload('UserPromptSubmit'))
    assert result.returncode == 0 and result.stderr == b''
    expected = 'laya · light task (p=0.86) → GPT-6 Luna at low effort fits this task'
    assert json.loads(result.stdout) == {'systemMessage': expected}
    decision=json.loads((box[1]/'decisions.jsonl').read_text().splitlines()[0])
    assert decision['status']=='decided' and decision['prompt']=='PRIVATE PROMPT'
    assert decision['shown_text'] == expected
    assert decision['answers'] == box[2]['fake_answers']
    assert decision['harness'] == 'codex'
    assert decision['checkpoint']['model_mode'] == 'fake'
    assert decision['suggestion'] == {'model':'gpt-6-luna','display':'GPT-6 Luna','effort':'low','class':'quick'}
    time.sleep(1.2)
    receipt=rows(box[0])
    assert [r['event'] for r in receipt] == ['start','normal_exit']
    assert receipt[1]['returned_normally'] is True
    assert 'PRIVATE PROMPT' not in box[0].with_name('receipts.jsonl').read_text()
    assert stat.S_IMODE(box[0].parent.stat().st_mode)==0o700
    assert stat.S_IMODE(box[0].with_name('receipts.jsonl').stat().st_mode)==0o600


def test_listener_no_restart_and_deadline(box):
    listener=socket.socket();listener.bind(('127.0.0.1',box[2]['port']));listener.listen()
    try:
        started=time.monotonic()
        result=run(box,['hook','UserPromptSubmit'],payload('UserPromptSubmit'))
        assert result.returncode==0 and result.stdout==result.stderr==b''
        assert time.monotonic()-started<1.65
        assert rows(box[0]) == []
    finally:
        listener.close()


def test_open_stdin_deadline(box):
    started=time.monotonic()
    proc=subprocess.Popen([sys.executable,'-I',str(box[0]),'hook','UserPromptSubmit'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=box[3])
    try:
        proc.wait(timeout=3)
        assert proc.returncode==0 and proc.stdout.read()==b'' and time.monotonic()-started<1.65
        assert rows(box[0])==[]
    finally:
        proc.stdin.close()
        if proc.poll() is None: proc.kill();proc.wait()


def runner(box, body):
    code=f"import runpy,signal,time; b=runpy.run_path({str(box[0])!r}); from laya_harness import service; {body}; b['service_mode']()"
    return subprocess.Popen([sys.executable,'-I','-c',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=box[3])

@pytest.mark.parametrize('signum',[signal.SIGHUP,signal.SIGINT,signal.SIGTERM])
def test_default_signal_receipt_and_same_termination(box,signum):
    proc=runner(box,f'signal.signal({int(signum)},signal.SIG_DFL); service.main=lambda: time.sleep(10)')
    try:
        deadline=time.monotonic()+3
        while not rows(box[0]) and time.monotonic()<deadline: time.sleep(.01)
        assert rows(box[0])[0]['event']=='start'
        proc.send_signal(signum);proc.wait(timeout=3)
        assert proc.returncode == -signum
        assert rows(box[0])[-1]['signal']==signal.Signals(signum).name
    finally:
        if proc.poll() is None: proc.kill();proc.wait()

@pytest.mark.parametrize('handler',['signal.SIG_IGN','lambda s,f: None'])
def test_preserve_ignored_and_callable(box,handler):
    proc=runner(box,f'signal.signal(signal.SIGTERM,{handler}); service.main=lambda: time.sleep(.3)')
    deadline=time.monotonic()+3
    while not rows(box[0]) and time.monotonic()<deadline: time.sleep(.01)
    proc.send_signal(signal.SIGTERM);proc.wait(timeout=3)
    assert proc.returncode==0
    assert [r['event'] for r in rows(box[0])]==['start','signal','normal_exit']


def test_exception_class_only(box):
    proc=runner(box,"service.main=lambda: (_ for _ in ()).throw(ValueError('PRIVATE SECRET'))")
    proc.wait(timeout=3)
    assert proc.returncode != 0
    assert rows(box[0])[-1]['exception_class']=='ValueError'
    assert 'PRIVATE SECRET' not in box[0].with_name('receipts.jsonl').read_text()

@pytest.mark.parametrize('kind',['symlink','fifo','directory'])
def test_bad_receipt_does_not_block_termination(box,kind):
    path=box[0].with_name('receipts.jsonl');target=box[0].parent/'target'
    target.write_text('untouched')
    if kind=='symlink': path.symlink_to(target)
    elif kind=='fifo': os.mkfifo(path)
    else: path.mkdir()
    proc=runner(box,'signal.signal(signal.SIGTERM,signal.SIG_DFL); service.main=lambda: time.sleep(10)')
    time.sleep(.15);proc.send_signal(signal.SIGTERM);proc.wait(timeout=3)
    assert proc.returncode == -signal.SIGTERM and target.read_text()=='untouched'


def test_receipt_oserror_best_effort(box,monkeypatch):
    spec=importlib.util.spec_from_file_location('diag',box[0]);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    monkeypatch.setattr(module.os,'open',lambda *a,**kw: (_ for _ in ()).throw(OSError('PRIVATE SECRET')))
    module.receipt('normal_exit',returned_normally=True)
    assert rows(box[0])==[]


@pytest.mark.parametrize('event', ['SessionStart', 'UserPromptSubmit'])
def test_route_exact_argv_and_interpreter_with_spaces(box,event):
    code = f"import runpy,json; b=runpy.run_path({str(box[0])!r}); from laya_harness import __main__,spawn; __main__.main=lambda argv: print(json.dumps([argv,spawn.service_argv('/path with spaces/python')])); b['main'](['hook',{event!r}])"
    result=subprocess.run([sys.executable,'-I','-c',code],capture_output=True,env=box[3],timeout=3)
    assert result.returncode==0
    assert json.loads(result.stdout)==[['hook','codex',event],['/path with spaces/python','-I',str(box[0]),'service']]


def test_callable_handler_actually_invoked(box):
    proc=runner(box,'signal.signal(signal.SIGTERM,lambda s,f: __import__("os")._exit(23)); service.main=lambda: time.sleep(10)')
    deadline=time.monotonic()+3
    while not rows(box[0]) and time.monotonic()<deadline: time.sleep(.01)
    proc.send_signal(signal.SIGTERM);proc.wait(timeout=3)
    assert proc.returncode==23 and rows(box[0])[-1]['event']=='signal'


def test_default_int_handler_preserved(box):
    proc=runner(box,'service.main=lambda: time.sleep(10)')
    deadline=time.monotonic()+3
    while not rows(box[0]) and time.monotonic()<deadline: time.sleep(.01)
    proc.send_signal(signal.SIGINT);proc.wait(timeout=3)
    assert proc.returncode != 0
    assert [r['event'] for r in rows(box[0])]==['start','signal','exception']
    assert rows(box[0])[-1]['exception_class']=='KeyboardInterrupt'


def test_failed_writer_preserves_termination(box):
    proc=runner(box,"b['receipt'].__globals__['os'].open=lambda *a,**k: (_ for _ in ()).throw(OSError('PRIVATE')); signal.signal(signal.SIGTERM,signal.SIG_DFL); service.main=lambda: time.sleep(10)")
    time.sleep(.15);proc.send_signal(signal.SIGTERM);proc.wait(timeout=3)
    assert proc.returncode == -signal.SIGTERM and rows(box[0])==[]


def test_metadata_exact_keys_and_existing_mode(box):
    path=box[0].with_name('receipts.jsonl');path.touch(mode=0o644)
    result=run(box,['service'])
    assert result.returncode==0
    records=rows(box[0])
    assert set(records[0])=={'ts','pid','ppid','pgid','sid','event'}
    assert set(records[1])=={'ts','pid','returned_normally','event'}
    assert stat.S_IMODE(path.stat().st_mode)==0o600
```
