# AGENTS.md: working rules and handoff state for laya-harness

Codex reads this file automatically. Claude Code built stage 0 up to the point recorded below; continue from here.

## The user's rules (from their global instructions; they apply to every agent)

1. **No implementation before the documentation, and the mockups where there is a UI.** A change to product source, tests, copy, schema or shipping config lands in the spec and the plan first, committed, then in code. Obvious fixes are no exception. Reading, searching and running the existing tests are never gated.
2. **Plan preflight.** Every code block written into the plan must already have been executed and verified. The plan is generated from verified files, never typed by hand (see "Workbench" below).
3. **The spec is the contract.** Implementation and review are judged against the files on disk, not against chat or prompt text.
4. **Ask the user first** before any download, before touching `~/.claude/settings.json` or any `.claude/settings*.json`, and before `git push`. Push only after the user approves acceptance.
5. **Never use the Fable model family** for anything.
6. **One commit for the implementation at the end** (plan Task 8 Step 8). Doc changes are committed separately, before the code they describe.

## What the project is

laya-harness is a local "System 1" advisor for Claude Code. A hook sends each prompt to a local laya-mlx service. Deterministic rules turn the model's answers into at most two advisory lines shown to the user, and each prompt is written as one row to a local log. It always fails open.

- **Spec:** `docs/superpowers/specs/2026-10-08-laya-harness-design.md`.
- **Plan:** `docs/superpowers/plans/2026-10-08-laya-harness-stage0.md`.
- **Gate profile:** `docs/workflows/two-agent-swe-workflow.md`.
- **Interpreter:** use `.venv/bin/python` for everything; never call a bare `python` or `pytest`.

## State at handoff (2026-10-09)

- **Docs:** committed on `main`. The accepted review fixes are specified in `f74681f` and `16ab512`; the regenerated plan is `0c07e35`. The user's D16 addition is preserved.
- **Implementation:** Tasks 1–7 and Task 8 Step 1 are on disk, **uncommitted**. All ten accepted P1 findings and the accepted P2 test gaps were fixed through the workbench procedure below. Independent contract review returned **APPROVED**, with no findings in the fix-round scope.
  - All 34 final file blocks are byte-identical to the generated plan, including the Task 7 replacement in `__main__.py`.
  - The repo fake suite gives `345 passed, 1 deselected in 80.94 s`; independent workbench verification gives `345 passed, 1 deselected in 80.35 s`.
  - Every task's cumulative GREEN and stub RED was replayed. Task 6 has one import-only test that passes stubs; a separate third-party-import mutation proves its sensitivity. The other accepted P2 tests also caught deliberate mutations.
  - **Model exception for this fix round:** the user authorized Codex implementers and an independent Codex reviewer because Claude limits were exhausted. This does not permanently change the signed-off model routing.
- **Per-task snapshots:** kept in `refs/laywip/stage0/*`; list them with `git for-each-ref refs/laywip`. Diff any two to see a review round.
- **Task 8 progress (Claude, 2026-10-09), each checked by an independent run:**
  - **Fix round re-verified:** all 34 file blocks match the plan (`drift.py` 1–8; Task 6 shows only the expected `__main__.py` drift). The plan regenerates byte for byte. The suite gives `345 passed, 1 deselected`; `-m real_model` gives `1 passed`.
  - **Step 2 done:** an offline editable install, per the user's choice and plan commit `11c03e8`: `pip install --no-index --no-build-isolation -e ".[dev]"`. `.venv/bin/laya-harness status` printed the expected line. Recorded in the gate profile (`33cf522`).
  - **Step 3 done:** both gates above, and `git status --porcelain -- docs/` is empty.
  - **Step 4, half done:** the cached weights were verified (complete, and the sha256 matches the pin), then `laya-harness setup` ran. It printed "checkpoint already in place" and the snippet, the hook self-check passed, and it wrote `~/.laya-harness/config.json` (0600). `status` now shows `down · mode show · checkpoint 047678560251`.
  - **Step 4 complete (Codex):** the user explicitly approved the exact project hook draft. `.claude/settings.local.json` was created byte-identically from `.workbench/acceptance-settings-draft.json`, using the registered exec-form argv and 8/3/3 s timeouts. It is git-ignored.
  - **Step 5 in progress:** fake-light, fake-heavy and fake-plan-only copy and execution are confirmed from the user’s notices and isolated decision rows (**41.1 ms**, **46.4 ms**, **62.8 ms**, no client/service diagnostics). Screenshot comparison remains pending. The user approved the both-profile transition; the service was stopped (exit 0), and the **both-lines** fake profile is configured in mode `show`, awaiting a new Code-tab session. Its baseline starts at 6376 decision-log bytes and zero client/service bytes. The prior config is preserved in `.workbench/acceptance-config-before.json` (0600). Profile baselines and reduced observations are stored in `.workbench/acceptance-*-log-baseline.json` and `.workbench/acceptance-*-observed.json`. Progress is recorded in `docs/qa/design-qa.md`, whose overall status is in progress.
  - **Note:** `~/.laya-harness/x/` is a stray directory dated 2026-10-08 14:27, probably left by an early probe. Leave it unless the user asks you to remove it.
