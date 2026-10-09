# laya-harness — design

| | |
|---|---|
| Status | Draft for sign-off (documentation gate). Checks 1–6 done (Appendix C); mockup in §4.12 and `docs/mockups/`. |
| Date | 2026-10-08 |
| Scope | The whole system at roadmap level. Stage 0 in implementable detail. |
| Review | Stage 0 was put through a six-lens design review before this draft (Appendix B). |

## 1. What laya-harness is

**A local execution router for agentic coding harnesses.** It uses Laya, a small local
typed-decision model (laya-mlx, MLX on Apple silicon), to read each prompt you send to Claude
Code or Codex. It classifies the prompt into a harness-neutral *execution profile*, then
recommends how to configure the harness for that task.

laya-harness is the umbrella for the whole system, the web HUD included (D15). The boundaries
below bind the **Laya component**. The Bridge and the HUD, when they arrive, may start sessions
and run skills; Laya still only classifies.

Boundaries that every stage keeps:

- **Laya sits above the harness, never inside its agent loop.** It never launches agents, runs
  shell commands, edits files or judges individual tool calls. It recommends at the start of a
  task, and the harness keeps full native autonomy afterwards.
- **Laya owns only the probabilistic part:** prompt → requirements. Reading the harness's
  current state and comparing it with the profile is deterministic adapter code.
- **Claude Code and Codex are not normalised into one product.** Only the semantic layer, the
  execution profile, is shared. Each adapter translates it into its own harness's features.
- **Confidence is per field,** and each recommendation fires on its own field's threshold.
- **Laya's numbers are untrusted until measured.** Upstream reports base checkpoints near
  chance on unseen typed decisions (0.362) and over-confident as shipped. Training on the
  user's own history (stage 3) is expected to be necessary.

### 1.1 System 1 under a System-2 harness

Laya is **System 1**: fast, automatic, run on every prompt, costing no tokens, offering
impressions with a confidence and never deliberating or acting. Upstream describes it the same
way: a "System 1 decision engine", whose main call is `system_one`. Claude Code and Codex are
**System 2**: slow, deliberate and in charge, and so is the user. Five principles follow, and
every stage keeps them:

- **P1. Feel instant.** System 1 adds no noticeable wait. The typical cost is about 0.13 s (check
  6). Any longer wait is a defect to be minimised, not a feature. The up-to-4 s wait on a cold
  first prompt (D7) is a known exception, forced by unloading the model on an 8 GiB Mac. Stage 2
  treats the idle-timeout or resident-service question as core quality, not tuning.
- **P2. Silent when unsure.** Below its threshold laya says nothing. It never fills silence with
  low-confidence advice.
- **P3. System 2 decides.** A suggestion never restricts the harness or the user. Stage 4's notes
  to the harness are hints, with their confidence, sent only for fields that passed measurement.
- **P4. Guard against anchoring.** System 2 tends to endorse whatever System 1 suggests. A note
  such as "quick task" must never lead Claude to investigate less than the task needs. Notes are
  worded as considerations, never as limits, and stage 2 checks whether notes change the
  harness's behaviour for the worse.
- **P5. Intuition earns trust through feedback.** Intuitive judgement is reliable only in a
  regular environment with quick, clear feedback (Kahneman and Klein, 2009). The decision log
  and stages 2–3 supply that feedback, through what actually ran, what it cost, and where the
  user interrupted or corrected. Until a field is measured, its numbers are untrusted.

## 2. Architecture (all stages)

```
 Claude Code / Codex hooks ──▶ client (stdlib only) ──▶ local service (127.0.0.1)
         ▲                          │                      └─ laya-mlx checkpoint + question sets
         │ one line to the user     │                          → execution profile (per-field p)
         │ (later: note to harness, ▼
         │  or stop the prompt)   harness adapter (deterministic rules)
         └──────────────────────────┤  profile × harness state → mismatches → channel
                                    ▼
                         ~/.laya-harness/decisions.jsonl ──▶ measure (stage 2) ──▶ train (stage 3)
```

**Execution profile (the semantic layer).** Fields grow by stage. Mismatch types:
MODEL, REASONING, MODE, CONTEXT, CAPABILITY, PARALLELISM_OPPORTUNITY, SKILL_OPPORTUNITY,
PERMISSION, ENVIRONMENT, HARNESS. HARNESS (cross-harness advice) is supported by the design
but stays off by default.

**Who acts decides the channel** (stage 4 onwards; stage 0 only shows lines to the user):

| Who acts | Mismatches | Channel |
|---|---|---|
| The user | MODEL, REASONING, PERMISSION, ENVIRONMENT, CAPABILITY, HARNESS | Stop the first prompt of a session and explain |
| The user | CONTEXT (start fresh) | Stop the prompt that starts a new task in an old session |
| The harness | MODE (plan first), PARALLELISM, SKILL | One short `additionalContext` note; the prompt proceeds and the harness decides |

## 3. Roadmap (top-down: make it work, then refine)

Each stage updates this document before any of its code is written.

| Stage | Outcome |
|---|---|
| **0. First working version (Claude Code)** | Section 4. Prompt → hook → service → three questions → one-line suggestion → logged. Advises only, never stops a prompt. |
| 1. Codex | The same client in a Codex `UserPromptSubmit` command hook; the Codex adapter reads `~/.codex/config.toml`. Proves the shared semantic layer. |
| 2. Measure | Readers for Claude Code transcripts and Codex sessions; out-of-the-box accuracy per field on held-out sessions; checkpoint comparison; display thresholds tuned. |
| HUD. Web front door (D15) | The Bridge and a web HUD, with their own spec and mockups first. Day one sits between a read-only view and the full dashboard: routing decisions and receipts plus a chosen set of actions and reports, fixed when the stage starts. No voice in its first phase. Obsidian plugin later. |
| 3. Learn | Training cases from outcomes, the user's labels and logged overrides; split by session; a GPU fine-tune with upstream `laya-train` (off this Mac, with explicit approval); `laya-mlx convert`; swap and re-measure. |
| 4. Act | Prompt-stopping and harness notes switched on per field that clears its threshold. MODEL and REASONING become separate suggestions. |
| 5. Widen | More profile fields (CONTEXT, CAPABILITY, SKILL, PERMISSION, ENVIRONMENT); other question sets ("done without proof" Stop check, turn-end notifier, bulk classifier, context picker); cross-harness advice, off by default. |

## 4. Stage 0 — design

### 4.1 Flow

Three hooks run the same client.

- **SessionStart** creates the session file and makes sure the service is running. On a new
  session (`startup`) it waits up to 4 s while the service is starting, so the first prompt
  usually meets a ready model (decision D7, §4.3). It prints nothing. In the desktop app it does
  not receive the model (Appendix C).
- **UserPromptSubmit** sends the prompt to the service, applies the Claude Code adapter rules,
  prints at most two lines for the user, and logs one row.
