import json
import os
import stat
import threading
from pathlib import Path

import pytest

from laya_harness import session_state, source, transcript

PAYLOADS = json.loads((Path(__file__).parent / "fixtures" / "payloads.json").read_text())
DEFAULT = session_state.DEFAULT


# --- prompt source (spec §4.7) -------------------------------------------------------------

@pytest.mark.parametrize(
    "name, expected",
    [
        ("user_prompt_human", "human"),
        ("user_prompt_task_notification", "task-notification"),
        ("user_prompt_agent_message", "agent"),
        ("user_prompt_cross_session", "peer"),
    ],
)
def test_classify_captured_payloads(name, expected):
    assert source.classify(PAYLOADS[name]) == expected


def test_classify_subagent_guard():
    assert source.classify(dict(PAYLOADS["user_prompt_human"], agent_id="a1")) == "subagent"
    assert source.classify(dict(PAYLOADS["user_prompt_human"], transcript_path="/x/subagents/a.jsonl")) == "subagent"


@pytest.mark.parametrize("agent_id", [None, "", False, 0])
def test_agent_id_presence_is_a_subagent_even_when_falsy(agent_id):
    assert source.classify(dict(PAYLOADS["user_prompt_human"], agent_id=agent_id)) == "subagent"
    assert source.classify(dict(PAYLOADS["user_prompt_task_notification"], agent_id=agent_id)) == "task-notification"


def test_agent_type_alone_is_still_human():
    # a main session started with --agent carries agent_type on every prompt
    assert source.classify(dict(PAYLOADS["user_prompt_human"], agent_type="reviewer")) == "human"


def test_prefix_wins_over_agent_id():
    payload = dict(PAYLOADS["user_prompt_task_notification"], agent_id="a1")
    assert source.classify(payload) == "task-notification"


def test_non_string_prompt_and_path_are_human():
    assert source.classify({"prompt": 5, "transcript_path": 7}) == "human"


# --- transcript tail (spec §4.6) -----------------------------------------------------------

def _row(model, ts, effort="high", **extra):
    return json.dumps(
        {"type": "assistant", "timestamp": ts, "effort": effort, "message": {"model": model}, **extra}
    )


def test_last_assistant_returns_newest_main_thread_reply(tmp_path):
    t = tmp_path / "t.jsonl"
    t.write_text(
        "\n".join(
            [
                _row("claude-opus-4-6", "2026-10-08T04:18:27.000Z"),
                json.dumps({"type": "user", "message": {"content": "hi"}}),
                _row("claude-opus-4-7", "2026-10-08T04:28:11.000Z", effort="medium"),
                _row("claude-haiku-5-5", "2026-10-08T04:29:00.000Z", isSidechain=True),
                _row("<synthetic>", "2026-10-08T04:30:00.000Z"),
            ]
        )
        + "\n"
    )
    reply = transcript.last_assistant(str(t))
    assert reply == {"model": "claude-opus-4-7", "effort": "medium", "ts": 1791433691.0}


def test_last_assistant_never_blocks_on_a_fifo(tmp_path):
    """Spec §4.6: only a regular file is read. Opening a FIFO would block the hook until killed."""
    fifo = tmp_path / "transcript.fifo"
    os.mkfifo(fifo)
    results = []
    worker = threading.Thread(target=lambda: results.append(transcript.last_assistant(str(fifo))), daemon=True)
    worker.start()
    worker.join(2)
    blocked = worker.is_alive()
    if blocked:  # release a reader stuck in open() so the test can finish
        os.close(os.open(fifo, os.O_WRONLY | os.O_NONBLOCK))
        worker.join(2)
    assert not blocked and results == [None]


def test_last_assistant_missing_empty_or_not_a_string(tmp_path):
    assert transcript.last_assistant(None) is None
    assert transcript.last_assistant(str(tmp_path / "nope.jsonl")) is None
    (tmp_path / "empty.jsonl").write_text("")
    assert transcript.last_assistant(str(tmp_path / "empty.jsonl")) is None
    assert transcript.last_assistant(1) is None  # never treated as a file descriptor
    os.fstat(1)  # stdout is still open


