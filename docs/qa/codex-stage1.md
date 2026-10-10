# Codex Stage 1 verification and acceptance

Date: 2026-10-10 (Asia/Kolkata). Status: **automated gates passed; native production acceptance pending**.

The native capability probe is recorded separately in codex-preflight.md. It establishes completed delivery in user-opened Hook stats, not an inline banner. The production mockup/copy contract is docs/mockups/codex-stage1-hook-stats.svg and the Stage 1 design C4/C7.

- Design review approved after harness-aware status and measurable acceptance clauses were added.
- Adapter review approved; parser-depth failure has an actual RED regression and safe fallback.
- Client contract review approved after malformed log discriminator, watchdog setup and error snapshot fixes; all three were demonstrated RED before GREEN.
- 16 final files were generated as literal plan blocks, committed before promotion, and match workbench/repo bytes. Intentional Stage 0 integration drift: client.py, __main__.py, commands.py.
- Final fake suite: **487 passed, 1 deselected in 95.91 s**. Offline pinned real-model gate: **1 passed, 487 deselected in 3.72 s**.
- Exact prepared native replacement commands, isolated temp home/free port: SessionStart silent/exit 0 and ready after **175.6 ms**; UserPromptSubmit one exact both-lines message/exit 0 after **61.5 ms**, one decided Codex row with hook model provenance and null actual effort.

Production draft: .workbench/codex-production-hooks.draft.json (0600). It replaces only this project's approved temporary SessionStart/UserPromptSubmit probe, with absolute venv interpreter and native shell command strings, timeout 8/3 seconds. No unrelated plugin hooks change. Installation is complete as recorded below. Native trust/reload, fake display states, real prediction, complete native duration receipts, C7 sample counts, cold/down/off/survival/no-harm and visual review remain pending. The live configuration is now the saved real-model configuration, restored with user authorization as recorded below. Claude acceptance remains deferred and Stage 0/Stage 1 implementation is uncommitted. No download, push or user-level hook edit occurred.

## Approved production replacement

The user approved the exact production draft. Project `.codex/hooks.json` now matches it byte for byte, mode 0600, with a private rollback copy at `.workbench/codex-probe/hooks.before-production.json`. Native trust settings were not changed or bypassed. The temporary probe command is no longer registered; its evidence remains preserved.

Before native capture, the controller verified the existing fake-both profile and mode show, and read-only status reported down. Baseline `.workbench/codex-acceptance-both-baseline.json` records decisions 6376 bytes, client 0 bytes and service 0 bytes, plus config/hook hashes. No live model/config change occurred. Next: user reloads/reviews the two project definitions in Settings → Hooks, opens a fresh project chat, sends the synthetic prompt, and captures expanded UserPromptSubmit in Hook stats. Expected light p=.86 model line followed by plan p=.88 line. All native acceptance gates remain pending until observed.

## Native BOTH capture — 2026-10-10, 17:15:59

The user's `Screenshot 2026-10-10 at 5.15.59 PM.png` shows Runs 6, Blocked 0, Failed 0. Our project SessionStart and UserPromptSubmit both completed; the other four runs are unrelated plugin hooks. One Message entry contains the exact expected light model line followed by the exact plan line, both readable and unclipped. Independent visual review returned **APPROVED for the captured BOTH state only**; native controls belong to Codex, and its wider panel fits the plan text on one line.

The fresh-chat decision row is session `01a125a1-b767-74f0-a7dd-85ec75a9c80b`, turn `01a125a1-e0f2-7263-b2c0-61c161e193d1`, timestamp 2026-10-10T11:45:29.611309Z (17:15:29 local). Status decided, exact both-lines shown_text, suggestion gpt-6-luna/low/class quick; both suppress reasons null. Active model gpt-6.1-sol from hook, actual effort null. Recorded row latency **78.6 ms**, cold false, fake checkpoint provenance, no truncation or dropped characters. This latency stops before logging/exit and does not establish the complete native-duration gate. Reduced evidence is private at `.workbench/codex-acceptance-both-observed.json`.

Two Codex rows arrived after the baseline: the fresh-chat capture and a separate row for the user's follow-up in the controller chat (80.8 ms). They are not duplicate rows for one prompt. Combined decision-log growth is 5046 bytes; client.log and service.log gained zero bytes. Hook and config hashes still match the baseline. The BOTH copy/native execution/visual check is passed; other fake states, real prediction and C7 timing/sample/down/cold/off/survival gates remain pending.

## Authorized real-model restoration

The user authorized the exact `.workbench/codex-real-config.diff`. The controller stopped fake service pid 60526, restored `.workbench/codex-real-config.draft.json` byte-identically to the saved pre-acceptance configuration with mode 0600, then stopped restarted service pid 61297. Final read-only status: `down · mode show · checkpoint 047678560251`. Model mode is real and fake_answers is absent; the pinned local model path, interpreter, port and show mode are retained. No download occurred. The prior fake configuration is privately preserved at `.workbench/codex-config-before-real.json`.

