# Stage 2 — Measure: offline evaluation foundation

Date: 2026-10-11. Status: **written design proposed; not approved for implementation**.
Contract parents: umbrella §1.1, §3, §4.10, §4.13, §11 and D16;
Codex C3/C5/C7; macOS service-launch contract. Implementation uses the existing
two-agent workflow and verified literal-plan workbench procedure.

## Purpose and scope

Measure whether the local classifier's three fields support useful advice, before claiming
quality or cost benefits or displaying calibrated confidence in the future HUD. Stage 2
proceeds on main while Claude native acceptance remains on codex/claude-acceptance. Reading
Claude history does not establish Claude hook acceptance. The existing live advisors,
question wording, display thresholds, fit tables, launch ownership and hook behavior remain
unchanged during this first measurement phase (Stage 2A).

Start with explicit local inputs, import/label/report workflows and existing decision outputs.
Do not train, download checkpoints, replay coding tasks, launch agents, change models in a
harness, alter live config, install hooks, or push data. Later Stage 2 phases separately design
cached-checkpoint/question-set comparisons, measured threshold proposals, controlled quality
and cost comparisons, memory-pressure/latency experiments, and deferred runtime-hardening
items. Stage 2A does not silently declare those umbrella Stage 2 items complete.

## Approaches considered

1. **Offline history and decision evaluation (recommended first).** Exploits the data already
available, preserves the live hook contract, makes missing evidence visible and creates a
labelled held-out set. It cannot establish a causal benefit of choosing a cheaper model.
2. **Replay all prompts through multiple checkpoints immediately.** Useful after dataset and
label design, but expensive and confounded without independent labels; alternative weights
are not yet approved for download. Specify this as a later isolated offline pass.
3. **Live randomized model/effort routing.** Could compare outcomes but changes user's work,
needs explicit experimental approval and stronger correctness evaluation. Not Stage 2A.

## M1 Local import boundary and privacy

A new offline command family imports only explicitly named decision logs and harness
transcript/session files into an explicitly named output directory. No automatic scan of
all ~/.claude or ~/.codex history. Inputs are read-only; no source files, live state, config,
service jobs, logs or hooks are modified. No service requests or third-party imports are
needed to import, label or report. Treat transcript text as data, never instructions.

Outputs and their parents created by the workflow are 0700 directories and 0600 regular
files. Reject symlink/device/FIFO inputs and outputs; use nonblocking opens and fstat so
replacement of a pathname with a FIFO cannot block. Reject unsafe output replacement; writes
are atomic and never overwrite an unrelated existing dataset/report. Outputs include private
prompt text only where needed for independent labelling; summaries omit raw text by default.
Nothing is added to Git automatically. Tests use temporary inputs/outputs only.

Process JSONL incrementally with a 4 MiB per-line limit and bounded JSON nesting errors;
skip over-limit, malformed, non-object and unknown-type records with reason counts and
line-number diagnostics without echoing contents. Snapshot regular input files at the start,
record byte length and SHA256, and refuse to finalize a report if any source snapshot changed
while reading. Partial tails are counted and excluded, not treated as valid examples.

## M2 Normalized evidence and identity

A versioned private manifest records source identities/hashes, harness, reader version,
session IDs, source record IDs/line numbers, availability and exclusion counts. Prompt
examples retain exact text, timestamp, native prompt/turn identity when present, known
model/effort with provenance, and references to observed decisions, assistant messages,
completion/error events and token usage. Unknown values remain null with a reason; absent
usage is not zero usage and defaults are not evidence of active effort.

Join a decision to history by harness/session plus native prompt/turn ID when available.
A missing native ID permits a match only when exact text and timestamp yield one candidate
within the same session and within five seconds of the decision timestamp; ambiguous or conflicting candidates remain unmatched. Report these
rather than guessing. Repeated import of the same manifest is idempotent by native identity
or source-file-hash/line identity; forked/copied sessions are not assumed independent.

Claude reader handles main-thread user/assistant records, text content and block content,
source indicators, model/effort, message IDs, timestamps and usage. Apply the existing source
filter semantics; skip sidechains and synthetic assistant models. Tool results, attachments,
queued tasks and nonhuman messages are not human prompts. Missing source evidence is marked
unknown, not quietly promoted to confirmed human.

Codex reader handles session_meta, turn_context, response_item messages, event_msg lifecycle
and token records. Turn IDs anchor joins. Read active model/effort from the relevant
turn_context, never from ambient config defaults. Distinguish actual user input from injected
agent/peer/tool/developer content; unsupported attribution is unknown. Do not count event and
response-item representations of one user input twice. Token_usage_record and token_count
may repeat cumulative usage: retain provenance and deduplicate, never sum both blindly.
Reject conflicting turn identities; preserve incomplete and aborted turns as such.

Observed preflight on 2026-10-11 inspected only key names/counts from one saved two-turn
Codex session and one Claude transcript. Codex has session_meta, turn_context,
response_item/message, task_started/task_complete, token_usage_record and token_count.
Claude has user/assistant message blocks, sidechain flags, promptId/sessionId and usage.
This proves local fixture shapes to cover, not universal host compatibility. Unknown host
formats produce explicit unsupported/excluded counts. Implementation planning must execute
reader fixtures before writing literal plan blocks.

## M3 Independent labels and exclusions

