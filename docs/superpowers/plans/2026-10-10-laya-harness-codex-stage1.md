# laya-harness — Stage 1 Codex workbench plan

Status: workbench task outline; production copy is gated on replacing this outline with literal verified code/test blocks. Scope approved by the user; no final implementation commit while acceptance remains pending.

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
