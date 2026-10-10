# Codex Stage 1 preflight evidence

Date: 2026-10-10 (Asia/Kolkata). Overall status: **in progress**. No Codex adapter is installed or accepted.

- Existing baseline: `.venv/bin/python -m pytest -q` with loopback access: **345 passed, 1 deselected in 80.57 s**. The sandboxed attempt failed on temporary socket binds; this was an environment restriction, not a code regression.
- Stage-0 drift check: **34 final file blocks and 18 stub blocks match literal bytes in the repo**.
- Desktop runtime: **0.162.0-alpha.2**, distinct from Homebrew CLI **0.155.1**. Desktop protocol schema exported offline to `/private/tmp/laya-codex-desktop-schema`.
- Native isolated preflight: quoted commands, timeout 8/3 seconds and exact-definition trust recognized. No real configuration or credentials used. OS sandbox denied external network, including attempted runtime websocket prewarm. No model request submitted.
- Neither thread/start nor debug prompt-input ran the configured hooks. They cannot establish warning rendering, payload delivery or model-context separation. Those checks remain pending a live synthetic turn.
- Temporary probe script: direct SessionStart emits nothing/exit 0; prompt emits exactly the fixed JSON systemMessage/exit 0; malformed JSON emits nothing/exit 0; stderr empty. Metadata capture omits synthetic prompt text and is mode 0600 in a 0700 directory. Direct execution establishes the script contract only, not native hook behavior.
- Exact script and installation draft are recorded in `docs/superpowers/plans/2026-10-10-laya-harness-codex-preflight.md`. Both plan blocks match executed workbench files byte for byte.

Project probe installation awaits user approval. No `.codex/hooks.json` has been created. Claude acceptance remains deferred until its weekly limit replenishes; no pending Claude gate is marked passed or waived.
