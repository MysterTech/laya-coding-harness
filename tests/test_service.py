import http.client
import importlib.abc
import importlib.util
import hashlib
import json
import math
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from conftest import FAKE_ANSWERS, write_config
from laya_harness import config, predictor, resources
from laya_harness import service as service_module
from procs import env_for, request, start_service, stop, wait_health


@pytest.fixture
def service(configured, home):
    procs = []

    def launch(**changes):
        if changes:
            write_config(home, **changes)
        proc = start_service(home)
        procs.append(proc)
        return proc

    yield launch
    for proc in procs:
        stop(proc)


# --- endpoints and request checks ------------------------------------------------------

def test_health_and_profile_in_fake_mode(service, configured):
    service()
    health = wait_health(configured["port"])
    assert health["app"] == "laya-harness" and health["state"] == "ready"
    assert health["question_set"] == {"id": "profile_v0", "sha256": resources.questions_sha256()}
    status, body = request(configured["port"], "POST", "/v1/profile", {"prompt": "fix the typo"})
    assert status == 200
    assert body["answers"] == FAKE_ANSWERS
    assert body["checkpoint"]["revision"] == "047678560251f28113ee8f5df4be82102c7bf336"
    assert body["versions"]["laya_harness"] == "0.0.0"


def test_health_and_profile_carry_every_field(service, configured):
    proc = service()
    health = wait_health(configured["port"])
    ck = resources.checkpoint()
    assert health["pid"] == proc.pid  # `laya-harness stop` signals this pid
    assert health["version"] == "0.0.0" and health["reason"] is None
    assert health["checkpoint"] == {"repo": ck["repo"], "revision": ck["revision"], "model_mode": "fake"}
    status, body = request(configured["port"], "POST", "/v1/profile", {"prompt": "x"})
    assert status == 200
    assert body["app"] == "laya-harness"
    assert body["input_chars_dropped"] == 0 and body["truncated"] is False
    assert body["usage"] == {"truncated": False, "state_tokens": 0, "state_tokens_dropped": 0}
    assert body["versions"] == {"laya_harness": "0.0.0", "laya_mlx": None}
    assert body["checkpoint"] == health["checkpoint"] and body["question_set"] == health["question_set"]


def test_profile_reports_the_predictors_laya_mlx_version():
    class Stub:
        laya_mlx_version = "9.9.9"

        def predict(self, prompt):
            return {"answers": {}, "usage": {"truncated": True}, "input_chars_dropped": 0}

    server = service_module._Server(("127.0.0.1", 0), service_module._Handler)
    st = service_module._State({"model_mode": "fake"}, server.server_address[1])
    st.predictor, st.state = Stub(), "ready"
    server.st = st
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        status, body = request(st.port, "POST", "/v1/profile", {"prompt": "x"})
        assert status == 200
        assert body["versions"]["laya_mlx"] == "9.9.9" and body["usage"] == {"truncated": True}
        assert body["input_chars_dropped"] == 0 and body["truncated"] is True
    finally:
        server.shutdown()
        server.server_close()


def test_rejects_foreign_host_origin_and_content_type(service, configured):
    service()
    port = configured["port"]
    wait_health(port)
    assert request(port, "GET", "/v1/health", headers={"Host": f"evil.example:{port}"})[0] == 403
    assert request(port, "GET", "/v1/health", headers={"Origin": "http://evil.example"})[0] == 403
    assert request(port, "GET", "/v1/health", headers={"Host": f"localhost:{port}"})[0] == 200
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    conn.request("POST", "/v1/profile", body=b'{"prompt": "x"}', headers={"Content-Type": "text/plain"})
    assert conn.getresponse().status == 415
    assert request(port, "GET", "/nope")[0] == 404
    assert request(port, "POST", "/v1/profile", {"wrong": 1})[0] == 400


