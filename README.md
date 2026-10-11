# laya-harness

**A local advisor for Claude Code and Codex.** Laya reads your prompt, estimates the work it needs, and suggests a model, reasoning effort, or planning step. You choose whether to follow the advice; your coding agent keeps control of the task.

The goal is better code without spending more on a model or effort setting unless it improves the result. The current version establishes the advisory pipeline. Its task-to-model mappings are provisional; quality gains and cost savings have not yet been established.

**Status: experimental.** Both adapters are implemented. Automated gates and several native Codex checks have passed; full native acceptance is still in progress, and Claude acceptance remains pending.

**Publication note:** this repository currently publishes a documentation preview. The implementation and some linked design/QA artifacts remain local pending acceptance; the installation instructions will become usable when those files are published.

## What it does

- Classifies human prompts locally with `laya-mlx` on Apple silicon.
- Shows at most two lines: model/effort advice, then planning advice.
- Suggests a model on the first human prompt of a session. Planning has independent suppression rules.
- Stays silent below its thresholds: **0.80** for the light/heavy task tier and **0.85** for planning.
- Logs decisions, suppression reasons, and failures locally for later evaluation.
- Fails open: unavailable models, service failures, or exhausted deadlines let the prompt proceed without advice.

Example Codex output, using illustrative display-test scores:

```text
laya · light task (p=0.86) → GPT-6 Luna at low effort fits this task
laya · reads like a multi-step change (p=0.88) → Plan mode (/plan), or tell Codex to plan first
```

The scores are model outputs, **not calibrated probabilities of correctness**. Laya does not automatically change models, effort, or Plan mode, edit your project, or run coding agents. Parallel-work suitability is classified and logged but does not produce advice yet.

## Requirements

- An Apple silicon Mac. Inference uses MLX; other platforms are not validated.
- Python **3.11 or newer**, with a virtual environment.
- Claude Code or Codex with compatible native command hooks. Compatibility across all host versions is not established.
- About **807 MB** for the checkpoint download, plus the Python environment and runtime memory. Local testing used an M2 Mac; memory use and latency depend on the machine and prompt.

## Install

```sh
git clone https://github.com/MysterTech/laya-coding-harness.git
cd laya-coding-harness
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/laya-harness setup
```

Dependency installation uses the network. `setup` downloads the pinned checkpoint from `aac6fef/laya-mlx` on Hugging Face unless a complete, matching copy is already present. It verifies the weights' SHA-256, writes local configuration, checks the hook command, and prints a Claude Code hook snippet. **It does not install hooks for you.**

The package pins `laya-mlx==0.3.0`; [checkpoint.json](laya_harness/checkpoint.json) records the model revision, checksum, required files, and inference settings. After setup, inference loads local files offline.

Keep the virtual environment at a stable path. Hooks use its absolute interpreter path; moving or deleting it requires regenerating the definitions.

## Connect your coding harness

### Claude Code

Merge the snippet printed by `setup` into `~/.claude/settings.json`, or use project-local `.claude/settings.local.json` for an initial trial. Preserve existing settings and hooks.

The snippet registers `SessionStart`, `UserPromptSubmit`, and `PostModelSwitch`. It uses an absolute interpreter as `command`, with a separate `args` array and native timeouts of 8, 3, and 3 seconds. Session and model-switch hooks are silent; prompt advice is returned as a `systemMessage`.

Complete any native approval or reload required by your host, then start a fresh session and send a human prompt. Below-threshold prompts show nothing. Claude's remaining native and visual checks are recorded in [Claude QA](docs/qa/design-qa.md).

### Codex

Generate definitions using the same builder exercised by the tests:

```sh
.venv/bin/python -I -c 'import json, sys; from laya_harness.codex_hookargv import settings_snippet; print(json.dumps(settings_snippet(sys.executable), indent=2))'
```

Save the output as `.codex/hooks.json` in the project you want to use, merging it with any existing hooks. Keep this file local because its commands contain an absolute interpreter path.

Codex registers `SessionStart` and `UserPromptSubmit`, with native timeouts of 8 and 3 seconds. Its format uses one shell command string; the builder quotes paths for you. Do not copy Claude's separate `args` format into Codex.

In the tested desktop app, open **Settings → Hooks**, reload the definitions, and review or trust them through the native controls. Start a fresh project chat.

**Where to see advice:** open the hook-shaped message action to view **Hook stats**, then expand the project `UserPromptSubmit` entry. Advice appears as a **Message** there; it is not automatically displayed as an inline banner. Silent hooks have no Message entry.

Advice uses the user-facing `systemMessage` channel. Laya does not emit plain stdout or `additionalContext` as model instructions. Complete direct model-input auditing remains a validation limitation.

### macOS background activity

For the tested Codex desktop installation, enable **ChatGPT** under **System Settings → General → Login Items & Extensions → Background App Activity** if you want the service to survive quitting the desktop app.

In a controlled local comparison, macOS unloaded the service job with this permission disabled; the same service survived after it was enabled. Laya never changes this setting. See [launch QA](docs/qa/macos-service-launch.md) for evidence and limits.

This does not start laya at login or keep it resident permanently. The service starts on demand and exits after **15 minutes idle**. If macOS unloads it, the next eligible hook can request another startup.

## Everyday controls

Run these from the checkout:

