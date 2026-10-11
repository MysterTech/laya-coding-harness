"""Process-level tests of the hook client (spec §6): they run the exact registered argv."""

import copy
import fcntl
import json
import os
import signal
import socket
import stat
import subprocess
import sys
import threading
import time
import types
from pathlib import Path

import pytest

from conftest import write_config
from laya_harness import client, hookargv
from procs import env_for, request, start_service, stop, wait_health

PAYLOADS = json.loads((Path(__file__).parent / "fixtures" / "payloads.json").read_text())
ABOVE_GATE = {
    "difficulty": {"type": "choice", "choice": "architecture",
                   "probabilities": {"quick": 0.03, "routine": 0.06, "multi_file": 0.3, "architecture": 0.61}},
    "plan_first": {"type": "noul", "noul": 0.91},
    "parallel": {"type": "noul", "noul": 0.2},
}


def run_hook(home, event, payload, harness="claude-code", timeout=15):
    argv = hookargv.hook_argv(sys.executable, harness, event)
    data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    started = time.monotonic()
    result = subprocess.run(argv, input=data, capture_output=True, env=env_for(home), timeout=timeout)
    result.elapsed = time.monotonic() - started
    assert result.returncode == 0, result
    out = result.stdout.decode()
    assert out == "" or set(json.loads(out)) == {"systemMessage"}
    return result


def rows(home):
    path = home / "decisions.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def loads(home):
    path = home / "fake_loads.txt"
    return len(path.read_text().split()) if path.exists() else 0


@pytest.fixture
def cleanup(configured):
    """Stop any service a hook spawned on the test port."""
    procs = []
    yield procs
    for proc in procs:
        stop(proc)
    try:
        status, body = request(configured["port"], "GET", "/v1/health", timeout=0.5)
        if status == 200 and body.get("app") == "laya-harness":
            os.kill(body["pid"], signal.SIGTERM)
    except OSError:
        pass


class Listener(threading.Thread):
    """A foreign listener on the test port: "junk" answers with garbage, "hang" never replies."""

    def __init__(self, port, mode):
        super().__init__(daemon=True)
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", port))
        self.sock.listen(8)
        self.mode, self.held = mode, []

    def run(self):
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            if self.mode == "junk":
                conn.recv(65536)
                conn.sendall(b"HTTP/1.0 200 OK\r\n\r\nnot laya at all")
                conn.close()
            else:
                self.held.append(conn)

    def close(self):
        self.sock.close()
        for conn in self.held:
            conn.close()


class Trickle(Listener):
    """A foreign listener that answers one byte every 0.2 s: each read is quick, the whole is not."""

    def run(self):
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            self.held.append(conn)
            threading.Thread(target=self._drip, args=(conn,), daemon=True).start()

    def _drip(self, conn):
        try:
            conn.recv(65536)
            for byte in b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n{}":
                conn.sendall(bytes([byte]))
                time.sleep(0.2)
        except OSError:
            pass


def human(prompt="fix the typo in README", session="sess-1"):
    return dict(PAYLOADS["user_prompt_human"], prompt=prompt, session_id=session, transcript_path="")


def served_reply(**changes):
    reply = {"app": "laya-harness", "answers": copy.deepcopy(ABOVE_GATE), "usage": {"truncated": False},
             "input_chars_dropped": 0, "truncated": False,
             "checkpoint": {"repo": "aac6fef/laya-mlx", "revision": "r", "model_mode": "fake"},
             "question_set": {"id": "profile_v0", "sha256": "0" * 64},
             "versions": {"laya_harness": "9.9.9", "laya_mlx": "0.3.0"}}
    reply.update(changes)
    return reply


# --- fail-open --------------------------------------------------------------------------

def test_bad_event_and_harness_print_nothing(configured, home):
    assert run_hook(home, "NoSuchEvent", human()).stdout == b""
    assert run_hook(home, "UserPromptSubmit", human(), harness="nope").stdout == b""
    assert "unknown" in (home / "client.log").read_text()


def test_garbage_stdin_prints_nothing(configured, home):
    assert run_hook(home, "UserPromptSubmit", b"\x00not json").stdout == b""
    assert "hook failed" in (home / "client.log").read_text()


@pytest.mark.parametrize("payload", [b"\x00not json", b"[1, 2]", b"", json.dumps(dict(PAYLOADS["user_prompt_human"],
                                     session_id=5, transcript_path="")).encode()])