def test_profile_post_rejects_foreign_host_and_any_origin(service, configured):
    service()
    port = configured["port"]
    wait_health(port)
    prompt = {"prompt": "x"}
    assert request(port, "POST", "/v1/profile", prompt, headers={"Host": f"evil.example:{port}"})[0] == 403
    for origin in ("http://evil.example", f"http://127.0.0.1:{port}"):  # any Origin, even a local one
        assert request(port, "POST", "/v1/profile", prompt, headers={"Origin": origin})[0] == 403


def test_bad_bodies_and_paths(service, configured):
    service()
    port = configured["port"]
    wait_health(port)
    assert request(port, "POST", "/v1/profile", {"prompt": 5})[0] == 400
    assert request(port, "POST", "/v1/profile", ["x"])[0] == 400
    assert request(port, "POST", "/v1/elsewhere", {"prompt": "x"})[0] == 404
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    conn.request("POST", "/v1/profile", body=b"{not json", headers={"Content-Type": "application/json"})
    assert conn.getresponse().status == 400
    conn.close()


@pytest.mark.parametrize("media_type, expected", [
    ("application/jsonp", 415),
    ("application/json-garbage", 415),
    ("application/json; charset=utf-8", 200),
    ("Application/JSON; charset=utf-8", 200),
])
def test_profile_requires_the_parsed_json_media_type(service, configured, media_type, expected):
    service()
    wait_health(configured["port"])
    assert request(configured["port"], "POST", "/v1/profile", {"prompt": "x"},
                   headers={"Content-Type": media_type})[0] == expected


def test_binds_loopback_only(monkeypatch, configured):
    import http.server

    seen = []

    def refuse(self):
        seen.append(self.server_address)
        raise OSError(98 if sys.platform.startswith("linux") else 48, "taken")

    monkeypatch.setattr(http.server.HTTPServer, "server_bind", refuse)
    assert service_module.main() == 0
    assert seen == [("127.0.0.1", configured["port"])]


# --- loading, single instance, imports ------------------------------------------------

def test_profile_answers_503_while_loading(service, configured):
    service(fake_load_seconds=3)
    health = wait_health(configured["port"], want=("loading",))
    assert health["state"] == "loading"
    assert request(configured["port"], "POST", "/v1/profile", {"prompt": "x"}) == (
        503, {"app": "laya-harness", "state": "loading", "reason": None})


def test_failed_load_is_not_ready_and_stays_bound(service, configured):
    proc = service(fake_load_error="corrupt model.safetensors")
    health = wait_health(configured["port"], want=("not_ready",))
    assert health["reason"] == "RuntimeError: corrupt model.safetensors"
    time.sleep(1.0)
    assert proc.poll() is None
    assert request(configured["port"], "POST", "/v1/profile", {"prompt": "x"})[0] == 503


def test_failed_load_loads_once_then_idles_out(service, configured, home):
    proc = service(fake_load_error="corrupt model.safetensors", idle_seconds=2)
    port = configured["port"]
    pid = wait_health(port, want=("not_ready",))["pid"]
    for _ in range(3):  # spec §6: several prompts in a row, at most one load
        assert request(port, "POST", "/v1/profile", {"prompt": "x"}) == (
            503, {"app": "laya-harness", "state": "not_ready", "reason": "RuntimeError: corrupt model.safetensors"})
    assert wait_health(port, want=("not_ready",))["pid"] == pid
    proc.wait(timeout=2 + 3)  # §4.4 step 4: stays bound only until its idle timeout
    assert proc.returncode == 0
    # counted over the service's whole life, so a slow retry loop is caught too
    assert (home / "fake_loads.txt").read_text().split() == [str(pid)]


def test_system_exit_during_loading_becomes_not_ready(monkeypatch, capsys):
    class Exiting:
        def load(self):
            raise SystemExit(2)

    monkeypatch.setattr(predictor, "make", lambda *args, **kwargs: Exiting())
    st = service_module._State({"model_mode": "fake"}, 0)
    before = st.last_end
    service_module._load(st)
    assert st.state == "not_ready" and st.reason == "SystemExit: 2"
    assert st.last_end >= before and st.predictor is None
    assert capsys.readouterr().err == "load failed: SystemExit: 2\n"


