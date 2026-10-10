# laya-harness — Stage 1 Codex workbench plan

Status: independently reviewed workbench implementation, with literal verified code/test blocks below. Production copy follows this plan commit; controller repo gates and native acceptance follow promotion. Scope approved by the user; no final implementation commit while acceptance remains pending.

Contract: `docs/superpowers/specs/2026-10-09-laya-harness-codex-design.md` C1–C7. Native preflight: `docs/qa/codex-preflight.md`. Mockup: `docs/mockups/codex-stage1-hook-stats.svg`. Apply the repo gate profile and temporary Codex model-routing exception.

## Global constraints

Docs and mockup first, independently reviewed and committed. Use `.workbench/stage1-verify/`, with an isolated `.venv` whose import path selects that copy even under `-I`. Preserve `.workbench/plan-verify/` and Stage 0 plan/snapshots. Each task starts with genuinely failing behavioral tests, then GREEN. All tests use temporary state, temporary CODEX_HOME and free ports; no model/download/native UI calls by subagents. Use only `.venv/bin/python`. No git mutation by subagents. Exact production hook installation is a later reviewed replacement; no real config changes during development.

## Task 1 — Codex requirements and adapter

Implement and verify C3's bounded config-default reader, C4's Codex catalog/fit/resources/copy and deterministic adapter, and C1's native command builder. Own only new Codex modules/data and focused tests. Existing adapter and data stay unchanged. RED must demonstrate behavioral failure against stubs, not an import/fixture error. Independently review against the spec and mockup.

## Task 2 — Native client and deadline

Implement and verify C1–C3/C5's Codex hook client and harness-aware status log reader, existing client dispatch and Codex-only entry-point watchdog. Reuse shared service/state/log primitives while preserving Claude paths. Own client integration, commands.py catalog selection, new Codex client module and focused unit/subprocess tests. Include real subprocess execution of the exact native generated command, malformed/off/agent input, open stdin, service deadlines/outcomes, lifecycle sources and state concurrency. Independently review against the disk spec; run the complete existing regression suite in the workbench.

## Task 3 — Generate the production plan and promote

The controller generates literal blocks from GREEN files, recording executed RED/GREEN commands and outputs, and commits the completed plan before copying any file into the production tree. Compare every Stage 1 plan block byte for byte against workbench and production. Report intentional Stage 0 plan drift caused by integration; do not retrofit its older blocks. Record separate Stage 1 WIP snapshots. Run the full fake suite and controller-only offline pinned real-model gate. Independent final contract review covers both tasks.

## Task 4 — Native acceptance and cleanup

Prepare the exact production hook draft replacing the temporary probe, preserving unrelated hooks, and obtain approval before applying. User reloads/reviews trust through Codex UI. Controller and user perform C6/C7 native acceptance with fixed profiles and capture Hook stats; judge text against the copy deck/mockup and row provenance against isolated log baselines. Real prediction, readiness after startup, cold/down/off/no-harm and detached service survival remain live gates. Restore saved real config before ordinary use. Claude acceptance stays deferred. Do not claim full acceptance from automated tests or the probe. Keep implementation uncommitted until the agreed acceptance gate and final single-commit step; never push without separate approval.

## Preflight results already executed

Repo fake regression: 345 passed, 1 deselected in 80.57 s with loopback access. Stage 0 blocks: 34 final files and 18 stubs match literal bytes. Stage 1 workbench import under `-I` selects `.workbench/stage1-verify/laya_harness/__init__.py`. Workbench existing focused tests `tests/test_adapter.py tests/test_resources.py tests/test_source_session.py`: 123 passed in 0.20 s. New source/test blocks will be generated only after execution, as required by AGENTS.md.


## Executed verification and review

Task 1's four focused files were executed with `.venv/bin/python -m pytest -q tests/test_codex_adapter.py tests/test_codex_context.py tests/test_codex_resources.py tests/test_codex_hookargv.py`: initial stub RED 55 behavioral failures; final GREEN 60 passed in 0.05 s. The bounded-read regression had a separate RED; actual deeply nested TOML raised RecursionError in its RED, then the all-null fallback passed. Initial independent review approved the static adapter/catalog/command contract; final review included the parser-depth regression.

Task 2's `tests/test_codex_client.py` and `tests/test_codex_client_process.py` were executed: initial unit RED 29 failed/1 passed; watchdog RED 3 failures; initial focused final GREEN 62 passed in 16.92 s. Independent review requested malformed-log discriminator tolerance, watchdog setup fail-open and error snapshot preservation. C1/C5 moved first in commit 2734242. New regression RED 20 failed/62 deselected; targeted GREEN 20 passed. Final `.venv/bin/python -m pytest -q tests/test_codex*.py`: 142 passed in 14.42 s. Legacy affected regressions `.venv/bin/python -m pytest -q tests/test_commands.py tests/test_client_process.py`: 127 passed in 17.45 s.

Controller whole workbench fake suite before that three-finding delta: 467 passed, 1 deselected in 94.74 s. The final independent re-review returned APPROVED after `.venv/bin/python -m pytest -q tests/test_codex_client.py tests/test_codex_client_process.py tests/test_codex_context.py tests/test_commands.py` (131 passed in 15.38 s), plus `tests/test_client_process.py` (96 passed in 16.55 s). Final whole repo and real-model results will be recorded after promotion; none is inferred from the pre-fix run.

Observed existing fixtures/helpers: configured, home, free_port, FAKE_ANSWERS, write_config; procs.env_for/start_service/stop/wait_health; test_client_process.Listener/Trickle/rows. New native tests use payload(), env() with temporary CODEX_HOME, command() from the actual native builder, and externally measured hook() duration. Model and effort defaults are nullable and kept separately from active payload model/unknown effort. No file deletion is planned. Symbol call sites and shared integration were enumerated before the changes: client.run, __main__._hook, commands.unknown_models, service_client.profile/health and session_state.transaction. Python is the only implementation language at this boundary.

Generate/check with `.venv/bin/python -B .workbench/gen_stage1_plan.py` and `--check`. The generator reads only files differing from `.workbench/stage1-baseline`; source and tests below are final forms, not patches. WIP evidence: refs/laywip/codex-stage1/task-0, task-1, task-1.r2, task-2.r2 and task-2.r3. Ignore the earlier task-2 snapshot containing scratch bytecode; task-2.r2 replaced its review scope with explicit paths. Private execution logs/diffs are regenerable under /private/tmp/laya-codex-stage1/.

Intentional Stage 0 plan integration drift after promotion is limited to laya_harness/client.py, __main__.py and commands.py. The new Stage 1 blocks supersede those final forms. Preserve the old plan and original workbench; other Stage 0 file bytes must match that baseline. New Codex files are additions, not retroactive changes to the Stage 0 plan.

## Verified implementation blocks

These literal files are generated from the isolated GREEN workbench. Commands and results must be recorded in the verification section before promotion.

### `laya_harness/__main__.py`

