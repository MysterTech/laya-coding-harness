# laya-harness — Codex support design brief

Date: 2026-10-09. Status: Stage 1 scope approved by the user; native preflight in progress. Detailed adapter contract follows verified preflight.

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

Local CLI reports codex-cli 0.155.1. Its help exposes hook trust support. No Codex hooks have been installed for laya-harness and no desktop capability probe has run yet. Live laya-harness still has the both-lines fake profile configured from Claude acceptance; restore verified real configuration before ordinary use, with authorization for the live configuration change.

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
