# Codex native failure/off acceptance — 2026-10-11

Contract: Codex C7/C8 and macOS launch/background-activity contract. Controller-only live acceptance; no product implementation. Preserve real config, production hooks, background permission and weights. No downloads/login settings/unrelated jobs/source edits/push.

## Executed preflight

Existing nonresponsive/off subprocess checks:4passed26deselected3.27s. Actual named test_failed_load_same_process_across_native_prompts separately:1passed0.30s. Existing reviewed timing wrapper tests:18passed1.80s. No new timing implementation. Controller failure_preflight.py exercised actual missing-directory predictor in temporary home/freeport: three silent/exit0/not_ready hooks68.620/52.142/49.155ms, samePID/no spawn. Off: two silent/exit0 hooks46.418/45.815ms, no rows/sessionchanges/spawn. Existing tests/test_client_process.Listener(port,hang):1433.002ms, timeout row/no spawn. No weights/downloads; missing checks fail before model import. All temporary services/listeners cleaned. Private preflight-observed.json.

## Prepared exact artifacts

.workbench/codex-failure-acceptance directory0700, drafts/diffs0600: off.config.json/diff changes only modeoff; missing.config.json/diff changes only model_dir to a nonexistent private/tmp pathname; nonresponsive.config.json/diff changes only port to64972 (never47913/liveport). real.config.json is exact rollback. hooks.draft.json/hooks.diff reuse independently reviewed timing two-command replacement, same8/3timeouts; hooks.production.json exactrollback. Native Reload hooks/trust required after install/restore.

## Approval and sequence

Approve the three exact config diffs, timing-hook diff and restorations, at most five health-verified service stops, plus one controller-owned temporary hang listener on the drafted port. If occupied, no takeover: prepare another draft. Reuse existing tested Listener class, bind127.0.0.1, hard600s lifetime; cleanup only its controller-owned PID. No native test flag/homeoverride and no stop command against foreign listener.

1. Stop1 before timing hooks install; retain real config. User Reload/review, fresh chat `Reply with just: down check ready.` Controller verifies readyPID/jobruns.
2. Stop2 after that SessionStart; immediate offsets/runbaseline. User SAMEchat `Reply with just: down check.` CaptureUPS/noMessage and completedreply. Require one started_service row, one jobrun increase/newPID and ready afterUPSexit. Then user Cmd+Q/reopenwithin2min with backgroundenabled; samePID/readiness required. Controller followups are separate rows.
3. Stop3 before missingconfig. Freshchat sends three numbered missingcheck prompts. Require no messages, not_ready rows, samePID/jobruns and no repeatloads, zero blocked/failed and completedreplies. Do not create missing directory.
4. Stop4 before offconfig; record decisionbytes/sessionJSON hashes/jobruns. Freshchat sends two numbered offcheck prompts. Require no rows/sessionupdates/spawn/messages and completedreplies; instrumentation receipts/private diagnostics are allowed.
5. Stop5 (may already be down) before nonresponsiveconfig. Bind controlledlistener first; verify then install draft. Freshchat listenercheck prompt: silent timeout row, advisor-child≤1.6s, no jobrun increase/spawn, completedreply/zero blocked/failed. If listener cap expires or cannotbind, capture invalid.
6. Close only controlledlistener; verifyrefusal. Restore exactrealconfig0600 and productionhooks0600; no service should remain from off/listener phases. Unexpectedownservice must not exceed stopapproval. User Reload/review restoration. Save hashes/state.

Timing wrapper receipts measure advisor-child launchthroughtermination, not native scheduler overhead. Existing20turn sample not repeated; aggregate Hook stats evidence remains separatelyrequired. Preflight does not pass nativegates. Claude acceptance deferred.