```python
"""Entry point: `python -I -m laya_harness hook claude-code <Event>` (hooks) and the
`laya-harness` console script (commands)."""

import time

_STARTED = time.monotonic()  # the hook's duration is measured from process start (spec §8)

import os  # noqa: E402
import sys  # noqa: E402


def _hook(args: list) -> None:
    """Never raises, always exits 0, and writes at most one JSON object to stdout (spec §4.2).

    Exit code 2 would block the prompt in every project, so argument errors, bad input and
    crashes all end the same way: nothing on stdout, exit 0, a line in client.log.
    """
    harness, event = (list(args) + [None, None])[:2]
    if harness == "codex":
        # Whole-process budget, including stdin and potentially blocked private paths.
        try:
            import signal

            def expired(signum, frame):
                os._exit(0)

            signal.signal(signal.SIGALRM, expired)
            budget = 4.5 if event == "SessionStart" else 1.5
            remaining = _STARTED + budget - time.monotonic()
            if remaining <= 0:
                os._exit(0)
            signal.setitimer(signal.ITIMER_REAL, remaining)
        except BaseException:  # noqa: BLE001 — watchdog failure must not touch state
            os._exit(0)
    out = None
    real_stdout = None
    try:
        real_stdout = os.dup(1)
        os.dup2(os.open(os.devnull, os.O_WRONLY), 1)  # nothing a library or child writes reaches Claude
        sys.stdout = sys.stderr  # stray prints must never reach Claude's context
        from . import paths

        try:
            paths.ensure_home()
            log_fd = os.open(paths.client_log(), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            os.fchmod(log_fd, 0o600)
            os.dup2(log_fd, 2)
        except BaseException:  # noqa: BLE001
            pass
        harness, event = (list(args) + [None, None])[:2]
        if harness == "codex" and len(args) != 2:
            raise ValueError("Codex hook requires exactly harness and event")
        raw = sys.stdin.buffer.read()  # read stdin to the end before anything is spawned
        from . import client

        out = client.run(harness, event, raw, _STARTED)
    except BaseException as exc:  # noqa: BLE001
        try:
            from . import decision_log

            decision_log.problem(f"hook failed: {type(exc).__name__}: {exc}")
        except BaseException:  # noqa: BLE001
            pass
    try:
        if out and real_stdout is not None:
            os.write(real_stdout, out.encode("utf-8"))
    finally:
        os._exit(0)


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] == ["hook"]:
        _hook(argv[1:])
    from . import commands

    return commands.main(argv)


if __name__ == "__main__":
    sys.exit(main())
```

### `laya_harness/adapter_codex.py`

```python
"""Deterministic Codex advice with native plan copy and unknown active effort (C4)."""

from . import catalog as catalog_mod
from . import copytext
from .adapter_claude_code import tier_and_class

RULES_VERSION = "codex_v0"


def decide(answers: dict, *, first_human: bool, plan_shown: bool, permission_mode, prompt: str,
           display: dict, catalog: dict, fit: dict, session: dict) -> dict:
    """Return {"lines", "line_for", "suppress_reason", "suggestion", "mismatches"}.

    `lines` holds at most two strings: the model line first, then the plan line.
    `line_for` names them: {"model": line or None, "plan": line or None}.
    `suppress_reason` is per line: {"model": reason or None, "plan": reason or None}.
    """
    line_for, reasons, suggestion = {"model": None, "plan": None}, {"model": None, "plan": None}, None

    tier, tier_p, cls = tier_and_class(answers["difficulty"]["probabilities"])
    if not first_human:
        reasons["model"] = "not_first_prompt"
    elif tier_p < display["difficulty"]["min_tier_p"]:
        reasons["model"] = "below_threshold"
    else:
        suggestion = catalog_mod.select(cls, catalog, fit)
        if suggestion is None:
            reasons["model"] = "no_fit"
        else:
            line_for["model"] = copytext.model_line(tier, tier_p, suggestion["display"], suggestion["effort"])

    plan = answers["plan_first"]["noul"]
    plan_rules = display["plan_first"]
    if plan < plan_rules["show_threshold"]:
        reasons["plan"] = "below_threshold"
    elif permission_mode == "plan" or prompt.lstrip().startswith("/plan"):
        reasons["plan"] = "plan_mode"
    elif not (first_human or len(prompt) >= plan_rules["min_chars"]):
        reasons["plan"] = "too_short"
    elif plan_shown:
        reasons["plan"] = "already_shown"
    else:
        line_for["plan"] = plan_line(plan)

    mismatches = [
        {"type": "MODEL+REASONING", "profile": {"tier": tier, "tier_p": tier_p, "class": cls},
         "state": {"model": session.get("model"), "effort": session.get("effort")},
         "channel_later": "user"},
        {"type": "MODE", "profile": {"plan_first": plan},
         "state": {"permission_mode": permission_mode}, "channel_later": "harness"},
        {"type": "PARALLELISM_OPPORTUNITY", "profile": {"parallel": answers["parallel"]["noul"]},
         "state": {}, "channel_later": "harness"},
    ]
    lines = [line for line in (line_for["model"], line_for["plan"]) if line]
    return {"lines": lines, "line_for": line_for, "suppress_reason": reasons, "suggestion": suggestion,
            "mismatches": mismatches}


def plan_line(noul: float) -> str:
    return (f"laya · reads like a multi-step change (p={noul:.2f}) → "
            "Plan mode (/plan), or tell Codex to plan first")
```

### `laya_harness/client.py`

```python
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
```

### `laya_harness/codex_client.py`