def test_reply_beyond_the_tail_is_not_returned(tmp_path, monkeypatch):
    monkeypatch.setattr(transcript, "TAIL_BYTES", 300)
    t = tmp_path / "t.jsonl"
    filler = json.dumps({"type": "user", "message": {"content": "x" * 400}})
    t.write_text(_row("claude-opus-4-7", "2026-10-08T04:28:11.000Z") + "\n" + filler + "\n")
    assert transcript.last_assistant(str(t)) is None


def test_cut_off_first_line_is_dropped(tmp_path, monkeypatch):
    t = tmp_path / "t.jsonl"
    row = _row("claude-opus-4-7", "2026-10-08T04:28:11.000Z")
    t.write_text("junk-before-the-seek-point" + row + "\n")
    monkeypatch.setattr(transcript, "TAIL_BYTES", len(row) + 1)  # the seek lands where the row starts
    assert transcript.last_assistant(str(t)) is None


def test_half_written_and_non_json_lines_are_skipped(tmp_path):
    t = tmp_path / "t.jsonl"
    t.write_text(
        _row("claude-opus-4-7", "2026-10-08T04:28:11.000Z") + "\n"
        + "not json at all\n"
        + "123\n"
        + json.dumps({"type": "assistant", "message": "oops"}) + "\n"
        + '{"type": "assistant", "message": {"mod'
    )
    assert transcript.last_assistant(str(t))["model"] == "claude-opus-4-7"


def test_excessively_nested_transcript_row_is_skipped(tmp_path):
    t = tmp_path / "t.jsonl"
    t.write_text(_row("claude-opus-4-7", "2026-10-08T04:28:11.000Z") + "\n"
                 + "[" * 2000 + "0" + "]" * 2000 + "\n")
    assert transcript.last_assistant(str(t))["model"] == "claude-opus-4-7"


@pytest.mark.parametrize("bad", ["garbage", 17])
def test_bad_timestamp_gives_none(tmp_path, bad):
    t = tmp_path / "t.jsonl"
    t.write_text(json.dumps({"type": "assistant", "timestamp": bad, "message": {"model": "m"}}) + "\n")
    assert transcript.last_assistant(str(t)) == {"model": "m", "effort": None, "ts": None}


@pytest.mark.parametrize("bad_effort", [{"level": "high"}, 3])
def test_non_string_effort_counts_as_none(tmp_path, bad_effort):
    t = tmp_path / "t.jsonl"
    t.write_text(json.dumps({"type": "assistant", "effort": bad_effort, "message": {"model": "m"}}) + "\n")
    assert transcript.last_assistant(str(t))["effort"] is None


def test_last_assistant_reads_only_the_tail(tmp_path, monkeypatch):
    monkeypatch.setattr(transcript, "TAIL_BYTES", 300)
    t = tmp_path / "t.jsonl"
    t.write_text(
        _row("claude-opus-4-6", "2026-10-08T04:18:27.000Z") + "\n" + ("x" * 1000) + "\n"
        + _row("claude-opus-4-7", "2026-10-08T04:28:11.000Z") + "\n"
    )
    assert transcript.last_assistant(str(t))["model"] == "claude-opus-4-7"


# --- session files (spec §4.6) -------------------------------------------------------------

def test_session_file_round_trip_is_private(home):
    state = session_state.load("sess-1")
    assert state["model"] is None and state["prompt_count"] == 0
    state["prompt_count"] = 3
    session_state.save("sess-1", state)
    assert session_state.load("sess-1")["prompt_count"] == 3
    path = home / "sessions" / "sess-1.json"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_unsafe_session_id_is_hashed(home):
    session_state.save("../evil", dict(DEFAULT))
    files = [p.name for p in (home / "sessions").iterdir()]
    assert len(files) == 1 and len(files[0]) == 64 + len(".json")


