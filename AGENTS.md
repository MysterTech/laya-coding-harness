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
  - **Not yet done:** writing the snippet's `hooks` object into the repo's `.claude/settings.local.json` (git-ignored, and it does not exist yet). This needs the user's explicit yes first. When asked, they chose to continue in Codex instead of answering.
  - **Note:** `~/.laya-harness/x/` is a stray directory dated 2026-10-08 14:27, probably left by an early probe. Leave it unless the user asks you to remove it.
- **Not done yet: Task 8 Steps 4 (the settings file) to 9:** acceptance with the user, visual QA, the single commit, and the hook install.
- **Non-blocking review items** are listed in `.workbench/deferred_p3.md` and in `.workbench/codex-stage0-review-prompt.md`.

## Next steps, in order

1. **Resume Task 8 at Step 4's settings file.** Ask the user to approve creating `.claude/settings.local.json` with exactly the `hooks` object from `.venv/bin/laya-harness setup` (or from `hookargv.settings_snippet`). Then do Step 5: acceptance, with fake mode first. Give the user written UI steps and read `~/.laya-harness/decisions.jsonl`, `client.log` and `service.log`. Run `laya-harness stop` before every config, mode or code change. Then Steps 6–9.
2. **Any further accepted fix round** uses the same docs-first procedure:
   1. edit the spec and commit it;
   2. change the code and tests in `.workbench/plan-verify/` and run them there: GREEN, plus RED against the stubs in `.workbench/plan-stubs/`;
   3. update the counts and notes in `.workbench/gen_plan.py`, regenerate the plan, and commit it;
   4. copy the verified blocks into the repo;
   5. run the drift check and the full suite.
3. **When the user resumes Task 8 Steps 2–9,** follow the plan. Several steps need the user: installing hooks into `~/.claude/settings.json` needs their approval of the exact diff, and acceptance needs them to work in the Claude app.
4. **After stage 0:** a design round for the Bridge and the web HUD (spec D14 and D15). The spec and mockups come first.

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