def test_client_error_still_logs_an_error_row(configured, home, payload):
    assert run_hook(home, "UserPromptSubmit", payload).stdout == b""
    assert [r["status"] for r in rows(home)] == ["error"]  # spec §5: one row, status error
    assert rows(home)[0]["input_chars_dropped"] is None and rows(home)[0]["truncated"] is None
    assert "hook failed" in (home / "client.log").read_text()


def test_hook_argv_is_the_registered_exec_form():
    assert hookargv.hook_argv("/x/py", "claude-code", "UserPromptSubmit") == [
        "/x/py", "-I", "-m", "laya_harness", "hook", "claude-code", "UserPromptSubmit"]


def test_state_files_are_private(configured, home, cleanup):
    run_hook(home, "UserPromptSubmit", human())  # nothing bound: spawns, so service.log exists too
    wait_health(configured["port"])
    run_hook(home, "NoSuchEvent", human())
    assert stat.S_IMODE(home.stat().st_mode) == 0o700
    for name in ("decisions.jsonl", "client.log", "service.log"):
        assert stat.S_IMODE((home / name).stat().st_mode) == 0o600, name


def test_mode_off_does_nothing(configured, home):
    write_config(home, mode="off")
    result = run_hook(home, "UserPromptSubmit", human())
    assert result.stdout == b"" and rows(home) == [] and loads(home) == 0


# --- UserPromptSubmit ---------------------------------------------------------------------

def test_service_down_spawns_once_and_shows_nothing(configured, home, cleanup):
    write_config(home, fake_load_seconds=1)
    first = run_hook(home, "UserPromptSubmit", human())
    second = run_hook(home, "UserPromptSubmit", human(session="sess-2"))
    assert first.stdout == b"" and second.stdout == b""
    assert rows(home)[0]["status"] == "started_service" and rows(home)[0]["cold"] is True
    wait_health(configured["port"])
    assert loads(home) == 1


def test_first_prompt_shows_both_lines_and_logs_the_row(configured, home, cleanup):
    write_config(home, fake_answers=ABOVE_GATE)
    cleanup.append(start_service(home))
    wait_health(configured["port"])
    result = run_hook(home, "UserPromptSubmit", human("redesign the auth layer and migrate JWT handling"))
    assert json.loads(result.stdout) == {"systemMessage": (
        "laya · heavy task (p=0.91) → Opus 5.5 at xhigh effort fits this task\n"
        "laya · reads like a multi-step change (p=0.91) → Plan mode (mode menu, then 4), or tell Claude to plan first")}
    row = rows(home)[-1]
    assert row["status"] == "decided" and row["source"] == "human"
    assert row["suggestion"] == {"model": "claude-opus-5-5", "display": "Opus 5.5", "effort": "xhigh",
                                 "class": "architecture"}
    assert row["question_set"]["id"] == "profile_v0" and row["prompt_id"] == "prompt-1"
    assert row["versions"]["adapter_rules"] == "claude_code_v0"
    assert row["latency_ms"] > 0
    second = run_hook(home, "UserPromptSubmit", human("x" * 300))
    assert second.stdout == b""
    assert rows(home)[-1]["suppress_reason"] == {"model": "not_first_prompt", "plan": "already_shown"}


def test_machine_turns_record_source_and_reason(configured, home):
    for name in ("user_prompt_task_notification", "user_prompt_agent_message", "user_prompt_cross_session"):
        run_hook(home, "UserPromptSubmit", dict(PAYLOADS[name], transcript_path=""))
    assert [r["source"] for r in rows(home)] == ["task-notification", "agent", "peer"]
    assert all(r["suppress_reason"] == {"model": "not_human", "plan": "not_human"} for r in rows(home))


def test_row_records_what_the_service_ran(configured, home, monkeypatch):
    reply = served_reply()
    monkeypatch.setattr(client.service_client, "profile", lambda port, prompt, deadline: ("ok", reply))
    out = client.run("claude-code", "UserPromptSubmit", json.dumps(human()).encode(), time.monotonic())
    row = rows(home)[-1]
    assert out and row["status"] == "decided"
    assert row["question_set"] == reply["question_set"]  # what produced the answers, not the client's file
    assert row["versions"]["service_laya_harness"] == "9.9.9" and row["versions"]["laya_harness"] == "0.0.0"
    assert "run laya-harness stop" in (home / "client.log").read_text()


