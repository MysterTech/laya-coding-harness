"""The hook client (spec §4.1–§4.3, §4.6–§4.10). Standard library only: never imports laya_mlx.

`run` returns the text for stdout (one JSON object) or None. It may raise; the entry point in
`__main__` turns every failure into "print nothing, exit 0".
"""

import json
import time

from . import (__version__, adapter_claude_code, config, decision_log, resources, service_client,
               session_state, source, spawn, transcript)

PROFILE_DEADLINE = 1.5
WAIT_BUDGET = 4.0
HEALTH_TIMEOUT = 0.5


def run(harness, event, raw: bytes, started: float):
    if harness == "codex":
        from . import codex_client

        return codex_client.run(event, raw, started)
    if harness != "claude-code":
        decision_log.problem(f"unknown harness {harness!r}")
        return None
    cfg = config.load()
    if cfg["mode"] == "off":
        return None
    payload, logged = None, []
    try:
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("hook input is not a JSON object")
        if event == "SessionStart":
            _session_start(cfg, payload)
            return None
        if event == "PostModelSwitch":
            _model_switch(payload)
            return None
        if event == "UserPromptSubmit":
            return _prompt(cfg, payload, started, logged)
    except BaseException:
        if event == "UserPromptSubmit" and not logged:
            _error_row(cfg, payload if isinstance(payload, dict) else {}, started)
        raise  # `__main__` writes the client.log line and still exits 0
    decision_log.problem(f"unknown event {event!r}")
    return None


def _error_row(cfg: dict, payload: dict, started: float) -> None:
    """Spec §5, §4.10: a client error still leaves one row, with status `error`."""
    try:
        row = _base_row(cfg, payload, None, time.time())
        row.update(status="error", latency_ms=round((time.monotonic() - started) * 1000, 1))
        decision_log.append(row)
    except BaseException:  # noqa: BLE001 — the log itself may be what failed
        pass


def _ensure_service(cfg: dict, port: int) -> bool:
    """Start the service if nothing is bound to the port. Return True if this call spawned it."""
    outcome, _ = service_client.health(port, timeout=0.3)
    if outcome == "refused":
        spawn.spawn_service(cfg)
        return True
    if outcome in ("foreign", "timeout"):
        decision_log.problem(f"port {port}: {outcome} on the health check; no service started")
    return False


def _wait_until_ready(port: int, spawned: bool) -> None:
    """Spec §4.3: poll for at most 4 s, and only while the service is starting."""
    deadline = time.monotonic() + WAIT_BUDGET
    first = True
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        outcome, body = service_client.health(port, timeout=min(HEALTH_TIMEOUT, remaining))
        if outcome == "ok":
            if body.get("state") != "loading":
                return
        elif outcome == "refused":
            if not spawned:
                return
        elif outcome == "timeout":
            if first:
                return
        else:
            return
        first = False
        time.sleep(min(0.1, max(0.0, deadline - time.monotonic())))


def _session_start(cfg: dict, payload: dict) -> None:
    sid = payload.get("session_id") or ""
    with session_state.transaction(sid) as state:
        session_state.on_session_start(state, payload.get("source"))
    port = config.port(cfg)
    spawned = _ensure_service(cfg, port)
    if payload.get("source") == "startup":
        _wait_until_ready(port, spawned)


def _model_switch(payload: dict) -> None:
    sid = payload.get("session_id") or ""
    with session_state.transaction(sid) as state:
        session_state.on_model_switch(state, payload.get("to_model"), time.time())