Fresh baseline `.workbench/codex-acceptance-real-baseline.json`, timestamp 2026-10-10T11:52:54.937219Z: decisions 13546 bytes, client/service 0 bytes. Config SHA256 `1a1f5b7c451aa559684d35a587e914f0269dfd8979c40162171f41a06001170f`; production hook hash is unchanged. The first sandboxed status read reported unreachable/error; the authorized localhost read succeeded, and the final read confirms down. A fresh native project chat must exercise real SessionStart and prediction; no real native result is claimed yet. Remaining fake visual states may be revisited later; this transition does not mark them passed or waive them.

## Real-mode native capture — 2026-10-10, 17:32:46

The user screenshot shows Runs 6, Blocked 0, Failed 0, completed project SessionStart and UserPromptSubmit, with no Message entry. This establishes native fail-open execution, not a decided real profile. Three new Codex rows since the real baseline: session `01a125b0-1436-7f92-bfaf-558f99f63199` at 12:01:19Z returned loading (116.2 ms, cold true); session `01a125b1-20fd-75d1-b78d-e7c2fe8dee6a` at 12:02:11Z returned timeout (1408.4 ms); the controller-chat screenshot follow-up at 12:03:17Z also returned timeout (1406.5 ms). No row has answers or shown_text. Client log gained 152 bytes with two deadline diagnostics; service log gained 685 bytes with model temperature calibration warning/settings output. Reduced private evidence: `.workbench/codex-acceptance-real-observed.json`. The screenshot alone does not identify which fresh session it displays; both fresh-session outcomes are preserved rather than assigning one without evidence.

Health confirms pid 61945 ready with real pinned checkpoint. One bounded direct synthetic localhost profile returned ok in 1437.9 ms: quick .3454, routine .5318, multi_file .0571, architecture .0657, plan_first .067, parallel .1298. This profile is below advisory thresholds, but the direct request bypasses the native hook and does not pass native prediction or timing gates. Its latency is close to the hook budget; the cause of prior slower requests is undetermined. No source/config changes, restarts or downloads were made during diagnosis. Real native prediction remains pending; repeat the same short prompt in the warm chat and inspect its row. Complete native duration receipts and all other C7 samples remain pending.

## Successful warm real prediction — 2026-10-10, 17:35:51

The repeat screenshot shows Runs 2, Blocked 0, Failed 0: completed project UserPromptSubmit and unrelated plugin Stop, no Message. Its matching row in the same session `01a125b1-20fd-75d1-b78d-e7c2fe8dee6a`, turn `01a125b4-1031-7931-a5b1-4faa31fc4906`, at 12:05:20Z is **decided**, pinned checkpoint model_mode real, cold false, row latency **793.4 ms**. Model line suppressed as not_first_prompt; plan suppressed as below_threshold (.0593). Difficulty probabilities quick .3167, routine .5584, multi_file .0603, architecture .0645. This confirms successful real prediction through the native production hook and correct silent delivery for the recorded gates, without asserting classifier accuracy or complete-process timing. Reduced evidence `.workbench/codex-acceptance-real-warm-observed.json`.

The controller-chat screenshot follow-up separately timed out at 1402.5 ms; it is not a duplicate of the successful repeat turn. Client diagnostics now total 228 bytes; service remains 685 bytes. Latency variability and the remaining C7 timing/sample/cold/down/off/survival gates remain open. No source/config changes were made.

## Temporary timing instrumentation preflight

C8 was specified/committed before implementation. No hook-duration receipts were found in the observed native rollout (no hook events), projected items (user/agent messages only) or hook-target runtime logs (zero matches). Local instrument `.workbench/codex-timing/capture.py` and tests use synthetic children only. Behavioral RED 15 failed; final GREEN 18 passed, controller replay 18 passed in 1.00 s, independent review APPROVED with 18 passed in 1.04 s. Ten externally timed synthetic runs establish approximately 28–30 ms wrapper overhead; child receipts measure launch through exit, not native whole-wrapper duration. Two generated plan blocks match verified files byte for byte. Visual review N/A: UI/copy unchanged.

The exact temporary two-command replacement is prepared at `.workbench/codex-timing/hooks.draft.json`, diff `.workbench/codex-timing/hooks.diff`, with unchanged event timeouts and private production rollback. It is **not installed**; exact user approval and native reload/trust are pending. Receipts store only event/time/duration/exit/timeout, never prompt or output. No real-home change, source edit, download or push occurred. Native 20-human-turn steps are prepared at `.workbench/codex-timing-native-steps.md`; additional fake states and cold/down/off/survival gates remain separate and pending.