```python
"""Native Codex hook normalization, session lifecycle and advisory rows (C1–C5)."""

import json
import time
from . import (__version__, adapter_codex, codex_context, codex_resources, config,
               decision_log, resources, service_client, session_state, spawn)

PROFILE_DEADLINE = 1.5
WAIT_BUDGET = 4.0
HEALTH_TIMEOUT = 0.5


def _validate(payload, event):
    if not isinstance(payload, dict) or payload.get("hook_event_name") != event:
        raise ValueError("native event does not match invocation")
    for key in ("session_id", "model", "cwd", "permission_mode"):
        if not isinstance(payload.get(key), str) or not payload[key]:
            raise ValueError("missing native " + key)
    if payload.get("transcript_path") is not None and not isinstance(payload["transcript_path"], str):
        raise ValueError("invalid transcript_path")
    if event == "SessionStart":
        if payload.get("source") not in ("startup", "resume", "clear", "compact", "fork"):
            raise ValueError("invalid lifecycle source")
    elif not isinstance(payload.get("turn_id"), str) or not payload["turn_id"] or not isinstance(payload.get("prompt"), str):
        raise ValueError("invalid prompt identity")


def run(event, raw, started):
    if event not in ("SessionStart", "UserPromptSubmit"):
        return None
    cfg = config.load()
    if cfg["mode"] == "off":
        return None
    payload, logged, snapshot = None, [], None
    try:
        payload = json.loads(raw.decode("utf-8"))
        _validate(payload, event)
        if event == "SessionStart":
            _session_start(cfg, payload)
            return None
        snapshot = {"model": payload["model"], "effort": None, "model_source": "hook"}
        return _prompt(cfg, payload, started, logged, snapshot)
    except BaseException:
        if event == "UserPromptSubmit" and not logged:
            _error_row(cfg, payload if isinstance(payload, dict) else {}, started, snapshot)
        raise


def _error_row(cfg: dict, payload: dict, started: float, snapshot) -> None:
    """Spec §5, §4.10: a client error still leaves one row, with status `error`."""
    try:
        row = _base_row(cfg, payload, None, time.time())
        row.update(status="error", session=snapshot,
                   latency_ms=round((time.monotonic() - started) * 1000, 1))
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


def _identity(state, payload):
    state.update(model=payload["model"], effort=None, model_source="hook")


def _session_start(cfg: dict, payload: dict) -> None:
    with session_state.transaction("codex:" + payload["session_id"]) as state:
        if payload["source"] in ("startup", "clear", "fork"):
            state.update(prompt_count=0, model_line_shown=False, plan_shown=False)
        _identity(state, payload)
    port = config.port(cfg)
    spawned = _ensure_service(cfg, port)
    if payload["source"] == "startup":
        _wait_until_ready(port, spawned)


def _base_row(cfg: dict, payload: dict, src: str, now: float) -> dict:
    questions = resources.questions()
    return {
        "schema_version": decision_log.SCHEMA_VERSION,
        "ts": decision_log.iso(now),
        "session_id": payload.get("session_id"),
        "prompt_id": payload.get("turn_id"),
        "turn_id": payload.get("turn_id"),
        "harness": "codex",
        "codex_defaults": codex_context.defaults(),
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
                     "adapter_rules": adapter_codex.RULES_VERSION,
                     "catalog": codex_resources.catalog_sha256()},
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


def _prompt(cfg: dict, payload: dict, started: float, logged: list, snapshot: dict):
    now = time.time()
    prompt = payload.get("prompt") or ""
    src = "agent" if "agent_id" in payload or "agent_type" in payload else "human"
    sid = "codex:" + payload["session_id"]
    row = _base_row(cfg, payload, src, now)
    with session_state.transaction(sid) as current:
        _identity(current, payload)
        first_human = current["prompt_count"] == 0
        if src == "human":
            current["prompt_count"] += 1
        state = dict(current)
        snapshot.update({key: state[key] for key in ("model", "effort", "model_source")})
    if src != "human":
        row.update(status="skipped", suppress_reason={"model": "not_human", "plan": "not_human"})
        return _finish(row, state, started, None, logged)

    port = config.port(cfg)
    remaining = max(0.0, started + PROFILE_DEADLINE - time.monotonic() - 0.10)
    outcome, body = service_client.profile(port, prompt, remaining) if remaining else ("timeout", None)
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
        decision = adapter_codex.decide(
            body["answers"], first_human=first_human, plan_shown=latest["plan_shown"],
            permission_mode=payload.get("permission_mode"), prompt=prompt, display=questions["display"],
            catalog=codex_resources.catalog(), fit=codex_resources.fit(), session=state)
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
```

### `laya_harness/codex_context.py`

```python
"""Bounded user configuration defaults, never evidence of active session effort (C3)."""

import os
from pathlib import Path
import stat
import tomllib

MAX_BYTES = 64 * 1024


def defaults() -> dict:
    """Expose only model/effort defaults and their provenance; fail open on bad files."""
    empty = {"model": None, "effort": None, "source": None}
    home = Path(os.environ["CODEX_HOME"]) if "CODEX_HOME" in os.environ else Path.home() / ".codex"
    path = home / "config.toml"
    try:
        if not stat.S_ISREG(path.stat().st_mode):
            return empty
        # NONBLOCK plus fstat prevents a replacement FIFO from blocking between stat/open.
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
                return empty
            data = stream.read(MAX_BYTES)
            if os.fstat(stream.fileno()).st_size > MAX_BYTES:
                return empty
        config = tomllib.loads(data.decode("utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError, RecursionError):
        return empty
    model = config.get("model")
    effort = config.get("model_reasoning_effort")
    return {"model": model if isinstance(model, str) else None,
            "effort": effort if isinstance(effort, str) else None,
            "source": "user_config_default"}
```

### `laya_harness/codex_hookargv.py`

```python
"""Native synchronous Codex command hooks, using the shared argv builder (C1)."""

import shlex

from .hookargv import hook_argv

EVENTS = ("SessionStart", "UserPromptSubmit")
TIMEOUTS = {"SessionStart": 8, "UserPromptSubmit": 3}


def hook_entry(interpreter: str, event: str) -> dict:
    return {"type": "command", "command": shlex.join(hook_argv(interpreter, "codex", event)),
            "timeout": TIMEOUTS[event]}


def settings_snippet(interpreter: str) -> dict:
    return {"hooks": {event: [{"hooks": [hook_entry(interpreter, event)]}] for event in EVENTS}}
```

### `laya_harness/codex_resources.py`

```python
"""Codex recommendation subset and provisional fits, kept separate from Claude (C4)."""

import hashlib
import json
from pathlib import Path

CATALOG = Path(__file__).parent / "data" / "codex_models.json"
FIT = Path(__file__).parent / "data" / "codex_fit.json"


def catalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def fit() -> dict:
    return json.loads(FIT.read_text(encoding="utf-8"))


def catalog_sha256() -> str:
    """One provenance hash over the catalog followed by the fit table's raw bytes."""
    return hashlib.sha256(CATALOG.read_bytes() + FIT.read_bytes()).hexdigest()
```

### `laya_harness/commands.py`