def test_a_failed_row_write_never_marks_a_line_as_shown(configured, home, monkeypatch):
    monkeypatch.setattr(client.service_client, "profile", lambda port, prompt, deadline: ("ok", served_reply()))

    def full_disk(row):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(client.decision_log, "append", full_disk)
    with pytest.raises(OSError):
        client.run("claude-code", "UserPromptSubmit", json.dumps(human()).encode(), time.monotonic())
    state = json.loads((home / "sessions" / "sess-1.json").read_text())
    assert state["model_line_shown"] is False and state["plan_shown"] is False


def test_lone_surrogate_prompt_still_shows_and_logs(configured, home, cleanup):
    write_config(home, fake_answers=ABOVE_GATE)
    cleanup.append(start_service(home))
    wait_health(configured["port"])
    result = run_hook(home, "UserPromptSubmit", human("redesign the auth layer \ud83d and migrate JWT handling"))
    assert result.stdout != b"" and rows(home)[-1]["status"] == "decided"


def test_machine_turns_are_skipped_without_calling_the_service(configured, home):
    for name in ("user_prompt_task_notification", "user_prompt_agent_message", "user_prompt_cross_session"):
        payload = dict(PAYLOADS[name], transcript_path="")
        assert run_hook(home, "UserPromptSubmit", payload).stdout == b""
    assert [r["status"] for r in rows(home)] == ["skipped"] * 3
    assert loads(home) == 0  # nothing was spawned
    assert not (home / "sessions" / "sess-1.json").exists()  # session state untouched


def test_log_only_shows_nothing_but_records_why(configured, home, cleanup):
    write_config(home, fake_answers=ABOVE_GATE, mode="log-only")
    cleanup.append(start_service(home))
    wait_health(configured["port"])
    assert run_hook(home, "UserPromptSubmit", human()).stdout == b""
    assert rows(home)[-1]["suppress_reason"] == {"model": "log_only", "plan": "log_only"}


def test_slow_reply_times_out_quickly(configured, home, cleanup):
    write_config(home, fake_predict_seconds=3)
    cleanup.append(start_service(home))
    wait_health(configured["port"])
    result = run_hook(home, "UserPromptSubmit", human())
    assert result.stdout == b"" and result.elapsed < 2.0
    assert rows(home)[-1]["status"] == "timeout"
    assert not (home / "service.log").exists()  # a timeout never spawns (spec §4.3)


@pytest.mark.parametrize("mode, status", [("junk", "error"), ("hang", "timeout")])
def test_foreign_listener_is_left_alone(configured, home, mode, status):
    listener = Listener(configured["port"], mode)
    listener.start()
    try:
        result = run_hook(home, "UserPromptSubmit", human())
    finally:
        listener.close()
    assert result.stdout == b"" and result.elapsed < 2.5
    assert rows(home)[-1]["status"] == status and loads(home) == 0
    assert not (home / "service.log").exists()  # spawn_service opens it: nothing was spawned
    assert f"port {configured['port']}" in (home / "client.log").read_text()  # spec §5: one line


@pytest.mark.parametrize("event, limit", [("UserPromptSubmit", 2.0), ("SessionStart", 1.5)])
def test_trickling_listener_cannot_stretch_the_deadline(configured, home, event, limit):
    listener = Trickle(configured["port"], "trickle")
    listener.start()
    try:
        result = run_hook(home, event, human() if event == "UserPromptSubmit" else start_payload(), timeout=30)
    finally:
        listener.close()
    assert result.elapsed < limit and not (home / "service.log").exists()


def test_spawned_service_is_detached_and_logs_stderr(configured, home, cleanup):
    write_config(home, fake_load_error="broken")  # the service prints "load failed" to stderr
    run_hook(home, "UserPromptSubmit", human())
    body = wait_health(configured["port"], want=("not_ready",))
    assert os.getsid(body["pid"]) == body["pid"]  # its own session: the hook runner cannot reap it
    deadline = time.monotonic() + 2
    while "load failed" not in (home / "service.log").read_text() and time.monotonic() < deadline:
        time.sleep(0.05)
    assert "load failed" in (home / "service.log").read_text()


