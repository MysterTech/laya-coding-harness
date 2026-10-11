"""The one place that builds the hook command (spec §4.2, §10). setup, the tests and the
install snippet all use it, so what is tested is exactly what is registered."""

EVENTS = ("SessionStart", "UserPromptSubmit", "PostModelSwitch")
TIMEOUTS = {"SessionStart": 8, "UserPromptSubmit": 3, "PostModelSwitch": 3}


def hook_argv(interpreter: str, harness: str, event: str) -> list:
    return [interpreter, "-I", "-m", "laya_harness", "hook", harness, event]


def hook_entry(interpreter: str, event: str) -> dict:
    argv = hook_argv(interpreter, "claude-code", event)
    return {"type": "command", "command": argv[0], "args": argv[1:], "timeout": TIMEOUTS[event]}


def settings_snippet(interpreter: str) -> dict:
    return {"hooks": {event: [{"hooks": [hook_entry(interpreter, event)]}] for event in EVENTS}}