Provide private label exports keyed by example ID, prompt text and only pre-prompt context
available to the classifier. Hide predicted choices/probabilities, shown advice, model
selection and subsequent outcomes from the classifier-label view. Human labels cover
quick/routine/multi_file/architecture difficulty, boolean plan_first and parallel, or unknown
for any field, with optional rationale. Label meaning follows the packaged profile_v0
questions; document the rubric and examples before implementation. Unknown is excluded from
that field's accuracy denominator and reported explicitly. Disagreements are retained, with
an explicit adjudicated label if available; no model prediction can create its own truth.

Separately collect task boundary IDs, correctness evidence, user corrections, redo turns,
overrides and explicit acceptance. Completion without an error is a weak execution signal,
not proof of correct code; interruption is not automatically failure. Missing or disputed
correctness stays unknown. The export/import format is validated, rejects unknown example
IDs and duplicate/conflicting labels, and never silently overwrites prior annotations.

Exclude fake-model decisions, acceptance/probe sessions explicitly listed in the import
manifest, nonhuman/unknown-source prompts, invalid outputs and truncation from primary
classifier-quality metrics. Record each exclusion; separate truncation/failure slices remain
available. Never infer that a short prompt is a probe from its wording alone. Runtime
statistics include real human outcomes such as started_service/loading/not_ready/timeout/error,
with their own denominator, so quality reports cannot hide unavailable predictions.

## M4 Session holdouts and measurement

Create deterministic development/validation/test partitions at the session-group level.
Connected sessions sharing an explicit task, fork ancestry, or identical normalized prompt (Unicode NFC, with whitespace runs collapsed)
are one leakage group. Use seed 20261011 by default. Group identity is the SHA256 of sorted canonical example IDs
joined by newlines; SHA256 of dataset version, seed and group identity, separated by newlines,
modulo 100 assigns 0–59 development, 60–79 validation and 80–99 test. Record all identities
and the seed; this gives deterministic approximate 60/20/20 proportions. No turn from one group crosses partitions. Dataset amendments
create a new version; preserve previous splits and reports. Empty partitions or absent labels
report insufficient evidence; do not fabricate accuracy or tune from the test partition.

Report four-class difficulty confusion matrix and accuracy; separate light/heavy tier accuracy
using quick+routine versus multi_file+architecture; boolean precision/recall/confusion counts
for plan_first and parallel; multiclass Brier score and binary Brier scores; ten equal-width confidence bins
with counts/observed accuracy (left-inclusive, right-exclusive except the final bin includes 1); and coverage/precision at the current display thresholds.
Metrics use finite validated values in [0,1] with valid probability totals, and raw unrounded
scores. Difficulty prediction is the greatest probability with ties resolved in packaged
question order; the tier prediction compares the two summed tier probabilities and resolves
ties to light. Boolean predictions use raw noul >= 0.5; also report display-threshold
precision/coverage separately. Report numerator/denominator and session-group count, not percentages alone. Undefined
precision/recall/calibration is null with a reason. The first report is descriptive, not a
claim of calibration from a small sample. Future threshold choices use validation data only;
held-out test is reported once for a frozen candidate. Preserve question/checkpoint/catalog/
adapter versions so different settings are not pooled as if identical.

Separate classification from actual display gates: report raw threshold eligibility and
observed shown/suppressed decisions, including first-prompt, plan-mode, minimum-length and
already-shown rules. Runtime summaries include status shares, cold/missed-first-profile share,
truncation share and latency quantiles, clearly labelling logged latency as shorter than
complete-process timing. Do not reuse row latency as proof of hook deadlines.

## M5 D16 quality/cost evidence and reviewed changes

Group outcomes by task/class/model/version/effort only where labels and provenance support it.
Count correction/redo turns in task cost. Deduplicate native token usage and distinguish
input, cached input and output rates using a versioned price snapshot; an unsupported price
or ambiguous attribution gives unknown cost, not an estimate using another model. Token
records alone do not prove monetary billing or plan-limit consumption. Observational history
is confounded by task difficulty/user model choice; label comparisons descriptive and never
assert a causal quality gain. Report missing correctness, effort and usage coverage.

Do not recommend a fit-table replacement from classifier accuracy alone. A later comparison
requires enough independent tasks, an explicit success criterion, uncertainty and a
class-specific significant-quality-gain criterion approved by the user. Produce proposals
as reviewable diffs with evidence; no automatic changes to live questions/thresholds/catalogs
or fit tables. Fable remains excluded from recommendations and experiments.

## M6 Testing and acceptance of Stage 2A

Requirement-derived fixture tests cover both observed formats, main/sidechain attribution,
nonhuman messages, block text, duplicates, fork groups, absent/ambiguous IDs, repeated token
records, unsupported formats, malformed/deep/oversized JSON, incomplete tails, file replacement,
private modes and source immutability. Metric tests use small manually computed datasets,
including threshold-boundary scores, unknown labels, invalid probabilities, empty classes,
leakage grouping and deterministic splits. Mutation checks prove missing filters/deduplication,
wrong metric denominators and leakage cause failures. No fixture contains actual private
prompt text from the user's history.

Use the workbench with actual behavioral RED/GREEN and independent contract review. Generate
literal implementation plan blocks from executed verified files, commit docs before promotion,
and run full existing fake gates plus focused measurement tests; cached real gate remains
controller-only if inference boundaries change. A private controller import/report using
explicit approved source files proves read-only operation, private modes, meaningful exclusion
counts and provenance. No accuracy target is invented as a gate; an insufficient dataset is
reported, with labelling/sampling work remaining. New commands and output schemas receive a
separate verified implementation plan after written-spec approval.