def _base_row(cfg: dict, payload: dict, src: str, now: float) -> dict:
    questions = resources.questions()
    return {
        "schema_version": decision_log.SCHEMA_VERSION,
        "ts": decision_log.iso(now),
        "session_id": payload.get("session_id"),
        "prompt_id": payload.get("prompt_id"),
        "transcript_path": payload.get("transcript_path"),
        "cwd": payload.get("cwd"),
        "event": "UserPromptSubmit",
        "source": src,
        "mode": cfg["mode"],
        "status": None,
        "shown_text": None,
        "suppress_reason": None,
        "suggestion": None,
        "prompt": payload.get("prompt") or "",
        "truncated": None,
        "input_chars_dropped": None,
        "answers": None,
        "usage": None,
        "mismatches": None,
        "checkpoint": None,
        "question_set": {"id": questions["id"], "sha256": resources.questions_sha256()},
        "versions": {"laya_harness": __version__, "laya_mlx": None,
                     "adapter_rules": adapter_claude_code.RULES_VERSION,
                     "catalog": resources.catalog_sha256()},
        "session": None,
        "permission_mode": payload.get("permission_mode"),
        "latency_ms": None,
        "cold": False,
    }


def _finish(row: dict, state: dict, started: float, out, logged: list):
    row["session"] = {"model": state["model"], "effort": state["effort"], "model_source": state["model_source"]}
    row["latency_ms"] = round((time.monotonic() - started) * 1000, 1)
    decision_log.append(row)
    logged.append(True)
    return out


def _prompt(cfg: dict, payload: dict, started: float, logged: list):
    now = time.time()
    prompt = payload.get("prompt") or ""
    src = source.classify(payload)
    sid = payload.get("session_id") or ""
    row = _base_row(cfg, payload, src, now)
    if src != "human":
        state = session_state.load(sid)
        row.update(status="skipped", suppress_reason={"model": "not_human", "plan": "not_human"})
        return _finish(row, state, started, None, logged)

    with session_state.transaction(sid) as state:
        first_human = state["prompt_count"] == 0
        reply = transcript.last_assistant(payload.get("transcript_path")) if state["prompt_count"] >= 1 else None
        session_state.on_human_prompt(state, now, reply)

    port = config.port(cfg)
    outcome, body = service_client.profile(port, prompt, PROFILE_DEADLINE)
    if outcome == "refused":
        spawn.spawn_service(cfg)
        status = "started_service"
    elif outcome == "ok":
        status = "decided"
    elif outcome in ("loading", "not_ready", "timeout"):
        status = outcome
        if outcome == "timeout":
            decision_log.problem(f"port {port}: no complete reply within {PROFILE_DEADLINE} s")
    else:
        status = "error"
        decision_log.problem(f"unexpected reply from the service on port {port}")
    row["status"] = status
    row["cold"] = status in ("started_service", "loading")
    if status != "decided":
        return _finish(row, state, started, None, logged)

    questions = resources.questions()
    with session_state.transaction(sid) as latest:
        decision = adapter_claude_code.decide(
            body["answers"], first_human=first_human, plan_shown=latest["plan_shown"],
            permission_mode=payload.get("permission_mode"), prompt=prompt, display=questions["display"],
            catalog=resources.catalog(), fit=resources.fit(), session=state)
        reasons = dict(decision["suppress_reason"])
        if cfg["mode"] == "log-only":
            for key, line in decision["line_for"].items():
                if line:
                    reasons[key] = "log_only"
            shown = []
        else:
            shown = decision["lines"]

        row.update(shown_text="\n".join(shown) or None, suppress_reason=reasons,
                   suggestion=decision["suggestion"], mismatches=decision["mismatches"],
                   answers=body["answers"], usage=body["usage"], truncated=body["truncated"],
                   input_chars_dropped=body["input_chars_dropped"], checkpoint=body["checkpoint"])
        versions = body["versions"]
        row["versions"].update(laya_mlx=versions["laya_mlx"], service_laya_harness=versions["laya_harness"])
        served = body["question_set"]  # the row records what produced the answers (spec §4.10, §5)
        if served != row["question_set"]:
            decision_log.problem(f"the service runs question set {served} but the client has "
                                 f"{row['question_set']}: run laya-harness stop")
        row["question_set"] = served
        out = json.dumps({"systemMessage": "\n".join(shown)}, ensure_ascii=False) if shown else None
        out = _finish(row, state, started, out, logged)
        if shown:  # after the row: a failed write never marks a line as shown
            if decision["line_for"]["model"]:
                latest["model_line_shown"] = True
            if decision["line_for"]["plan"]:
                latest["plan_shown"] = True
    return out
