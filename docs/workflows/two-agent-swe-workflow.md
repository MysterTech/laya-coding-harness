# Two-Agent SWE Workflow — laya-harness Gate Profile

> **Status: signed off by the user on 2026-10-08.** TDD stays on (golden rule 4), and plan
> commits go directly on `main`.
>
> **The workflow itself lives in the portable core:**
> `~/.claude/workflows/two-agent-swe-workflow.md`, which defines the roles, golden rules,
> commit cadence, review loop and model routing. Read it first; it is the contract.
>
> This file is **only** laya-harness's gate profile: the exact commands and paths the core
> refers to. It changes when the repo's tooling changes, never when the workflow changes.
> Every command below was executed on 2026-10-08 before being written down; the results are
> recorded next to it.

## Environment

- **Repo:** `~/Code Playground/laya-harness`. The path contains a space, so quote it in every
  command. Run every command from the repo root.
- **Interpreter:** `.venv/bin/python`: Python 3.11.17 with laya-mlx 0.3.0, MLX 0.32.3 and
  pytest 9.1.1. The project is installed editable with `.venv/bin/python -m pip install -e
  ".[dev]"`, which makes `python -I -m laya_harness` importable from any directory, as the hooks
  require. **Never call a bare `python` or `pytest`.**
- **Offline:** `tests/conftest.py` sets `HF_HUB_OFFLINE=1`, so no test can download anything.
- **Spec:** `docs/superpowers/specs/2026-10-08-laya-harness-design.md` is the contract.

## TDD

Golden rule 4 applies; it is **not waived**. Only the user can waive it.

## Subagent gates

The implementer and reviewers may run these, and nothing else:

```bash
.venv/bin/python -m pytest -q              # every fake-based test; real_model tests deselected by default
.venv/bin/python -m pytest -q <paths>      # focused run
git diff --check                           # whitespace self-review (read-only)
```

Executed 2026-10-08: `pytest -q` exit 0 (1 passed, 1 deselected);
`pytest -q tests/test_scaffold.py` exit 0; `git diff --cached --check` exit 0 (the
controller ran the staged form on the new files).

**Subagents must not:**

- run `-m real_model` or load the real checkpoint;
- start a laya-harness service on port 47913, or touch `~/.laya-harness`;
- edit `~/.claude/settings.json`, or any `.claude/settings*.json`;
- register or trigger Claude Code hooks;
- download anything.

Tests that need a state directory or a port use a temporary `LAYA_HARNESS_HOME` and a free
port (spec §4.11) once that mechanism exists.

## Controller gates

Run in full once per plan, at the final gate:

```bash
.venv/bin/python -m pytest -q              # full fake-based suite
.venv/bin/python -m pytest -q -m real_model    # pinned checkpoint, offline
```

Executed 2026-10-08: both exit 0. The `real_model` run needs
`~/.laya-harness/models/laya-mlx@047678560251f28113ee8f5df4be82102c7bf336`, which check 6
downloaded and checksummed. It emits one `RuntimeWarning`: laya-mlx clamping the checkpoint's
`choice:11+` temperature. That is upstream behaviour; the stage-0 questions have 4 options and
are unaffected.

**Controller-only steps that are not commands:**

- **Real-session acceptance (spec §8).** Steps that need the desktop app's UI are done by the
  user from written steps. The controller reads `~/.laya-harness/decisions.jsonl`,
  `client.log` and `service.log` and judges the results.
- **The install diff (spec §10).** It is shown to the user and applied only with their
  approval.

**laya-harness commands (controller only; recorded 2026-10-09, stage-0 Task 8 Step 2).**
The console script was registered offline with
`.venv/bin/python -m pip install --no-index --no-build-isolation -e ".[dev]"` (exit 0; the
venv already holds setuptools 84.0.0 and pytest, so nothing is downloaded).

```bash
.venv/bin/laya-harness status   # read-only: one line, service state · mode · checkpoint · logs
.venv/bin/laya-harness stop     # exit 0: stopped or not running; exit 1: port not laya-harness, nothing stopped
.venv/bin/laya-harness mode show|log-only|off
.venv/bin/laya-harness setup    # reuses the checksummed checkpoint; downloads only with the user's approval
```

Executed 2026-10-09: `status` exit 0, printing
`laya-harness: down · mode show · checkpoint not set up · logs /Users/thunderstruck/.laya-harness`.
`setup`, `stop` and `mode` are run at Task 8 Steps 4–5, each recorded with its result there.
Subagents never run these commands: they act on the real `~/.laya-harness`.