- **PostModelSwitch** records the new model when the user changes it mid-session, and prints
  nothing.

The service runs laya-mlx, answers three questions per prompt, and exits after 15 idle minutes.

### 4.2 Client (hook contract)

- Invoked as `laya-harness hook claude-code <Event>`. It is registered in **exec form**: the
  absolute path of the project venv's python as `command`, and
  `["-I", "-m", "laya_harness", "hook", "claude-code", "<Event>"]` as `args`.
  - `-I` keeps the working directory off `sys.path` and ignores `PYTHON*` variables.
  - One function builds this argv. `setup`, the tests and the install snippet all use it.
- **Standard library only;** it never imports laya_mlx or MLX.
- It reads stdin to the end, catches every exception including `SystemExit`, and **always
  exits 0**. An exit code of 2 would block the prompt in every project.
- **stdout is empty, or exactly one JSON object `{"systemMessage": "..."}`,** written last.
  Anything else on stdout becomes context for Claude. SessionStart always prints nothing.
- Diagnostics go to `~/.laya-harness/client.log`, one line per problem.
- It calls the service with a **1.5 s total deadline**, enforced on the wall clock: a listener
  that trickles bytes cannot stretch it. Check 6 confirms or adjusts this.
- stdout is also redirected at the file-descriptor level for the hook's run, so nothing written
  by a library or a child process can reach Claude's context; the one JSON object goes to a
  saved copy of the original descriptor.
- **The hook is synchronous, and that is a deliberate cost.** Claude Code holds the prompt
  until the hook exits ("blocks model processing until it completes", hooks docs), so the
  client's whole run time is added before Claude starts: at most about 1.6 s (the 1.5 s
  deadline plus local work), usually much less. Stage 0 does not promise zero added delay. The
  hook must not be made async: an async hook's `systemMessage` goes to Claude, which would
  break the rule that laya adds nothing to Claude's context.
- The port comes from `~/.laya-harness/config.json`. Hooks in the desktop app do not inherit
  variables exported in the user's shell, so the port is never read from an environment
  variable.

### 4.3 Starting the service

- The client starts the service **only when connecting is refused**, meaning nothing is bound
  to the port. It never starts one on a timeout, an error, a `loading` reply, or a reply that
  is not from laya-harness.
- The service is started fully detached, and the client does not wait:
  `Popen([venv_python, "-I", "-m", "laya_harness.service"], stdin=DEVNULL, stdout=DEVNULL,
  stderr=<append to ~/.laya-harness/service.log, mode 0600>, start_new_session=True,
  cwd=~/.laya-harness)`. Then the client exits.
- The client exits promptly after spawning. The design review found that the hook runner
  bundled with Claude Code 2.1.288 and 2.1.289 kills everything a still-running hook started
  when the hook times out; the docs do not say this. Acceptance (§8, step 3a) confirms that a
  service spawned this way reaches `ready` after the hook exits and survives the session
  closing.
- **Warm-up wait (SessionStart, `startup` only; D7).** After making sure the service is
  running, the client polls `/v1/health` until it reports `ready`, for at most 4 s in total,
  with each poll's timeout capped at the time left. It stops waiting at once on `not_ready`, on
  any reply that is not from laya-harness, on an error reply, when the first poll times out, or
  when mode is `off`. It keeps waiting only while the state is `loading`, or while the port is
  refused just after this hook spawned the service. Check 6 measured 2.1–2.8 s from spawn to
  ready, so the first reply after the service has been idle is usually about that much slower.
  The other SessionStart sources (`resume`, `clear`, `compact`, `fork`) never wait.

### 4.4 Service

Run as `python -I -m laya_harness.service`. It never writes to stdout.

**Startup order:**

1. Using the standard library only: read `config.json`, check that `idle_seconds` is a positive
   number (anything else, NaN included, exits 1 before binding, so a broken watcher can never
   keep the model resident), then bind `127.0.0.1:<port>`. If the port is taken, exit 0. **The
   bind is the single-instance lock,** so two sessions can never load the model twice.
2. Serve `GET /v1/health` from a thread. It returns
   `{"app": "laya-harness", "version", "pid", "state": "loading|ready|not_ready", "reason"}`.
   Until the model is ready, `POST /v1/profile` answers 503 `{"state": "loading"}`.
3. Set `HF_HUB_OFFLINE=1`, import laya_mlx, and load the checkpoint **from the absolute local
   directory in `config.json`, never by repo id.** If `config.json` records a revision that is
   not the pinned one (the pin was bumped but setup not re-run), the load fails with
   `run laya-harness setup`, so no row is ever labelled with a checkpoint that was not loaded.
   - Load with `batch_size=1` and `pad_to_multiple=128`, then set `agent.cfg["max_len"] = 512`.
     Check 6 showed why: batching the three questions raised MLX peak memory to 1.37 GiB,
     against 1.17 GiB one at a time at the same speed; and without padding, the first prompt of
     each new length took up to 8.5 s.
   - Write the effective calibration temperatures to `service.log` once.
   - Warm every padded length (128, 256, 384 and 512 tokens) with throwaway prompts of
     increasing size, about 1.7 s in total. The state is then `ready`.
4. **If any of step 3 fails** (missing or corrupt files, a tokenizer error, a Metal error),
   the state becomes `not_ready` with the reason, and the service **stays bound** until its
   idle timeout. A broken model therefore never causes a cycle of restarts, each loading about
   1 GB.

**Requests:**

- The service rejects any request whose `Host` is not `127.0.0.1:<port>` or `localhost:<port>`,
  any request with an `Origin` header, and any POST that is not `application/json`. This
  blocks browsers reaching localhost through CSRF or DNS rebinding. Other processes run by the
  same user are out of scope, since they can read the log anyway.
- All MLX work runs under **one lock**. Health checks are answered on a separate thread while
  inference runs.
- `POST /v1/profile` takes `{"prompt": str}`. It returns Laya's raw `answers` and `usage`,
  plus `checkpoint` (repo and SHA), `question_set` (id and sha256), and the laya-mlx and
  laya-harness versions. If inference raises, the reply is 500 `{"error": <exception class>}`
  with one line in `service.log`, and the service stays `ready`.
- The real predictor passes at most the first 65,536 characters of a prompt to laya-mlx, far
  more than 512 tokens of any text, so a huge paste cannot hold the interpreter lock for
  seconds while it is tokenized. `truncated` is unaffected.
- The questions file and config are read once at startup. **After changing code, config or
  questions, run `laya-harness stop`.** Version checks between client and service are deferred
  (§11).