def test_spawn_does_not_hold_the_hook_pipes(configured, home, cleanup):
    write_config(home, fake_print_stdout=True)
    argv = hookargv.hook_argv(sys.executable, "claude-code", "UserPromptSubmit")
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env_for(home))
    proc.stdin.write(json.dumps(human()).encode())
    proc.stdin.close()
    proc.wait(timeout=10)
    exited = time.monotonic()
    out, err = proc.stdout.read(), proc.stderr.read()  # returns at EOF on both pipes
    assert time.monotonic() - exited < 0.5
    assert proc.returncode == 0 and out == b""
    assert wait_health(configured["port"])["state"] == "ready"  # the child outlived the hook


# --- SessionStart and PostModelSwitch -----------------------------------------------------

def start_payload(source="startup"):
    return dict(PAYLOADS["session_start_startup"], source=source, transcript_path="")


def test_startup_waits_while_loading_then_returns(configured, home, cleanup):
    write_config(home, fake_load_seconds=1.5)
    result = run_hook(home, "SessionStart", start_payload())
    assert result.stdout == b""
    assert 1.0 < result.elapsed < 3.5
    assert wait_health(configured["port"], timeout=0.5)["state"] == "ready"


def test_startup_gives_up_after_four_seconds(configured, home, cleanup):
    write_config(home, fake_load_seconds=8)
    result = run_hook(home, "SessionStart", start_payload())
    assert 3.8 < result.elapsed < 5.5 and result.stdout == b""


def test_startup_returns_at_once_when_not_ready(configured, home, cleanup):
    write_config(home, fake_load_error="broken")
    cleanup.append(start_service(home))
    wait_health(configured["port"], want=("not_ready",))
    assert run_hook(home, "SessionStart", start_payload()).elapsed < 1.0


@pytest.mark.parametrize("mode", ["junk", "hang"])
def test_startup_returns_at_once_on_foreign_listener(configured, home, mode):
    listener = Listener(configured["port"], mode)
    listener.start()
    try:
        result = run_hook(home, "SessionStart", start_payload())
    finally:
        listener.close()
    assert result.elapsed < 1.5 and loads(home) == 0
    assert not (home / "service.log").exists()
    assert "no service started" in (home / "client.log").read_text()


@pytest.mark.parametrize("source", ["resume", "clear", "compact", "fork"])
def test_other_sources_start_the_service_without_waiting(configured, home, cleanup, source):
    write_config(home, fake_load_seconds=8)
    assert run_hook(home, "SessionStart", start_payload(source)).elapsed < 1.0
    wait_health(configured["port"], want=("loading",))  # started; this also lets cleanup stop it


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


@pytest.mark.parametrize("replies, spawned, polls", [
    ([("ok", {"state": "ready"})], False, 1),
    ([("ok", {"state": "not_ready"})], False, 1),
    ([("foreign", None)], False, 1),
    ([("error", None)], False, 1),
    ([("timeout", None)], True, 1),
    ([("refused", None)], False, 1),
    ([("refused", None)] * 3 + [("ok", {"state": "ready"})], True, 4),
    ([("ok", {"state": "loading"}), ("timeout", None), ("ok", {"state": "ready"})], False, 3),
])
def test_wait_stop_conditions(monkeypatch, replies, spawned, polls):
    clock, seen = FakeClock(), []
    monkeypatch.setattr(client, "time", types.SimpleNamespace(monotonic=clock.monotonic, sleep=clock.sleep))

    def health(port, timeout):
        seen.append(timeout)
        return replies[min(len(seen), len(replies)) - 1]

    monkeypatch.setattr(client.service_client, "health", health)
    client._wait_until_ready(1, spawned)
    assert len(seen) == polls


def test_wait_caps_each_poll_at_the_time_left(monkeypatch):
    clock, seen = FakeClock(), []
    monkeypatch.setattr(client, "time", types.SimpleNamespace(monotonic=clock.monotonic, sleep=clock.sleep))

    def health(port, timeout):
        seen.append(timeout)
        clock.now += timeout
        return "ok", {"state": "loading"}

    monkeypatch.setattr(client.service_client, "health", health)
    client._wait_until_ready(1, spawned=True)
    assert clock.now <= client.WAIT_BUDGET + 1e-6 and seen[-1] < client.HEALTH_TIMEOUT


def test_startup_in_mode_off_starts_nothing(configured, home):
    write_config(home, mode="off")
    assert run_hook(home, "SessionStart", start_payload()).elapsed < 1.0
    assert loads(home) == 0