```python
"""`laya-harness setup | status | stop | mode` (spec §4.5, §4.11). Only `setup` touches the
network, and only to download the pinned checkpoint."""

import argparse
import json
import os
import signal
import subprocess
import sys

from . import codex_resources, catalog, config, hookargv, paths, resources, service_client

SETUP_SESSION = "laya-setup-check"


def _download(checkpoint: dict, model_dir) -> None:
    from huggingface_hub import snapshot_download

    model_dir.mkdir(parents=True, exist_ok=True)
    snapshot_download(checkpoint["repo"], revision=checkpoint["revision"], local_dir=str(model_dir),
                      allow_patterns=checkpoint["files"])


def _complete(model_dir, checkpoint: dict) -> bool:
    return all((model_dir / name).is_file() for name in checkpoint["required"])


def setup(download=None, out=None) -> int:
    out = out or sys.stdout
    paths.ensure_home()
    ck = resources.checkpoint()
    model_dir = paths.models_dir() / f"laya-mlx@{ck['revision']}"
    weights = model_dir / "model.safetensors"
    if _complete(model_dir, ck) and resources.sha256_file(weights) == ck["weights_sha256"]:
        print(f"checkpoint already in place: {model_dir}", file=out)
    else:
        print(f"downloading the pinned checkpoint (about 807 MB) from {ck['repo']}@{ck['revision'][:12]} "
              f"into {model_dir}", file=out)
        (download or _download)(ck, model_dir)
        if not _complete(model_dir, ck) or resources.sha256_file(weights) != ck["weights_sha256"]:
            print("the download is incomplete or does not match the pinned sha256", file=out)
            return 1
    cfg = config.load()
    cfg.update(interpreter=sys.executable, model_dir=str(model_dir), repo=ck["repo"], revision=ck["revision"])
    config.save(cfg)

    argv = hookargv.hook_argv(sys.executable, "claude-code", "PostModelSwitch")
    probe = {"session_id": SETUP_SESSION, "hook_event_name": "PostModelSwitch"}
    result = subprocess.run(argv, input=json.dumps(probe).encode(), capture_output=True, timeout=30)
    (paths.sessions_dir() / f"{SETUP_SESSION}.json").unlink(missing_ok=True)
    if result.returncode != 0 or result.stdout:
        print(f"the hook command failed its check (exit {result.returncode})", file=out)
        return 1
    print("Add these hooks to ~/.claude/settings.json (spec §10):", file=out)
    print(json.dumps(hookargv.settings_snippet(sys.executable), indent=2), file=out)
    return 0


def unknown_models() -> set:
    known = {"codex": catalog.known(codex_resources.catalog()),
             "claude-code": catalog.known(resources.catalog())}
    seen = set()
    path = paths.decisions_path()
    if not path.is_file():
        return seen
    with open(path, encoding="utf-8", errors="replace") as f:  # line by line: the log can be large
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            session = row.get("session") if isinstance(row, dict) else None
            model = session.get("model") if isinstance(session, dict) else None
            name = catalog.canonical(model) if isinstance(model, str) else None
            harness = row.get("harness") if isinstance(row, dict) else None
            if harness is None:
                harness = "claude-code"
            elif not isinstance(harness, str) or not harness:
                continue
            if name and name not in known.get(harness, set()):
                seen.add(name)
    return seen


def status(out=None) -> int:
    out = out or sys.stdout
    cfg = config.load()
    outcome, body = service_client.health(config.port(cfg), timeout=0.5)
    if outcome == "refused":
        state = "down"
    elif outcome == "ok":
        state = body["state"] + (f" ({body['reason']})" if body.get("reason") else "")
    else:
        state = f"unreachable ({outcome})"
    revision = (cfg.get("revision") or "")[:12] or "not set up"
    print(f"laya-harness: {state} · mode {cfg['mode']} · checkpoint {revision} · logs {paths.home()}", file=out)
    unknown = unknown_models()
    if unknown:
        print("models in the log that the catalog does not list: " + ", ".join(sorted(unknown)), file=out)
    return 0


def stop(out=None) -> int:
    out = out or sys.stdout
    cfg = config.load()
    outcome, body = service_client.health(config.port(cfg), timeout=0.5)
    if outcome == "refused":
        print("laya-harness: not running", file=out)
        return 0
    if outcome != "ok":
        print(f"laya-harness: port {config.port(cfg)} did not answer as laya-harness ({outcome}); "
              "nothing stopped", file=out)
        return 1
    pid = body.get("pid")
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 1 or pid == os.getpid():
        print(f"laya-harness: the service reported an invalid pid {pid!r}; nothing stopped", file=out)
        return 1
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:  # it exited between the health check and the signal
        print("laya-harness: not running", file=out)
        return 0
    print(f"stopped the service (pid {body['pid']})", file=out)
    if cfg["mode"] != "off":
        print("note: the next prompt starts it again; `laya-harness mode off` keeps it down", file=out)
    return 0


def set_mode(value: str, out=None) -> int:
    out = out or sys.stdout
    if value not in config.MODES:
        raise ValueError(f"mode must be one of {', '.join(config.MODES)}, not {value!r}")
    cfg = config.load()
    cfg["mode"] = value
    config.save(cfg)
    print(f"mode: {value}", file=out)
    return 0


def main(argv) -> int:
    parser = argparse.ArgumentParser(prog="laya-harness")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("setup", help="download the pinned checkpoint and print the hooks snippet")
    sub.add_parser("status", help="one line: service state, mode, checkpoint, logs")
    sub.add_parser("stop", help="stop the running service")
    mode = sub.add_parser("mode", help="show, log-only or off")
    mode.add_argument("value", choices=config.MODES)
    args = parser.parse_args(argv)
    if args.command == "setup":
        return setup()
    if args.command == "status":
        return status()
    if args.command == "stop":
        return stop()
    return set_mode(args.value)
```

### `laya_harness/data/codex_fit.json`

```json
{
  "classes": {
    "quick": [{"family": "luna", "effort": "low"}, {"family": "sol", "effort": "low"}],
    "routine": [{"family": "sol", "effort": "medium"}],
    "multi_file": [{"family": "sol", "effort": "high"}],
    "architecture": [{"family": "astra", "effort": "xhigh"}]
  }
}
```

### `laya_harness/data/codex_models.json`

```json
{
  "source": "Installed Codex picker metadata and official OpenAI model pages, checked 2026-10-10: https://developers.openai.com/api/docs/models/gpt-6-luna, https://developers.openai.com/api/docs/models/gpt-6.1-sol, https://developers.openai.com/api/docs/models/gpt-6-astra. Supported recommendation subset; standard list prices per million tokens.",
  "models": [
    {"id": "gpt-6-luna", "display": "GPT-6 Luna", "family": "luna", "version": "6", "price": {"input": 0.1, "output": 0.5}, "effort_levels": ["low", "medium", "high", "xhigh", "max"], "in_picker": true, "allowed": true},
    {"id": "gpt-6.1-sol", "display": "GPT-6.1 Sol", "family": "sol", "version": "6.1", "price": {"input": 2.0, "output": 10.0}, "effort_levels": ["low", "medium", "high", "xhigh", "max", "ultra"], "in_picker": true, "allowed": true},
    {"id": "gpt-6-astra", "display": "GPT-6 Astra", "family": "astra", "version": "6", "price": {"input": 10.0, "output": 50.0}, "effort_levels": ["low", "medium", "high", "xhigh", "max", "ultra"], "in_picker": true, "allowed": true}
  ]
}
```

### `tests/test_codex_adapter.py`