- **Idle exit.** Idle time is counted from the end of the last health or profile request, or
  from the end of loading if that is later. A rejected request (400, 403, 404, 415) does not
  count. The service never idles out while `loading`, so a hung load keeps answering `loading`
  at once and `laya-harness stop` can still find it. On idle exit the service first closes its
  listener, so a later connect is refused and the client starts a fresh service (§4.3); it then
  finishes every request it has already accepted, and exits 0. A connection that sends nothing
  is dropped after 5 s, so it cannot keep the model resident. (The 5 s applies to each read: a
  local process that trickles a byte every few seconds can hold the exit open. Same-user
  processes are out of scope, and a browser cannot do it; see §11.)
- A client that gives up before its reply (its 1.5 s deadline) is routine: the broken pipe is
  not logged. Other handler errors still go to `service.log` with a traceback.
- A **fake-model mode** (set in `config.json`) returns fixed answers without importing
  laya_mlx. Tests and the first acceptance step use it.

### 4.5 Checkpoint and setup

- **Checkpoint:** `aac6fef/laya-mlx`, the general English model (ModernBERT-large, 421M,
  512-token context). It is pinned in the committed file `laya_harness/checkpoint.json`:
  revision `047678560251f28113ee8f5df4be82102c7bf336` and weights sha256
  `b9c07bf14be2fa5c78a9193a3e6d840ac80e89e62fc40f425834c3d8a6eaa3de`, both taken from
  laya-mlx's `benchmarks/results/hub-publication.json`. Any change of checkpoint is a reviewed
  diff.
- It was not chosen for a benchmark score. The typed-decisions checkpoint's 0.766 was measured
  on its own four synthetic workflows and does not carry over to coding prompts. **Every
  stage-0 checkpoint is expected to be near chance on these questions and uncalibrated for
  them.** Stage 2 compares checkpoints.
- **`laya-harness setup`** is run by the user. It is the only thing that touches the network,
  and the user approves the 807 MB download first. In order, it:
  1. creates `~/.laya-harness` with mode 0700;
  2. downloads the pinned commit, only the files laya-mlx needs (`model.safetensors`,
     `rl_agent_config.json`, `encoder/config.json`, `tokenizer/*`, `mlx_config.json`), into
     `~/.laya-harness/models/laya-mlx@<sha>`, and checks the weights' sha256. A copy already in
     place is reused only when every required file is present and the weights match; check 6
     left one there. If a download leaves a required file missing or the weights wrong, setup
     fails;
  3. writes `config.json`: interpreter path, model directory, repo and SHA, port `47913`, and
     mode `show`. The file's other fields are `model_mode` (`real`, or `fake` for tests and
     acceptance step 1, with `fake_answers`) and `idle_seconds` (900);
  4. runs the exact registered hook argv once with a sample input;
  5. prints the `settings.json` snippet. It never edits `settings.json` itself.

### 4.6 Session state

The client owns session state, one file per session:
`~/.laya-harness/sessions/<session_id>.json` (mode 0600), holding
`{model, effort, model_source, switched_at, first_prompt_after_switch_at, prompt_count,
model_line_shown, plan_shown, updated}`.

The desktop app gives hooks **no model or effort on a session's first prompt** (Appendix C), so
both start unknown. They are filled in for logging as they become visible:

- `PostModelSwitch` sets `model` from `to_model` (`model_source: post_model_switch`), records
  `switched_at`, and clears `first_prompt_after_switch_at`. The next human prompt sets
  `first_prompt_after_switch_at` to its own submission time.
- From the second human prompt on, the client reads the transcript's last assistant row and
  takes its `effort` as the row carries it (none if the row has none, or carries something other
  than a string, so a stale effort is never logged against a model that takes no effort), and takes `message.model` (`model_source: transcript`) **only if no switch is
  pending**. A switch is pending until the transcript holds an assistant row timestamped after
  `first_prompt_after_switch_at` (strictly after; a row without a timestamp never ends a
  pending switch). Assistant rows carry no `promptId`, so timestamps are the
  link. This matters because check 2 saw the transcript still showing the old model after a
  switch. Without the rule, a stale reply would overwrite the switch and log the old model
  against a prompt that runs on the new one.
- The client reads only the transcript's tail (the last 256 KB) to keep the hook fast, skipping
  a cut-off first line, rows that are not JSON objects, sidechain rows and synthetic models. A
  `transcript_path` that is not a string, is not a regular file (a device or a FIFO would
  block), or is missing or unreadable leaves the values as they were. The reader cannot detect a lagging transcript; the pending-switch rule
  above handles that.
- A session file that cannot be read as a JSON object with the expected field types starts again
  from the defaults, so one corrupt file cannot turn every later prompt in that session into an
  error.
- The `startup` and `fork` sources reset `prompt_count`, `model_line_shown` and `plan_shown`;
  `resume`, `clear` and `compact` leave them alone. On each **human** prompt (§4.7), the
  client increments `prompt_count` before calling the service.

### 4.7 Prompt source

`UserPromptSubmit` also fires on turns the user did not type. Each prompt is classified from
the hook input:

| Source | Recognised by (observed in check 4) |
|---|---|
| task-notification | the prompt starts with `<task-notification` |
| agent | the prompt starts with `<agent-message` (a subagent handing back) |
| peer | the prompt starts with `<cross-session-message` (another session) |
| subagent | `agent_id` is present, or `transcript_path` contains `/subagents/` (not seen in the desktop app; kept as a guard). `agent_type` alone is not used: the hooks docs say it is also set in a main session started with `--agent`. |
| human | everything else |

The prefixes are checked first, so a prefixed prompt is classified by its prefix even when it
also carries `agent_id`.

Non-human prompts are logged with their source and are **not sent to the service** (status
`skipped`), which saves the inference for turns that never show a line. They never show a line
and never change
`prompt_count`. `/loop` and scheduled-task turns look human, which stage 0 accepts. The
transcript records each turn's origin exactly (`origin.kind`), and the stage-2 history reader
uses that instead of these prefixes.

### 4.8 Questions

`laya_harness/questions/profile_v0.json` (shipped inside the package) has an `id` and per-question display thresholds. The service
records its sha256.

| Field | Type | Question | Shown when |
|---|---|---|---|
| `difficulty` | choice | How much work does the request in this message need? Options, in this order: *quick question or tiny edit* / *routine single-area change* / *multi-file feature or debugging* / *architecture, migration or hard reasoning* | tier probability ≥ 0.8 (§4.9) |
| `plan_first` | noul | Should this request be planned before any file is edited? | noul ≥ 0.85 plus the MODE rules |
| `parallel` | noul | Does it contain independent subtasks that could run in parallel? | never in stage 0 (logged only); its threshold of 0.85 is recorded for stage 4 |

Choice and yes/no only, because upstream calls ordinal `score` the weakest question type.

### 4.9 Claude Code adapter rules

Current models only, **never Fable.** Each decision logs the profile value, the harness state
it was compared with, the mismatch type, and the channel it will use from stage 4.

**MODEL + REASONING (from `difficulty`)**

