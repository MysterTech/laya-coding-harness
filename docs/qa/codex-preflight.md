# Codex Stage 1 preflight evidence

Date: 2026-10-10 (Asia/Kolkata). Overall status: **in progress**. No Codex adapter is installed or accepted.

- Existing baseline: `.venv/bin/python -m pytest -q` with loopback access: **345 passed, 1 deselected in 80.57 s**. The sandboxed attempt failed on temporary socket binds; this was an environment restriction, not a code regression.
- Stage-0 drift check: **34 final file blocks and 18 stub blocks match literal bytes in the repo**.
- Desktop runtime: **0.162.0-alpha.2**, distinct from Homebrew CLI **0.155.1**. Desktop protocol schema exported offline to `/private/tmp/laya-codex-desktop-schema`.
- Native isolated preflight: quoted commands, timeout 8/3 seconds and exact-definition trust recognized. No real configuration or credentials used. OS sandbox denied external network, including attempted runtime websocket prewarm. No model request submitted.
- Neither thread/start nor debug prompt-input ran the configured hooks. They cannot establish warning rendering, payload delivery or model-context separation. Those checks remain pending a live synthetic turn.
- Temporary probe script: direct SessionStart emits nothing/exit 0; prompt emits exactly the fixed JSON systemMessage/exit 0; malformed JSON emits nothing/exit 0; stderr empty. Metadata capture omits synthetic prompt text and is mode 0600 in a 0700 directory. Direct execution establishes the script contract only, not native hook behavior.
- Exact script and installation draft are recorded in `docs/superpowers/plans/2026-10-10-laya-harness-codex-preflight.md`. Both plan blocks match executed workbench files byte for byte.

The user approved both direction and exact temporary draft. Project `.codex/hooks.json` is installed byte-identically and verified mode 0600. At installation, capture and native trust review were pending; the subsequent observations below supersede that state. Read-only app-bundle inspection confirms Settings → Hooks, Reload hooks, project sources and trust controls. Claude acceptance remains deferred until its weekly limit replenishes; no pending Claude gate is marked passed or waived.

## First live synthetic turn

User supplied `Screenshot 2026-10-10 at 9.42.06 AM.png`. It shows the synthetic 40-character prompt and successful reply `hook check complete.`, with no inline probe warning visible. Metadata capture confirms SessionStart and UserPromptSubmit executed in session `01a12402-8b93-7fb3-a041-51127b7634f3`, turn `01a12402-938f-79d2-927e-afe70a4bd8ab`, active model `gpt-6.1-sol`, permission mode `default`. SessionStart source was `startup`; prompt input had no source or agent fields. The project hook definitions match the approved draft, and both exact native trust hashes are recorded.

Read-only inspection of the installed app's `local-conversation-turn`, `user-message` and `hook-stats-dialog` bundles shows hook warning entries are collected in Hook stats, opened through the hook-shaped message action icon. The dialog labels warning entries as Message. The screenshot establishes successful execution but not message delivery inside that panel. Expanded UserPromptSubmit history is the next capture; no additional prompt is needed for this display check.

The sentinel is absent from the persisted rollout. This alone does not prove absence from model input. Context-separation evidence remains pending. Automatic inline visibility is not established; Stage 1 copy/mockups must reflect the actual native surface rather than assuming Claude's banner behavior.

## Expanded Hook stats capture

The user supplied `Screenshot 2026-10-10 at 9.49.42 AM.png`: Runs 2, Blocked 0, Failed 0; Completed UserPromptSubmit / Project; Message `laya · Codex hook check (temporary probe)`. The separate Stop / Plugin entry is unrelated. Native execution and user-side warning delivery are confirmed. The supported surface requires opening Hook stats; no inline banner is claimed. Official systemMessage semantics and rollout sentinel absence support context separation, while direct model-input auditing remains a limitation. This is preflight evidence, not production adapter acceptance.
