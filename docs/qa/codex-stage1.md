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

## Approved timing hook installation — 2026-10-10

The user approved the exact timing diff. Controller stopped service pid 64572 (exit 0), verified the live hooks still matched the reviewed production rollback, and atomically installed `.workbench/codex-timing/hooks.draft.json` byte-identically into project `.codex/hooks.json`, mode 0600. Real configuration SHA256 remains `1a1f5b7c451aa559684d35a587e914f0269dfd8979c40162171f41a06001170f`; no config/model change or download. Timing hooks hash `b7987033a3fca3aa841f88c399c418a591c64b10d4a9afade160f63dc324bc46`. Private baseline `.workbench/codex-timing/native-baseline.json` at 2026-10-10T12:34:51.273813Z records decisions 24224 bytes, client 304 bytes, service 1370 bytes, receipts zero bytes. The production definitions remain preserved for restoration. Native Reload hooks/review trust and the 20-human-turn capture are now user steps; no native timing gate is claimed from installation.

## Twenty manual timing turns and restoration — 2026-10-10

Session `01a125d2-7003-7203-a31d-929833714887` has all numbered prompts 1–20, each one unique turn/decision row and one unambiguous UserPromptSubmit receipt. Persisted native rollout contains 20 task_started and 20 task_complete events, matching all sample turn IDs and expected numbered replies, with no error/turn_aborted events. All 20 advisor children exited 0, zero instrumentation timeouts; durations min **181.374 ms**, median **512.706 ms**, nearest-rank p95 **682.976 ms**, max **690.045 ms**. These are launch-through-exit advisor durations, excluding wrapper overhead (synthetic preflight about 28–30 ms), not native whole-wrapper receipts. The measured advisor timing sample is within C7's approximately 1.6-second bound; aggregate native Hook stats blocked/failed/timeout-notice counts have not been captured for all 20, so do not claim the entire native UI/no-harm gate closed from receipts alone.

Nineteen sample rows are decided with real checkpoint provenance; prompt 2 is started_service/cold true. Prompt 1 ran at 12:38Z, prompt 2 at 14:37Z, a nearly two-hour gap longer than the 900-second idle timeout. That local service restart is expected fail-open behavior, not a hook failure. Only first prompt logged a model hint (light p=.94 → GPT-6 Luna at low effort); remaining decided prompts suppressed model as not_first_prompt and plan below_threshold. Client log gained zero bytes during this sample; service gained 1370 bytes containing two temperature-warning/settings load diagnostics and no predict/load failures. Config/hook hashes matched the baseline throughout. Reduced sample evidence `.workbench/codex-timing/native-observed.json`.

After analysis, controller stopped pid 67082 and restored the exact saved production definitions byte-identically, mode 0600; real configuration unchanged. The user then reported a credit-limit interruption and reran prompt 2. Preserve this as an additional turn, not a replacement: turn `01a12644-5417-7ad0-b666-5d2425d09758`, 14:42:54Z, started_service/cold true, row 60.2 ms, receipt 130.182 ms, exit0/no timeout. This second restart follows the controller's explicit stop for restoration. Codex credit interruption is user-reported and distinct from local hook outcomes. Receipts still arrive after file restoration because the native runtime retains the loaded timing definitions until Reload hooks; user reload/review is pending. A controller follow-up receipt was 1461.736 ms, exit0/no timeout, outside the numbered sample. Earlier latency variability is not erased by the faster short-prompt sample. Cold/down/off/fake-state/survival and Claude acceptance gates remain open.

## Authorized three-round cold capture — round 1 prepared

The user approved three service stops and reuse of the unchanged reviewed timing hooks, with real configuration retained and production restoration afterward. Round 1: stopped pid 70129, installed exact timing draft privately, verified config byte-identical to `.workbench/codex-timing/cold-config-before.json`, final status down/show/pinned checkpoint. Baseline `.workbench/codex-timing/cold-round-1-baseline.json` at 2026-10-10T15:27:34.335982Z: decisions 87233 bytes, client304, service4110, receipts3069. Native reload/review and fresh-chat cold check 1 are pending. Rounds 2–3 stops remain authorized; do not ask again. Capture/close-chat survival observations and first-profile proportion remain unmeasured. No config/code/model changes or downloads.

## Cold round 1 observed; round 2 prepared

