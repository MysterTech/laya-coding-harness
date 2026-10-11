"""The local laya service (spec §4.4). Run as `python -I -m laya_harness.service`.

Startup order: check `idle_seconds`, then bind 127.0.0.1:<port> using the standard library only
(the bind is the single-instance lock), serve /v1/health from a thread, then load the predictor.
A failed load leaves the service bound and `not_ready` until its idle timeout. It never writes
to stdout.
"""

import errno
import json
import math
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import __version__, config, paths, resources


class _State:
    def __init__(self, cfg: dict, port: int):
        self.cfg = cfg
        self.port = port
        self.lock = threading.Lock()  # guards the state and counters below
        self.mlx = threading.Lock()  # all inference runs under this lock
        self.state = "loading"
        self.reason = None
        self.inflight = 0
        self.last_end = time.monotonic()
        self.predictor = None
        ck = resources.checkpoint()
        self.checkpoint = {"repo": ck["repo"], "revision": ck["revision"], "model_mode": cfg["model_mode"]}
        question_snapshot, question_hash = resources.questions_snapshot()
        self.questions = question_snapshot["questions"]
        self.question_set = {"id": question_snapshot["id"], "sha256": question_hash}

    def health(self) -> dict:
        return {"app": "laya-harness", "version": __version__, "pid": os.getpid(), "state": self.state,
                "reason": self.reason, "checkpoint": self.checkpoint, "question_set": self.question_set}

    def begin(self) -> None:
        with self.lock:
            self.inflight += 1

    def end(self) -> None:
        with self.lock:
            self.inflight -= 1
            self.last_end = time.monotonic()


class _Server(ThreadingHTTPServer):
    daemon_threads = False  # server_close() then waits for every request already accepted

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionResetError)):
            return  # the client gave up (its 1.5 s deadline): routine, not a service problem
        super().handle_error(request, client_address)


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    timeout = 5  # a connection that sends nothing is dropped, so it cannot hold the service open

    def log_message(self, *args):  # keep service.log for real problems
        pass

    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _forbidden(self) -> bool:
        st = self.server.st
        allowed = {f"127.0.0.1:{st.port}", f"localhost:{st.port}"}
        if self.headers.get("Host") not in allowed or "Origin" in self.headers:
            self._send(403, {"error": "forbidden"})
            return True
        return False

    def do_GET(self):
        if self._forbidden():
            return
        if self.path == "/v1/health":
            st = self.server.st
            st.begin()
            try:
                self._send(200, st.health())
            finally:
                st.end()
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self._forbidden():
            return
        if self.path != "/v1/profile":
            self._send(404, {"error": "not found"})
            return
        if self.headers.get_content_type() != "application/json":
            self._send(415, {"error": "application/json required"})
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            prompt = body["prompt"]
            if not isinstance(prompt, str):
                raise ValueError("prompt must be a string")
        except (ValueError, KeyError, TypeError):
            self._send(400, {"error": "expected {\"prompt\": str}"})
            return
        st = self.server.st
        st.begin()
        try:
            if st.state != "ready":
                self._send(503, {"app": "laya-harness", "state": st.state, "reason": st.reason})
                return
            try:
                with st.mlx:
                    result = st.predictor.predict(prompt)
            except Exception as exc:  # noqa: BLE001 — a predict failure is answered, never dropped
                print(f"predict failed: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
                self._send(500, {"error": type(exc).__name__})
                return
            self._send(200, {"app": "laya-harness", "answers": result["answers"], "usage": result["usage"],
                             "input_chars_dropped": result["input_chars_dropped"],
                             "truncated": result["usage"]["truncated"] or result["input_chars_dropped"] > 0,
                             "checkpoint": st.checkpoint, "question_set": st.question_set,
                             "versions": {"laya_harness": __version__,
                                          "laya_mlx": st.predictor.laya_mlx_version}})
        finally:
            st.end()


def _watch_idle(st: _State, server, stopped: threading.Event, idle_seconds: float) -> None:
    while not stopped.is_set():
        time.sleep(0.2)
        with st.lock:  # never idle while loading: a hung load keeps answering `loading`
            idle = (st.state != "loading" and st.inflight == 0
                    and time.monotonic() - st.last_end >= idle_seconds)
        if idle:
            server.socket.close()  # a later connect is refused, so the client starts a fresh service
            server.shutdown()
            stopped.set()


def _load(st: _State) -> None:
    from . import predictor

    try:
        p = predictor.make(st.cfg, questions=st.questions)
        p.load()
        with st.lock:  # the idle clock starts again when loading ends
            st.predictor = p
            st.state = "ready"
            st.last_end = time.monotonic()
    except BaseException as exc:  # noqa: BLE001 — any load failure means not_ready
        with st.lock:
            st.reason = f"{type(exc).__name__}: {exc}"
            st.state = "not_ready"
            st.last_end = time.monotonic()
        print(f"load failed: {st.reason}", file=sys.stderr, flush=True)


def _idle_seconds(cfg: dict) -> float:
    """`idle_seconds` as a finite positive number. Anything else is refused before the
    bind: a watcher that cannot count would keep the model resident for good."""
    value = cfg["idle_seconds"]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"idle_seconds must be a positive number, not {cfg['idle_seconds']!r}")
    return float(value)


def main() -> int:
    cfg = config.load()
    port = config.port(cfg)
    idle_seconds = _idle_seconds(cfg)
    try:
        server = _Server(("127.0.0.1", port), _Handler)
    except OSError as exc:
        if exc.errno == errno.EADDRINUSE:
            return 0
        raise
    paths.ensure_home()
    st = _State(cfg, port)
    server.st = st
    stopped = threading.Event()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    threading.Thread(target=_watch_idle, args=(st, server, stopped, idle_seconds), daemon=True).start()
    _load(st)
    stopped.wait()
    server.server_close()  # joins the requests already accepted
    return 0


if __name__ == "__main__":
    sys.exit(main())