def test_concurrent_starts_load_once(configured, home):
    write_config(home, fake_load_seconds=3)
    procs = [start_service(home) for _ in range(4)]
    try:
        time.sleep(1.0)
        exited = [p for p in procs if p.poll() is not None]
        assert len(exited) == 3 and all(p.returncode == 0 for p in exited)
        wait_health(configured["port"])
        assert len((home / "fake_loads.txt").read_text().split()) == 1
    finally:
        for p in procs:
            stop(p)


IMPORT_PROBE = (  # runs the service as `-m` does (the __main__ guard included), then lists new imports
    "import runpy, sys\n"
    "before = set(sys.modules)\n"
    "try:\n"
    "    runpy.run_module('laya_harness.service', run_name='__main__')\n"
    "    rc = 0\n"
    "except SystemExit as exc:\n"
    "    rc = exc.code\n"
    "new = {m.partition('.')[0] for m in set(sys.modules) - before}\n"
    "sys.stderr.write(' '.join(sorted(new - set(sys.stdlib_module_names) - {'laya_harness'})) or 'stdlib only')\n"
    "sys.exit(rc)\n")


def test_service_imports_only_stdlib_when_port_taken_or_fake(configured, home):
    """§4.4 step 1 (standard library only before the bind) and fake mode (never laya_mlx or mlx)."""
    argv = [sys.executable, "-I", "-c", IMPORT_PROBE]
    with socket.socket() as holder:  # port taken: exit 0 at the bind
        holder.bind(("127.0.0.1", configured["port"]))
        holder.listen()
        taken = subprocess.run(argv, env=env_for(home), stdin=subprocess.DEVNULL, capture_output=True, timeout=10)
    assert (taken.returncode, taken.stdout, taken.stderr) == (0, b"", b"stdlib only")
    assert not (home / "fake_loads.txt").exists()
    write_config(home, idle_seconds=1)  # port free: a fake load, then an idle exit
    served = subprocess.run(argv, env=env_for(home), stdin=subprocess.DEVNULL, capture_output=True, timeout=15)
    assert (served.returncode, served.stdout, served.stderr) == (0, b"", b"stdlib only")
    assert len((home / "fake_loads.txt").read_text().split()) == 1


# --- inference -------------------------------------------------------------------------

def test_inference_is_serialised_and_health_answers_during_it(service, configured):
    service(fake_predict_seconds=1.0)
    port = configured["port"]
    wait_health(port)
    statuses = []

    def call():
        statuses.append(request(port, "POST", "/v1/profile", {"prompt": "x"}, timeout=5)[0])

    threads = [threading.Thread(target=call, daemon=True) for _ in range(2)]
    started = time.monotonic()
    for t in threads:
        t.start()
    time.sleep(0.3)
    status, body = request(port, "GET", "/v1/health", timeout=0.5)  # answered while inference runs
    assert (status, body["state"]) == (200, "ready")
    for t in threads:
        t.join(timeout=5)
    assert statuses == [200, 200]
    assert time.monotonic() - started >= 1.9  # one MLX lock: the two predictions ran one after the other


