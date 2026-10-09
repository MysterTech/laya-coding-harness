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

- **Docs:** committed on `main`. Run `git log` to see them. The latest plan commit is `a11bdb8`.
- **Implementation:** Tasks 1–7 and Task 8 Step 1 are on disk, **uncommitted**. Each task was reviewed independently and approved, with no P1 or P2 findings left.
  - Every file is byte-identical to its plan block.
  - `.venv/bin/python -m pytest -q` gives `255 passed, 1 deselected` (about 75 s).
- **Per-task snapshots:** kept in `refs/laywip/stage0/*`; list them with `git for-each-ref refs/laywip`. Diff any two to see a review round.
- **Not done yet: Task 8 Steps 2–9.** These are: console-script install, final gates, setup, acceptance with the user, visual QA, the single commit, and the hook install. They are on hold for the user's Codex review.
- **Non-blocking review items** are listed in `.workbench/deferred_p3.md` and in `.workbench/codex-stage0-review-prompt.md`.

## Next steps, in order

1. **Codex review.** Run the review prompt in `.workbench/codex-stage0-review-prompt.md` in a read-only sandbox. Report the findings to the user.
2. **Fix rounds for the findings the user accepts.** For each one, docs first:
   1. edit the spec and commit it;
   2. change the code and tests in `.workbench/plan-verify/` and run them there: GREEN, plus RED against the stubs in `.workbench/plan-stubs/`;
   3. update the counts and notes in `.workbench/gen_plan.py`, regenerate the plan, and commit it;
   4. copy the verified blocks into the repo;
   5. run the drift check and the full suite.
3. **Task 8 Steps 2–9,** as the plan describes them. Several steps need the user: installing hooks into `~/.claude/settings.json` needs their approval of the exact diff, and acceptance needs them to work in the Claude app.
4. **After stage 0:** a design round for the Bridge and the web HUD (spec D14 and D15). The spec and mockups come first.

## Workbench (`.workbench/`, ignored by git through `.git/info/exclude`)

- `plan-verify/`: the verified copy of the repo the plan is generated from. Its `.venv` is a bare venv with a `.pth` that points at the repo venv's site-packages, so `python -I -m laya_harness ...` subprocesses import this copy rather than the repo. Run `cd .workbench/plan-verify && .venv/bin/python -m pytest -q`.
- `plan-stubs/`: the stub modules for each task, used for the RED check. `stubify.py <module.py>` regenerates a stub: the bodies become `raise NotImplementedError`, and docstrings, constants and classes are kept.
- `gen_plan.py`: rebuilds the plan from `plan-verify/` and `plan-stubs/`. It holds each task's metadata, notes and test counts (`red=`, `total=`). Run:
  `python3 gen_plan.py "<repo>/docs/superpowers/plans/2026-10-08-laya-harness-stage0.md" '`1606ae9` (every later commit changes only `docs/` and `README.md`)'`.
  It currently reproduces the committed plan byte for byte.
- `drift.py <task>`: compares the repo's files for a task against `plan-verify/`.
  - It runs from `.workbench/`.
  - Task 6 always shows `__main__.py` as drifted, because Task 7 edits it by design. The Task 7 check covers the final form.
- **Scratch copies for mutation or RED runs:** use a fresh venv the same way, `python3.11 -m venv --without-pip` plus a `.pth` holding the copy's path and the repo venv's site-packages. A plain copy would import the repo through its editable install.

## Things never to do in tests or reviews

- Never use port 47913 or `~/.laya-harness`. Tests use a temporary `LAYA_HARNESS_HOME` and free ports; the test guard enforces this.
- Never run `-m real_model` unless you are acting as the controller. It reads the pinned weights from `~/.laya-harness/models/`.
- Never run `laya-harness setup`, `stop` or `mode` against the real home without the user.
