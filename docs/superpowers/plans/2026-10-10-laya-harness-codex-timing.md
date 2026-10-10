# Temporary Codex acceptance timing preflight

Contract: Stage 1 design C7–C8. Scope: prepare and verify local workbench instrumentation; no shipping source edit, real-home config change, hook installation or model request.

1. Implement C8 instrument and requirement-derived subprocess tests in `.workbench/codex-timing/`, using the repo `.venv/bin/python` for tests and inherited registered interpreter for child commands. Demonstrate behavioral RED then GREEN. Preserve all advisor files.
2. Controller executes the focused tests before documenting their command/results, generates literal code blocks from verified files, and commissions an independent review against C8. Visual review N/A: no UI or copy changes.
3. Commit generated plan before preparing the exact temporary hook replacement. Show reviewed diff for user approval; do not install until approved.
4. After approval, install exact draft privately, record baseline and guide native reload/trust and human captures. Restore production hooks after measured acceptance. Claude acceptance remains deferred.

Literal verified blocks and observed gate results will be appended after preflight; none are guessed here.

## Verified preflight

Implemented and executed in the isolated local workbench. Behavioral stub RED: 15 failed in 0.35 s; initial GREEN: 15 passed in 0.86 s; expanded final suite: 18 passed in 1.71 s. Controller replay `.venv/bin/python -m pytest -q .workbench/codex-timing/test_capture.py`: 18 passed in 1.00 s. Synthetic CLI external durations 66.382–107.576 ms, child receipts 36.888–77.660 ms, wrapper overhead 28.331–29.916 ms. No advisor/model requests or live changes. Tests copy the CLI to a temporary tree with a synthetic interpreter shim. The observed helper is `measure(event, command, receipt, limit)`; production main constructs a fixed absolute advisor command.

Task snapshot: refs/laywip/codex-timing/task-1; isolated diff `/private/tmp/laya-codex-timing/task-1.diff`. Independent review APPROVED with no findings; reviewer replay: 18 passed in 1.04 s. Visual review N/A: unchanged native UI/copy.

## Verified file: .workbench/codex-timing/capture.py

```python
"""Local acceptance instrument; never stores child input or output."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time


LIMITS = {'SessionStart': 4.6, 'UserPromptSubmit': 1.6}


def append_receipt(path, row):
    path = Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.parent.is_symlink() or not path.parent.is_dir():
        return
    path.parent.chmod(0o700)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return
        os.fchmod(fd, 0o600)
        os.write(fd, (json.dumps(row, separators=(',', ':')) + '\n').encode())
    finally:
        os.close(fd)


def measure(event, command, receipt, limit):
    if event not in LIMITS:
        return 0
    child = None
    start = time.monotonic()
    timed_out = False
    exit_code = None
    try:
        child = subprocess.Popen(command)
        try:
            exit_code = child.wait(timeout=max(0, limit - (time.monotonic() - start)))
        except subprocess.TimeoutExpired:
            timed_out = True
            child.kill()
            exit_code = child.wait()
    except BaseException:
        if child is not None:
            try:
                child.kill()
                exit_code = child.wait()
            except BaseException:
                pass
    duration_ms = (time.monotonic() - start) * 1000
    try:
        append_receipt(receipt, {
            'event': event,
            'ts': datetime.now(timezone.utc).isoformat(),
            'duration_ms': round(duration_ms, 3),
            'exit_code': exit_code,
            'timed_out': timed_out,
        })
    except BaseException:
        pass
    return 0


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1 or args[0] not in LIMITS:
        return 0
    event = args[0]
    script = Path(__file__).absolute()
    interpreter = str(script.parents[2] / '.venv/bin/python')
    command = [interpreter, '-I', '-m', 'laya_harness', 'hook', 'codex', event]
    try:
        return measure(event, command, script.with_name('receipts.jsonl'), LIMITS[event])
    except BaseException:
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
```

## Verified file: .workbench/codex-timing/test_capture.py

