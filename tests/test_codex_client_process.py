"""Run native shell commands with whole-process wall-clock bounds (C1/C6)."""
import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path
import pytest
from laya_harness import codex_hookargv, session_state
from procs import env_for, start_service, stop, wait_health
from test_client_process import Listener, Trickle, rows
from test_codex_client import payload
from conftest import write_config


def env(home):
    value=env_for(home)
    value["CODEX_HOME"] = str(home / "private codex config")
    return value


def command(event, interpreter=None):
    return codex_hookargv.hook_entry(interpreter or sys.executable,event)["command"]


def hook(home,event="UserPromptSubmit",value=None):
    started=time.monotonic()
    result=subprocess.run(command(event),shell=True,input=json.dumps(value or payload(event)).encode(),
                          capture_output=True,env=env(home),timeout=7)
    result.elapsed=time.monotonic()-started
    assert result.returncode == 0 and result.stderr == b""
    assert result.stdout == b"" or set(json.loads(result.stdout)) == {"systemMessage"}
    return result


@pytest.mark.parametrize("event,bound",[("UserPromptSubmit",1.65),("SessionStart",4.65)])
def test_watchdog_stdin_open(configured,home,event,bound):
    started=time.monotonic()
    proc=subprocess.Popen(command(event),shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,env=env(home))
    try:
        proc.stdin.write(b"{");proc.stdin.flush()
        proc.wait(timeout=bound+1)
        elapsed=time.monotonic()-started
        assert proc.returncode == 0 and proc.stdout.read() == b"" and elapsed < bound
        assert rows(home) == []
    finally:
        proc.stdin.close()
        if proc.poll() is None:
            proc.kill();proc.wait()


@pytest.mark.parametrize("kind",["hang","junk","trickle"])
def test_nonresponding_service_no_spawn_bounded(configured,home,kind):
    listener=Trickle(configured["port"],kind) if kind == "trickle" else Listener(configured["port"],kind)
    listener.start()
    try:
        result=hook(home)
    finally:
        listener.close()
    assert result.stdout == b"" and result.elapsed < 1.65
    assert [r["status"] for r in rows(home)] == ["error" if kind == "junk" else "timeout"]
    assert not (home/"service.log").exists()


def test_slow_prediction_whole_command_bound(configured,home):
    write_config(home,fake_predict_seconds=4)
    proc=start_service(home)
    try:
        wait_health(configured["port"])
        result=hook(home)
        assert result.stdout == b"" and result.elapsed < 1.65
        assert [r["status"] for r in rows(home)] == ["timeout"]
    finally:
        stop(proc)


def test_blocked_local_diagnostic_path_deadline(configured,home):
    path=home/"client.log"
    os.mkfifo(path)
    started=time.monotonic()
    result=subprocess.run(command("UserPromptSubmit"),shell=True,input=b"garbage",capture_output=True,
                          env=env(home),timeout=3)
    assert result.returncode == 0 and result.stdout == b"" and time.monotonic()-started < 1.65


@pytest.mark.parametrize("value",[b"garbage",b"[]",b"",json.dumps(payload(model=None)).encode()])
def test_malformed_exact_command_error_row(configured,home,value):
    result=subprocess.run(command("UserPromptSubmit"),shell=True,input=value,capture_output=True,env=env(home),timeout=3)
    assert result.returncode == 0 and result.stdout == result.stderr == b""
    assert [r["status"] for r in rows(home)] == ["error"]


def test_shell_metacharacter_interpreter_and_private_files(configured,home,tmp_path):
    target=tmp_path/"space ' quote; $(echo nope)"
    target.mkdir()
    (target / "bin").mkdir()
    (target / "pyvenv.cfg").write_text((Path(sys.prefix) / "pyvenv.cfg").read_text())
    (target / "lib").symlink_to(Path(sys.prefix) / "lib", target_is_directory=True)
    interpreter=target/"bin"/"python"
    interpreter.symlink_to(sys.executable)
    result=subprocess.run(command("UserPromptSubmit",str(interpreter)),shell=True,input=json.dumps(payload(agent_id="")).encode(),
                          capture_output=True,env=env(home),timeout=3)
    assert result.returncode == 0 and result.stdout == result.stderr == b""
    assert [r["status"] for r in rows(home)] == ["skipped"]
    assert stat.S_IMODE(home.stat().st_mode)==0o700
    for path in [home/"client.log",home/"decisions.jsonl",* (home/"sessions").iterdir()]:
        assert stat.S_IMODE(path.stat().st_mode)==0o600