```python
import copy

import pytest

from laya_harness import adapter_codex as adapter, resources

DISPLAY = resources.questions()["display"]
CATALOG = {"models": [
    {"id": "gpt-6-luna", "display": "GPT-6 Luna", "family": "luna", "version": "6", "price": {"input": .1}, "effort_levels": ["low"], "allowed": True, "in_picker": True},
    {"id": "gpt-6.1-sol", "display": "GPT-6.1 Sol", "family": "sol", "version": "6.1", "price": {"input": 2}, "effort_levels": ["low", "medium", "high"], "allowed": True, "in_picker": True},
    {"id": "gpt-6-astra", "display": "GPT-6 Astra", "family": "astra", "version": "6", "price": {"input": 10}, "effort_levels": ["xhigh"], "allowed": True, "in_picker": True},
]}
FIT = {"classes": {"quick": [{"family": "luna", "effort": "low"}, {"family": "sol", "effort": "low"}], "routine": [{"family": "sol", "effort": "medium"}], "multi_file": [{"family": "sol", "effort": "high"}], "architecture": [{"family": "astra", "effort": "xhigh"}]}}
LIGHT = "laya · light task (p=0.86) → GPT-6 Luna at low effort fits this task"
HEAVY = "laya · heavy task (p=0.91) → GPT-6 Astra at xhigh effort fits this task"
PLAN = "laya · reads like a multi-step change (p=0.88) → Plan mode (/plan), or tell Codex to plan first"


def answers(quick=.6, routine=.26, multi=.08, arch=.06, plan=.2, parallel=.1, confidence=.99):
    return {"difficulty": {"probabilities": {"quick": quick, "routine": routine, "multi_file": multi, "architecture": arch}}, "plan_first": {"noul": plan, "confidence": confidence}, "parallel": {"noul": parallel}}


def run(a=None, **kwargs):
    params = dict(first_human=True, plan_shown=False, permission_mode="auto", prompt="fix typo", display=DISPLAY, catalog=CATALOG, fit=FIT, session={"model": "gpt-6-luna", "effort": None})
    params.update(kwargs)
    return adapter.decide(a if a is not None else answers(), **params)


@pytest.mark.parametrize("a,lines", [
    (answers(), [LIGHT]),
    (answers(quick=.03, routine=.06, multi=.3, arch=.61), [HEAVY]),
    (answers(quick=.4, routine=.3, multi=.2, arch=.1, plan=.88), [PLAN]),
    (answers(plan=.88), [LIGHT, PLAN]),
    (answers(quick=.4, routine=.3, multi=.2, arch=.1), []),
])
def test_copy_states_and_exact_return_keys(a, lines):
    d = run(a)
    assert d["lines"] == lines
    assert set(d) == {"lines", "line_for", "suppress_reason", "suggestion", "mismatches"}
    assert d["line_for"] == {"model": next((x for x in lines if " task (" in x), None), "plan": next((x for x in lines if "multi-step" in x), None)}
    assert adapter.RULES_VERSION == "codex_v0"


@pytest.mark.parametrize("quick,routine,expected", [(.1,.7,"0.80"), (.4501,.3501,"0.80"), (.4501,.3551,"0.81"), (.4,.3999,None)])
def test_tier_gate_and_display_boundary(quick, routine, expected):
    d = run(answers(quick=quick, routine=routine, multi=.1, arch=1-quick-routine-.1))
    if expected is None:
        assert d["lines"] == [] and d["suppress_reason"]["model"] == "below_threshold"
    else:
        assert f"(p={expected})" in d["lines"][0]


@pytest.mark.parametrize("p,expected", [(.85,"0.85"), (.8496,None), (.8567,"0.86")])
def test_independent_plan_gate_ignores_confidence(p, expected):
    d = run(answers(quick=.4, routine=.3, plan=p, confidence=1-p))
    assert d["lines"] == ([] if expected is None else [f"laya · reads like a multi-step change (p={expected}) → Plan mode (/plan), or tell Codex to plan first"])


@pytest.mark.parametrize("probs,expected", [
    ({"quick": .25, "routine": .25, "multi_file": .25, "architecture": .25}, ("light", .5, "quick")),
    ({"quick": .05, "routine": .05, "multi_file": .45, "architecture": .45}, ("heavy", .9, "multi_file")),
])
def test_tie_rules(probs, expected):
    assert adapter.tier_and_class(probs) == expected


@pytest.mark.parametrize("kwargs,model,plan", [
    ({"first_human": False}, "not_first_prompt", "too_short"),
    ({"permission_mode": "plan"}, None, "plan_mode"),
    ({"prompt": "  /plan stuff"}, None, "plan_mode"),
    ({"plan_shown": True}, None, "already_shown"),
    ({"first_human": False, "prompt": "x"*199, "plan_shown": True}, "not_first_prompt", "too_short"),
    ({"first_human": False, "prompt": "x"*200}, "not_first_prompt", None),
    ({"first_human": False, "permission_mode": "plan", "plan_shown": True}, "not_first_prompt", "plan_mode"),
])
def test_suppression_precedence(kwargs, model, plan):
    d = run(answers(plan=.88), **kwargs)
    assert d["suppress_reason"] == {"model": model, "plan": plan}


def test_same_model_unknown_effort_does_not_suppress():
    d = run()
    assert d["lines"] == [LIGHT]
    assert d["suggestion"] == {"model": "gpt-6-luna", "display": "GPT-6 Luna", "effort": "low", "class": "quick"}


@pytest.mark.parametrize("cls,a,model,effort", [
    ("routine", answers(quick=.1,routine=.7,multi=.1,arch=.1), "gpt-6.1-sol", "medium"),
    ("multi_file", answers(quick=.03,routine=.06,multi=.61,arch=.3), "gpt-6.1-sol", "high"),
])
def test_other_fit_classes(cls,a,model,effort):
    assert run(a)["suggestion"] == {"model": model, "display": "GPT-6.1 Sol", "effort": effort, "class": cls}


@pytest.mark.parametrize("change", ["allowed", "in_picker", "effort_levels"])
def test_ineligible_cheapest_falls_back(change):
    cat = copy.deepcopy(CATALOG)
    cat["models"][0][change] = [] if change == "effort_levels" else False
    assert run(catalog=cat)["suggestion"]["model"] == "gpt-6.1-sol"


@pytest.mark.parametrize("field,text", [("id", "gpt-fable-6"), ("family", "Fable"), ("display", "GPT Mythos")])
def test_injected_forbidden_catalog_cannot_recommend(field, text):
    cat = copy.deepcopy(CATALOG)
    cat["models"][0][field] = text
    fit = {"classes": {"quick": [{"model": cat["models"][0]["id"], "effort": "low"}]}}
    d = run(catalog=cat, fit=fit)
    assert d["lines"] == [] and d["suggestion"] is None and d["suppress_reason"]["model"] == "no_fit"


def test_no_fit_does_not_gate_plan():
    d = run(answers(plan=.88), fit={"classes": {}})
    assert d["lines"] == [PLAN] and d["suppress_reason"]["model"] == "no_fit"


def test_cheapest_then_newest_numeric_version():
    cat = copy.deepcopy(CATALOG)
    old = copy.deepcopy(cat["models"][0])
    old.update(id="gpt-luna-5", version="5", display="Luna 5")
    newer = copy.deepcopy(old)
    newer.update(id="gpt-luna-6.10",version="6.10",display="Luna 6.10")
    cat["models"] += [old,newer]
    fit = {"classes": {"quick": [{"model": m["id"], "effort": "low"} for m in (cat["models"][0], old, newer)]}}
    assert run(catalog=cat, fit=fit)["suggestion"]["model"] == "gpt-luna-6.10"
    newer["price"] = {"input": .2}
    assert run(catalog=cat, fit=fit)["suggestion"]["model"] == "gpt-6-luna"


def test_three_mismatch_entries_and_parallel_log_only():
    d = run(answers(quick=.4,routine=.3,multi=.2,arch=.1,parallel=.99))
    assert d["lines"] == []
    assert d["mismatches"] == [
        {"type": "MODEL+REASONING", "profile": {"tier": "light", "tier_p": .7, "class": "quick"}, "state": {"model": "gpt-6-luna", "effort": None}, "channel_later": "user"},
        {"type": "MODE", "profile": {"plan_first": .2}, "state": {"permission_mode": "auto"}, "channel_later": "harness"},
        {"type": "PARALLELISM_OPPORTUNITY", "profile": {"parallel": .99}, "state": {}, "channel_later": "harness"},
    ]
```