```python
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
import shutil
import shlex

import pytest


SCRIPT = Path(__file__).with_name('capture.py')
spec = importlib.util.spec_from_file_location('timing_capture', SCRIPT)
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


def run_measure(tmp_path, code, event='UserPromptSubmit', limit=1.6, receipt=None):
    receipt = receipt or tmp_path / 'private' / 'receipts.jsonl'
    driver = (
        'import importlib.util; '
        f's=importlib.util.spec_from_file_location("capture", {str(SCRIPT)!r}); '
        'm=importlib.util.module_from_spec(s); s.loader.exec_module(m); '
        f'raise SystemExit(m.measure({event!r}, { [sys.executable, "-I", "-c", code]!r}, {str(receipt)!r}, {limit!r}))'
    )
    start = time.monotonic()
    result = subprocess.run([sys.executable, '-I', '-c', driver], input=b'PRIVATE PROMPT', capture_output=True, timeout=3)
    return result, receipt, (time.monotonic() - start) * 1000


@pytest.mark.parametrize('output', ['', '{"systemMessage":"PRIVATE OUTPUT"}\n'])
def test_passthrough_and_private_receipt(tmp_path, output):
    result, receipt, _ = run_measure(tmp_path, f'import sys; assert sys.stdin.buffer.read()==b"PRIVATE PROMPT"; sys.stdout.write({output!r}); sys.stderr.write("child stderr")')
    assert result.returncode == 0
    assert result.stdout == output.encode()
    assert result.stderr == b'child stderr'
    rows = receipt.read_text().splitlines()
    assert len(rows) == 1
    row = json.loads(rows[0])
    assert set(row) == {'event', 'ts', 'duration_ms', 'exit_code', 'timed_out'}
    assert row['event'] == 'UserPromptSubmit'
    assert row['exit_code'] == 0 and row['timed_out'] is False
    assert row['duration_ms'] > 0
    assert row['ts'].endswith('+00:00')
    assert 'PRIVATE' not in rows[0]
    assert stat.S_IMODE(receipt.stat().st_mode) == 0o600
    assert stat.S_IMODE(receipt.parent.stat().st_mode) == 0o700


def test_child_failure_returns_zero(tmp_path):
    result, receipt, _ = run_measure(tmp_path, 'raise SystemExit(7)')
    assert result.returncode == 0
    assert json.loads(receipt.read_text())['exit_code'] == 7


def test_timeout_kills_and_reaps(tmp_path):
    pidfile = tmp_path / 'pid'
    result, receipt, elapsed = run_measure(tmp_path, f'import os,time; open({str(pidfile)!r},"w").write(str(os.getpid())); time.sleep(20)', limit=.15)
    assert result.returncode == 0 and elapsed < 1000
    row = json.loads(receipt.read_text())
    assert row['timed_out'] is True and row['exit_code'] == -9
    with pytest.raises(ProcessLookupError):
        os.kill(int(pidfile.read_text()), 0)


def test_symlink_receipt_refused(tmp_path):
    target = tmp_path / 'target'
    target.write_text('untouched')
    receipt = tmp_path / 'private' / 'receipts.jsonl'
    receipt.parent.mkdir()
    receipt.symlink_to(target)
    result, _, _ = run_measure(tmp_path, 'pass', receipt=receipt)
    assert result.returncode == 0
    assert target.read_text() == 'untouched'


@pytest.mark.parametrize('kind', ['directory', 'fifo', 'parent_file'])
def test_write_failure_and_nonregular_are_fail_open(tmp_path, kind):
    receipt = tmp_path / 'private' / 'receipts.jsonl'
    if kind == 'parent_file':
        receipt.parent.write_text('not a directory')
    else:
        receipt.parent.mkdir()
        receipt.mkdir() if kind == 'directory' else os.mkfifo(receipt)
    result, _, elapsed = run_measure(tmp_path, 'print("child ran")', receipt=receipt)
    assert result.returncode == 0 and result.stdout == b'child ran\n'
    assert elapsed < 1000


@pytest.mark.parametrize('args', [[], ['Unknown'], ['UserPromptSubmit', 'extra']])
def test_invalid_cli_silent_no_child(monkeypatch, args, capsys):
    def forbidden(*args, **kwargs):
        pytest.fail('invalid invocation launched child')
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    assert capture.main(args) == 0
    assert capsys.readouterr() == ('', '')


@pytest.mark.parametrize('event,limit', [('SessionStart',4.6), ('UserPromptSubmit',1.6)])
def test_cli_fixed_registered_command(monkeypatch, event, limit):
    calls = []
    monkeypatch.setattr(capture, 'measure', lambda *args: calls.append(args) or 0)
    assert capture.main([event]) == 0
    expected_python = str(SCRIPT.parents[2] / '.venv/bin/python')
    assert calls == [(event, [expected_python, '-I', '-m', 'laya_harness', 'hook', 'codex', event], SCRIPT.with_name('receipts.jsonl'), limit)]


def test_launch_failure_returns_zero(tmp_path):
    assert capture.measure('UserPromptSubmit', ['/nonexistent/laya-timing-child'], tmp_path/'private'/'receipts.jsonl', 1.6) == 0


def test_invalid_measure_no_child(tmp_path, monkeypatch):
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: pytest.fail('launched'))
    assert capture.measure('Invalid', [sys.executable], tmp_path/'receipt', 1.6) == 0


def test_existing_receipt_permissions_repaired_and_appended(tmp_path):
    receipt = tmp_path/'private'/'receipts.jsonl'
    receipt.parent.mkdir(mode=0o755)
    receipt.write_text('{"previous":true}\n')
    receipt.chmod(0o644)
    result, _, _ = run_measure(tmp_path, 'pass', receipt=receipt)
    assert result.returncode == 0
    assert len(receipt.read_text().splitlines()) == 2
    assert stat.S_IMODE(receipt.stat().st_mode) == 0o600
    assert stat.S_IMODE(receipt.parent.stat().st_mode) == 0o700


def test_receipt_write_exception_is_fail_open(tmp_path, monkeypatch):
    def fail_write(*args):
        raise OSError('unwritable')
    monkeypatch.setattr(capture, 'append_receipt', fail_write)
    assert capture.measure('SessionStart', [sys.executable, '-I', '-c', 'pass'], tmp_path/'receipt', 4.6) == 0


def synthetic_cli(tmp_path):
    script = tmp_path/'.workbench'/'codex-timing'/'capture.py'
    script.parent.mkdir(parents=True)
    shutil.copyfile(SCRIPT, script)
    interpreter = tmp_path/'.venv'/'bin'/'python'
    interpreter.parent.mkdir(parents=True)
    code = 'import sys; assert sys.argv[1:]==["-I","-m","laya_harness","hook","codex","UserPromptSubmit"]; assert sys.stdin.buffer.read()==b"PRIVATE PROMPT"; print(\'{"systemMessage":"synthetic"}\')'
    interpreter.write_text('#!/bin/sh\nexec ' + shlex.join([sys.executable, '-I', '-c', code]) + ' "$@"\n')
    interpreter.chmod(0o700)
    return script


def test_actual_cli_passthrough_and_complete_bound(tmp_path):
    script = synthetic_cli(tmp_path)
    start = time.monotonic()
    result = subprocess.run([sys.executable, '-I', str(script), 'UserPromptSubmit'], input=b'PRIVATE PROMPT', capture_output=True, timeout=2)
    elapsed = (time.monotonic()-start)*1000
    assert result.returncode == 0 and result.stderr == b''
    assert result.stdout == b'{"systemMessage":"synthetic"}\n'
    row = json.loads(script.with_name('receipts.jsonl').read_text())
    assert row['exit_code'] == 0 and row['timed_out'] is False
    assert 0 < row['duration_ms'] <= elapsed < 1600
```