- **Tier:** light = P(quick) + P(routine); heavy = P(multi-file) + P(architecture). The tier
  with the larger sum is chosen, and a tie goes to light. The line is eligible only if that sum is
  ≥ 0.8 (D11). Check 6: on the first prompts of
  100 past sessions it would fire 81% of the time at 0.6 and 13% at 0.8, and the rule is at
  most about one session in five.
- **Suggestion:** within the chosen tier, the more likely class (quick or routine, or
  multi-file or architecture; a tie goes to the lighter class) is looked up in the fit table, and the cheapest allowed option is
  suggested (§4.13). With the default table: quick → Haiku 5.5 at low, routine → Sonnet 5.5 at medium,
  multi-file → Opus 5.5 at high, architecture → Opus 5.5 at xhigh.
- Shown **only on the first human prompt of a session** (`prompt_count` was 0), at most once.
  A dropdown change made during the first turn applies from turn 2, while the context is still
  small. Switching later throws away more of the model-scoped prompt cache.
- **Not compared with the current setting** (decision D10), because the app gives hooks no model
  or effort on the first prompt. The line names what fits the task, and the user checks it
  against the dropdown. The model and effort the session actually runs are logged as they
  become visible (§4.6), so stage 2 can measure how often the line was redundant or followed.
  Compared suggestions are deferred to stage 4.
- If the service fails on that prompt, the session gets no model line. That is logged, and
  acceptance records how often it happens.
- Channel: user.

**MODE (from `plan_first`)** — shown only when all of these hold:

- noul ≥ 0.85;
- `permission_mode` is not `plan`, and the prompt, ignoring leading whitespace, does not start
  with `/plan` (a longer command such as `/planning` also matches, which errs toward silence);
- it is the first human prompt, or the prompt is at least 200 characters long;
- `plan_shown` is false for this session.

The line appears as the turn starts, after the synchronous hook has held the prompt for at
most about 1.6 s (§4.2). It cannot change the mode of the turn it appears with; switching to
Plan mode then applies from the next prompt. Stage 4 moves it to a harness note that Claude can
act on in the same turn. Channel: user now, harness from stage 4.

**PARALLELISM (from `parallel`):** logged, never shown. Channel: harness from stage 4.

**Numbers shown:** the tier line shows the tier's summed probability; the plan line shows
`noul`. **Gating uses the values exactly as laya-mlx returns them** (each probability rounded to
four decimals); the tier sum adds two such values and is rounded to four decimals, so float noise
cannot move a value across a threshold. **Display formats the gated value to two
decimals** (`f"{v:.2f}"`), so 0.7802 shows as `p=0.78`. Laya's `confidence` field is never used
for display or gating, because for `choice` it is normalised entropy, not a probability. These are raw scores after upstream's
temperature scaling and are **not calibrated for this task** until stage 2 measures them.

### 4.10 Decision log

`~/.laya-harness/decisions.jsonl` (mode 0600) gets **one row per UserPromptSubmit,
failures included,** unless the mode is `off`. A client error (bad input, a failed write of
session state) still leaves a row with status `error`, carrying whatever keys are known. Rows
are JSON with non-ASCII escaped, so a prompt with a broken surrogate is still logged. The row
is written before the session's "shown" flags are saved, so a failed write can never mark a
line as shown that the user did not see.