@pytest.mark.parametrize("content", ["null", "[1, 2]", "not json", '{"prompt_count": null}',
                                     '{"switched_at": "x"}', '{"plan_shown": 1}', '{"prompt_count": true}',
                                     '{"prompt_count": -1}', '{"switched_at": true}'])
def test_corrupt_session_file_starts_from_defaults(home, content):
    (home / "sessions").mkdir(parents=True)
    (home / "sessions" / "sess-1.json").write_text(content)
    assert session_state.load("sess-1") == DEFAULT


def test_excessively_nested_session_file_starts_from_defaults(home):
    (home / "sessions").mkdir(parents=True)
    (home / "sessions" / "sess-1.json").write_text("[" * 2000 + "0" + "]" * 2000)
    assert session_state.load("sess-1") == DEFAULT


def test_a_valid_non_default_state_round_trips(home):
    """An over-strict type check would silently reset every session (spec §4.6, §4.9)."""
    state = session_state.on_model_switch(dict(DEFAULT), "claude-opus-4-7", now=1000.0)
    state = session_state.on_human_prompt(state, 1010.0, None)
    state.update(prompt_count=5, effort="high", model_line_shown=True, plan_shown=True)
    session_state.save("sess-1", state)
    loaded = session_state.load("sess-1")
    assert loaded == state
    assert isinstance(loaded["updated"], float)
    assert (loaded["switched_at"], loaded["first_prompt_after_switch_at"]) == (1000.0, 1010.0)


# --- session start (spec §4.6) -------------------------------------------------------------

@pytest.mark.parametrize("payload", ["session_start_startup", "session_start_resume"])
def test_session_start_from_captured_sources(payload):
    state = dict(DEFAULT, prompt_count=4, model_line_shown=True, plan_shown=True)
    state = session_state.on_session_start(state, PAYLOADS[payload]["source"])
    reset = PAYLOADS[payload]["source"] == "startup"
    assert (state["prompt_count"], state["model_line_shown"], state["plan_shown"]) == (
        (0, False, False) if reset else (4, True, True))


@pytest.mark.parametrize("src, reset", [("startup", True), ("fork", True), ("resume", False),
                                        ("clear", False), ("compact", False)])
def test_which_sources_reset_the_counters(src, reset):
    state = session_state.on_session_start(dict(DEFAULT, prompt_count=4, model_line_shown=True, plan_shown=True), src)
    assert (state["prompt_count"], state["model_line_shown"], state["plan_shown"]) == (
        (0, False, False) if reset else (4, True, True))


# --- prompts, transcript and switches (spec §4.6) ------------------------------------------

def test_second_prompt_takes_model_and_effort_from_transcript():
    state = session_state.on_human_prompt(dict(DEFAULT), 100.0, None)
    assert state["prompt_count"] == 1 and state["model"] is None
    state = session_state.on_human_prompt(state, 200.0, {"model": "claude-opus-5-5", "effort": "xhigh", "ts": 150.0})
    assert (state["model"], state["effort"], state["model_source"]) == ("claude-opus-5-5", "xhigh", "transcript")


def test_first_prompt_ignores_transcript():
    state = session_state.on_human_prompt(dict(DEFAULT), 100.0, {"model": "m", "effort": "low", "ts": 50.0})
    assert state["model"] is None and state["effort"] is None


def test_missing_transcript_keeps_the_values():
    state = dict(DEFAULT, prompt_count=2, model="M", effort="high", model_source="transcript")
    state = session_state.on_human_prompt(state, 300.0, None)
    assert (state["prompt_count"], state["model"], state["effort"], state["model_source"]) == (
        3, "M", "high", "transcript")