def test_systemexit_and_stray_stdout_failopen(configured,home):
    code='''from laya_harness import client, __main__
def fail(*a):
 print("context leak")
 raise SystemExit(2)
client.run=fail
__main__._hook(["codex","UserPromptSubmit"])
'''
    result=subprocess.run([sys.executable,"-I","-c",code],input=json.dumps(payload()).encode(),capture_output=True,
                          env=env(home),timeout=3)
    assert result.returncode == 0 and result.stdout == result.stderr == b""
    assert "SystemExit: 2" in (home/"client.log").read_text()


def test_bad_args_off_and_unsupported_silent(configured,home):
    write_config(home,mode="off")
    for tail in ["", "codex", "codex UserPromptSubmit", "codex PostModelSwitch"]:
        result=subprocess.run([sys.executable,"-I","-m","laya_harness","hook",*tail.split()],input=b"garbage",
                              capture_output=True,env=env(home),timeout=3)
        assert result.returncode == 0 and result.stdout == result.stderr == b""
    assert rows(home) == [] and not list((home/"sessions").glob("*.json"))


def test_extra_codex_args_are_invalid_silent_invocation(configured,home):
    result=subprocess.run([sys.executable,"-I","-m","laya_harness","hook","codex","UserPromptSubmit","extra"],
                          input=json.dumps(payload(agent_id="")).encode(),capture_output=True,env=env(home),timeout=3)
    assert result.returncode == 0 and result.stdout == result.stderr == b""
    assert rows(home) == []


def test_native_startup_waits_ready_and_both_copy_survives_exit(configured,home):
    from test_client_process import ABOVE_GATE
    write_config(home,fake_load_seconds=.3,fake_answers=ABOVE_GATE)
    body=None
    try:
        assert hook(home,"SessionStart").stdout == b""
        body=wait_health(configured["port"],timeout=1)
        assert rows(home) == []
        result=hook(home)
        assert json.loads(result.stdout) == {"systemMessage":(
            "laya · heavy task (p=0.91) → GPT-6 Astra at xhigh effort fits this task\n"
            "laya · reads like a multi-step change (p=0.91) → Plan mode (/plan), or tell Codex to plan first")}
        assert result.elapsed < 1.65 and [r["status"] for r in rows(home)] == ["decided"]
        assert os.getsid(body["pid"]) == body["pid"]
        assert wait_health(configured["port"],timeout=1)["pid"] == body["pid"]
    finally:
        if body:os.kill(body["pid"],15)


def test_failed_load_same_process_across_native_prompts(configured,home):
    write_config(home,fake_load_error="missing model")
    proc=start_service(home)
    try:
        initial=wait_health(configured["port"],want=("not_ready",))
        for turn in ("1","2","3"):
            assert hook(home,value=payload(turn_id=turn)).stdout == b""
        assert [r["status"] for r in rows(home)] == ["not_ready"]*3
        assert wait_health(configured["port"],want=("not_ready",))["pid"] == initial["pid"]
        assert len((home/"fake_loads.txt").read_text().split()) == 1
        assert not (home/"service.log").exists()
    finally:
        stop(proc)


def test_codex_hook_standard_library_imports(configured,home):
    code='''import importlib.abc, sys
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  name=fullname.partition('.')[0]
  if name not in sys.stdlib_module_names and name != 'laya_harness':
   raise AssertionError('third-party import: '+fullname)
sys.meta_path.insert(0,Guard())
from laya_harness import codex_client, __main__
assert 'laya_mlx' not in sys.modules and 'mlx' not in sys.modules
'''
    result=subprocess.run([sys.executable,"-I","-c",code],capture_output=True,env=env(home),timeout=3)
    assert result.returncode == 0,result.stderr.decode()


@pytest.mark.parametrize("event", ["UserPromptSubmit", "SessionStart"])
@pytest.mark.parametrize("api", ["import", "signal", "setitimer"])
@pytest.mark.parametrize("exception", ["RuntimeError", "SystemExit"])
def test_watchdog_setup_failure_exits_before_input_or_state(home, event, api, exception):
    code = f'''import builtins, signal
from laya_harness import __main__
def fail(*args, **kwargs):
    raise {exception}(2)
if {api!r} == "import":
    original_import = builtins.__import__
    def guarded_import(name, *args, **kwargs):
        if name == "signal":
            fail()
        return original_import(name, *args, **kwargs)
    builtins.__import__ = guarded_import
else:
    setattr(signal, {api!r}, fail)
__main__._hook(["codex", {event!r}])
'''
    proc = subprocess.Popen([sys.executable, "-I", "-c", code], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env(home))
    try:
        proc.wait(timeout=1)
        assert proc.returncode == 0
        assert proc.stdout.read() == proc.stderr.read() == b""
        assert not home.exists()
    finally:
        proc.stdin.close()
        if proc.poll() is None:
            proc.kill()
            proc.wait()
