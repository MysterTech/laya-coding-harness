# Codex Stage 1 verification and acceptance

Date: 2026-10-10 (Asia/Kolkata). Status: **automated gates passed; native production acceptance pending**.

The native capability probe is recorded separately in codex-preflight.md. It establishes completed delivery in user-opened Hook stats, not an inline banner. The production mockup/copy contract is docs/mockups/codex-stage1-hook-stats.svg and the Stage 1 design C4/C7.

- Design review approved after harness-aware status and measurable acceptance clauses were added.
- Adapter review approved; parser-depth failure has an actual RED regression and safe fallback.
- Client contract review approved after malformed log discriminator, watchdog setup and error snapshot fixes; all three were demonstrated RED before GREEN.
- 16 final files were generated as literal plan blocks, committed before promotion, and match workbench/repo bytes. Intentional Stage 0 integration drift: client.py, __main__.py, commands.py.
- Final fake suite: **487 passed, 1 deselected in 95.91 s**. Offline pinned real-model gate: **1 passed, 487 deselected in 3.72 s**.
- Exact prepared native replacement commands, isolated temp home/free port: SessionStart silent/exit 0 and ready after **175.6 ms**; UserPromptSubmit one exact both-lines message/exit 0 after **61.5 ms**, one decided Codex row with hook model provenance and null actual effort.

Production draft: .workbench/codex-production-hooks.draft.json (0600). It replaces only this project's approved temporary SessionStart/UserPromptSubmit probe, with absolute venv interpreter and native shell command strings, timeout 8/3 seconds. No unrelated plugin hooks change. Installation is complete as recorded below. Native trust/reload, fake display states, real prediction, complete native duration receipts, C7 sample counts, cold/down/off/survival/no-harm and visual review remain pending. The current live config is the preserved fake both-lines profile; restore saved real configuration with the user's authorization before ordinary use. Claude acceptance remains deferred and Stage 0/Stage 1 implementation is uncommitted. No download, push or user-level hook edit occurred.

## Approved production replacement

The user approved the exact production draft. Project `.codex/hooks.json` now matches it byte for byte, mode 0600, with a private rollback copy at `.workbench/codex-probe/hooks.before-production.json`. Native trust settings were not changed or bypassed. The temporary probe command is no longer registered; its evidence remains preserved.

Before native capture, the controller verified the existing fake-both profile and mode show, and read-only status reported down. Baseline `.workbench/codex-acceptance-both-baseline.json` records decisions 6376 bytes, client 0 bytes and service 0 bytes, plus config/hook hashes. No live model/config change occurred. Next: user reloads/reviews the two project definitions in Settings → Hooks, opens a fresh project chat, sends the synthetic prompt, and captures expanded UserPromptSubmit in Hook stats. Expected light p=.86 model line followed by plan p=.88 line. All native acceptance gates remain pending until observed.

## Native BOTH capture — 2026-10-10, 17:15:59

The user's `Screenshot 2026-10-10 at 5.15.59 PM.png` shows Runs 6, Blocked 0, Failed 0. Our project SessionStart and UserPromptSubmit both completed; the other four runs are unrelated plugin hooks. One Message entry contains the exact expected light model line followed by the exact plan line, both readable and unclipped. Independent visual review returned **APPROVED for the captured BOTH state only**; native controls belong to Codex, and its wider panel fits the plan text on one line.

The fresh-chat decision row is session `01a125a1-b767-74f0-a7dd-85ec75a9c80b`, turn `01a125a1-e0f2-7263-b2c0-61c161e193d1`, timestamp 2026-10-10T11:45:29.611309Z (17:15:29 local). Status decided, exact both-lines shown_text, suggestion gpt-6-luna/low/class quick; both suppress reasons null. Active model gpt-6.1-sol from hook, actual effort null. Recorded row latency **78.6 ms**, cold false, fake checkpoint provenance, no truncation or dropped characters. This latency stops before logging/exit and does not establish the complete native-duration gate. Reduced evidence is private at `.workbench/codex-acceptance-both-observed.json`.

Two Codex rows arrived after the baseline: the fresh-chat capture and a separate row for the user's follow-up in the controller chat (80.8 ms). They are not duplicate rows for one prompt. Combined decision-log growth is 5046 bytes; client.log and service.log gained zero bytes. Hook and config hashes still match the baseline. The BOTH copy/native execution/visual check is passed; other fake states, real prediction and C7 timing/sample/down/cold/off/survival gates remain pending.

The controller prepared, but did not apply, `.workbench/codex-real-config.draft.json`, byte-identical to the saved pre-acceptance real config. Its exact diff is `.workbench/codex-real-config.diff`: restore model_mode real, remove fake_answers, retain show mode, port, interpreter, pinned local model path and checkpoint. Stopping the current fake service and applying that draft await user authorization. No download is needed. Remaining fake visual states may be revisited later; this transition does not mark them passed or waive them.