- **Not done yet: Task 8 Steps 5–9:** acceptance with the user, visual QA, the single commit, and the user-level hook install.
- **Non-blocking review items** are listed in `.workbench/deferred_p3.md` and in `.workbench/codex-stage0-review-prompt.md`.

## Next steps, in order

**2026-10-09 user steering:** Claude acceptance is deferred until its weekly limit replenishes. Begin Codex support design and test it in the Codex desktop app. The user approved Stage 1 (“then go for it”). Its contract is `docs/superpowers/specs/2026-10-09-laya-harness-codex-design.md`. The preflight plan is `docs/superpowers/plans/2026-10-10-laya-harness-codex-preflight.md`; evidence is `docs/qa/codex-preflight.md`. Baseline re-run: 345 passed, 1 deselected in 80.57 s. Native offline configuration/trust checks passed; live synthetic delivery is confirmed below, with direct model-input auditing still limited. The exact temporary project probe draft `.workbench/codex-probe/hooks.draft.json` has been prepared and directly tested; the user approved both direction and exact draft, and `.codex/hooks.json` is installed byte-identically with mode 0600. Native hook trust and first live synthetic execution are confirmed: both events captured for session `01a12402-8b93-7fb3-a041-51127b7634f3`, Codex replied successfully. The user screenshot shows no inline warning. Installed app code routes warning entries into Hook stats via the hook-shaped message-action icon; expanded UserPromptSubmit panel capture confirms exact delivery (Runs 2, Blocked 0, Failed 0). Official systemMessage semantics establish the user channel; direct model-input auditing remains a limitation. The installed app has Settings → Hooks with Reload hooks and project trust controls. Keep the temporary project hooks locally excluded from Git snapshots. Stage 1 production code is now on disk, uncommitted, after the generated literal plan was committed; detailed build state follows below. Claude acceptance remains pending, not waived. The both-lines fake profile is still configured; the approved production Codex hooks are installed and their BOTH capture is confirmed below.

1. **Deferred until Claude usage replenishes: resume Task 8 Step 5 at the fake-both UI check.** The user approved the transition and it is complete. Inspect new decision/log bytes against `.workbench/acceptance-both-log-baseline.json` after the next capture. Project hooks are already approved and created. The user opens a new Claude Code session in normal coding mode and sends a human prompt; expect the light model hint followed by the plan hint on a second line. Light, heavy and plan-only text/execution checks are done, but screenshots are still needed for visual QA. Continue the rest of spec §8. Run `laya-harness stop` before every config, mode or code change. Real-model config must be restored for real acceptance checks. Then Steps 6–9; user-level settings still require approval of their exact diff.
2. **Any further accepted fix round** uses the same docs-first procedure:
   1. edit the spec and commit it;
   2. change the code and tests in `.workbench/plan-verify/` and run them there: GREEN, plus RED against the stubs in `.workbench/plan-stubs/`;
   3. update the counts and notes in `.workbench/gen_plan.py`, regenerate the plan, and commit it;
   4. copy the verified blocks into the repo;
   5. run the drift check and the full suite.
3. **When the user resumes Task 8 Steps 2–9,** follow the plan. Several steps need the user: installing hooks into `~/.claude/settings.json` needs their approval of the exact diff, and acceptance needs them to work in the Claude app.
4. **After stage 0:** a design round for the Bridge and the web HUD (spec D14 and D15). The spec and mockups come first.


### Stage 1 Codex build state (2026-10-10)

