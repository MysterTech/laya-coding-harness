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
