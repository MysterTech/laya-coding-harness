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