def test_model_switch_records_model_and_prints_nothing(configured, home):
    payload = dict(PAYLOADS["post_model_switch"], transcript_path="")
    assert run_hook(home, "PostModelSwitch", payload).stdout == b""
    state = json.loads((home / "sessions" / "sess-1.json").read_text())
    assert state["model"] == "claude-opus-4-7" and state["model_source"] == "post_model_switch"


def test_settings_snippet_uses_the_same_argv():
    snippet = hookargv.settings_snippet("/x/py")
    entry = snippet["hooks"]["UserPromptSubmit"][0]["hooks"][0]
    assert [entry["command"], *entry["args"]] == hookargv.hook_argv("/x/py", "claude-code", "UserPromptSubmit")
    assert {e: snippet["hooks"][e][0]["hooks"][0]["timeout"] for e in hookargv.EVENTS} == {
        "SessionStart": 8, "UserPromptSubmit": 3, "PostModelSwitch": 3}


# --- accepted review regressions (spec §4.2, §4.4, §4.6, §4.10) ---------------------------

@pytest.mark.parametrize("mode", ["show", "off"])
def test_quiet_hook_tightens_existing_client_log(configured, home, mode):
    write_config(home, mode=mode)
    path = home / "client.log"
    path.write_text("")
    path.chmod(0o644)
    assert run_hook(home, "UserPromptSubmit", human("<task-notification done>")).stdout == b""
    assert path.read_text() == ""
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_hook_imports_only_the_standard_library(configured, home):
    code = """
import importlib.abc, sys
class BlockThirdParty(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        name = fullname.partition('.')[0]
        if name not in sys.stdlib_module_names and name != 'laya_harness':
            raise AssertionError('third-party import: ' + fullname)
sys.meta_path.insert(0, BlockThirdParty())
from laya_harness import client, hookargv, __main__
assert 'laya_mlx' not in sys.modules and 'mlx' not in sys.modules
"""
    result = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True,
                            env=env_for(home), timeout=5)
    assert result.returncode == 0, result.stderr.decode()


def test_injected_hook_system_exit_still_exits_zero(configured, home):
    code = """
from laya_harness import client, __main__
def fail(*args):
    raise SystemExit(2)
client.run = fail
__main__._hook(['claude-code', 'UserPromptSubmit'])
"""
    result = subprocess.run([sys.executable, "-I", "-c", code], input=json.dumps(human()).encode(),
                            capture_output=True, env=env_for(home), timeout=5)
    assert result.returncode == 0 and result.stdout == b""
    assert "SystemExit: 2" in (home / "client.log").read_text()


def test_failed_first_prompt_consumes_model_eligibility_before_inference(configured, home, monkeypatch):
    replies = iter([("timeout", None), ("ok", served_reply())])
    counts = []

    def profile(port, prompt, deadline):
        counts.append(json.loads((home / "sessions" / "sess-1.json").read_text())["prompt_count"])
        return next(replies)

    monkeypatch.setattr(client.service_client, "profile", profile)
    for _ in range(2):
        assert client.run("claude-code", "UserPromptSubmit", json.dumps(human()).encode(), time.monotonic()) is None
    assert counts == [1, 2]
    assert [r["status"] for r in rows(home)] == ["timeout", "decided"]
    assert rows(home)[1]["suppress_reason"] == {"model": "not_first_prompt", "plan": "too_short"}


@pytest.mark.parametrize("field, value", [
    ("app", "other-app"), ("app", None), ("answers", None),
    ("answers.difficulty.probabilities.quick", True),
    ("answers.difficulty.probabilities.routine", "0.1"),
    ("answers.difficulty.probabilities.multi_file", -0.01),
    ("answers.difficulty.probabilities.architecture", 1.01),
    ("answers.plan_first.noul", float("nan")),
    ("answers.parallel.noul", float("inf")),
    ("usage", []), ("usage.truncated", 1),
    ("checkpoint.repo", ""), ("checkpoint.revision", None),
    ("question_set.id", ""), ("question_set.sha256", "g" * 64),
    ("versions.laya_harness", 2), ("versions.laya_mlx", []),
    ("input_chars_dropped", True), ("input_chars_dropped", -1),
    ("input_chars_dropped", 1.5), ("truncated", 0), ("truncated", True),
])
def test_malformed_profile_is_error_without_advice_or_spawn(configured, home, monkeypatch, field, value):
    reply = served_reply()
    parts = field.split(".")
    target = reply
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value
    monkeypatch.setattr(client.service_client, "_call", lambda *args: (200, json.dumps(reply).encode()))
    assert client.run("claude-code", "UserPromptSubmit", json.dumps(human()).encode(), time.monotonic()) is None
    assert [r["status"] for r in rows(home)] == ["error"]
    assert rows(home)[0]["shown_text"] is None and loads(home) == 0
    assert not (home / "service.log").exists()
    assert "unexpected reply" in (home / "client.log").read_text()