@pytest.mark.parametrize("changes, state, status", [
    ({}, "ready", 200),
    ({"fake_load_error": "corrupt model.safetensors"}, "not_ready", 503),
    ({"fake_predict_error": "metal::malloc failed"}, "ready", 500),
])
def test_service_never_writes_to_stdout(configured, home, changes, state, status):
    write_config(home, idle_seconds=1, **changes)
    proc = start_service(home, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        wait_health(configured["port"], want=(state,))
        assert request(configured["port"], "POST", "/v1/profile", {"prompt": "x"})[0] == status
        out, err = proc.communicate(timeout=10)  # idle exit, so the interpreter flushes its buffers
    finally:
        stop(proc)
    assert proc.returncode == 0 and out == b""
    if state == "not_ready":
        assert b"load failed: RuntimeError: corrupt model.safetensors" in err
    if status == 500:  # §4.4: one line in service.log
        assert err.count(b"predict failed:") == 1 and b"RuntimeError: metal::malloc failed" in err


def test_a_client_that_gives_up_is_not_logged(capsys):
    server = service_module._Server(("127.0.0.1", 0), service_module._Handler)
    try:
        for exc in (BrokenPipeError(32, "Broken pipe"), ConnectionResetError(54, "Connection reset")):
            try:
                raise exc
            except OSError:
                server.handle_error(None, ("127.0.0.1", 1))
        assert capsys.readouterr().err == ""
        try:
            raise ValueError("a real problem")
        except ValueError:
            server.handle_error(None, ("127.0.0.1", 1))
        assert "ValueError: a real problem" in capsys.readouterr().err  # still logged with a traceback
    finally:
        server.server_close()


def test_predict_failure_is_a_500_and_the_service_stays_ready(service, configured):
    proc = service(fake_predict_error="metal::malloc failed")
    wait_health(configured["port"])
    assert request(configured["port"], "POST", "/v1/profile", {"prompt": "x"}) == (500, {"error": "RuntimeError"})
    assert proc.poll() is None
    assert wait_health(configured["port"])["state"] == "ready"


# --- idle exit -------------------------------------------------------------------------

def test_idle_exit_never_mid_request(service, configured):
    proc = service(idle_seconds=1, fake_predict_seconds=2.5)
    wait_health(configured["port"])
    result = {}

    def call():
        result["status"] = request(configured["port"], "POST", "/v1/profile", {"prompt": "x"}, timeout=5)[0]

    t = threading.Thread(target=call)
    t.start()
    time.sleep(1.5)
    assert proc.poll() is None  # idle time passed, but a request is in flight
    t.join()
    assert result["status"] == 200
    proc.wait(timeout=5)
    assert proc.returncode == 0


def test_idle_clock_waits_for_the_load(service, configured):
    proc = service(idle_seconds=1, fake_load_seconds=3)
    port = configured["port"]
    wait_health(port, want=("loading",))
    time.sleep(1.5)  # idle_seconds have passed, but the model is still loading
    assert request(port, "GET", "/v1/health", timeout=0.5)[1]["state"] in ("loading", "ready")
    wait_health(port)
    time.sleep(0.5)  # the idle clock restarted when the load ended
    assert request(port, "GET", "/v1/health", timeout=0.5)[1]["state"] == "ready"
    proc.wait(timeout=5)
    assert proc.returncode == 0  # and the service still exits once idle


@pytest.mark.parametrize("changes", [{}, {"fake_load_error": "corrupt model.safetensors"}])
def test_idle_clock_restarts_when_the_load_ends(service, configured, changes):
    """§4.4: idle time counts from the end of loading. No request is made while the 2.5 s load
    runs, so only the reset at the end of `_load` keeps the service up past that point."""
    proc = service(idle_seconds=2, fake_load_seconds=2.5, **changes)
    wait_health(configured["port"], want=("loading",))  # the only request, near the load's start
    time.sleep(2.5 + 1.0)  # the load has ended; an idle clock started at the poll would have fired
    assert proc.poll() is None
    proc.wait(timeout=5)
    assert proc.returncode == 0


def test_idle_timer_restarts_after_each_request(service, configured):
    proc = service(idle_seconds=1.5)
    port = configured["port"]
    wait_health(port)
    for _ in range(4):  # 2.8 s in all: well past one idle period counted from start-up
        time.sleep(0.7)
        assert request(port, "POST", "/v1/profile", {"prompt": "x"})[0] == 200
    assert proc.poll() is None
    proc.wait(timeout=1.5 + 2)
    assert proc.returncode == 0


def test_health_requests_extend_the_idle_deadline(service, configured):
    proc = service(idle_seconds=2)
    port = configured["port"]
    wait_health(port)
    for _ in range(4):  # 3.2 s of health checks, more than one idle period from start-up
        time.sleep(0.8)
        assert request(port, "GET", "/v1/health")[0] == 200
    assert proc.poll() is None
    proc.wait(timeout=5)
    assert proc.returncode == 0


def test_slow_health_response_stays_inflight_and_restarts_idle_at_its_end(monkeypatch):
    server = service_module._Server(("127.0.0.1", 0), service_module._Handler)
    st = service_module._State({"model_mode": "fake"}, server.server_address[1])
    st.state = "ready"
    server.st = st
    entered, release, stopped = threading.Event(), threading.Event(), threading.Event()
    original = service_module._Handler._send

    def slow_send(self, code, body):
        entered.set()
        assert release.wait(timeout=3)
        original(self, code, body)

    monkeypatch.setattr(service_module._Handler, "_send", slow_send)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    replies = []
    caller = threading.Thread(target=lambda: replies.append(request(st.port, "GET", "/v1/health")))
    watcher = threading.Thread(target=service_module._watch_idle,
                               args=(st, server, stopped, 0.1), daemon=True)
    try:
        caller.start()
        assert entered.wait(timeout=2)
        request_started = st.last_end
        watcher.start()
        time.sleep(0.35)  # beyond the idle period while the response is still blocked
        assert st.inflight == 1 and server.socket.fileno() != -1
        assert st.last_end == request_started
        released_at = time.monotonic()
        release.set()
        caller.join(timeout=2)
        assert not caller.is_alive() and replies[0][0] == 200
        assert st.inflight == 0 and st.last_end >= released_at
    finally:
        stopped.set()
        release.set()
        caller.join(timeout=3)
        if watcher.ident is not None:
            watcher.join(timeout=3)
        server.shutdown()
        server.server_close()


@pytest.mark.parametrize("method, path, body, headers, expected", [
    ("POST", "/v1/profile", {"prompt": 5}, {}, 400),
    ("GET", "/v1/health", None, {"Origin": "http://evil.example"}, 403),
    ("GET", "/missing", None, {}, 404),
    ("POST", "/v1/profile", {"prompt": "x"}, {"Content-Type": "text/plain"}, 415),
])
def test_rejected_requests_do_not_extend_idle_residence(service, configured, method, path, body, headers, expected):
    proc = service(idle_seconds=0.5)
    port = configured["port"]
    wait_health(port)
    deadline = time.monotonic() + 1.5
    rejected = 0
    while time.monotonic() < deadline:
        try:
            assert request(port, method, path, body, headers)[0] == expected
            rejected += 1
        except ConnectionRefusedError:
            break
        time.sleep(0.1)
    proc.wait(timeout=max(0.001, deadline + 0.3 - time.monotonic()))
    assert rejected >= 1 and proc.returncode == 0


def test_idle_exit_refuses_connections_before_it_stops(configured, home):
    """§4.3/§4.4: once the idle exit starts, a connect is refused (the client respawns), never
    accepted into the backlog and then reset when the listener closes."""
    cfg = config.load()
    port = config.port(cfg)
    server = service_module._Server(("127.0.0.1", port), service_module._Handler)
    st = service_module._State(cfg, port)
    st.state = "ready"
    seen = []

    def shutdown():  # stands in for server.shutdown(): probe the port at the moment the exit starts
        try:
            socket.create_connection(("127.0.0.1", port), timeout=1).close()
            seen.append("accepted")
        except ConnectionRefusedError:
            seen.append("refused")

    server.shutdown = shutdown
    try:
        watcher = threading.Thread(target=service_module._watch_idle,
                                   args=(st, server, threading.Event(), 0.1), daemon=True)
        watcher.start()
        watcher.join(timeout=5)
    finally:
        server.server_close()
    assert seen == ["refused"]


def test_idle_exit_finishes_a_request_already_accepted(service, configured):
    proc = service(idle_seconds=1)
    port = configured["port"]
    wait_health(port)
    body = b'{"prompt": "x"}'
    with socket.create_connection(("127.0.0.1", port), timeout=5) as s:
        s.sendall(f"POST /v1/profile HTTP/1.0\r\nHost: 127.0.0.1:{port}\r\n"
                  f"Content-Type: application/json\r\nContent-Length: {len(body)}\r\n\r\n".encode())
        time.sleep(2.0)  # the idle exit starts while this request is still being read
        assert proc.poll() is None
        s.sendall(body)
        assert s.recv(65536).startswith(b"HTTP/1.0 200")
    proc.wait(timeout=5)
    assert proc.returncode == 0


def test_idle_exit_is_not_held_open_by_a_silent_client(service, configured):
    proc = service(idle_seconds=1)
    wait_health(configured["port"])
    with socket.create_connection(("127.0.0.1", configured["port"]), timeout=10):
        proc.wait(timeout=9)  # idle 1 s + the 5 s handler timeout + margin
    assert proc.returncode == 0


@pytest.mark.parametrize("value", ["15m", None, [], math.nan, 0, -5])
def test_bad_idle_seconds_exits_before_loading(configured, home, value):
    write_config(home, idle_seconds=value)
    proc = start_service(home, stderr=subprocess.PIPE)
    try:
        _, err = proc.communicate(timeout=5)
    finally:
        stop(proc)
    assert proc.returncode == 1 and b"idle_seconds must be a positive number" in err
    assert not (home / "fake_loads.txt").exists()


def test_bad_idle_seconds_is_refused_before_the_bind(configured, home):
    """§4.4 step 1: with the port taken, a service that checked after binding would exit 0."""
    write_config(home, idle_seconds=0)
    with socket.socket() as holder:
        holder.bind(("127.0.0.1", configured["port"]))
        holder.listen()
        proc = start_service(home, stderr=subprocess.PIPE)
        try:
            _, err = proc.communicate(timeout=5)
        finally:
            stop(proc)
    assert proc.returncode == 1 and b"idle_seconds must be a positive number" in err


@pytest.mark.parametrize("value", [True, False, "10", math.inf, -math.inf])
def test_non_numeric_or_non_finite_idle_is_refused_before_binding(configured, home, value):
    write_config(home, idle_seconds=value)
    with socket.socket() as holder:
        holder.bind(("127.0.0.1", configured["port"]))
        holder.listen()
        proc = start_service(home, stderr=subprocess.PIPE)
        try:
            _, err = proc.communicate(timeout=5)
        finally:
            stop(proc)
    assert proc.returncode == 1 and b"idle_seconds must be a positive number" in err
    assert not (home / "fake_loads.txt").exists()


# --- the real predictor, without weights -------------------------------------------------

def test_real_predictor_rejects_missing_dir_without_download(monkeypatch, tmp_path):
    import laya_mlx.agent as agent_module

    def no_downloads(*args, **kwargs):
        raise AssertionError("snapshot_download must never be called")

    monkeypatch.setattr(agent_module, "snapshot_download", no_downloads)
    with pytest.raises(FileNotFoundError, match="missing model.safetensors"):
        predictor.RealPredictor({"model_dir": str(tmp_path / "absent")}).load()
    with pytest.raises(FileNotFoundError, match="absolute"):
        predictor.RealPredictor({"model_dir": "relative/dir"}).load()


def test_real_predictor_refuses_a_revision_that_is_not_pinned(tmp_path):
    pinned = resources.checkpoint()["revision"]
    with pytest.raises(ValueError, match=f"names revision 000000000000, not the pinned {pinned[:12]}: "
                                         "run laya-harness setup"):
        predictor.RealPredictor({"model_dir": str(tmp_path), "revision": "0" * 40}).load()
    with pytest.raises(FileNotFoundError, match="missing model.safetensors"):  # the pinned one goes on
        predictor.RealPredictor({"model_dir": str(tmp_path / "absent"), "revision": pinned}).load()


def test_real_predictor_loads_offline_with_check6_settings(monkeypatch, tmp_path, capsys):
    """§4.4 step 3 without weights: a stand-in laya_mlx records the offline flag at import and at
    load, the load arguments, max_len at every warm-up, the temperatures and the version."""
    ck = resources.checkpoint()
    model_dir = tmp_path / "model"
    for name in ck["required"]:
        (model_dir / name).parent.mkdir(parents=True, exist_ok=True)
        (model_dir / name).write_text("{}")
    seen = {}

    class Agent:
        temperature = (1.25, 1.5)
        temperature_by_options = {"4": 1.25}

        def __init__(self):
            self.cfg = {"max_len": 8192}
            self.predicted = []

        def predict(self, prompt, questions):
            self.predicted.append((prompt, self.cfg["max_len"], questions))
            return {"answers": {}, "usage": {"truncated": False}}

    def load(path, **kwargs):
        seen.update(path=path, kwargs=kwargs, offline_at_load=os.environ.get("HF_HUB_OFFLINE"), agent=Agent())
        return seen["agent"]

    class FakeLayaMlx(importlib.abc.MetaPathFinder, importlib.abc.Loader):
        def find_spec(self, name, path, target=None):
            return importlib.util.spec_from_loader(name, self) if name == "laya_mlx" else None

        def create_module(self, spec):
            return None

        def exec_module(self, module):
            seen["offline_at_import"] = os.environ.get("HF_HUB_OFFLINE")
            module.__version__ = "9.9.9"
            module.load = load

    monkeypatch.setitem(sys.modules, "laya_mlx", None)
    monkeypatch.delitem(sys.modules, "laya_mlx")  # teardown puts back the real module, if any
    monkeypatch.setattr(sys, "meta_path", [FakeLayaMlx(), *sys.meta_path])
    monkeypatch.delenv("HF_HUB_OFFLINE", raising=False)

    assert isinstance(predictor.make({"model_mode": "real", "model_dir": str(model_dir)}), predictor.RealPredictor)
    p = predictor.RealPredictor({"model_dir": str(model_dir), "revision": ck["revision"]})
    p.load()

    assert seen["offline_at_import"] == "1" and seen["offline_at_load"] == "1"
    assert seen["path"] == str(model_dir)
    assert seen["kwargs"] == {"dtype": "float16", "batch_size": 1, "pad_to_multiple": 128}
    questions = resources.questions()["questions"]
    warmed = [(0 if pr == "warm-up" else len(pr.split()), max_len) for pr, max_len, _ in seen["agent"].predicted]
    assert warmed == [(w, 512) for w in ck["warmup_words"]]
    assert all(q == questions for *_, q in seen["agent"].predicted)
    assert p.laya_mlx_version == "9.9.9"
    assert p.predict("fix the typo") == {"answers": {}, "usage": {"truncated": False}, "input_chars_dropped": 0}
    assert seen["agent"].predicted[-1] == ("fix the typo", 512, questions)
    out, err = capsys.readouterr()
    assert out == ""
    assert json.loads(err.strip().splitlines()[-1]) == {"temperature": [1.25, 1.5], "temperature_by_options": {"4": 1.25}}


def test_real_predictor_caps_the_prompt_before_tokenizing():
    seen = []

    class Agent:
        def predict(self, prompt, questions):
            seen.append(prompt)
            return {"answers": {}, "usage": {}}

    p = predictor.RealPredictor({"model_dir": "/unused"})
    p.agent = Agent()
    prompt = "head " + "x" * 5_000_000 + " tail"
    p.predict(prompt)
    assert predictor.PROMPT_CHAR_CAP == 65536
    assert seen == [prompt[:65536]] and seen[0].startswith("head ")  # the beginning is kept, as laya-mlx's own truncation does


@pytest.mark.parametrize("length", [65535, 65536, 65543])
@pytest.mark.parametrize("token_truncated", [False, True])
def test_character_cap_is_reported_without_changing_raw_usage(length, token_truncated):
    usage = {"truncated": token_truncated, "state_tokens": 258, "state_tokens_dropped": 0,
             "future_field": {"value": "retained"}}
    seen = []

    class Agent:
        def predict(self, prompt, questions):
            seen.append(prompt)
            return {"answers": {}, "usage": usage}

    p = predictor.RealPredictor({"model_dir": "/unused"})
    p.agent = Agent()
    result = p.predict("-" * length)
    assert result["input_chars_dropped"] == max(0, length - 65536)
    assert seen == ["-" * min(length, 65536)]
    assert result["usage"] is usage and usage == {
        "truncated": token_truncated, "state_tokens": 258, "state_tokens_dropped": 0,
        "future_field": {"value": "retained"}}


@pytest.mark.parametrize("characters_dropped, token_truncated", [(0, False), (0, True), (7, False), (7, True)])
def test_profile_aggregates_character_and_token_truncation(characters_dropped, token_truncated):
    usage = {"truncated": token_truncated, "state_tokens": 258, "state_tokens_dropped": 0}

    class Stub:
        laya_mlx_version = "9.9.9"

        def predict(self, prompt):
            return {"answers": FAKE_ANSWERS, "usage": usage, "input_chars_dropped": characters_dropped}

    server = service_module._Server(("127.0.0.1", 0), service_module._Handler)
    st = service_module._State({"model_mode": "fake"}, server.server_address[1])
    st.predictor, st.state = Stub(), "ready"
    server.st = st
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        status, body = request(st.port, "POST", "/v1/profile", {"prompt": "x"})
        assert status == 200 and body["app"] == "laya-harness"
        assert body["input_chars_dropped"] == characters_dropped
        assert body["truncated"] is (token_truncated or characters_dropped > 0)
        assert body["usage"] == usage
    finally:
        server.shutdown()
        server.server_close()


def test_question_snapshot_survives_an_edit_before_predictor_loading(monkeypatch, tmp_path):
    original = resources.QUESTIONS.read_bytes()
    question_file = tmp_path / "questions.json"
    question_file.write_bytes(original)
    monkeypatch.setattr(resources, "QUESTIONS", question_file)
    st = service_module._State({"model_mode": "real", "model_dir": "/unused"}, 0)
    changed = json.loads(original)
    changed["id"] = "edited"
    changed["questions"]["difficulty"]["instructions"] = "changed after state creation"
    question_file.write_text(json.dumps(changed))
    executed = []
    monkeypatch.setattr(predictor.RealPredictor, "load", lambda self: executed.append(self.questions))
    service_module._load(st)
    assert st.state == "ready"
    assert executed == [json.loads(original)["questions"]]
    assert st.question_set == {"id": json.loads(original)["id"], "sha256": hashlib.sha256(original).hexdigest()}


def test_service_reads_the_question_bytes_only_once(monkeypatch, tmp_path):
    import builtins

    original = resources.QUESTIONS.read_bytes()
    question_file = tmp_path / "questions.json"
    question_file.write_bytes(original)
    monkeypatch.setattr(resources, "QUESTIONS", question_file)
    opens = []
    path_open, builtin_open = Path.open, builtins.open

    def trace_path(self, *args, **kwargs):
        if self == question_file:
            opens.append(self)
        return path_open(self, *args, **kwargs)

    def trace_builtin(file, *args, **kwargs):
        if file == question_file:
            opens.append(file)
        return builtin_open(file, *args, **kwargs)

    monkeypatch.setattr(Path, "open", trace_path)
    monkeypatch.setattr(builtins, "open", trace_builtin)
    st = service_module._State({"model_mode": "real", "model_dir": "/unused"}, 0)
    monkeypatch.setattr(predictor.RealPredictor, "load", lambda self: None)
    service_module._load(st)
    assert st.state == "ready" and opens == [question_file]
    assert st.question_set["sha256"] == hashlib.sha256(original).hexdigest()