| Group | Fields |
|---|---|
| Keys | `schema_version`, `ts`, `session_id`, `prompt_id`, `transcript_path`, `cwd`, `source` |
| Outcome | `status`: decided, skipped (non-human prompt, not sent), started_service, loading, not_ready, timeout or error; `mode`; `shown_text`, and `suppress_reason` recorded per line as `{model, plan}`, each one of: below_threshold, not_first_prompt, not_human, plan_mode, already_shown, too_short, no_fit or log_only. When several apply, the first in this order is recorded: model line not_first_prompt, below_threshold, no_fit; plan line below_threshold, plan_mode, too_short, already_shown; `suggestion` (model id, effort, class) |
| Input | `prompt`, `truncated` (from Laya's `usage`) |
| Laya output | the raw `answers` and `usage` |
| Versions | `checkpoint` (repo, SHA), `question_set` (id, sha256, as reported by the service when it answered), `laya_mlx`, `laya_harness` (the client's) and `service_laya_harness` (the service's, when it answered), `adapter_rules`, `catalog` (sha256 of the catalog and the fit table). A question set that differs between client and service also gets a line in `client.log`. |
| Session state | `model`, `effort` and `model_source` as known at that prompt (§4.6), `permission_mode` |
| Timing | `latency_ms`, `cold` |

- Rows join to Claude Code transcripts on `prompt_id` (confirmed in check 4).
- Everything stays on this Mac. This log seeds stages 2 and 3.

### 4.11 Commands

All commands use the standard library only, apart from the download in `setup`.

| Command | Does |
|---|---|
| `laya-harness setup` | §4.5 |
| `laya-harness status` | one line: down / loading / ready / not_ready (with reason), mode, checkpoint SHA, log paths, and any model seen in the log that the catalog does not list |
| `laya-harness stop` | stops the PID reported by `/v1/health`. It warns when mode is not `off`, since the next prompt restarts the service. |
| `laya-harness mode show\|log-only\|off` | `show` is normal. `log-only` logs everything and shows nothing. `off` makes the client exit at once, without starting anything or logging. |

`LAYA_HARNESS_HOME` moves the state directory, and with it `config.json` and the port, **in
tests only.** Under the test flag, the client and service refuse to use `~/.laya-harness` or
port 47913.

### 4.12 What the user sees (copy deck — the mockup)

The line is delivered as the `UserPromptSubmit` hook's `systemMessage`. It is shown to the user
and not added to Claude's context: the hooks docs say so, and the bundled Claude Code 2.1.288
and 2.1.289 do not pass it to the model. At most two lines, joined by `\n`, each at most 120
characters. Stage 0 never blocks a prompt and never adds `additionalContext`.

**Rendering (check 1).** The Code tab shows the message as a collapsible *Claude Code notice*
and puts `UserPromptSubmit says:` in front of each line. That prefix does not name laya, so
every line keeps its own `laya ·`. Long lines wrap. Screenshots of the surface, taken with the
check-1 test strings, which differ slightly from the final copy below:
[single line](../../mockups/stage0-check1-single-line.png),
[two lines](../../mockups/stage0-check1-two-lines.png), and
[a machine turn wrongly given a line](../../mockups/stage0-check4-machine-turn.png), which §4.7
now prevents.

**This copy deck, plus those screenshots, is the mockup.**

| State | Exact text |
|---|---|
| (a) first human prompt, light tier ≥ 0.8, model with effort levels | `laya · light task (p=0.86) → Sonnet 5.5 at medium effort fits this task` |
| (a) first human prompt, light tier ≥ 0.8, default quick option | `laya · light task (p=0.86) → Haiku 5.5 at low effort fits this task` |
| (a) first human prompt, light tier ≥ 0.8, option without an effort (for example Haiku 4.5, if the fit table names it) | `laya · light task (p=0.86) → Haiku 4.5 fits this task` |
| (a) first human prompt, heavy tier ≥ 0.8 | `laya · heavy task (p=0.91) → Opus 5.5 at xhigh effort fits this task` |
| (d) plan first | `laya · reads like a multi-step change (p=0.88) → Plan mode (mode menu, then 4), or tell Claude to plan first` |
| (e) both on the first human prompt | (a) on the first line, (d) on the second |
| (g) nothing shown | the service is starting, loading, not ready, slow or erroring; the prompt is not human; a score is below its threshold; not the first human prompt (model line); plan already shown, already in Plan mode, or the prompt is too short; mode is `log-only` or `off` |

The model name in (a) is the catalog's `display` name, and the effort is the fit-table option's
effort (§4.13). A model with no effort levels is named without one.

### 4.13 Model catalog and fit table (Claude Code adapter)

Laya judges only how much the task needs (§4.9's tier and class); it never sees a model name.
Which model and effort to suggest is deterministic adapter data (D12, D13).

- **Catalog:** `laya_harness/data/claude_code_models.json`, committed. It has one entry per model
  and version in the desktop app's model picker: `id`, `display` name, `family`, `version`,
  `price` (input and output per MTok, plus `input_above_100k` and `output_above_100k` where pricing
  is tiered; cache-read prices are left out until a later stage uses them), `effort_levels` (empty
  for a model that takes none), `in_picker`, `menu` (`main` or `more`) and `allowed`, under a
  top-level `source` note that names where the values came from. The user or controller confirms `in_picker` when the catalog
  is refreshed.
  - **Fable is never allowed.** The rule refuses any model whose family, id or display name
    contains "fable" or "mythos" (Mythos is Fable's sibling line), whatever the `allowed` flag
    says and in any letter case.
  - The newest version in each family is allowed by default. Older versions are listed with
    `allowed: false` and opted in by editing the file, for example to keep a version whose
    behaviour the user prefers.
  - **Starting catalog.** The picker contents come from the user's screenshot
    (`docs/reference/model-picker-2026-10-08.png`). IDs and prices come from the models
    overview and the Haiku 5.5 page on platform.claude.com (read 2026-10-08), and the older
    versions' effort levels from the effort docs on platform.claude.com (read 2026-10-08). The IDs of the
    older versions also appear in the user's transcripts.

    | Model | ID | Picker | Allowed by default | Price in / out per MTok | Effort levels |
    |---|---|---|---|---|---|
    | Opus 5.5 | `claude-opus-5-5` | main menu | yes | $4 / $20 | low–max (default medium) |
    | Sonnet 5.5 | `claude-sonnet-5-5` | main menu | yes | $2 / $10 | low–max (default high) |
    | Haiku 5.5 | `claude-haiku-5-5` | main menu | yes | $0.10 / $0.50 for prompts up to 100k tokens; $0.50 / $2.50 above | low–max (default medium) |
    | Opus 5 | `claude-opus-5` | More models | opt-in | $5 / $25 | low–max |
    | Opus 4.8 | `claude-opus-4-8` | More models | opt-in | $5 / $25 | low–max |
    | Opus 4.7 | `claude-opus-4-7` | More models | opt-in | $5 / $25 | low–max |
    | Opus 4.6 | `claude-opus-4-6` | More models | opt-in | $5 / $25 | low, medium, high, max |
    | Sonnet 5 | `claude-sonnet-5` | More models | opt-in | $2 / $10 | low–max |
    | Sonnet 4.6 | `claude-sonnet-4-6` | More models | opt-in | $3 / $15 | low, medium, high, max |
    | Haiku 4.5 | `claude-haiku-4-5` | More models | opt-in | $1 / $5 | none |
    | Fable 5.1, Fable 5 | `claude-fable-5-1`, `claude-fable-5` | listed ("requires usage credits") | **never** | $10 / $50 | low–max |

  - The Fable entries exist only so that the catalog recognises them and the rule can refuse
    them; their values are never used for a suggestion.
  - Haiku 5.5 was released on 2026-10-07. Anthropic positions it for high-volume work such as
    classification, routing, extraction and subagent tasks, not specifically for coding. It is
    in the default fit table only for quick tasks, and stage 2 checks how it does there.
- **Fit table:** `laya_harness/data/claude_code_fit.json`, committed and edited by the user. For
  each difficulty class it lists the acceptable options. An option names either a family (its
  newest allowed version) or a specific model id, plus an effort. Defaults:

  | Class | Acceptable options |
  |---|---|
  | quick | Haiku at low; Sonnet at low |
  | routine | Sonnet at medium |
  | multi-file | Opus at high |
  | architecture | Opus at xhigh |

- **Rule (cheapest that fits).** Take the class §4.9 chose, keep the options whose model is
  allowed and in the picker, and suggest the one with the lowest input price (the base tier
  where pricing is tiered); ties go to the newest version, compared number by number (5.5 is
  newer than 5, and 4.10 newer than 4.8). Every current model prices output at 5× input, so
  ordering by output gives the same result.
  - An option qualifies only if its model supports the option's effort. An option may leave the
    effort unset, and the line then names only the model; that is the only way a model with no
    effort levels (Haiku 4.5) is suggested. An option asking for an effort the model lacks
    (xhigh on Opus 4.6) does not qualify, and the next option is tried.
  - An option whose model cannot be resolved (not in the catalog, not allowed, not in the
    picker) is skipped, and the next option is tried. If no option qualifies, nothing is shown
    (`suppress_reason: no_fit`).
  - Older versions currently cost the same as, or more than, the newest in their family. So an
    opted-in older version is suggested only when the fit table names it by id and no cheaper
    option fits.
- **Refresh.** Hooks cannot read the app's picker, so the catalog is edited by hand when models
  change, as a reviewed diff. `laya-harness status` lists any model seen in the decision log
  (from `PostModelSwitch` or the transcript) that the catalog does not know.
- **Learning (stages 2–3).** The user's history spans many versions. Stage 2 measures, per model
  and version, which classes ran without interruptions or corrections and at what token cost,
  and proposes fit-table changes as reviewed diffs.

## 5. Failure handling — laya stays out of the way

| Situation | What happens |
|---|---|
| The hook cannot launch (missing interpreter, broken install) | Exec form exits 1 or 127: a non-blocking notice. Never 2, so a prompt is never blocked. |
| Any client error | Nothing on stdout, exit 0, one line in `client.log`, a row with status `error`. |
| Nothing bound to the port | The client starts the service detached and shows nothing (`started_service`). |
| Service loading | The client gives up at once (`loading`). |
| Reply over 1.5 s, or unexpected | Nothing shown (`timeout` / `error`). |
| Port held by something that is not laya, or a listener that never replies | No service started, nothing shown, one line in `client.log`. |
| Weights missing or corrupt, or load fails | `not_ready` with a reason; the service stays bound; nothing is downloaded and nothing restarts in a loop. |
| Inference raises | 500 from the service, nothing shown (`error`); the service stays `ready`. |
| A load that kills the process (a native abort, a jetsam kill) | The port is freed, so the next prompt starts another load. Known limitation; a crash marker is deferred (§11). |
| Prompt longer than 512 tokens | Laya keeps the beginning (the service passes at most 65,536 characters); the row is marked `truncated`. |
| Stale service after a code or config change | `laya-harness stop`. Every row records the versions that produced it. |

**Explicit hook timeouts:** SessionStart 8 s (it may wait 4 s, §4.3), UserPromptSubmit 3 s, PostModelSwitch 3 s. The service listens on 127.0.0.1 only. `~/.laya-harness` is mode 0700.

## 6. Testing

- **Unit tests (fakes):**
  - adapter rules: model line only when `prompt_count` was 0; never Fable; no `decision` key
    ever; the tier sums and the 0.8 gate; MODE eligibility; once per session; no plan line in
    Plan mode; a noul of 0.30 with `confidence` 0.70 shows nothing; the number shown is the
    gated value formatted to two decimals (including 0.7802 → `0.78` and a value just under a
    threshold, such as 0.8496 for 0.85, being suppressed even though it would display as `0.85`);
  - switch precedence (regression): a `PostModelSwitch` to model B, then a transcript whose last
    reply is still model A, keeps B; a later reply on B, timestamped after the first prompt
    submitted after the switch, is accepted; a reply on A from the turn that was in flight
    during the switch is ignored;
  - the catalog and fit table: the cheapest allowed option wins, ties go to the newest; Fable is
    never suggested, even if listed; a disallowed or not-in-picker model is skipped; an older
    version is chosen only when the fit table names it and nothing cheaper fits; a model with no
    effort levels is named without one; no qualifying option gives `no_fit`;
  - canonical model names; prompt-source detection on the payloads captured in check 4;
    session-state updates from `PostModelSwitch` and from the transcript, including a missing
    transcript; the question-file format; assembling a profile; SessionStart and
    PostModelSwitch print nothing.
- **Client, process-level.** These run the exact registered argv from the shared function,
  with a temporary `LAYA_HARNESS_HOME` and a free port. Cases: bad event name, garbage stdin,
  service down, slow reply, unexpected reply, a foreign listener returning junk, a listener that
  never replies. Each must give exit 0, stdout empty or one JSON object with only
  `systemMessage`, and a service started only on connection refused.
  - Spawn test: with the client's stdout and stderr as pipes, it starts a long-lived fake
    service that sleeps and prints. Both pipes close within about 0.2 s of the client exiting,
    and the child is still alive.
  - SessionStart wait: waits while the service reports `loading` and returns once it is
    `ready`; gives up after 4 s; returns at once on `not_ready`, a foreign listener, an error
    reply, a first-poll timeout and mode `off`; never waits for `resume`, `clear`, `compact`
    or `fork`.
- **Service (fake model, no weights):**
  - endpoints, with every field of health and profile; the Host, Origin and Content-Type checks
    on GET and POST; bad bodies (400) and unknown paths (404); a bind to 127.0.0.1 only;
  - N services started at once with a fake 3 s load, giving exactly one load while the others
    exit 0 within 1 s (measured about 0.1 s); a service whose port is taken, and a fake-mode
    service, import nothing outside the standard library (no laya_mlx, no mlx);
  - one MLX lock, with health answered while inference runs; nothing written to stdout, ready
    or not ready; a predict failure answered 500 with the service still `ready`;
  - idle exit on a short timer: never mid-request, never while loading, counted from the last
    health or profile request; refusing rather than resetting a late connect; finishing a
    request already accepted; not held open by a silent connection; a bad `idle_seconds`
    exiting before any load;
  - a failing or corrupt load giving `not_ready` while staying bound, loading once over several
    prompts, then idling out;
  - the real predictor with a stand-in laya_mlx: `HF_HUB_OFFLINE` set before the import, the
    check-6 load arguments, `max_len`, every warm-up length, the temperatures on stderr, the
    version, the prompt cap and a revision mismatch; a missing model directory never
    triggering a download (`snapshot_download` patched to fail the test if called).
- **Real model:** check 6 only, run on request.

## 7. Check first (throwaway, before writing anything to keep)

**All six checks were run on 2026-10-08; the results are in Appendix C.**

Checks 1–5 use a throwaway hook in this project's own `.claude/settings.local.json`, which
records the raw stdin, `$CLAUDE_EFFORT` and timestamps to a scratch file and is removed
afterwards. Check 6 needs the checkpoint download. **The user is asked before either.** Steps
that need the desktop app's UI are done by the user, following written steps.

1. **Display.** Return a `systemMessage` with the shortest state and with the longest two-line
   state (e). Screenshot both in the Code tab; these complete the mockup. Look for a Plan-mode
   shortcut. If the line does not render, the fallbacks in order are a display-only band in the
   Code tab (a Claude Code plugin) and a macOS notification. The copy deck and mockup are then
   redone for that surface before sign-off.
2. **Model.** Pick a non-default model in the dropdown before the first message, then send a
   prompt. Record what SessionStart receives, and whether `PostModelSwitch` fires (and when,
   relative to UserPromptSubmit) on that pick, on a mid-session change, and on resume.
3. **Effort.** Is `$CLAUDE_EFFORT` set in the UserPromptSubmit hook's environment?
4. **Payloads.** Trigger a typed prompt, a background subagent reporting back, a background
   Bash command finishing, a message from another session, and a small workflow. For each,
   record whether the hook fired, plus the start of `prompt`, `agent_id`, `agent_type`,
   `transcript_path` and `session_id`. Confirm `prompt_id` equals the transcript's `promptId`.
   Keep one UserPromptSubmit and one SessionStart payload, with the prompt text scrubbed, as
   test fixtures.
5. **Exec form with a space.** An exec-form hook whose absolute command path contains a space
   runs in the Code tab.
6. **Real model on the M2.** One script, with the desktop app open, `HF_HUB_OFFLINE=1`, the
   pinned checkpoint, the three real questions, and two prompts: about 100 tokens, and one that
   fills 512 tokens. Measure: time from spawn to the first `/v1/profile` answer; first-call
   latency; warm p50 and p95 over about 20 calls; whole-process RSS and MLX peak memory.
   - Pass: all three questions answered; the four choice probabilities sum to 1 within 0.0002
     (each is rounded to four decimals); each noul is in [0, 1];
     the long prompt is marked truncated; warm p95 under about 1.0 s (otherwise lower the token
     cap); peak memory under about 1.2 GB.
   - The cold-start time goes to the user, who decides whether stage 0 needs a SessionStart
     wait (decision D7).
   - Optional, asked together with the download: run the three questions over 50–100 past
     prompts and count how often each line would fire. Raise a threshold if its line would
     fire in more than about one session in five.

## 8. Acceptance (stage 0 is done when)

In real Code-tab sessions, with the hooks registered as in §10 (project-level during
acceptance):

1. **Fake model, then real.** With the fake model returning a fixed profile, the lines match
   §4.12 exactly and the rows are logged. With the real model, record whatever appears.
2. **No harm.** Over at least 20 prompts: zero blocked prompts, zero hook-timeout notices, and
   the **complete UserPromptSubmit hook duration** at most about 1.6 s worst case. The client
   logs it from process start to exit, covering the service call, the transcript read,
   session-state updates and logging.
3. **Down paths.** (a) Service stopped, one prompt: nothing shown, Claude responds, the service
   is started exactly once, reaches `ready` after the spawning hook has exited, and is still
   running after that session is closed. (b) Model directory empty: several prompts show nothing, and
   nothing restarts in a loop. (c) A fake listener that never replies: the prompt goes through
   within about 1.6 s with nothing shown.
4. **Cold start.** In a new session with the service stopped, SessionStart waits and the
   first prompt gets a profile, with the first reply delayed by at most about 4 s. Record the
   share of sessions whose first human prompt still got no profile; that is information, not a
   gate.
5. **Off switch.** With `laya-harness mode off`, no row is written and nothing is started.

## 9. Build order and process gates

1. Sign-off on this document and the mockup (§4.12 plus check 1's screenshots).
2. Add pytest to the project venv, which was created for check 6 (Python 3.11.17,
   laya-mlx 0.3.0, MLX 0.32.3), add a trivial test, and run it.
3. Draft the two-agent gate profile from commands that have actually been run: pytest on fakes
   for implementers; controller-only tiers for the real model (check 6), real-session acceptance
   and the install diff; visual verification against §4.12. The user signs it off before the
   first implementer is dispatched.
4. Implementation plan (writing-plans), then the build.
5. Acceptance (§8), then install (§10).

## 10. Install and uninstall

- During acceptance, the hooks live in this project's `.claude/settings.local.json`.
- At the end of stage 0, three exec-form entries go into the user-level
  `~/.claude/settings.json` so laya runs in every project: SessionStart (8 s), UserPromptSubmit
  (3 s) and PostModelSwitch (3 s). `setup` prints the snippet and has already run the exact
  command. **The diff is shown to the user and applied only with approval.**
- `laya-harness mode off` turns laya off without touching settings. Removing the entries
  uninstalls it. `~/.laya-harness` holds every piece of state.

## 11. Deferred

| To | Item |
|---|---|
| Stage 2 | Version checks between client and service, reloading the questions file without a restart, a stuck-inference watchdog, an outage notice. |
| Stage 2 | Memory pressure on the 8 GiB Mac: latency after 10–15 idle minutes with sessions open; then set_wired_limit, cache limits, or accepting logged misses. |
| Stage 2 | Question wording: an effort-scale `difficulty` without topic words, compared on history. |
| Stage 2 | Checkpoint comparison (English, typed-decisions, multilingual) on a labelled set; tune thresholds on history; apply the prompt-source filter in the history reader. |
| Stage 2 | How often the uncompared model line (D10) was redundant, and how often it was followed, from the logged session state. |
| Stage 2 | A fit table from evidence: per model and version, which classes ran without interruptions or corrections and at what token cost, proposed as reviewed diffs to the fit table (§4.13). |
| Stage 3 | Refit per-field thresholds and calibration from outcomes and labels. |
| Stage 4 | MODEL and REASONING as separate suggestions compared with the current setting (known from the second prompt on): effort on later prompts, model after clear, compact or resume; harness notes for MODE and PARALLELISM; prompt-stopping never fires on non-human turns; calibrated wording for scores. |
| Stage 5 | CONTEXT advice using SessionStart's `prompt_cache_likely_expired`, `seconds_since_last_response` and `context_tokens`, and PostModelSwitch's `prompt_cache_warm` and `estimated_cache_write_usd` (all observed in check 4). |
| Stage 2 | The idle-timeout length, or a launchd agent, chosen from the cold-start share recorded in acceptance step 4 and from memory pressure (F14). |
| Stage 2 | A crash marker, so a load that kills the process (a native abort, a jetsam kill) is not retried on every prompt (§5). |
| Stage 2 | A per-connection deadline, so a local process trickling bytes cannot hold the service's idle exit open (§4.4). |

## Appendix A — Decisions

| # | Date | Decision |
|---|---|---|
| D1 | 2026-10-07 | Laya is a local execution router above the harness, not a model router and never inside the agent loop. |
| D2 | 2026-10-07 | Build top-down: a crude end-to-end version first, then refine stage by stage. |
| D3 | 2026-10-07 | Order: Claude Code (0), Codex (1), measure (2), learn (3), act (4), widen (5). |
| D4 | 2026-10-07 | Training on the user's own history is part of the plan, not optional. |
| D5 | 2026-10-07 | The project lives at `~/Code Playground/laya-harness`, package `laya_harness`, in its own venv. |
| D6 | 2026-10-06 | When stopping prompts is switched on (stage 4), user-actionable mismatches stop the first prompt with an explanation. |
| D7 | 2026-10-08 | At first, no SessionStart wait until check 6 measured the cold start. Revised after check 6 (2.1–2.8 s to ready): a new session waits up to 4 s while the service is starting. |
| D8 | 2026-10-08 | Plan-first is shown in stage 0; parallel is logged only. |
| D9 | 2026-10-08 | Start with the general English checkpoint, pinned by SHA. |
| D10 | 2026-10-08 | The model/effort line is suggested on the first human prompt without comparison, because hooks cannot see the model or effort then (Appendix C). |
| D11 | 2026-10-08 | Model-line threshold raised from 0.6 to 0.8 under the spec's one-session-in-five rule (check 6). |
| D12 | 2026-10-08 | Best fit means the cheapest allowed model and effort that the fit table accepts for the task's class. |
| D13 | 2026-10-08 | The catalog lists every model version in the picker. The newest per family is allowed by default, older versions are opt-in, and Fable is never allowed. |
| D14 | 2026-10-08 | Target architecture adopted: front doors (an Obsidian plugin and a web HUD, with voice) → a Bridge → **Laya as the tier router** (in place of TypeSafe's Jev, whose wire protocol laya-serve already speaks) → Tier 1 rules and vault data, Tier 2 a small fast model, Tier 3 a Claude Code or Codex session or skill → **Obsidian as the memory**, with a receipt per request. Stage 0 finishes its reusable core (Tasks 1–5: state, data, session state, adapter and catalog, the Laya service); the in-session hooks (Tasks 6–7) and stage-0 acceptance are parked until the Bridge design decides how the service is started. The Bridge gets its own spec and mockups. *Parking lifted by D15.* |
| D15 | 2026-10-08 | laya-harness is the umbrella and the UI is in its scope; §1's boundaries bind the Laya component. The first front door is a web HUD, without voice in its first phase; the Obsidian plugin comes later. The HUD stage follows stage 2 (Measure), so it shows measured confidence rather than raw guesses. The harness is built first: Tasks 6–7 and stage-0 acceptance are unparked as written, the hook starting the service itself; the Bridge later reuses or replaces that start-up path. |

## Appendix B — Design review (2026-10-07 to 2026-10-08)

Six independent critics (hook mechanics, model validity, walking-skeleton discipline,
operations and security, product fit, verification and process) raised 22 findings, merged
from 40: 15 major and 7 minor. Each was checked twice, once trying to refute it and once
deciding whether to fix it now or later. None was refuted: 8 were confirmed as stated, and 14
were real but overstated in severity or in the size of the fix.
19 were marked fix-now and 3 deferred; a final completeness pass added 5. The automated rewrite
was then trimmed to keep stage 0 thin.

| Id | Finding (short) | Resolution |
|---|---|---|
| F1 | Spawning from a hook can leak pipes or stdout into Claude's context | §4.3 spawn contract; explicit hook timeouts; spawn test |
| F2 | Launch failures can exit 2 and block every prompt | §4.2 exec form, `-I`, catch everything, exit 0 |
| F3 | SessionStart cannot warm the model before the first prompt | D7: a bounded 4 s wait on new sessions, sized from check 6's measured cold start |
| F4 | Loading by repo id contacts the network on every start | §4.4 offline local load; §4.5 pinned SHA, setup only |
| F5 | A TCP port alone allows concurrent ~1 GB loads | §4.4 bind before import; spawn only on connection refused; Host/Origin checks |
| F6 | The prompt hook fires on machine turns | §4.7 prompt source |
| F7 | Session state had no owner | §4.6 session files |
| F8 | The log could not be joined or attributed | §4.10 |
| F9 | No display thresholds | §4.8, §4.9 |
| F10 | Plan-first and parallel bypassed the adapter | §4.9 MODE rule; parallel logged only |
| F11 | Model and effort bundled | Deferred to stage 4 |
| F12 | The typed-decisions score does not transfer | D9; §4.5 |
| F13 | Long prompts may exceed the time budget | 512-token cap; check 6 |
| F14 | Memory pressure on 8 GiB | Deferred to stage 2 |
| F15 | No gate-profile step | §9 |
| F16 | `p=` was not tied to a field | §4.9 numbers shown |
| F17 | Question wording mixes size and topic | Deferred to stage 2 |
| F18 | Check 1 vs Claude receiving the line | Display-only, cited from the docs and shipped code |
| F19 | No version handshake or health escalation | Versions in every row; the rest deferred to stage 2 |
| F20 | Lifecycle commands undefined | §4.11 |
| F21 | Acceptance not measurable | §8 |
| F22 | Copy only for two states | §4.12 copy deck |
| C1 | Threading and watchdog | One lock around MLX; watchdog deferred |
| C2 | SessionStart waiting 8 s when broken | The §4.3 wait stops at once in every broken state |
| C3 | Load failures cause a restart loop | §4.4 step 4: `not_ready`, stays bound |
| C4 | Code changes not picked up | `laya-harness stop`; versions per row |
| C5 | UI steps and screenshots undefined | §7 and §8: UI steps done by the user |

## Appendix C — Check results (2026-10-08)

Run in the desktop app's Code tab (`CLAUDE_CODE_ENTRYPOINT=claude-desktop`) with a throwaway
exec-form hook in this project's `.claude/settings.local.json`, since removed. The raw captures
are kept git-ignored in `.claude/spike/` until the test fixtures are made from them.

| Check | Result |
|---|---|
| 1. Display | **Pass.** A UserPromptSubmit `systemMessage` renders as a collapsible *Claude Code notice*, each line prefixed `UserPromptSubmit says:`; two lines render as two prefixed lines; long lines wrap. Plan mode: open the mode menu, then press 4 (1 Auto, 2 Manual, 3 Accept edits, 4 Plan). |
| 2. Model | **Not available on the first prompt.** SessionStart input has no `model`, on `startup` or `resume`. A model picked before the first message fires no hook. A mid-session dropdown change fires `PostModelSwitch` (`source: sdk`, `from_model`, `to_model`) about 1 s before the next prompt. Resume fired no `PostModelSwitch`. At the first prompt's hook the transcript file did not exist yet. After a switch, the transcript still showed the old model when the next prompt's hook ran. Each transcript reply row carries `message.model`. |
| 3. Effort | **Not available to the prompt hook.** `$CLAUDE_EFFORT` is unset and the input has no `effort`. Each transcript reply row carries `effort` and `perTurnEffort`. |
| 4. Payloads | UserPromptSubmit input: `session_id`, `prompt_id`, `prompt`, `permission_mode`, `transcript_path`, `cwd`, `scratchpad_dir`, `session_title`, `hook_event_name`. The hook's `prompt_id` equals the transcript's `promptId`. SessionStart runs to completion before the first prompt is processed: a 3 s delay held it back. Machine turns fire UserPromptSubmit with prompts starting `<task-notification>`, `<agent-message from=` and `<cross-session-message from=`; no `agent_id` was ever present, and one task notification fired no hook. The transcript records origin per turn (`origin.kind`: human, task-notification, peer). SessionStart also carries `prompt_cache_likely_expired`, `seconds_since_last_response`, `context_tokens` and `estimated_cache_write_usd`. PostModelSwitch also carries `prompt_cache_warm`, `cache_ttl`, `pricing` and `requested_model`. |
| 5. Exec form, path with a space | **Pass.** The hook ran with `command` set to an absolute path inside "Code Playground". |
| 6. Real model on the M2 | **Pass, with three settings changes** (§4.4, §4.9). Run with the pinned checkpoint, offline, with the desktop app open and 37% of memory free. All three questions answered; choice sums 0.9999–1.0001; nouls in range; an 888-token prompt marked truncated (430 tokens dropped). Warm: 0.13 s typical, 0.43–0.47 s at 512 tokens. Without padding, the first prompt of each new length took up to 8.5 s (4 of 100 over 1.5 s); padded to multiples of 128 and warmed, the worst was 0.53 s with none over 1.5 s. MLX peak memory 1.37 GiB batched, 1.17 GiB one question at a time; whole-process RSS 0.6–0.9 GiB. Cold start with the final settings: 2.1–2.8 s from spawn to ready (imports 0.3–0.5 s, load 0.1–0.5 s, warm-up 1.7 s); the weights were in the file cache, so a start from a cold disk may be slower. Fire rates on the first prompts of 100 past sessions: model line 81% at 0.6, 43% at 0.7, 13% at 0.8; plan line 11% at 0.85; parallel 8% at 0.85. Fourteen obvious prompts: light/heavy tier right 14/14, exact class 9/14 (multi-file never chosen). |