def test_accepted_reply_without_effort_clears_it():
    state = dict(DEFAULT, prompt_count=2, model="claude-opus-5-5", effort="xhigh", model_source="transcript")
    state = session_state.on_human_prompt(state, 300.0, {"model": "claude-haiku-4-5", "effort": None, "ts": 250.0})
    assert (state["model"], state["effort"]) == ("claude-haiku-4-5", None)


def test_switch_precedence_regression():
    """Spec §4.6 + §6: switch to B; stale transcript still on A keeps B; a reply on B after the
    first post-switch prompt is accepted; a reply on A from the in-flight turn is ignored."""
    state = dict(DEFAULT, prompt_count=1, model="claude-opus-4-6", model_source="transcript")
    state = session_state.on_model_switch(state, PAYLOADS["post_model_switch"]["to_model"], now=1000.0)
    assert (state["model"], state["model_source"], state["switched_at"]) == ("claude-opus-4-7", "post_model_switch", 1000.0)
    state = session_state.on_human_prompt(state, 1010.0, {"model": "claude-opus-4-6", "effort": "high", "ts": 1005.0})
    assert (state["model"], state["model_source"], state["first_prompt_after_switch_at"]) == (
        "claude-opus-4-7", "post_model_switch", 1010.0)
    state = session_state.on_human_prompt(state, 1030.0, {"model": "claude-opus-4-7", "effort": "high", "ts": 1020.0})
    assert (state["model"], state["model_source"], state["switched_at"], state["first_prompt_after_switch_at"]) == (
        "claude-opus-4-7", "transcript", None, None)


def _pending(model="claude-opus-4-7"):
    state = dict(DEFAULT, prompt_count=1, model="claude-opus-4-6", model_source="transcript")
    state = session_state.on_model_switch(state, model, now=1000.0)
    return session_state.on_human_prompt(state, 1010.0, {"model": "claude-opus-4-6", "effort": "high", "ts": 1005.0})


def test_reply_at_exactly_the_first_prompt_time_keeps_the_switch():
    state = session_state.on_human_prompt(_pending(), 1030.0, {"model": "claude-opus-4-6", "effort": "high", "ts": 1010.0})
    assert (state["model"], state["model_source"]) == ("claude-opus-4-7", "post_model_switch")


def test_reply_without_timestamp_keeps_the_switch():
    state = session_state.on_human_prompt(_pending(), 1030.0, {"model": "claude-opus-4-6", "effort": "high", "ts": None})
    assert (state["model"], state["model_source"]) == ("claude-opus-4-7", "post_model_switch")


def test_effort_is_taken_while_a_switch_is_pending():
    state = session_state.on_human_prompt(_pending(), 1030.0, {"model": "claude-opus-4-6", "effort": "low", "ts": 1005.0})
    assert (state["model"], state["effort"]) == ("claude-opus-4-7", "low")


def test_a_new_switch_resets_the_first_prompt_time():
    state = dict(DEFAULT, prompt_count=1, model="A", model_source="transcript")
    state = session_state.on_model_switch(state, "B", now=1000.0)
    state = session_state.on_human_prompt(state, 1010.0, None)  # first prompt after A -> B
    state = session_state.on_model_switch(state, "C", now=1025.0)
    assert state["first_prompt_after_switch_at"] is None
    state = session_state.on_human_prompt(state, 1030.0, {"model": "B", "effort": "high", "ts": 1020.0})
    assert (state["model"], state["first_prompt_after_switch_at"]) == ("C", 1030.0)


def test_first_prompt_after_a_switch_is_recorded_even_without_a_reply():
    state = session_state.on_model_switch(dict(DEFAULT), "claude-opus-4-7", now=5.0)
    state = session_state.on_human_prompt(state, 9.0, None)
    assert (state["prompt_count"], state["first_prompt_after_switch_at"]) == (1, 9.0)


def test_switch_without_model_changes_nothing():
    state = session_state.on_model_switch(dict(DEFAULT), None, now=5.0)
    assert state["switched_at"] is None and state["model"] is None
