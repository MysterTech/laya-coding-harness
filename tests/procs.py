"""Helpers for process-level tests: start the real service module and talk to it."""

import http.client
import json
import os
import subprocess
import sys
import time


def env_for(home) -> dict:
    env = dict(os.environ)
    env["LAYA_HARNESS_HOME"] = str(home)
    env["LAYA_HARNESS_TEST"] = "1"
    env["HF_HUB_OFFLINE"] = "1"
    return env


def start_service(home, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) -> subprocess.Popen:
    return subprocess.Popen([sys.executable, "-I", "-m", "laya_harness.service"], env=env_for(home),
                            stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr)


def request(port, method, path, body=None, headers=None, timeout=2.0):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    payload = None if body is None else json.dumps(body).encode()
    hdrs = {"Content-Type": "application/json"} if body is not None else {}
    hdrs.update(headers or {})
    conn.request(method, path, body=payload, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    try:
        return resp.status, json.loads(data)
    except ValueError:
        return resp.status, data


def wait_health(port, want=("ready",), timeout=10.0) -> dict:
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        try:
            status, body = request(port, "GET", "/v1/health", timeout=0.5)
            last = body
            if status == 200 and body.get("state") in want:
                return body
        except OSError:
            pass
        time.sleep(0.05)
    raise AssertionError(f"service never reached {want}; last health: {last}")


def stop(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
