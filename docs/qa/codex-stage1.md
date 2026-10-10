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