Round 1 screenshot (21:03:03 local): Runs6/Blocked0/Failed0, completed project SS/UPS, exact real light p=.91 → GPT-6 Luna low line. Session `01a12671-b407-79e0-8174-c7c6724be2ff`, turn `01a12671-c204-7682-b5d8-cd9dd58da8b6`: decided/real, row292.1ms, first profile available. SS advisor-child3058.208ms; UPS343.994ms, both exit0/no timeout, within respective4.6s/1.6s bounds (wrapper overhead separately established). Health after user returned ready/real pid70902. No new client diagnostics; service685-byte calibration/settings load output. Config/hook hashes unchanged. Explicit chat closure was not confirmed in the screenshot message, so post-closure survival remains unconfirmed; readiness after return is observed. Reduced evidence `.workbench/codex-timing/cold-round-1-observed.json`.

Under existing three-stop approval, controller stopped pid70902 and prepared round2 baseline at15:34:01.759728Z: decisions92723/client304/service4795/receipts3435. Status down; timing hooks and real/show config unchanged. User next opens a fresh project chat and sends cold check2, captures expanded SS/UPS and closes the chat. Round3 stop remains authorized. No reload needed because definitions have not changed since round1.

## Cold round 2 observed; round 3 prepared

Round2 screenshot (21:05:59 local): Runs6/Blocked0/Failed0, completed project SS/UPS, real light p=.89 → GPT-6 Luna low. Session `01a12674-54bd-7e22-964d-903562ec1922`, turn `01a12674-5aa0-7132-b1fd-9778bce4a6e8`, decided/real, row260.2ms. SS advisor-child3079.945ms/UPS292.803ms, exit0/no timeout, within bounds; healthready real pid71608 after return. First-profile availability2/2 so far. Client0/service685 additional bytes (load diagnostics). Explicit chat closure still unconfirmed. Reduced cold-round-2-observed.json. Initial observation extraction assumed exact prompt punctuation and found no match; corrected extraction uses the observed unique turn ID and timestamp-correlated receipts, without changing runtime data.

Performed approved stop3 pid71608. Round3 baseline at15:36:50.563657Z: decisions98207/client304/service5480/receipts3802. Final status down; unchanged real/show config and timing hooks. Next fresh project chat cold check3, screenshot, closechat/confirm closure. No reload needed. The three authorized cold stops are now consumed; restore production hooks after this capture per phase authorization.

## Cold round 3 and three-round summary

Round3 screenshot21:08:30 local: Runs6/Blocked0/Failed0, completed project SS/UPS, exact real light p=.90 → GPT-6 Luna low. Session `01a12676-0830-76f3-95ea-33cc520ca13e`, turn `01a12676-8815-7fb0-8b17-c8495a6b3a42`, decided/real, row386.8ms. SS advisor-child3280.186ms/UPS451.404ms, exit0/no timeout. Service ready/real pid72336 after return. Controller screenshot follow-up separately timed out (row1404.8ms; child1435.189ms), outside the cold synthetic sample, preserving the latency-variability finding. Client growth76/service685 bytes. Config/hook hashes unchanged during capture.

Across3 cold rounds: SS3058.208/3079.945/3280.186ms, UPS343.994/292.803/451.404ms; first profiles decided3/3, missed proportion0/3. Screenshots zero blocked/failed each. All measured advisor-child durations within C7 bounds; wrapper overhead remains separately measured. Private cold-summary.json and cold-round-3-observed.json record reduced evidence. Exact production definitions restored0600 after capture, without another stop or configuration change. Native reload/review pending.

User asked whether closing means navigation or archival. Controller's prior wording was ambiguous: neither action establishes actual session/host termination. Do not require archival or infer survival from it. C7 session-exit survival remains unverified; this is a specification operationalization gap, not a product failure. Proposed stronger observation: user quits Codex and reopens within5minutes, controller checks same ready PID72336 against private survival-before-app-exit.json. This must not be claimed from merely changing chats or seeing an unrelated Stop plugin entry. The service remains running for this observation; no app exit has occurred yet.

## Quit/reopen survival observation — changed PID

