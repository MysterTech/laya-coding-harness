# Temporary Codex acceptance timing preflight

Contract: Stage 1 design C7–C8. Scope: prepare and verify local workbench instrumentation; no shipping source edit, real-home config change, hook installation or model request.

1. Implement C8 instrument and requirement-derived subprocess tests in `.workbench/codex-timing/`, using the repo `.venv/bin/python` for tests and inherited registered interpreter for child commands. Demonstrate behavioral RED then GREEN. Preserve all advisor files.
2. Controller executes the focused tests before documenting their command/results, generates literal code blocks from verified files, and commissions an independent review against C8. Visual review N/A: no UI or copy changes.
3. Commit generated plan before preparing the exact temporary hook replacement. Show reviewed diff for user approval; do not install until approved.
4. After approval, install exact draft privately, record baseline and guide native reload/trust and human captures. Restore production hooks after measured acceptance. Claude acceptance remains deferred.

Literal verified blocks and observed gate results will be appended after preflight; none are guessed here.
