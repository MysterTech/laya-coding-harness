# Stage 0 acceptance and visual QA

Date: 2026-10-09 (Asia/Calcutta). Contract: spec §4.12 and §8; procedure: plan Task 8 and the project gate profile.

Status: **in progress**. Copy and execution evidence is recorded below. Screenshot comparison, the remaining acceptance scenarios and overall acceptance are pending.

| Surface/state | Evidence | Result |
|---|---|---|
| Fake light, first human prompt | User pasted the expanded Claude Code notice: `UserPromptSubmit says: laya · light task (p=0.86) → Haiku 5.5 at low effort fits this task`. Claude answered the prompt. | Exact copy matches §4.12. Full visual comparison pending a screenshot. |
| Fake heavy, first human prompt | User pasted the notice text: `laya · heavy task (p=0.91) → Opus 5.5 at xhigh effort fits this task`. Claude answered the prompt. | Exact copy matches §4.12. Full visual comparison pending a screenshot. |
| Fake plan-only, first human prompt | User pasted the exact plan-only notice and Claude answered the prompt. | Exact copy matches §4.12. Full visual comparison pending a screenshot. |
| Fake both | User approved the transition; service stopped and both-lines profile configured in mode `show`. Baseline: 6376 decision-log bytes, zero client/service bytes. | Awaiting a new Code-tab session in normal coding mode. |
| Real model and no-harm/down/cold/off checks | Not yet observed in real Code-tab sessions. | Pending. |

The light check has one decision row, status `decided`, session `f6ae72ed-2fb0-45e9-9fed-6938b59d5516`, prompt `c7bb18fb-9c34-4893-b64b-dc8ffb29c78e`. Its recorded hook duration is **41.1 ms**, with the exact expected `shown_text`, fake-model provenance, no truncation and zero dropped characters. No new bytes appeared in `client.log` or `service.log` since the acceptance baseline. This is one prompt, not the required 20-prompt no-harm gate.

The heavy check has one new decision row past the heavy baseline (2118 bytes), status `decided`, session `49ab05e5-384c-4199-93c0-0ec43f35f01f`, prompt `2ab66b4b-e62b-4501-a995-20e55e8ed1f5`. Its recorded hook duration is **46.4 ms**, `cold: false`, with the exact expected `shown_text`, suggestion `claude-opus-5-5` / `xhigh` / class `architecture`, plan suppressed as `below_threshold`, fake-model provenance, no truncation and zero dropped characters. `client.log` and `service.log` are still 0 bytes. The row records an unknown session model (`null`); per D10, the model hint on the first human prompt is not compared with the current settings.

The service was stopped before changing to the both-lines fake profile, following explicit user approval. No configuration changes may occur during the next capture. The final visual verdict requires screenshots compared against the copy deck and `docs/mockups/stage0-check1-*.png`; pasted text does not establish layout, wrapping or visual fidelity.

The plan-only check has one new human decision row past the 4303-byte baseline, status `decided`, session `47577b93-27ea-467c-afe9-978919681891`, prompt `ac5ed00a-5330-4b0a-ac0f-46b73ba7c594`. Its recorded hook duration is **62.8 ms**, `cold: false`, with the exact plan hint, the model line suppressed as `below_threshold`, permission mode `auto`, fake-model provenance, no truncation and zero dropped characters. No client/service diagnostic bytes were added. After this observation, the user approved the both-profile transition; that profile is now configured for the next capture.