The user confirmed completing reload, Cmd+Q and reopen. Before: real ready pid72336, baseline15:41:22.789156Z. After: real ready pid73868, process start21:19:17 local, PPID1; old PID absent. The return prompt at15:49:17Z logged loading/cold true,76.8ms. At diagnostic15:49:43Z, elapsed500.775s from baseline is shorter than900-second configured idle timeout, though longer than the requested5-minute return interval. Production hooks match the saved definitions. No applicable new crash diagnostic or service-log exit reason was found; calibration/settings output records the new load. No stop/config/source change was performed after round3 restoration.

**Survival is not established; the changed PID is an unresolved acceptance finding.** Do not attribute it to idle timeout, desktop cleanup, native crash or memory pressure without evidence. Private survival-after-app-exit.json preserves observations. A controlled immediate repeat is prepared in survival-repeat-before.json (pid73868); user quit/reopen within2minutes, then controller compares PID. This distinguishes reproducibility before proposing any docs-first implementation fix. Cold timing/first-profile results remain valid; session-exit survival and remaining down/off/display/Claude gates stay open.

## Survival repeat — inconclusive elapsed interval

On user “try now”, baseline pid73868 from15:50:38Z was2258.2seconds old (about38minutes), longer than configured900-second idle timeout. Live service readyreal pid75456; returnprompt loading/coldtrue72.5ms. This PID change cannot distinguish app-exit loss from expected idle shutdown. Preserve as inconclusive, not a reproduced survival failure or a pass. First changed-PID observation inside the idle interval remains unresolved. Reduced survival-repeat-after.json. No source/config/service changes made. Refresh the baseline immediately before the next user quit/reopen; return within2minutes to avoid this ambiguity.

## Immediate survival repeat — reproduced failure

Fresh baseline pid75456 at16:29:09.622287Z; user quit/reopened and returned at16:31:52Z. At first check elapsed179.6s, well within idle900s. Current readyreal pid76365; old PID absent. Returnprompt turn `01a126a8-0d25-7f52-b1c5-de5f3cf7f44a` loading/coldtrue132.1ms. This reproduces the same-process survival failure from the first inside-idle attempt; do not request more uninstrumented repetitions. Reduced survival-repeat-2-after.json. C7 shutdown-survival acceptance remains failed/unresolved; implementation acceptance cannot close.

Read-only investigation: current service PPID1/PGID76365, consistent with existing start_new_session detachment. OS IPC logs place old service disconnection22:00:39.812 local; desktop runtime logged stop_process16:30:37.845Z and launchd logged Codex exit0 at22:00:38.674 local. Temporal association establishes the quit boundary, not the killer/signal. No matching recent crash report, no service-specific launchd/runningboard/kernel termination record; root-only launchctl procinfo unavailable and no root access attempted. Installed application code has process cleanup paths, but none was proven to terminate this orphaned service. Local launchd.plist man page says default job cleanup targets the job's process group; service's separate PGID means that generic mechanism alone is not a proven explanation. Root cause remains unconfirmed; do not propose another setsid/nohup tweak or a launchd workaround without isolated behavioral evidence. No implementation, live config, hook or service changes during this investigation. Existing cold timings and fail-open results remain valid independently.


## Service-exit diagnostic preflight (2026-10-10)

C7 survival remains failed/reproduced inside the idle window; no root cause is claimed. User authorized targeted diagnostics. C9 spec committed a51f2b7; review-test clarification0993116; generated verified plan5765c62. Local bootstrap/test files only: initial behavioral stub19failed; corrected controller25passed7.20s, independent reviewer25passed7.29s **APPROVED**. Five scratch mutations prove exact copy/answers/suggestion/provenance/UPS routing sensitivity. Visual review N/A. Stage1 16 final blocks, timing2 and diagnostic2 remain byte-identical.

Exact private draft `.workbench/codex-exit-diagnostic/hooks.draft.json` (SHA256 e379e53682a78c73f65b68737418d72a05f8f7705466048341bba238e592f7c2) and `hooks.diff` change only SS/UPS commands, preserving timeout8/3 and unrelated contents; production rollback `hooks.production.json` preserved. Draft/rollback0600, directory0700. Not installed; no live stop/config changes. Next: user approves exactdiff plus one additional real service stop, then native reload/trust and one instrumented startup/quit/reopen. Original three cold-stop authorizations exhausted. Restoration after analysis requires authorized ordinary startup. SIGKILL/native-abort attribution unavailable; missing receipt is not cause evidence. Shipping implementation uncommitted; no push; Claude acceptance deferred.


### Exit diagnostic installed, awaiting native reload/startup