### `tests/test_codex_client.py`

```python
"""Native Codex contract C1–C5, isolated state and service doubles."""
import json
import time
import threading
import pytest
from laya_harness import client, session_state, config, commands
from test_client_process import served_reply, rows


def payload(event="UserPromptSubmit", **changes):
    value = dict(hook_event_name=event, session_id="same-native-id", model="gpt-6.1-sol",
                 cwd="/project", permission_mode="default", turn_id="turn-1", prompt="x" * 300,
                 source="startup")
    value.update(changes)
    return value


def run(value, event="UserPromptSubmit", started=None):
    return client.run("codex", event, json.dumps(value).encode(), started or time.monotonic())


@pytest.fixture(autouse=True)
def defaults_home(tmp_path, monkeypatch):
    path = tmp_path / "codex"
    path.mkdir()
    (path / "config.toml").write_text('model = "gpt-6-luna"\nmodel_reasoning_effort = "max"\nsecret = "do not log"\n')
    monkeypatch.setenv("CODEX_HOME", str(path))


def test_decided_row_copy_provenance_and_namespace(configured, home, monkeypatch):
    monkeypatch.setattr(client.service_client, "profile", lambda *a: ("ok", served_reply()))
    out = run(payload())
    assert json.loads(out)["systemMessage"] == (
        "laya · heavy task (p=0.91) → GPT-6 Astra at xhigh effort fits this task\n"
        "laya · reads like a multi-step change (p=0.91) → Plan mode (/plan), or tell Codex to plan first")
    row = rows(home)[0]
    assert row["harness"] == "codex" and row["turn_id"] == row["prompt_id"] == "turn-1"
    assert row["session"] == {"model": "gpt-6.1-sol", "effort": None, "model_source": "hook"}
    assert row["codex_defaults"] == {"model": "gpt-6-luna", "effort": "max", "source": "user_config_default"}
    assert row["versions"]["adapter_rules"] == "codex_v0"
    assert row["question_set"] == served_reply()["question_set"]
    assert "run laya-harness stop" in (home / "client.log").read_text()
    assert session_state.load("codex:same-native-id")["prompt_count"] == 1
    assert session_state.load("same-native-id")["prompt_count"] == 0


@pytest.mark.parametrize("outcome,status,cold", [("ok","decided",False),("refused","started_service",True),
    ("loading","loading",True),("not_ready","not_ready",False),("timeout","timeout",False),
    ("foreign","error",False),("error","error",False),("malformed","error",False)])
def test_outcomes_spawn_only_refused(configured, home, monkeypatch, outcome, status, cold):
    spawned = []
    monkeypatch.setattr(client.service_client,"profile",lambda *a:(outcome, served_reply() if outcome == "ok" else None))
    monkeypatch.setattr(client.spawn,"spawn_service",lambda cfg:spawned.append(cfg))
    run(payload())
    assert [(r["status"],r["cold"]) for r in rows(home)] == [(status,cold)]
    assert len(spawned) == (outcome == "refused")


@pytest.mark.parametrize("field,value", [("session_id",None),("model",""),("cwd",4),("permission_mode",False),
    ("turn_id",None),("prompt",None),("hook_event_name","SessionStart"),("transcript_path",3)])
def test_invalid_payload_error_without_inference(configured,home,monkeypatch,field,value):
    monkeypatch.setattr(client.service_client,"profile",lambda *a:pytest.fail("inference"))
    with pytest.raises(ValueError):
        run(payload(**{field:value}))
    assert [r["status"] for r in rows(home)] == ["error"]
    assert not list((home / "sessions").glob("*.json"))


@pytest.mark.parametrize("field,value", [("agent_id",None),("agent_id",""),("agent_type",False)])
def test_agent_presence_skips_but_snapshots_model(configured,home,monkeypatch,field,value):
    monkeypatch.setattr(client.service_client,"profile",lambda *a:pytest.fail("inference"))
    assert run(payload(**{field:value})) is None
    row=rows(home)[0]
    assert row["status"] == "skipped" and row["suppress_reason"] == {"model":"not_human","plan":"not_human"}
    assert row["session"]["model"] == "gpt-6.1-sol"
    assert session_state.load("codex:same-native-id")["prompt_count"] == 0


@pytest.mark.parametrize("source,reset",[("startup",True),("clear",True),("fork",True),("resume",False),("compact",False)])
def test_lifecycle_reset_and_startup_only_wait(configured,home,monkeypatch,source,reset):
    with session_state.transaction("codex:same-native-id") as state:
        state.update(prompt_count=7, model_line_shown=True, plan_shown=True, effort="high")
    calls=[]
    monkeypatch.setattr(client.service_client,"health",lambda *a,**k: (calls.append(1) or ("ok",{"state":"ready"})))
    assert run(payload("SessionStart",source=source),"SessionStart") is None
    state=session_state.load("codex:same-native-id")
    assert state["prompt_count"] == (0 if reset else 7)
    assert state["plan_shown"] is (not reset) and state["effort"] is None
    assert len(calls) == (2 if source == "startup" else 1)
    assert rows(home) == []


def test_remaining_budget_and_failed_first_eligibility(configured,home,monkeypatch):
    calls=[]
    replies=iter([("timeout",None),("ok",served_reply())])
    def profile(port,prompt,budget):
        calls.append((budget,session_state.load("codex:same-native-id")["prompt_count"]))
        return next(replies)
    monkeypatch.setattr(client.service_client,"profile",profile)
    run(payload(),started=time.monotonic()-0.4)
    run(payload())
    assert .85 < calls[0][0] < 1.02 and calls[1][0] <= 1.4
    assert [c[1] for c in calls] == [1,2]
    assert rows(home)[1]["suppress_reason"]["model"] == "not_first_prompt"


def test_off_and_unsupported_never_read_defaults(configured,home,monkeypatch):
    from laya_harness import codex_context
    monkeypatch.setattr(codex_context,"defaults",lambda:pytest.fail("defaults"))
    cfg=config.load();cfg["mode"]="off";config.save(cfg)
    assert client.run("codex","UserPromptSubmit",b"garbage",time.monotonic()) is None
    assert run(payload(),"PostModelSwitch") is None
    assert rows(home) == [] and not list((home / "sessions").glob("*.json"))


def test_log_only_does_not_set_flags(configured,home,monkeypatch):
    cfg=config.load();cfg["mode"]="log-only";config.save(cfg)
    monkeypatch.setattr(client.service_client,"profile",lambda *a:("ok",served_reply()))
    assert run(payload()) is None
    assert rows(home)[0]["suppress_reason"] == {"model":"log_only","plan":"log_only"}
    assert session_state.load("codex:same-native-id")["plan_shown"] is False


def test_concurrent_later_model_keeps_prompt_snapshot(configured,home,monkeypatch):
    def profile(*args):
        run(payload("SessionStart",model="gpt-6-astra",source="resume"),"SessionStart")
        return "ok",served_reply()
    monkeypatch.setattr(client.service_client,"health",lambda *a,**k:("ok",{"state":"ready"}))
    monkeypatch.setattr(client.service_client,"profile",profile)
    run(payload())
    assert session_state.load("codex:same-native-id")["model"] == "gpt-6-astra"
    assert rows(home)[0]["session"]["model"] == "gpt-6.1-sol"


def test_mixed_catalogs_and_legacy_rows(configured,home):
    values=[("codex","gpt-6-luna"),(None,"claude-opus-5-5"),("claude-code","gpt-6-luna"),
            ("codex","claude-opus-5-5"),("codex","gpt-other")]
    (home/"decisions.jsonl").write_text("\n".join(json.dumps({"harness":h,"session":{"model":m}}) for h,m in values))
    assert commands.unknown_models() == {"gpt-6-luna","claude-opus-5-5","gpt-other"}


def test_failed_append_leaves_flags_unclaimed_and_no_duplicate_decision(configured,home,monkeypatch):
    monkeypatch.setattr(client.service_client,"profile",lambda *a:("ok",served_reply()))
    real_append=client.decision_log.append
    def append(row):
        if row["status"] == "decided":
            raise OSError("disk full")
        real_append(row)
    monkeypatch.setattr(client.decision_log,"append",append)
    with pytest.raises(OSError):
        run(payload())
    state=session_state.load("codex:same-native-id")
    assert state["prompt_count"] == 1 and state["plan_shown"] is False and state["model_line_shown"] is False
    assert [r["status"] for r in rows(home)] == ["error"]


def test_overlapping_prompts_only_claim_plan_once(configured,home,monkeypatch):
    barrier=threading.Barrier(2)
    errors=[];outputs=[]
    def profile(*args):
        barrier.wait(timeout=2)
        return "ok",served_reply()
    def worker(turn):
        try:
            outputs.append(run(payload(turn_id=turn)))
        except BaseException as exc:
            errors.append(exc)
    monkeypatch.setattr(client.service_client,"profile",profile)
    workers=[threading.Thread(target=worker,args=(turn,)) for turn in ("a","b")]
    for thread in workers:thread.start()
    for thread in workers:thread.join(3)
    assert not errors and not any(thread.is_alive() for thread in workers)
    lines=[line for out in outputs if out for line in json.loads(out)["systemMessage"].splitlines()]
    assert sum("Plan mode" in line for line in lines) == 1
    assert sum("effort fits" in line for line in lines) == 1
    assert session_state.load("codex:same-native-id")["prompt_count"] == 2
    assert {r["prompt_id"] for r in rows(home)} == {"a","b"}


@pytest.mark.parametrize("outcome",["refused","loading","not_ready","timeout","foreign","error"])
def test_session_start_spawn_restrictions_and_silent_rows(configured,home,monkeypatch,outcome):
    spawned=[]
    monkeypatch.setattr(client.service_client,"health",lambda *a,**k:(outcome,{"state":outcome}))
    monkeypatch.setattr(client.spawn,"spawn_service",lambda cfg:spawned.append(cfg))
    assert run(payload("SessionStart",source="resume"),"SessionStart") is None
    assert len(spawned) == (outcome == "refused") and rows(home) == []


@pytest.mark.parametrize("replies,spawned,polls",[
    ([("ok",{"state":"not_ready"})],False,1), ([("foreign",None)],False,1),
    ([("timeout",None)],True,1), ([("refused",None)],False,1),
    ([("refused",None),("ok",{"state":"ready"})],True,2),
    ([("ok",{"state":"loading"}),("timeout",None),("ok",{"state":"ready"})],False,3)])
def test_codex_wait_stop_conditions(monkeypatch,replies,spawned,polls):
    from laya_harness import codex_client
    seen=[]
    def health(*a,**k):
        seen.append(k["timeout"])
        return replies[min(len(seen),len(replies))-1]
    monkeypatch.setattr(client.service_client,"health",health)
    codex_client._wait_until_ready(1,spawned)
    assert len(seen) == polls


@pytest.mark.parametrize("harness", [["codex"], {"name": "codex"}, 7, "", False, []])
def test_malformed_harness_skipped_with_mixed_legacy_rows(configured, home, harness):
    values = [
        {"harness": harness, "session": {"model": "malformed-only-model"}},
        {"harness": "codex", "session": {"model": "gpt-6-luna"}},
        {"session": {"model": "claude-opus-5-5"}},
        {"harness": None, "session": {"model": "claude-opus-5-5"}},
        {"harness": "claude-code", "session": {"model": "gpt-6-luna"}},
        {"harness": "codex", "session": {"model": "claude-opus-5-5"}},
        {"harness": "codex", "session": {"model": "gpt-other"}},
    ]
    (home / "decisions.jsonl").write_text("\n".join(json.dumps(row) for row in values))
    assert commands.unknown_models() == {"gpt-6-luna", "claude-opus-5-5", "gpt-other"}


def test_error_row_preserves_snapshot_after_concurrent_model_change(configured, home, monkeypatch):
    def profile(*args):
        run(payload("SessionStart", model="gpt-6-astra", source="resume"), "SessionStart")
        raise RuntimeError("prediction failed")
    monkeypatch.setattr(client.service_client, "health", lambda *a, **k: ("ok", {"state": "ready"}))
    monkeypatch.setattr(client.service_client, "profile", profile)
    with pytest.raises(RuntimeError, match="prediction failed"):
        run(payload())
    assert session_state.load("codex:same-native-id")["model"] == "gpt-6-astra"
    row, = rows(home)
    assert row["status"] == "error"
    assert row["session"] == {"model": "gpt-6.1-sol", "effort": None, "model_source": "hook"}


def test_error_before_capture_uses_validated_payload_identity(configured, home, monkeypatch):
    from laya_harness import codex_client
    monkeypatch.setattr(codex_client, "_prompt", lambda *a: (_ for _ in ()).throw(OSError("before capture")))
    with pytest.raises(OSError, match="before capture"):
        run(payload())
    row, = rows(home)
    assert row["status"] == "error"
    assert row["session"] == {"model": "gpt-6.1-sol", "effort": None, "model_source": "hook"}
    assert not list((home / "sessions").glob("*.json"))
```

