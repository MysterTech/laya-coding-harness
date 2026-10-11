"""Where a UserPromptSubmit prompt came from (spec §4.7). Only `human` prompts are profiled.

The prefixes are checked first. A subagent is recognised by `agent_id` or a `/subagents/`
transcript path, never by `agent_type` alone: that is also set in a main session started with
`--agent`.
"""

PREFIXES = (
    ("<task-notification", "task-notification"),
    ("<agent-message", "agent"),
    ("<cross-session-message", "peer"),
)


def classify(payload: dict) -> str:
    prompt = payload.get("prompt")
    prompt = prompt if isinstance(prompt, str) else ""
    for prefix, name in PREFIXES:
        if prompt.startswith(prefix):
            return name
    transcript_path = payload.get("transcript_path")
    if "agent_id" in payload or (isinstance(transcript_path, str) and "/subagents/" in transcript_path):
        return "subagent"
    return "human"