User approved exact diagnostic hook diff and one extra real-service stop. Exact draft installed byte-identically in `.codex/hooks.json`0600; service76365 stopped exit0. Real config remains byte-identical to saved real draft; statusdown. Private `.workbench/codex-exit-diagnostic/native-baseline.json` records file offsets and hashes. That stop approval is consumed; no diagnostic outcome yet. Next user Reload hooks/review native trust, fresh project chat `Reply with just: exit diagnostic ready.`, capture Hook stats, return here before quitting so controller can verify instrumented ready PID and save immediate pre-exit baseline. Then one Cmd+Q/reopen within2min; analyze receipts and restore exact production definitions outside capture. No extra controller prompt before fresh startup. No shipping edits/commit/push; Claude acceptance deferred.


### Exit diagnostic native startup confirmed

User screenshot (2026-10-10 22:34:30 local) shows Runs6/Blocked0/Failed0, completed project SS/UPS, exact real output `laya · light task (p=0.88) → GPT-6.1 Sol at medium effort fits this task`. Matching fresh-chat row turn01a126c5-7151-7712-8640-c50e02213265 is decided/real, warm604.1ms. Instrument start receipt PID79058/initialPPID79053/PGID79058/SID79058 at17:03:59.177224Z. Healthready/real, ps confirmsPPID1/ownPGID andbootstrap service command. Config/hooks hashes unchanged. Clientgrowth0; servicegrowth685bytes from startup. Reduced startup-observed.json. Controller first queried wrong /health endpoint (404), corrected /v1/health; no state mutation. Next immediate private before-app-exit.json then user Cmd+Q/reopenwithin2min, returnhere for receipt/PID comparison. No extra service stop authorized/needed. Survival still pending diagnostic result.


### Exit diagnostic: SIGTERM captured; production definitions restored

User completed Cmd+Q/reopen; check at17:08:00.310Z was69.758s after baseline, inside900s idle. PID79058 receipt records **SIGTERM** at17:07:08.070209Z; oldPID absent, replacement80121 ready/real/PPID1/ownPGID. Returnturn01a126c8-d17c-7d20-a77c-6509ec9267c4 logged loading54.6ms/coldtrue thenready. No normal_exit/exception receipt for79058. Realconfig and diagnostic hooks unchanged during capture. Desktop stop_process17:07:06.200Z, launchd appinactive22:37:06.892local, serviceSIGTERM ~1.9s later. Evidence establishes signal termination correlated with desktop exit, **not signal sender or exact cleanup mechanism**; native process-tree code search does not establish causation. C7 survival remains failed. Private after-app-exit.json records reduced evidence/timeline.

Exact production hooks restored byte-identically0600 after capture, no additionalstop/configchange. User native Reload hooks/review now needed. PID80121 is still the diagnostic bootstrap service (unchanged service.main); restoring definitions does not restart it. One approved stop consumed; no extra stop/start authorized. Leave it until ordinary idle exit or request authorization for concrete ordinary restart. Next investigate sender/cleanup mechanism with isolated evidence before productionfix; no more uninstrumented quit repetitions. Shipping implementation uncommitted, no push; Claude acceptance deferred.


### Exit signal sender identified; production reload confirmed

User confirmed native reload of restored production hooks; disk remains byte-identical to preserved production definitions. Read-only OS-log query with --info --debug over22:37:05–22:37:10local identified **loginwindow LaunchServices coalition cleanup**: appdeath lists79058/Python among non-application coalitionPIDs; `_LSForceQuitApplication` records `killing coalition pid 79058` and `killPID: pid=79058/<private> hard=NO succeeded` at22:37:08.046, immediately before instrumentSIGTERM17:07:08.070Z. This establishes the terminating actor/mechanism, replacing prior attribution limitation. Source processgroupdetachment remainscorrect butdoesnotremoveapplicationcoalitionmembership. Filtered sender-evidence.log and updated after-app-exit.json private. No persistentOSsettings/jobs, code/configchanges, or extra stop. PID80121 instrumentedservice leftrunning; ordinary productionhooks nowloaded.

Next productionfix must establish OS-owned service launch outside desktopcoalition, with controlled isolated lifecycle/cleanup evidence beforepromotion; no speculative setsid/nohup/SIGTERM-ignore fix. C9 diagnostic scope forbids persistentlaunchd/OSsettings, so any new launch mechanism requires a separate docs-first contract/workbench pass and authorization before live OS changes. C7survivalstillfaileduntilpostfixnativecheck. Implementationuncommitted/no push; Claudegatesdeferred.