### `tests/test_codex_client_process.py`

```python
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
```

### `tests/test_codex_context.py`

```python
import os
from pathlib import Path

import pytest

from laya_harness import codex_context

EMPTY = {"model": None, "effort": None, "source": None}


@pytest.fixture
def codex_home(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    return tmp_path


def test_only_defaults_and_provenance(codex_home):
    (codex_home / "config.toml").write_text('model="gpt-6.1-sol"\nmodel_reasoning_effort="high"\nsecret="private"\n[profiles.other]\nmodel="other"\n')
    assert codex_context.defaults() == {"model": "gpt-6.1-sol", "effort": "high", "source": "user_config_default"}


@pytest.mark.parametrize("text,expected", [
    ('model=1\nmodel_reasoning_effort=false', {"model": None, "effort": None, "source": "user_config_default"}),
    ('model="uncatalogued"', {"model": "uncatalogued", "effort": None, "source": "user_config_default"}),
    ('model_reasoning_effort="ultra"', {"model": None, "effort": "ultra", "source": "user_config_default"}),
    ('', {"model": None, "effort": None, "source": "user_config_default"}),
    ('model=[', EMPTY),
    ('model="x"\nmodel="y"', EMPTY),
])
def test_missing_fields_types_and_invalid_toml(codex_home, text, expected):
    (codex_home / "config.toml").write_text(text)
    assert codex_context.defaults() == expected


def test_missing_and_unreadable(codex_home, monkeypatch):
    assert codex_context.defaults() == EMPTY
    (codex_home / "config.toml").mkdir()
    assert codex_context.defaults() == EMPTY


@pytest.mark.parametrize("size,expected", [(65536, "gpt-6-luna"), (65537, None)])
def test_size_limit(codex_home, size, expected):
    prefix = b'model="gpt-6-luna"\n#'
    (codex_home / "config.toml").write_bytes(prefix + b'x' * (size - len(prefix)))
    assert codex_context.defaults()["model"] == expected
    if expected is None:
        assert codex_context.defaults() == EMPTY


def test_fifo_is_refused_without_opening(codex_home):
    os.mkfifo(codex_home / "config.toml")
    assert codex_context.defaults() == EMPTY


def test_device_is_refused(codex_home):
    (codex_home / "config.toml").symlink_to('/dev/null')
    assert codex_context.defaults() == EMPTY


def test_unset_home_uses_user_codex_directory(tmp_path, monkeypatch):
    monkeypatch.delenv("CODEX_HOME", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    user = tmp_path / ".codex"
    user.mkdir()
    (user / "config.toml").write_text('model="gpt-6-astra"')
    assert codex_context.defaults() == {"model": "gpt-6-astra", "effort": None, "source": "user_config_default"}


def test_unreadable_file_fails_open(codex_home, monkeypatch):
    (codex_home / "config.toml").write_text('model="gpt-6-luna"')
    def refuse(*args, **kwargs):
        raise PermissionError("denied")
    monkeypatch.setattr(os, "open", refuse)
    assert codex_context.defaults() == EMPTY


def test_invalid_utf8_fails_open(codex_home):
    (codex_home / "config.toml").write_bytes(b'\xff')
    assert codex_context.defaults() == EMPTY


def test_never_reads_more_than_64k(codex_home, monkeypatch):
    (codex_home / "config.toml").write_text('model="gpt-6-luna"')
    fdopen = os.fdopen
    class BoundedStream:
        def __init__(self, stream):
            self.stream = stream
        def __enter__(self):
            self.stream.__enter__()
            return self
        def __exit__(self, *args):
            return self.stream.__exit__(*args)
        def fileno(self):
            return self.stream.fileno()
        def read(self, n):
            assert n <= 65536
            return self.stream.read(n)
    monkeypatch.setattr(os, "fdopen", lambda *a, **kw: BoundedStream(fdopen(*a, **kw)))
    assert codex_context.defaults()["model"] == "gpt-6-luna"


def test_replaced_fifo_refused_after_open(codex_home, monkeypatch):
    (codex_home / "config.toml").write_text('model="gpt-6-luna"')
    fifo = codex_home / "fifo"
    os.mkfifo(fifo)
    real_open = os.open
    def replace_open(path, flags):
        assert flags & os.O_NONBLOCK
        return real_open(fifo, flags)
    monkeypatch.setattr(os, "open", replace_open)
    assert codex_context.defaults() == EMPTY


def test_unrelated_deep_toml_yields_null_defaults(codex_home):
    text = 'model = "gpt-6.1-sol"\nignored = ' + '{v = ' * 1100 + '1' + '}' * 1100
    (codex_home / "config.toml").write_text(text)
    assert codex_context.defaults() == EMPTY
```

