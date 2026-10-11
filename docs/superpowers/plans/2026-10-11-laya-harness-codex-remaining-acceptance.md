# Remaining Codex display acceptance — 2026-10-11

Contract: Codex C4/C5/C7, approved macOS launch contract and background-activity qualification. This is controller acceptance configuration, not product implementation. Live config remains real/show until approval of the prepared four-profile batch and exact restoration. Project hooks remain unchanged and no native trust bypass is permitted.

## Verified preparation

Four private drafts under `.workbench/codex-remaining/`: light.config.json, heavy.config.json, plan-only.config.json, silent.config.json; exact real.config.json rollback and per-profile diffs. Derived from saved real configuration, changing only model_mode to fake, mode to show and fake_answers. No standard-port listener is created for isolated tests. The drafts were exercised with temp home/free-port/interpreter/idle overrides, HF_HUB_OFFLINE and LAYA_HARNESS_TEST.

Controller executed `.venv/bin/python /private/tmp/laya-macos-service-fix/remaining_profiles.py`: all four SS/UPS pairs exited0 with empty stderr, exact expected output, one decided fake row per prompt. Initial observation assertion expected empty-string shown_text for silent; corrected to documented null, then reran all four successfully. This was a controller-check assumption, not a product change.

- light: SS 165.753 ms; UPS 57.162 ms; expected Message: laya · light task (p=0.86) → GPT-6 Luna at low effort fits this task; one decided row.
- heavy: SS 155.629 ms; UPS 55.766 ms; expected Message: laya · heavy task (p=0.91) → GPT-6 Astra at xhigh effort fits this task; one decided row.
- plan-only: SS 155.598 ms; UPS 58.526 ms; expected Message: laya · reads like a multi-step change (p=0.88) → Plan mode (/plan), or tell Codex to plan first; one decided row.
- silent: SS 160.447 ms; UPS 53.914 ms; expected Message: (none); one decided row.

## Native sequence

User approves the four exact draft/diffs plus real restoration and five health-verified service stops, one before each configuration transition. Controller installs atomically with0600, records offsets/hashes, and confirms down before capture. Do not mutate configuration during capture. For each profile in order light, heavy, plan-only, silent: user opens a fresh project chat, sends `Reply with just: display check.`, captures expanded project UserPromptSubmit in Hook stats, and returns here. Match a unique fresh-chat row and screenshot; require exact copy or no Message, zero blocked/failed, fake provenance, one row. Ignore controller-chat followup rows. BOTH is already passed; do not repeat it. After silent, stop and restore exact real config; verify byte equality. Permission remains enabled by the user. No hook replacement/reload, downloads, code edits, final implementation commit or push. Subsequent down/off checks require their own concrete review.