### Post-fix native survival: background activity comparison (2026-10-11)

The promoted launchd broker passed repo gates (534 fake tests and cached real-model gate). First native quit/reopen with ChatGPT background activity disabled changedPID90998→91932 within197.549s; loginwindow explicitly unloaded the exact job because it was not managed by BTM. After the user enabled background activity, a controlled quit/reopen with unchanged code/hooks/config retainedPID91932 ready/real after90.881s, samejob/runs1. C7 survival passed for the enabled configuration, with the disabled-setting limitation preserved. Private macos-launch/background-enabled-before.json and background-enabled-after.json. Remaining native acceptance gates and Claude acceptance are not inferred from this result.


### Remaining display preparation (2026-10-11)

Background dependency is now documented in launch/umbrella/Codex contracts and README (80af706). Four private fake configuration drafts plus exact real rollback/diffs are prepared under .workbench/codex-remaining; isolated controller preflight passed exact light/heavy/plan-only/silent copy, exit0/empty stderr and one decided fake row each. Native screenshots not inferred. Live config remains real/show; next exact batch review authorizes five stops/config transitions and user fresh-chat captures. Plan: 2026-10-11-laya-harness-codex-remaining-acceptance.md.


Remaining display batch approved (2026-10-11): all four exact fake drafts and real restoration, with five health-verified stops. Stop1 PID91932 exit0; light draft installed0600/byte-identical, confirmed down, productionhooks unchanged. Light baseline decisions142009/client760/service12330/launcher0bytes. Native light capture pending; four remaining stops already authorized. No result inferred from isolated preflight.


Light native display passed (2026-10-11): screenshot09:51:40 showsRuns6/Blocked0/Failed0, completedprojectSS/UPS, exact lightp.86→GPT-6Lunalow only. Independent visualreview APPROVED, legible singleline. Matched turn01a12931-6b93-7720-9149-acb0eeb2c701/session01a12931-6751-7b70-9db0-0ea96b1b4feb, decided/fake, row31.8ms/coldfalse, no newclient/service/launcherdiagnostics. First matching check expected no trailing newline; normalized strip and matchedunique displaycheck row. AnotherfreshREADMEprompt and controllerfollowup are separate rows, notduplicatecapture. Reduced light-observed.json.

Approved stop2 PID94777 exit0; heavy draft installed0600/byte-identical, confirmeddown. Heavy baseline decisions149088/client760/service12330/launcher0bytes; hooksunchanged. Nativeheavycapturepending; threeapprovedstopsremain forplan-only/silent/realrestore.


Heavy native display passed (2026-10-11): screenshot09:55:21 showsRuns6/Blocked0/Failed0, completedprojectSS/UPS, exact heavyp.91→GPT-6Astra xhigh only. Independent visualreview APPROVED, legible singleline. Unique displaycheck turn01a12934-fa64-70d1-b0d8-7df0ae4720b5/session01a12934-f651-7143-8cb4-6d1235d3de26, decided/fake, row35.3ms/coldfalse. Client/service/launcherdiagnosticgrowth0. Otherthreebaseline rows are outside theunique capture. Reducedheavy-observed.json.

Approvedstop3 PID95869 exit0; plan-onlydraft installed0600/byte-identical, confirmeddown. Baseline decisions157626/client760/service12330/launcher0bytes, hooksunchanged. Nativeplan-onlycapturepending; twoapprovedstopsremain silent/realrestore.


Plan-only native display passed (2026-10-11): screenshot09:59:07 showsRuns6/Blocked0/Failed0, completedprojectSS/UPS, exact planp.88→Plan mode(/plan), or tellCodex toplanfirst only. Independent visualreview APPROVED, legible singleline/no clipping. Unique turn01a12937-38bb-7bd0-95b6-f1d932ec0549/session01a12937-33e8-74f1-9b9c-bea73e1e9a32, decided/fake, row48.3ms/coldfalse; modelbelow_threshold/planunsuppressed. Client/service/launcherdiagnosticgrowth0; threeotherrows outsidecapture. Reducedplan-only-observed.json.

