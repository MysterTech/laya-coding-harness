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