- Contract independently approved: `docs/superpowers/specs/2026-10-09-laya-harness-codex-design.md` C1–C7. Mockup `docs/mockups/codex-stage1-hook-stats.svg`. Literal plan `docs/superpowers/plans/2026-10-10-laya-harness-codex-stage1.md`, generated/committed as 612def0 before promotion. Later doc commits record gates only.
- All 16 Stage 1 blocks match `.workbench/stage1-verify/` and production. Preserve `.workbench/stage1-baseline/` and original Stage 0 workbench. Old Stage 0 plan intentionally drifts only in client.py, __main__.py and commands.py; the Stage 1 final blocks supersede these. Other Stage 0 bytes remain unchanged.
- Independent adapter and final contract reviews APPROVED. Three client review fixes had 20 actual behavioral RED failures then GREEN; config parser depth has an actual RED. Final repo fake suite: 487 passed, 1 deselected in 95.91 s. Offline controller real-model gate: 1 passed, 487 deselected in 3.72 s.
- WIP refs `refs/laywip/codex-stage1/task-0`, task-1, task-1.r2, task-2.r2 and task-2.r3. The initial task-2 snapshot included scratch bytecode; task-2.r2 is the clean scope. Keep all original Stage 0 refs. Execution logs/diffs regenerate under /private/tmp/laya-codex-stage1/.
- Prepared exact replacement `.workbench/codex-production-hooks.draft.json` is private (0600). Its literal commands were tested with temporary homes/free port: SessionStart empty/exit0, ready after 175.6 ms; prompt exact both-lines systemMessage/exit0 after 61.5 ms, one Codex decided row. The user approved the exact replacement and it is now installed byte-identically in `.codex/hooks.json`, mode 0600; the temporary probe is no longer registered. Its evidence and private rollback copy are preserved. Native trust was not changed or bypassed.
- Native BOTH capture is now confirmed: project SessionStart/UPS completed, zero blocked/failed, exact two lines; independent visual review APPROVED for this state. Fresh-chat row latency 78.6 ms, fake provenance, active gpt-6.1-sol/effort unknown; no diagnostics. Reduced row at `.workbench/codex-acceptance-both-observed.json`. Other C7 gates remain pending. Next: ask approval to stop the fake service and restore `.workbench/codex-real-config.draft.json` (exact diff `.workbench/codex-real-config.diff`), then capture real prediction in a fresh chat. The draft is saved real config, not applied; no download is needed. The private baseline `.workbench/codex-acceptance-both-baseline.json` starts at decisions 6376 bytes and zero client/service bytes, with config/hook hashes; fake both-lines mode show was verified, and status was down. Gate C7 and QA `docs/qa/codex-stage1.md` govern subsequent measurable native acceptance. Current live service was confirmed down before promotion; live config still fake both-lines. Restore saved real config with user authorization before ordinary use. No native or Claude acceptance is inferred from automated gates. Implementation remains uncommitted; no push.

## Workbench (`.workbench/`, ignored by git through `.git/info/exclude`)

- `plan-verify/`: the verified copy of the repo the plan is generated from. Its `.venv` is a bare venv with a `.pth` that points at the repo venv's site-packages, so `python -I -m laya_harness ...` subprocesses import this copy rather than the repo. Run `cd .workbench/plan-verify && .venv/bin/python -m pytest -q`.
- `plan-stubs/`: the stub modules for each task, used for the RED check. `stubify.py <module.py>` regenerates a stub: the bodies become `raise NotImplementedError`, and docstrings, constants and classes are kept.
- `gen_plan.py`: rebuilds the plan from `plan-verify/` and `plan-stubs/`. It holds each task's metadata, notes and test counts (`red=`, optional `red_passes=` / `focused_total=`, and cumulative `total=`). From the repo root, the controller runs:
  `.venv/bin/python -B .workbench/gen_plan.py docs/superpowers/plans/2026-10-08-laya-harness-stage0.md '1606ae9 (later branch commits change documentation only)'`.
  It currently reproduces the committed plan byte for byte.
- `drift.py <task>`: compares the repo's files for a task against `plan-verify/`.
  - From the repo root, run `.venv/bin/python -B .workbench/drift.py <task>`.
  - Task 6 always shows `__main__.py` as drifted, because Task 7 edits it by design. The Task 7 check covers the final form.
- `check_plan_blocks.py`: the controller's literal-byte check of all final file blocks and stubs. `.venv/bin/python -B .workbench/check_plan_blocks.py --repo` checks the workbench and repo, applying the Task 7 replacement explicitly.
- `verify_fix_round.py`: controller replay of isolated cumulative GREEN and focused stub RED task boundaries. Logs are a regenerable cache in `/private/tmp/laya-stage0-fix-run/`.
- **Scratch copies for mutation or RED runs:** use the repo's `.venv/bin/python -m venv --without-pip` plus a `.pth` holding the copy's path and the repo venv's site-packages. A plain copy would import the repo through its editable install.

## Things never to do in tests or reviews

- Never use port 47913 or `~/.laya-harness`. Tests use a temporary `LAYA_HARNESS_HOME` and free ports; the test guard enforces this.
- Never run `-m real_model` unless you are acting as the controller. It reads the pinned weights from `~/.laya-harness/models/`.
- Never run `laya-harness setup`, `stop` or `mode` against the real home without the user.