| Command | Effect |
|---|---|
| `.venv/bin/laya-harness status` | Reports service state, mode, checkpoint, and log directory. |
| `.venv/bin/laya-harness mode show` | Classifies, logs, and displays eligible advice. Default mode. |
| `.venv/bin/laya-harness mode log-only` | Classifies and logs without displaying advice. |
| `.venv/bin/laya-harness mode off` | Disables inference, advice, decision rows, and hook-triggered startup. |
| `.venv/bin/laya-harness stop` | Stops the health-verified service. An eligible hook can start it again unless mode is off. |

Stop the service before changing its configuration. To disable advice and stop the currently loaded model:

```sh
.venv/bin/laya-harness stop
.venv/bin/laya-harness mode off
```

Remove only laya's entries from your harness settings to disconnect the hooks as well.

## How it works

```text
Human prompt → native hook → stdlib client → localhost service → laya-mlx
                                  ↑                              ↓
                         harness adapter ← execution profile
                                  ↓
                     user advice + local decision log
```

The model answers three questions: task difficulty, whether to plan first, and whether independent work could run in parallel. Deterministic adapters translate this shared profile into harness-specific suggestions using bundled catalogs and fit tables.

The hook client uses only Python's standard library; MLX stays in the service. The service listens on `127.0.0.1`, default port **47913**. On macOS, a bounded launcher requests an owned, on-demand per-user `launchd` job with no automatic login launch or automatic restart.

A new-session hook allows a bounded cold-start wait. Prompt service calls have a 1.5-second deadline; Codex additionally enforces whole-hook watchdogs of 1.5 seconds for prompts and 4.5 seconds for session startup. A down service can mean a silent first prompt while startup is requested. Loading and failure paths stay silent. A hard watchdog exit can occur before a decision row is written.

## Local data and privacy

Classification happens on your Mac. The harness makes no outbound inference request; setup is the checkpoint download step. Your coding host's own model requests and data handling are separate.

State lives in `~/.laya-harness/`:

| File or directory | Contents |
|---|---|
| `config.json` | Mode, port, interpreter, checkpoint location, and service settings. |
| `models/` | Pinned local checkpoint files. |
| `sessions/` | Per-harness session counters and advisory state. |
| `decisions.jsonl` | **Full prompt text**, identifiers, working directory, transcript path, answers, suggestions, suppression reasons, timing, and provenance. |
| `client.log`, `service.log` | Diagnostics. |

Private state directories use `0700`; configuration, decisions, and diagnostic files use `0600`. Logs can contain sensitive project information: review and redact them before sharing reports. `log-only` still stores prompts. `off` stops decision logging, although hook diagnostics may still be written.

The Claude adapter can read local transcript metadata to track model and effort. The Codex adapter records the supplied transcript path but does not open it; actual Codex effort is recorded as unknown rather than inferred from a default setting.

## Troubleshooting

- **No advice:** check `status`, your mode, and the decision row's `status` and `suppress_reason`. Confidence and session rules deliberately suppress advice; model suggestions are first-prompt only.
- **No Codex banner:** inspect the project prompt hook's Message in Hook stats.
- **Service is down:** this is normal after idle shutdown. An eligible hook requests startup; that prompt may receive no advice.
- **Service is not ready:** inspect `service.log` and confirm setup completed. Model-load failures do not trigger an automatic restart loop.
- **Hooks broke after moving the repo:** regenerate them with the new interpreter path, then reload and approve the changed definitions.
- **Service disappears on desktop quit:** check the macOS background activity setting above.

## Development and verification

```sh
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest -q
```

The default suite excludes `real_model` tests and uses fake inference, temporary state directories, and free ports. Tests must never use the production home or port. The pinned-checkpoint smoke test is a separate controller-only gate because it reads the real local model; follow [AGENTS.md](AGENTS.md) and the [workflow profile](docs/workflows/two-agent-swe-workflow.md) before running it.

Contributions follow a docs-first workflow: update the contract before implementation, verify workbench files before generating literal plan blocks, and review code against the contract on disk. See [AGENTS.md](AGENTS.md) for the project rules.

Recorded macOS launch build gates: **534 fake tests passed**, with one real-model test deselected; the separate cached real-model gate also passed. These are recorded results, not a claim that every host or workload is validated.

Native Codex evidence includes both-line delivery, real prediction, three cold starts, a 20-turn advisor timing sample, and app-exit survival with background activity enabled. Some display, down/off, and aggregate no-harm checks remain open. Timing varied on other turns; the short synthetic sample is not a general performance guarantee. Claude native acceptance remains pending.

- [Claude verification and acceptance](docs/qa/design-qa.md)
- [Codex verification and acceptance](docs/qa/codex-stage1.md)
- [macOS launch verification](docs/qa/macos-service-launch.md)

## Design and roadmap

Planned work includes held-out accuracy and quality/cost measurement, threshold calibration, learning from labeled outcomes, and a Bridge/web HUD. These are design directions, not shipped features.

- [Umbrella design](docs/superpowers/specs/2026-10-08-laya-harness-design.md)
- [Codex adapter contract](docs/superpowers/specs/2026-10-09-laya-harness-codex-design.md)
- [macOS service launch contract](docs/superpowers/specs/2026-10-10-laya-harness-macos-service-launch-design.md)
- [Question set](laya_harness/questions/profile_v0.json)

## License

Copyright (C) 2026 MysterTech.

laya-harness is licensed under the **GNU General Public License, version 3 only** (`GPL-3.0-only`). You may redistribute and modify it under those terms. It is provided without warranty; see [LICENSE](LICENSE) for the full text.

Dependencies and model weights retain their own licensing terms.
