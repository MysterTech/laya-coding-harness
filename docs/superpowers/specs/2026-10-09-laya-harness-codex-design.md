# laya-harness — Codex support design brief

Date: 2026-10-09. Status: Stage 1 scope approved by the user; native delivery preflight confirmed. Implementation contract below; production acceptance pending.

## Intent and acceptance order

The user wants the same local System-1 advisor in the Codex desktop app, with development and acceptance performed in Codex while Claude usage is exhausted. Claude stage-0 acceptance resumes after the weekly limit replenishes. Its completed automated gates and light/heavy/plan-only copy checks remain evidence; remaining checks are pending, not passed or waived. Stage-0 implementation remains uncommitted and its WIP refs are retained.

## Proposed integration

Use native Codex SessionStart and UserPromptSubmit command hooks with a Codex-specific adapter, reusing the existing local service, pinned checkpoint, question set, deadlines and fail-open entry point. Keep model/effort selection and plan copy specific to Codex. Never suggest Fable. Never change the user's model, effort or mode automatically.

Return either no stdout or exactly one JSON object containing systemMessage. Never emit plain text or additionalContext: Codex treats those as developer context. Never emit blocking fields or exit 2. The target remains user-only advice, whose actual rendering and absence from model context must be verified locally before claiming support.

Recommend project-local hooks for initial acceptance. A manually installed plugin is an alternative for later distribution, but introduces packaging and trust steps that the first adapter does not need. A manually invoked skill is another alternative, but does not satisfy automatic classification on every prompt.

Codex session identity and turn identity must be normalized without assuming Claude payload fields. State must distinguish harnesses; decision rows must identify the harness and adapter provenance. Preserve existing Claude semantics and log-reader compatibility. Do not copy Claude transcript parsing into the Codex adapter: official docs explicitly describe transcripts as an unstable interface. Model and effort read from config are defaults, not proof of the active UI selection; record their provenance and uncertainty.

Use the existing per-field confidence gates and first-human-prompt model hint, with independent plan-hint suppression in Plan mode. The Codex catalog and provisional fit mapping need verification against installed model availability and official capabilities before becoming contract data. Provisional fits are not measured quality claims; measurement remains stage 2.

## Required preflight before the detailed spec and plan

Confirm the installed desktop runtime's hook input, hook trust/reload behavior, command invocation, timeouts, warning rendering, and model-context separation. Verify SessionStart cold-load behavior rather than assuming it matches Claude. Capture only synthetic prompts in the capability probe. Prepare an exact project hook diff for user approval before installation; never bypass hook trust. CLI behavior is useful evidence but does not establish desktop acceptance.

Then specify exact payload normalization, state namespace, decision-log evolution, Codex copy deck/mockups, model catalog and fit rules, and acceptance commands on disk. Follow the workbench procedure: executed code/test blocks, committed docs first, Codex implementer and independent reviewer under the user's temporary model-routing exception, one final implementation commit per plan. Preserve isolation from the unfinished stage-0 implementation.

## Testing

Run automated adapter and hook subprocess tests using temporary homes and free ports, including deadline/failure paths and no network. Run Claude regression tests without Claude usage. Run the pinned real-model gate as controller only. Perform live Codex acceptance for fake copy, real prediction, cold/down/off paths and no harm; record visual evidence separately. Codex acceptance does not substitute for deferred Claude acceptance.

## Evidence and remaining uncertainty

Local CLI reports codex-cli 0.155.1; the desktop runtime is 0.162.0-alpha.2. The approved temporary probe is installed and native delivery is confirmed below. Production hooks are not installed. Live laya-harness still has the both-lines fake profile configured from Claude acceptance; restore verified real configuration before ordinary use, with authorization for the live configuration change.

Official documentation read on 2026-10-09:

- [Hooks](https://learn.chatgpt.com/docs/hooks): native prompt/session events, JSON systemMessage warnings, plain stdout/additionalContext model context, project hook discovery and exact-definition trust.
- [Plugin packaging](https://developers.openai.com/plugins/build/plugins): manually installed desktop plugins can carry lifecycle hooks; plugin installation alone does not trust them.

The shared contract is [the umbrella design](2026-10-08-laya-harness-design.md). This brief proposes starting Codex design before Claude acceptance completes; it does not amend stage-0 completion gates.

## Native preflight contract (controller only)

The desktop runtime is `/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex`, version `0.162.0-alpha.2`; the Homebrew CLI is `0.155.1`. Use the desktop binary for capability evidence. Its protocol schema was generated offline into `/private/tmp/laya-codex-desktop-schema`.

A scratch-only probe may run the desktop runtime with an isolated Codex home and synthetic session. It must not read credentials, send a model request, download anything, modify real config or bypass hook trust. Inspect model-visible prompt construction with the native debug command if possible. Stop and report any runtime behavior that cannot be verified without a live turn. An exact-trust hash set through the native configuration in the isolated home is permitted; global hook-trust bypass is forbidden.

A temporary project probe, when approved for installation, registers only SessionStart (timeout 8 seconds) and UserPromptSubmit (timeout 3 seconds). It runs the repo virtual-environment Python with `-I` and a dedicated absolute script path under `.workbench/codex-probe/`. The script uses only the standard library, exits 0 for every failure, emits nothing for SessionStart, and emits exactly `{"systemMessage": "laya · Codex hook check (temporary probe)"}` for UserPromptSubmit. It does not call laya-harness or its service.

The probe records only event, session/turn identifiers, model, permission mode, source, presence of agent fields, available field names and prompt character count. It never records prompt text, transcript contents or configuration contents. Capture files and directories have modes 0600 and 0700. The synthetic prompt used for a live check is `Reply with just: hook check complete.` User input and final assistant reply establish no-harm; the warning must be visible to the user and absent from model-visible context. Before the adapter is called supported, record warning rendering, trust behavior, payload and context-separation evidence. Probe removal is part of acceptance cleanup.

The project probe draft is reviewed before installation. It does not replace existing hooks; if a project hook file exists, prepare a merged diff and preserve unrelated hooks. No user-level hook file is changed by this preflight.

## Live preflight observation (2026-10-10)

The approved project probe ran SessionStart and UserPromptSubmit in a fresh desktop session and Codex answered the synthetic prompt. Actual input matches the native schema: active model, permission mode and turn ID are present; effort and human-source fields are absent. The screenshot has no inline warning. The installed app displays hook output through Hook stats, where warning entries are labeled Message; expanded panel delivery still needs capture. The adapter's user-visible channel and instant-advice acceptance must be specified against this surface before implementation. No banner or automatic inline warning is claimed.


## Expanded native panel evidence (2026-10-10)

The user's 09:49:42 screenshot confirms Hook stats: Runs 2, Blocked 0, Failed 0; Completed UserPromptSubmit / Project; Message `laya · Codex hook check (temporary probe)`. The other entry is an unrelated Stop plugin. The earlier screenshot confirms the synthetic reply completed. This is the supported surface: open the hook-shaped message action, expand UserPromptSubmit. Advice is not automatically visible inline. Official hook semantics identify systemMessage as user UI; plain stdout and additionalContext would enter developer context and are forbidden. Absence of the sentinel from the persisted rollout is supporting evidence, not a complete model-input audit. No production acceptance is inferred from this probe.

## Stage 1 implementation contract

These clauses supplement the umbrella spec; §4 remains the Claude contract. Shared service, checkpoint, questions, home, modes, private writes, no-download rule and service outcomes stay as specified there. Stage 1 does not change Claude behavior. Its plan is generated from the independently verified Stage 1 workbench before copying code into this repo. No implementation commit is made until the outstanding acceptance gates are satisfied.

### C1 Invocation and fail open

Register only SessionStart and UserPromptSubmit, using the existing argv builder with harness `codex`, absolute venv interpreter and `-I -m laya_harness hook codex <Event>`. Native Codex requires one shell command string: build it with `shlex.join(argv)`; never concatenate unquoted paths. Timeout is 8 seconds for SessionStart, 3 seconds for UserPromptSubmit, synchronous. The Codex hook invocation requires exactly the harness and event arguments; extra or missing arguments are silent invalid invocations, exit 0, without spawn or decision writes. No args member, async execution, blocking JSON, plain stdout or additionalContext. stdout is empty or exactly one object with systemMessage, written last through the saved descriptor. SessionStart is silent. Always exit 0, including SystemExit, malformed input and deadline exhaustion. Preserve stderr/client.log private redirection.

On this supported single-user Mac, arm a Codex-only POSIX wall-clock watchdog before reading stdin or touching state. From the entry point's start timestamp, UserPromptSubmit has 1.5 seconds for the whole hook; SessionStart has 4.5 seconds to allow the initial health check and the up-to-4-second startup wait. Timer expiration exits 0 silently, without blocking on diagnostics or log writes. Profile calls use the remaining prompt budget, reserving 0.10 seconds for local finalization; they never get a fresh 1.5 seconds after local work. A hard watchdog termination can leave no row; deadline priority is the explicit exception to one row per prompt. Tests must keep stdin open and exercise slow service replies. If importing or arming the watchdog fails, including SystemExit from either signal API, silently exit 0 before reading input or touching state. CLI commands and Claude hooks do not arm this timer.

### C2 Input and source

Require a JSON object whose hook_event_name matches the invocation. Common required fields are nonempty strings session_id, model, cwd and permission_mode. transcript_path may be absent, null or a string and is recorded but never opened. UserPromptSubmit additionally requires a nonempty string turn_id and a string prompt (empty is allowed). SessionStart requires source in startup, resume, clear, compact, fork. Native UPS has no human source field: treat a submission as human unless agent_id or agent_type is present, even when falsey. Such agent submissions are logged skipped/not_human without inference, spawn or prompt counting. Lifecycle source must never be used to infer prompt authorship. Ignore unrecognized optional fields. Invalid payloads show nothing, start nothing and best-effort write one error row for UPS. Off reads no config defaults and performs no state, prediction or decision writes; garbage stdin stays silent. An unsupported Codex event shows nothing and does not spawn.

### C3 Session and defaults

Use shared session transactions with key `codex:` followed by the session ID. The shared path encoder hashes this key, separating ordinary native UUIDs from Claude UUIDs. Codex does not use the Claude transcript reader or PostModelSwitch. On every valid event set model to payload.model, model_source to `hook`, and effort to null. Actual reasoning effort is unknown; never substitute a config default. Snapshot these values for the prompt row before inference. Concurrent later events must not be overwritten when shown flags are merged.

SessionStart startup, clear and fork reset prompt_count and shown flags; resume and compact preserve them. Only startup waits for readiness. The same refused-only spawn and loading/not_ready/foreign/first-timeout wait termination rules as umbrella §4.3 apply. No session lock is held while calling the service. Human prompts increment prompt_count exactly once before calling it. The model line is eligible only on the first human prompt, even if that prompt fails. Plan shown flags are checked against latest state under the final transaction, after inference; rows precede flags. Mode log-only does not mark advice shown.

Read the selected default model and model_reasoning_effort from `CODEX_HOME/config.toml`, or `~/.codex/config.toml` when CODEX_HOME is unset. These are configuration defaults only, separately recorded as codex_defaults `{model, effort, source}` with source `user_config_default`, or all null on missing/unreadable/malformed config. A parser depth failure (RecursionError from deeply nested TOML) also yields the all-null defaults result; an unrelated nested setting must not abort prompt classification. Never record other config fields or credentials. Read at most 64 KiB from a regular file, refuse FIFOs/devices, and ignore nonstring values. Use the standard-library TOML parser. No project-config merge or transcript inference is claimed in Stage 1.

### C4 Adapter, catalog and copy

Rules version is `codex_v0`. Use the question set's existing display thresholds, rounded tier sums and tie rules, independent plan gate, minimum prompt length and one-shot shown gates. Plan mode means permission_mode `plan` or a prompt beginning with `/plan` after left trimming. The embedded native hook schema supports permission_mode plan, but mapping from the desktop Plan collaboration setting to this field is not yet verified. The suppression promise applies to the received field and /plan prefix only; do not claim reliable detection of the native UI Plan setting until a controlled Plan-mode capture establishes it. Actual effort is unknown so there is no same-model suppression. Keep all three mismatch entries and parallelism log-only. At most two lines, model then plan. The model line uses the shared exact model_line formatter; the Codex plan line is exactly:

`laya · reads like a multi-step change (p=0.88) → Plan mode (/plan), or tell Codex to plan first`

Probability formatting is two decimals, including boundary tests. Exact fake display cases:

- Light, tier p .86, winning class quick: `laya · light task (p=0.86) → GPT-6 Luna at low effort fits this task`.
- Heavy, tier p .91, winning class architecture: `laya · heavy task (p=0.91) → GPT-6 Astra at xhigh effort fits this task`.
- Plan only: the plan line above.
- Both: light line, newline, plan line, in one systemMessage.
- Silent: no stdout.

The new Codex catalog contains the three supported recommendation models confirmed in the installed picker metadata: gpt-6-luna / GPT-6 Luna / family luna / version 6, gpt-6.1-sol / GPT-6.1 Sol / family sol / version 6.1, gpt-6-astra / GPT-6 Astra / family astra / version 6. All are in_picker and allowed. Efforts low, medium, high, xhigh, max are present for each; Sol and Astra also have ultra. Standard list input/output prices per million tokens, checked 2026-10-10, are Luna 0.1/0.5, Sol 2/10, Astra 10/50. This catalog is the supported recommendation subset, not a complete picker census; other active model IDs remain valid logging input. No Fable or Mythos recommendation is possible, including injected catalogs, per the shared selector.

Provisional fit options: quick Luna/low and Sol/low; routine Sol/medium; multi_file Sol/high; architecture Astra/xhigh. The shared selector chooses cheapest eligible input list price, newest numeric version on a tie, only supported effort and allowed/picker models. No option means no_fit. As in Stage 0, fits are provisional assumptions, not evidence of significant quality gains; D16 remains the goal and Stage 2 measures them. Hash the concatenated Codex catalog and fit bytes into each Codex row. Data files ship in the existing data/*.json package pattern; do not change the Claude catalog.

The mockup [Codex Hook stats copy states](../../mockups/codex-stage1-hook-stats.svg) uses the native panel observed in the user's screenshot. It specifies text, order, wrapping and user access; native controls/colors belong to Codex, not laya-harness. The /plan instruction is supported by [OpenAI's native Plan mode description](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex). Prices are from the official [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna), [Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol) and [Astra](https://developers.openai.com/api/docs/models/gpt-6-astra) model pages.

### C5 Decision row and outcomes

Append to the same private decisions.jsonl. Preserve every umbrella §4.10 field, schema_version 1 and reader compatibility. Add harness `codex`, turn_id from native input, prompt_id equal to turn_id, and codex_defaults as C3. Claude rows are unchanged and lack these additive fields. The status log reader selects the Codex catalog for harness codex and the Claude catalog for legacy rows without harness or with harness claude-code. Mixed logs must not report supported Codex models as unknown; genuinely uncatalogued active model IDs remain reported by the existing warning. Absent or null harness means legacy Claude; a nonstring or empty discriminator is malformed and that row is skipped for model checking rather than crashing status. Test list/object/number discriminators as well as mixed logs and legacy Claude rows; do not simply union catalogs, which would hide wrong-harness IDs. For malformed input, best-effort identity fields may be null, status error. session contains the prompt-time model/effort/model_source snapshot, including a best-effort error row after a validated prompt fails. Carry the captured snapshot through exception handling; never reload newer session state for that row. If failure occurs before state capture, use the validated payload identity (effort null, model_source hook); malformed unvalidated inputs may have null session. Adapter rules and catalog hash identify Codex; served checkpoint/question-set/versions still come from the shared service, including served-question mismatch diagnostics.

Outcome mapping is exactly: ok → decided; refused → spawn once and started_service; loading → loading; not_ready → not_ready; timeout → timeout; foreign/error/malformed → error. cold is true only for started_service or loading. No loading/not_ready/error/timeout outcome restarts the service. Record full prompt locally by design, shown_text only when returned in show mode, independent suppress reasons, answers, raw usage, truncation and dropped chars. Agent prompts write skipped with both reasons not_human. SessionStart writes no decision row. On normal client exceptions, best-effort append one error row unless already logged; log-write errors remain fail open. Hard timer termination and unreadable laya config are exceptions inherited/explicitly specified, not invented success rows.

### C6 Isolation, testing and acceptance

No new outbound network, third-party import, automatic model/mode change or hook installation. Reuse the shared loopback service security and offline checkpoint behavior. All automated tests use isolated LAYA_HARNESS_HOME and free ports; tests of config defaults use temporary CODEX_HOME. Pin exact payload normalization, defaults provenance, state namespaces, all reset sources, concurrency, adapter thresholds/ties/suppression, no forbidden model, catalog data/hash, outcome mapping, startup waits/spawn restrictions, malformed/agent/off paths, private modes and stdout/context exclusions. Subprocess tests invoke the generated native shell command, include paths with spaces/metacharacters, keep stdin open, and check deadline/exit0/single JSON. A deliberate break of the key gates must fail tests. Run the full Claude regression suite and controller-only offline real-model gate at the final build boundary.

Production installation is a separate exact reviewed replacement of the temporary probe. Preserve unrelated native hooks, keep project file private and Git-excluded, reload and trust the changed definition through Codex's native UI. No trust bypass. Live capture uses the existing approved fake profiles and records native panels for light/heavy/plan-only/both/silent before real prediction and cold/down/off/no-harm checks. Stop the service before changing live config; restore the saved real config before normal use. These changes require the user's participation/authorization. Native SessionStart actually reaching ready and detached service survival are acceptance checks, not conclusions from the isolated thread/start probe. Remove the temporary metadata probe on replacement. No Claude acceptance is inferred from Codex acceptance.


### C7 Measurable native acceptance

Carry over umbrella §8 with Codex desktop chats replacing Claude Code sessions and these explicit bounds. In a fixed fake configuration capture light, heavy, plan-only, both and silent Hook stats states and their corresponding one-row-per-prompt records; exact copy/order and provenance must match C4/C5. Repeat with the real pinned checkpoint and record its actual output without asserting classifier accuracy. Native trust is reviewed after each changed definition.

For at least 20 human prompts across those checks, require zero blocked prompts, zero failed hook entries and zero native hook-timeout notices. Complete UserPromptSubmit process duration must be at most about 1.6 seconds; the hard watchdog targets 1.5 seconds with scheduling tolerance. A row's latency_ms stops before final logging/exit and is only supporting timing evidence. Use external monotonic timing of the registered command for automated bounds; for live bounds use native start/completion receipts if available, or an independently timed acceptance wrapper prepared/verified in the workbench and approved as an exact temporary hook change. Do not mark the live timing gate passed using row latency alone. Record all sample counts and evidence in docs/qa/codex-stage1.md.

Down-path acceptance: (a) Stop the service after SessionStart and send one prompt: no laya message, Codex completes, exactly one new service load/spawn, service reaches ready after the UPS exits and remains reachable after that chat is closed. (b) With a deliberately missing model directory in a controller-approved temporary configuration, send at least three prompts: no laya message, rows not_ready after load failure, same bound PID across prompts, no repeated model loads. Restore valid config afterward. (c) A nonresponding temporary loopback listener: no laya message, completion within the UPS bound, no service spawn; never use the live standard port for the test listener.

Cold-start acceptance: in at least three new startup sessions with service initially stopped, record SessionStart duration (at most about 4.6 seconds whole process, including the 4-second readiness wait), and whether each first human prompt got a decided profile. The missed-first-profile proportion is reported, not a pass/fail accuracy gate. Detached ready service and shutdown survival remain required. Off: on at least two human prompts, no decision-log bytes, session updates, service spawn or laya message, while Codex completes normally (private diagnostic setup may still occur). These real-home transitions need user authorization, run sequentially outside capture, and restore saved real config. Claude gates remain pending independently.