Approvedstop4 PID96483 exit0; silentdraft installed0600/byte-identical, confirmeddown. Baseline decisions166317/client760/service12330/launcher0bytes, hooksunchanged. Nativesilentcapturepending; finalapprovedstop remains for exactrealrestore.


Silent native display passed (2026-10-11): screenshot10:00:51 showsRuns6/Blocked0/Failed0, completedprojectSS/UPS with noMessage. Independent visualreview APPROVED. Unique displaycheck turn01a1293a-062b-7690-b178-fdf725900e51/session01a12939-fd1f-7ba0-96d3-1b0c2396e62e, decided/fake, row31.9ms/coldfalse, shown_textnull, model/plan bothbelow_threshold. Client/service/launcherdiagnosticgrowth0; onecontrollerfollowup outsidecapture. Reducedsilent-observed.json.

Approvedstop5 PID97641 exit0; exactsavedrealconfiguration restoredatomically0600, model_modereal/modeshow/fake_answersremoved, confirmeddown. ConfigSHA1a1f5b7c451aa559684d35a587e914f0269dfd8979c40162171f41a06001170f; hooksunchangedSHAeb44c8089814b2afc08b0b308fd70e0c6751cb251d6978b78d22325494af5591. Allfivebatchstopauthorizationsconsumed. Private real-restored.json.

## Current acceptance checklist (2026-10-11)

| Gate | Current evidence |
|---|---|
| Fixed light/heavy/plan-only/both/silent copy and native visual states | Passed, independent visual approval and matching decided/fake rows. |
| Real prediction | Observed decided/real; latency variability retained. |
| Three cold startup samples | Recorded3/3 first decided profiles and bounded child durations; before launch ownership change. New broker real SessionStart observed2801.698ms. |
| Quit/reopen survival | Passed with user-enabled ChatGPT background activity; disabled-setting teardown limitation recorded in contract. |
| Twenty human turns | Timing/exit0/completion sample passed; aggregate native Hook stats evidence still pending. |
| Native down/missing-model/nonresponsive/off | Pending. Isolated fake tests do not substitute native evidence. |
| Claude acceptance | Deferred independently. |

No final acceptance, implementation commit or push is inferred.


### Native failure/off protocol prepared (2026-10-11)

Existing failure/off tests4passed, missing-load test1passed, timingwrapper18passed. Controlleractualmissing/off/hangpreflightpassed temporaryhomes/freeports withsilence/exit0/samePIDnot_ready/nooffmutations/boundedtimeoutnospawn. Shipping3launch+16Stage1blocks and2timingblocks unchanged. Plan2026-10-11-laya-harness-codex-failure-acceptance.md records reviewedtoolreuse/protocol. Private drafts/diffs/rollback under .workbench/codex-failure-acceptance: off, missing, nonresponsiveport64972, existingtiminghookdiff. Liveconfig/hooksunchanged. Nextuserexactbatchapproval coversatmostfivehealth-verifiedstops, threeconfigs/restorations, timinghooks/restoration andownedtemporarylistener; thenusernativeReload/startup/down/missing3/off2/listener1captures. Aggregate20Hookstatsevidence separate; Claude deferred; implementationuncommitted/nopush.


### Failure/off batch approved; timing hooks installed awaiting reload

User explicitlyapproved protocol/drafts/timinghooks/restorations/atmostfivestops andownedtemporarylistener. Stop1 consumedPID99617 exit0; exacttimingdraft installedatomically0600, SHA b7987033a3fca3aa841f88c399c418a591c64b10d4a9afade160f63dc324bc46. Realconfigbyte-identical unchangedSHA1a1f5b7c451aa559684d35a587e914f0269dfd8979c40162171f41a06001170f. Privatebatch-start-baseline.json: decisions173464/client760/service13700/launcher0/receipts4169bytes. Fourapprovedstopsremain; exactconfigs/rollback/timingproductionhooks preserved.

Nextuser Settings→Hooks Reload/review, freshprojectchat `Reply with just: down check ready.` and screenshotprojectSS/UPS. Controllerverify readyPID/jobruns/matchingrow+receipts then approvedstop2; userreturns SAMEfreshchat for downcheckprompt, no interveningcontrolleruserprompt thatcouldrestartservice. No failureconfiginstalledyet/listenerstartedyet. No repeatedapprovalquestionforbatch. Shippingimplementationuncommitted/nopush; Claudegatesdeferred.