## Stack reset

Here the "stack" is the local service, `~/.laya-harness`, and the project-level hooks used
during acceptance.

- **Before visual capture or acceptance:** stop the service, set the mode and the fake-model
  config, and start a new Code-tab session. The commands (`laya-harness stop`,
  `laya-harness mode …`, the config switch) are created by the stage-0 plan; the controller
  executes them and records them here before first use.
- **Nothing changes config, questions or code during capture.** The service reads them once at
  startup (spec §4.4).
- **Acceptance hooks live in this repo's `.claude/settings.local.json`,** which git ignores.
  The user-level `~/.claude/settings.json` is untouched until install (spec §10).

## Visual verification

| | |
|---|---|
| Surface | The UserPromptSubmit `systemMessage`, shown as a *Claude Code notice* in the desktop Code tab |
| Tool | Screenshots of the Code tab taken by the user (Cmd+Shift+4) from the controller's written steps. The controller cannot drive the desktop app. |
| State | Fake-model mode with a fixed profile per display state, so the text is deterministic (spec §8, step 1) |
| Mockups | Spec §4.12 copy deck for the exact text, and `docs/mockups/stage0-check1-*.png` for the rendering |
| Compare | The exact text of each display state against §4.12; layout and prefixes against the check-1 screenshots |
| QA record | `docs/qa/design-qa.md` |

## Run directory

Per-task diffs and screenshots, **outside the repo** so `git add -A` cannot stage them:

```
/private/tmp/claude-501/-Users-thunderstruck-Code-Playground-laya-harness/agent-run/<plan-slug>/
```

Verified creatable and writable on 2026-10-08. `/private/tmp` is cleared on reboot; the
contents are a regenerable cache, and the WIP refs are the durable record.

## WIP ref namespace

```
refs/laywip/<plan-slug>/task-N
```

Verified on 2026-10-08: create, list and delete all work.

## Model routing

As in the core: implementers on `sonnet`; code reviewers on `sonnet` for routine work and
`opus` for contract work; visual reviewer on `sonnet`. **Never `fable`.**

Contract files here are:

- the hook contract (spec §4.2);
- the service API (§4.4);
- session state (§4.6);
- the decision-log schema (§4.10);
- the install snippet (§10).

## Doc and commit conventions

- Remote: `origin` is `https://github.com/MysterTech/laya-coding-harness.git`, and `main` tracks
  `origin/main`. One commit per plan, by the controller only, on `main`, after the controller
  gates pass. The controller pushes it only after the user approves acceptance (decided
  2026-10-08). Subagents never push.
- Docs are git-tracked. Contract docs (the spec and plans) move in their own commit **before**
  the code that implements them.
- Specs live in `docs/superpowers/specs/`, plans in `docs/superpowers/plans/`, mockups in
  `docs/mockups/`, and the QA record in `docs/qa/`.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Never commit `.venv/`, `.claude/settings.local.json`, `.claude/spike/`, or anything from
  `~/.laya-harness`. `.gitignore` covers the first three.

## Stage 1 Codex supplement (2026-10-10)

The user approved Codex support while Claude limits are exhausted; use Codex implementers and independent Codex reviewers under the temporary routing exception. The Stage 1 contract is `docs/superpowers/specs/2026-10-09-laya-harness-codex-design.md`. Existing automated gates and isolation rules apply, with config-default tests using temporary CODEX_HOME. The baseline full fake suite was re-executed: 345 passed, 1 deselected in 80.57 s. Preserve the Stage 0 verification copy; build in `.workbench/stage1-verify/`, generate literal plan blocks from executed files, commit docs before copying production code. WIP namespace is `refs/laywip/codex-stage1/`.

Native UI evidence uses desktop runtime 0.162.0-alpha.2, not Homebrew CLI 0.155.1. User screenshots confirm the exact probe under Hook stats → Completed UserPromptSubmit / Project → Message, with 0 blocked/failed. The surface is user-opened Hook stats, not an automatic banner. Mockup: `docs/mockups/codex-stage1-hook-stats.svg`; QA: `docs/qa/codex-preflight.md` and subsequent production acceptance record. Screenshots remain user-controlled. Exact installation/replacement is reviewed before applying, and changed definitions are trusted only through the native UI. Claude acceptance remains deferred.
