# Stage 1 native Codex preflight plan

**Goal:** Verify native Codex prompt hooks and user-only warning output before writing the adapter contract.

**Execution:** Controller capability probe; the implementation build follows the two-agent workflow, replacing the Superpowers execution skills. No production source changes in this preflight.

**Spec:** `docs/superpowers/specs/2026-10-09-laya-harness-codex-design.md`, Native preflight contract. Scope approved by the user: “then go for it.”

## Global constraints

- Repo interpreter `.venv/bin/python`, Python 3.11; no download or credential use.
- Desktop binary `/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex`, verified `0.162.0-alpha.2`.
- No change to the shared service, live laya configuration, Claude settings, stage-0 code or WIP refs.
- Do not bypass native hook trust. Exact project hook draft approval precedes installation.
- Private probe directory/file modes 0700/0600; metadata only, no prompt text or transcript contents.
- Stage-0 literal-byte gate verified: 34 final blocks and 18 stubs match the repo.

## Task 1: Prepare the probe (complete)

The controller executed the script with three direct subprocess cases: SessionStart emitted no output and exited 0; UserPromptSubmit emitted exactly the expected JSON warning and exited 0; malformed prompt JSON emitted no output and exited 0. All stderr was empty. A synthetic sensitive string was absent from the metadata capture; capture mode was 0600. The synthetic capture was removed before live use.

The exact executed script at `.workbench/codex-probe/capture.py`:

```python
"""Temporary native Codex hook probe; see Stage 1 preflight contract."""
import json
import os
import sys
from pathlib import Path

try:
    event = sys.argv[1]
    payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    if event not in ("SessionStart", "UserPromptSubmit") or not isinstance(payload, dict):
        raise ValueError("invalid probe input")
    capture = Path(__file__).parent / "capture.jsonl"
    record = {key: payload.get(key) if isinstance(payload.get(key), str) else None
              for key in ("session_id", "turn_id", "model", "permission_mode", "source")}
    record.update(event=event, fields=sorted(payload),
                  agent_fields={key: key in payload for key in ("agent_id", "agent_type")},
                  prompt_chars=len(payload["prompt"]) if isinstance(payload.get("prompt"), str) else None)
    fd = os.open(capture, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.fchmod(fd, 0o600)
        os.write(fd, (json.dumps(record) + "\n").encode("utf-8"))
    finally:
        os.close(fd)
    if event == "UserPromptSubmit":
        os.write(1, json.dumps({"systemMessage": "laya · Codex hook check (temporary probe)"}, ensure_ascii=False).encode("utf-8"))
except BaseException:
    pass
os._exit(0)
```

The parsed hook draft at `.workbench/codex-probe/hooks.draft.json`:

```json
{
  "description": "Temporary laya-harness Stage 1 capability probe; no service calls or prompt text capture.",
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "'/Users/thunderstruck/Code Playground/laya-harness/.venv/bin/python' -I '/Users/thunderstruck/Code Playground/laya-harness/.workbench/codex-probe/capture.py' SessionStart",
            "timeout": 8
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "'/Users/thunderstruck/Code Playground/laya-harness/.venv/bin/python' -I '/Users/thunderstruck/Code Playground/laya-harness/.workbench/codex-probe/capture.py' UserPromptSubmit",
            "timeout": 3
          }
        ]
      }
    ]
  }
}
```

The project currently has no `.codex/hooks.json`. Preserve other project configuration. If that changes before installation, prepare a merged draft and show it to the user before applying.

## Task 2: Verify native runtime in isolation (complete within the offline boundary)

Observed: hooks/list recognizes both exact command definitions and 8/3-second timeouts. Native config/batchWrite of the exact definition hash changes scratch hooks from untrusted to trusted. Neither ephemeral nor durable thread/start, including explicit startup source, invokes SessionStart. The debug prompt-input command does not invoke either hook. These offline paths therefore establish configuration and trust only; warning execution and model-context separation still need a live synthetic turn. Native runtime ran under an OS sandbox denying network; its attempted websocket prewarm was denied. No credentials, real configuration or model request were used. Evidence is private under `/private/tmp/laya-codex-native-probe/`.

- Inspect native hook schema and trust metadata, using an isolated Codex home and synthetic session with no model request.
- Use exact-definition native trust in the isolated home; never a global bypass.
- Check systemMessage appears as a warning entry, and remains absent from model-visible context. If the debug path does not run prompt hooks, report that limit and rely on the live desktop gate rather than fabricating evidence.

## Task 3: Install the temporary project probe and capture (pending user approval)

- Show the exact draft above to the user for approval. After approval, create `.codex/hooks.json` byte-identical to it.
- User reviews/trusts the hooks through Codex’s native hook UI. Record observed review and reload behavior; do not write a guessed trust hash into real config.
- User starts a fresh Codex session in this repository and sends `Reply with just: hook check complete.`
- Inspect private metadata capture for the exact native payload. User confirms the fixed temporary warning and successful answer; collect expanded warning visual evidence.
- Establish context separation from native runtime evidence, not from whether the model happened to mention the warning.

## Task 4: Complete Stage 1 design and plan

- Expand the Stage 1 contract with verified payload normalization, harness-specific state and logging, active model versus config-default effort provenance, Codex catalog/fit and copy, native installation/trust rules, and failure gates.
- Create mockups from the observed warning surface and exact copy before shipping UI code.
- Commit design docs first. Then build and test the isolated workbench copy, generate the implementation plan from verified blocks, and commit that plan before copying production code into the repo.
- Use separate Codex implementer and contract reviewer under the user’s current routing exception. Controller runs the real-model gate and live Codex acceptance. Claude acceptance stays deferred, not waived.
