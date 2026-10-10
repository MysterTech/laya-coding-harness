# macOS service launch — coalition-survival fix design

Status: user approved design and isolated temporary-job tests. Production promotion/live changes remain separately reviewed.
Contract parents: umbrella design §4.2–§4.4, §5–§6, §8, §11; Codex design C1–C9. Purpose: repair native desktop shutdown survival without changing residency policy, classifier behavior or hook deadlines.

## Evidence and intended result

The instrumented service79058 had PPID1, its own process group/session and the ordinary venv interpreter. macOS loginwindow nevertheless retained it in Codex's application coalition and explicitly killed that coalition PID on desktop quit. Its SIGTERM receipt at17:07:08.070209Z matches loginwindow's killPID record at22:37:08.046local. Evidence: private `.workbench/codex-exit-diagnostic/after-app-exit.json` and `sender-evidence.log`; public QA narrative `docs/qa/codex-stage1.md`.

Success means the service is started only after connection refusal, reaches ready after its launching hook exits, survives Codex quitting, and still exits after900idle seconds. It must remain stoppable by the existing health-identified stop command. No restart follows a model failure, timeout, loading/not_ready reply, or desktop exit. User-only advice and local logs stay unchanged.

## Selected approach and alternatives

Use a per-user, on-demand launchd job for macOS production service launch. Register a private definition explicitly with `/bin/launchctl bootstrap gui/<uid> <definition>`, then request execution with `kickstart` without `-k`. launchd starts the service outside the desktop application's coalition. This last ownership/survival claim must be proved by isolated native preflight, then real acceptance; it is not inferred from documentation.

Do not use legacy submit: the installed launchctl manual says it keeps the program alive on failure. Do not put files in `~/Library/LaunchAgents`, enable login startup, set KeepAlive, or install a LaunchDaemon. A native responsibility-disclaim helper would add platform-specific compiled/private-API machinery; it is not selected. Repeated setsid/double-fork alone does not address the observed coalition membership. Ignoring SIGTERM would undermine explicit stop and is not a fix.

This advances only launch ownership from §11's deferred launchd question. The idle-timeout/resident-service policy remains deferred;900seconds and the memory footprint stay unchanged. Umbrella §4.3's literal Popen recipe must be amended before production promotion; the surrounding fail-open/refused-only rules remain binding.

## Launch and lifecycle requirements

The hook remains standard library only. It asynchronously starts a short-lived launcher using the configured absolute venv interpreter, isolated mode and no inherited stdin/stdout; that launcher registers/starts the launchd job. It never loads the predictor. The launcher's finite timeouts and private diagnostics must not extend the original hook watchdog or SS readiness wait. The job runs the same interpreter with `-I -m laya_harness.service`, private cwd, stdin/stdoutdevnull and stderrservice.log0600. No prompt bytes enter argv, plist, environment or launcher logs.

Definitions live inside the0700laya state directory, file0600, outside automatic LaunchAgents discovery. KeepAlive and RunAtLoad are false; no sockets, MachServices, timers, filesystem watch paths or restart trigger. launchd must not restart after idle exit, model errors, unexpected failure or explicit stop. A later refused connection is the only trigger for another execution. No automatic launch occurs at login/reboot.

Use an application-specific job label scoped to user/state/interpreter identity. Concurrent launchers must converge on the same immutable definition; an already-running service must never be killed/replaced. No kickstart-k, domain-wide bootout, enable/disable, signal ignore or global OS state changes. Identify and validate the expected job before reusing it; do not take over unrelated jobs. Definition/label identity, atomic private writes, registration-error handling and cleanup are finalized from executed preflight before literal production plan generation. Until these empirical details are resolved, this is a design contract, not executable plan code.

If launchd is unavailable or rejects registration/start, fail open with bounded private diagnostics. Do not silently fall back to the known broken macOS desktop launch. Non-macOS and ordinary fake subprocess fixtures retain the existing Popen path. Dedicated macOS launchd tests are separately marked/gated; a passing fake suite does not imply native launch ownership. Test flags/home overrides must be passed only in dedicated isolated preflight; no access to real home or standardport47913.

Existing stop still verifies the bound application's health identity and PID before SIGTERM; no launchd auto-restart can undo it. Model configuration is unchanged. Stale inactive registration cleanup must target only the verified owned label and must not interrupt a live request; the preflight must determine a minimal bounded lifecycle before implementation is promoted.

## Isolated preflight before production coding

Prepare workbench-only tooling and requirement-derived tests, then independently review it under the two-agent workflow. Generate literal blocks only from executed files. Start with actual behavioral RED for routing, deadlines, private definition contents, identity/collision checks, concurrency and failure handling. No shipping source edits yet.

A separately authorized controller gate may create a uniquely named temporary per-user launchd job pointing exclusively at a temporary LAYA_HARNESS_HOME, CODEX_HOME and free port with fake predictor. No real model or real-home state. Record exact definition/command, job/PID ownership, hook-process completion, one fake decided row, normal idle exit, no automatic restart after idle/failure/stop, and refused-only subsequent start. Exercise concurrent bootstrap/kickstart and paths with spaces. Always bootout only that exact temporary job and remove only its temporary files; verify cleanup even after failure. No user LaunchAgents or persistent enable/disable changes.

If the native gate cannot establish coalition independence without quitting the desktop, report that limit and prepare one reviewed controlled acceptance capture; do not substitute PPID1/process-group evidence, since the failed launch already had both. No new quit/reopen request until the proposed mechanism and instrumentation are reviewable.

After preflight, update umbrella §4.3/§6/§11 and Codex supplements with verified lifecycle details and the gate profile. Commit those docs and the generated production plan first. Implement through workbench RED/GREEN and independent contract review. Check all plan-block bytes, full Claude/Codex fake regression suite and controller-only cached real-model gate.

## Native promotion and acceptance

Show the concrete hook/service/config/OS-job diff before live changes. Native trust stays user-controlled. Live service stops, job registration/removal and any changed definition require the user's authorization. Preserve exact rollback; no push or final implementation commit until required acceptance. Re-run one ready-service quit/reopen inside the idle window, verify samePID/ready, then controlled stop/idle/no-restart checks. Preserve the earlier failed evidence. Claude acceptance remains deferred, not waived. No UI/copy changes: visual review N/A for this launch-only change.

## Sources

Installed macOS `/usr/share/man/man1/launchctl.1`: bootstrap registers definitions; kickstart runs an existing job, and-k explicitly kills a running instance; legacy submit keeps a job alive after failure. `/usr/share/man/man5/launchd.plist.5`: launch triggers, KeepAlive and RunAtLoad. CPython's [3.11.17 macOS launcher](https://github.com/python/cpython/blob/v3.11.17/Mac/Tools/pythonw.c) explains the observed Python.app executable; it does not establish coalition independence. Root cause is supported by the captured local macOS records, not inference from that source.