@pytest.mark.parametrize("field", ["app", "usage", "checkpoint", "question_set", "versions",
                                   "input_chars_dropped", "truncated"])
def test_missing_profile_field_is_an_error(configured, home, monkeypatch, field):
    reply = served_reply()
    del reply[field]
    monkeypatch.setattr(client.service_client, "_call", lambda *args: (200, json.dumps(reply).encode()))
    assert client.run("claude-code", "UserPromptSubmit", json.dumps(human()).encode(), time.monotonic()) is None
    assert rows(home)[0]["status"] == "error" and not (home / "service.log").exists()


def test_excessively_nested_profile_reply_is_error_without_advice(configured, home, monkeypatch):
    raw = ("[" * 2000 + "0" + "]" * 2000).encode()
    monkeypatch.setattr(client.service_client, "_call", lambda *args: (200, raw))
    assert client.run("claude-code", "UserPromptSubmit", json.dumps(human()).encode(), time.monotonic()) is None
    assert rows(home)[0]["status"] == "error" and not (home / "service.log").exists()
    assert "unexpected reply" in (home / "client.log").read_text()


@pytest.mark.parametrize("body", [{"state": "loading", "reason": None},
                                   {"app": "other-app", "state": "not_ready", "reason": "broken"},
                                   {"app": "laya-harness", "state": "other", "reason": "broken"},
                                   {"app": "laya-harness", "state": "loading"},
                                   {"app": "laya-harness", "state": "not_ready", "reason": {"why": "broken"}}])
def test_foreign_or_malformed_503_is_error(configured, home, monkeypatch, body):
    monkeypatch.setattr(client.service_client, "_call", lambda *args: (503, json.dumps(body).encode()))
    assert client.run("claude-code", "UserPromptSubmit", json.dumps(human()).encode(), time.monotonic()) is None
    assert rows(home)[0]["status"] == "error" and not (home / "service.log").exists()


@pytest.mark.parametrize("state, reason", [("loading", None), ("not_ready", "broken")])
def test_identified_503_records_loading_or_not_ready_without_restart(configured, home, monkeypatch, state, reason):
    reply = {"app": "laya-harness", "state": state, "reason": reason}
    monkeypatch.setattr(client.service_client, "_call", lambda *args: (503, json.dumps(reply).encode()))
    assert client.run("claude-code", "UserPromptSubmit", json.dumps(human()).encode(), time.monotonic()) is None
    assert rows(home)[0]["status"] == state and not (home / "service.log").exists()
    assert rows(home)[0]["input_chars_dropped"] is None and rows(home)[0]["truncated"] is None


@pytest.mark.parametrize("usage_truncated, dropped", [(False, 11), (True, 0), (False, 0)])
def test_valid_profile_records_character_and_aggregate_truncation(configured, home, monkeypatch,
                                                                usage_truncated, dropped):
    usage = {"truncated": usage_truncated, "input_tokens_dropped": 0}
    reply = served_reply(usage=usage, input_chars_dropped=dropped, truncated=usage_truncated or dropped > 0)
    reply["versions"]["laya_mlx"] = None
    monkeypatch.setattr(client.service_client, "_call", lambda *args: (200, json.dumps(reply).encode()))
    assert client.run("claude-code", "UserPromptSubmit", json.dumps(human()).encode(), time.monotonic())
    row = rows(home)[0]
    assert row["status"] == "decided" and row["usage"] == usage
    assert row["input_chars_dropped"] == dropped
    assert row["truncated"] is (usage_truncated or dropped > 0)