### `tests/test_codex_hookargv.py`

```python
import shlex

import pytest

from laya_harness import codex_hookargv


@pytest.mark.parametrize("event,timeout", [("SessionStart", 8), ("UserPromptSubmit", 3)])
@pytest.mark.parametrize("interpreter", ["/tmp/a b/.venv/bin/python", "/tmp/a'$(touch nope);`false`/.venv/bin/python"])
def test_native_command_roundtrip(event, timeout, interpreter):
    entry = codex_hookargv.hook_entry(interpreter, event)
    assert set(entry) == {"type", "command", "timeout"}
    assert entry["type"] == "command"
    assert entry["timeout"] == timeout
    assert shlex.split(entry["command"]) == [interpreter, "-I", "-m", "laya_harness", "hook", "codex", event]


def test_exact_two_synchronous_events():
    value = codex_hookargv.settings_snippet("/tmp/python")
    assert set(value) == {"hooks"}
    assert set(value["hooks"]) == {"SessionStart", "UserPromptSubmit"}
    for event, entries in value["hooks"].items():
        assert entries == [{"hooks": [codex_hookargv.hook_entry("/tmp/python", event)]}]


def test_unsupported_event_is_not_registered():
    with pytest.raises(KeyError):
        codex_hookargv.hook_entry("/tmp/python", "PostModelSwitch")
```

### `tests/test_codex_resources.py`

```python
import hashlib

from laya_harness import codex_resources as resources


def test_catalog_exact_recommendation_subset():
    rows = resources.catalog()["models"]
    expected = [
        ("gpt-6-luna", "GPT-6 Luna", "luna", "6", 0.1, 0.5, False),
        ("gpt-6.1-sol", "GPT-6.1 Sol", "sol", "6.1", 2, 10, True),
        ("gpt-6-astra", "GPT-6 Astra", "astra", "6", 10, 50, True),
    ]
    assert len(rows) == 3
    for row, (model, display, family, version, price_in, price_out, ultra) in zip(rows, expected):
        assert row == {"id": model, "display": display, "family": family, "version": version,
                       "price": {"input": price_in, "output": price_out}, "in_picker": True,
                       "allowed": True, "effort_levels": ["low", "medium", "high", "xhigh", "max"] + (["ultra"] if ultra else [])}
    assert "2026-10-10" in resources.catalog()["source"]


def test_fit_exact_provisional_options():
    assert resources.fit()["classes"] == {
        "quick": [{"family": "luna", "effort": "low"}, {"family": "sol", "effort": "low"}],
        "routine": [{"family": "sol", "effort": "medium"}],
        "multi_file": [{"family": "sol", "effort": "high"}],
        "architecture": [{"family": "astra", "effort": "xhigh"}],
    }


def test_hash_includes_both_raw_files(tmp_path, monkeypatch):
    before = resources.catalog_sha256()
    assert before == hashlib.sha256(resources.CATALOG.read_bytes() + resources.FIT.read_bytes()).hexdigest()
    for attr in ("CATALOG", "FIT"):
        with monkeypatch.context() as change:
            edited = tmp_path / attr
            edited.write_bytes(getattr(resources, attr).read_bytes() + b' ')
            change.setattr(resources, attr, edited)
            assert resources.catalog_sha256() != before
```
