"""Calls from the hook client to the local service (spec §4.2, §4.3). Standard library only.

Outcomes: "ok", "refused" (nothing bound to the port), "loading", "not_ready", "timeout",
"foreign" (a listener that is not laya-harness) and "error".
"""

import http.client
import json
import math
import re
import threading
import time


def _call(port: int, method: str, path: str, body, timeout: float):
    """One request with a wall-clock limit. The socket timeout applies to each read, so a
    listener that trickles bytes could otherwise stretch it without end (spec §4.2)."""
    result = {}

    def work():
        try:
            result["value"] = _request(port, method, path, body, timeout)
        except BaseException as exc:  # noqa: BLE001 — handed back to the caller below
            result["error"] = exc

    worker = threading.Thread(target=work, daemon=True)  # abandoned on timeout; the hook exits soon
    worker.start()
    worker.join(timeout)
    if worker.is_alive():
        raise TimeoutError(f"no complete reply within {timeout} s")
    if "error" in result:
        raise result["error"]
    return result["value"]


def _request(port: int, method: str, path: str, body, timeout: float):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"} if body is not None else {}
        conn.request(method, path, body=data, headers=headers)
        resp = conn.getresponse()
        return resp.status, resp.read()
    finally:
        conn.close()


def _json(raw):
    try:
        value = json.loads(raw)
    except (ValueError, RecursionError):
        return None
    return value if isinstance(value, dict) else None


def health(port: int, timeout: float):
    try:
        status, raw = _call(port, "GET", "/v1/health", None, timeout)
    except ConnectionRefusedError:
        return "refused", None
    except TimeoutError:
        return "timeout", None
    except (OSError, http.client.HTTPException):
        return "error", None
    body = _json(raw)
    if status == 200 and body is not None and body.get("app") == "laya-harness":
        return "ok", body
    return "foreign", None


def _probability(value) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and 0 <= value <= 1 and math.isfinite(value))


def _valid_profile(body: dict) -> bool:
    """Validate application identity and the fields consumed by the adapter and log (§4.4)."""
    if body.get("app") != "laya-harness":
        return False
    answers, usage = body.get("answers"), body.get("usage")
    if not isinstance(answers, dict) or not isinstance(usage, dict):
        return False
    difficulty = answers.get("difficulty")
    if not isinstance(difficulty, dict):
        return False
    probabilities = difficulty.get("probabilities")
    if not isinstance(probabilities, dict) or not all(
        _probability(probabilities.get(key)) for key in ("quick", "routine", "multi_file", "architecture")
    ):
        return False
    for key in ("plan_first", "parallel"):
        answer = answers.get(key)
        if not isinstance(answer, dict) or not _probability(answer.get("noul")):
            return False
    checkpoint, questions, versions = body.get("checkpoint"), body.get("question_set"), body.get("versions")
    if not isinstance(checkpoint, dict) or not all(
        isinstance(checkpoint.get(key), str) and checkpoint[key] for key in ("repo", "revision")
    ):
        return False
    if not isinstance(questions, dict) or not isinstance(questions.get("id"), str) or not questions["id"]:
        return False
    digest = questions.get("sha256")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-fA-F]{64}", digest) is None:
        return False
    if (not isinstance(versions, dict) or not isinstance(versions.get("laya_harness"), str)
            or "laya_mlx" not in versions or not isinstance(versions["laya_mlx"], (str, type(None)))):
        return False
    dropped = body.get("input_chars_dropped")
    if not isinstance(dropped, int) or isinstance(dropped, bool) or dropped < 0:
        return False
    truncated, token_truncated = body.get("truncated"), usage.get("truncated")
    return (isinstance(truncated, bool) and isinstance(token_truncated, bool)
            and truncated == (token_truncated or dropped > 0))


def profile(port: int, prompt: str, deadline: float):
    started = time.monotonic()
    try:
        status, raw = _call(port, "POST", "/v1/profile", {"prompt": prompt}, deadline)
    except ConnectionRefusedError:
        return "refused", None
    except TimeoutError:
        return "timeout", None
    except (OSError, http.client.HTTPException):
        return "error", None
    if time.monotonic() - started > deadline:
        return "timeout", None
    body = _json(raw)
    if status == 200 and body is not None and _valid_profile(body):
        return "ok", body
    if (status == 503 and body is not None and body.get("app") == "laya-harness"
            and body.get("state") in ("loading", "not_ready") and "reason" in body
            and isinstance(body["reason"], (str, type(None)))):
        return body["state"], body
    return "error", body