@pytest.mark.parametrize("event", ["UserPromptSubmit", "SessionStart", "PostModelSwitch"])
def test_session_lock_contention_is_bounded_and_tightens_lock(configured, home, event):
    lock = home / "sessions" / "sess-1.lock"
    with lock.open("w") as holder:
        lock.chmod(0o644)
        fcntl.flock(holder, fcntl.LOCK_EX)
        payload = (start_payload("fork") if event == "SessionStart" else
                   PAYLOADS["post_model_switch"] if event == "PostModelSwitch" else human())
        result = run_hook(home, event, payload)
    assert result.stdout == b"" and result.elapsed < 0.5
    assert [r["status"] for r in rows(home)] == (["error"] if event == "UserPromptSubmit" else [])
    assert loads(home) == 0 and not (home / "sessions" / "sess-1.json").exists()
    assert not (home / "service.log").exists()
    assert stat.S_IMODE(lock.stat().st_mode) == 0o600


def test_session_lock_wait_has_exact_fifty_millisecond_budget(configured, home, monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr(client.session_state, "time", types.SimpleNamespace(
        monotonic=clock.monotonic, sleep=clock.sleep))

    def busy(fd, operation):
        raise BlockingIOError("another hook holds the session")

    monkeypatch.setattr(client.session_state.fcntl, "flock", busy)
    with pytest.raises(TimeoutError, match="50 ms"):
        client.run("claude-code", "UserPromptSubmit", json.dumps(human()).encode(), time.monotonic())
    assert clock.now == pytest.approx(0.05)
    assert rows(home)[0]["status"] == "error" and loads(home) == 0


def test_switch_during_inference_is_preserved_and_row_keeps_submission_snapshot(configured, home, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    result, errors = [], []

    def profile(port, prompt, deadline):
        entered.set()
        assert release.wait(2)
        return "ok", served_reply()

    def prompt():
        try:
            result.append(client.run("claude-code", "UserPromptSubmit", json.dumps(human()).encode(), time.monotonic()))
        except BaseException as exc:
            errors.append(exc)

    monkeypatch.setattr(client.service_client, "profile", profile)
    worker = threading.Thread(target=prompt)
    worker.start()
    try:
        assert entered.wait(2)
        client.run("claude-code", "PostModelSwitch", json.dumps(dict(PAYLOADS["post_model_switch"],
                   to_model="claude-opus-5-5")).encode(), time.monotonic())
        switched = json.loads((home / "sessions" / "sess-1.json").read_text())
    finally:
        release.set()
        worker.join(2)
    assert not errors and not worker.is_alive() and result[0]
    state = json.loads((home / "sessions" / "sess-1.json").read_text())
    assert (state["model"], state["model_source"], state["switched_at"], state["first_prompt_after_switch_at"]) == (
        "claude-opus-5-5", "post_model_switch", switched["switched_at"], None)
    assert state["prompt_count"] == 1 and state["plan_shown"] is True
    assert rows(home)[0]["session"] == {"model": None, "effort": None, "model_source": None}
    assert stat.S_IMODE((home / "sessions" / "sess-1.lock").stat().st_mode) == 0o600


def test_overlapping_prompts_claim_plan_only_once_and_keep_both_counts(configured, home, monkeypatch):
    entered, second_entered, release = threading.Event(), threading.Event(), threading.Event()
    outputs, errors = [], []

    def profile(port, prompt, deadline):
        (entered if prompt.startswith("first") else second_entered).set()
        assert release.wait(2)
        return "ok", served_reply()

    def prompt(text):
        try:
            outputs.append(client.run("claude-code", "UserPromptSubmit", json.dumps(human(text)).encode(), time.monotonic()))
        except BaseException as exc:
            errors.append(exc)

    monkeypatch.setattr(client.service_client, "profile", profile)
    workers = [threading.Thread(target=prompt, args=(label + "x" * 300,)) for label in ("first", "second")]
    workers[0].start()
    try:
        assert entered.wait(2)
        workers[1].start()
        assert second_entered.wait(2)
    finally:
        release.set()
        for worker in workers:
            if worker.ident is not None:
                worker.join(2)
    assert not errors and not any(worker.is_alive() for worker in workers)
    lines = [line for out in outputs if out for line in json.loads(out)["systemMessage"].splitlines()]
    assert sum("Plan mode" in line for line in lines) == 1
    assert sum("effort fits" in line for line in lines) == 1
    state = json.loads((home / "sessions" / "sess-1.json").read_text())
    assert state["prompt_count"] == 2 and state["plan_shown"] is True
    assert len(rows(home)) == 2
