# Task 4 Report: One-Shot Codex CLI Workspace Execution

## Status

Completed and committed as `df750ee` (`Run one Codex call over selected sources`).

## Files

- `companion.py`
- `tests/test_companion_controls.py`

This report is recorded separately from the implementation commit.

## Implemented Scope

- Added `generation_source_workspace(payload)` to activate workspace execution only when more than one unique source is selected.
- Revalidated the conversation workspace and revision immediately before generation, preserved the actual `workspacePath` returned by validation, and rejected ordered source-ID mismatches or unreadable entries.
- Added a compact model-input contract that points Codex to `SOURCES.md`, preserves the user prompt, selected PDF text, current MarginNote node, task description, and write-target identifiers, and skips legacy document/upload text concatenation in multi-file mode.
- Kept `--sandbox read-only` and permitted only read-only inspection inside the selected workspace while forbidding mutation, patching, external side effects, and unrelated filesystem access.
- Started the multi-file Codex CLI process with the validated workspace as `cwd` and disabled the existing startup retry for that mode, preserving one `codex exec` invocation per request.
- Preserved the existing single-document system prompt, root `cwd`, document-context path, retry behavior, and backend routing.
- Required Codex CLI for multi-file requests. OpenAI-only, local-only, or unavailable-CLI configurations return `multi-file-workspace-cli-required` before generation; `auto` does not fall back to OpenAI after a CLI runtime failure.
- Parsed the final `资料读取：` acknowledgement into `codex.mn.sourceUsage.v1` with ordered `read`, `unread`, and `missing` source IDs.
- Marked incomplete multi-file action responses with `answerDerivedWritesEligible: false`. Rendering and button suppression remain assigned to Task 5.

## RED Evidence

Initial focused command:

```sh
python3 -m unittest tests.test_companion_controls.CompanionControlsTests.test_multi_file_cli_uses_workspace_cwd_and_one_process -v
```

Result: 1 test ran and failed. The legacy path launched six recorded subprocesses because it still entered document-context extraction before Codex; it therefore violated the one-shot workspace path before reaching the workspace-`cwd` assertion.

Initial grouped command covered workspace prompting, backend boundaries, acknowledgement parsing, and single-document compatibility. Result: 7 tests ran; 5 failed and 2 errored. Observed failures included OpenAI fallback in `auto`, direct OpenAI execution in OpenAI-only mode, no compact workspace contract, and absent `sourceUsage` fields.

Unavailable-CLI regression command:

```sh
python3 -m unittest tests.test_companion_controls.CompanionControlsTests.test_multi_file_unavailable_cli_returns_required_error_before_generation -v
```

Result: 1 test ran and failed because the backend was `codex-cli-error` instead of the required `multi-file-workspace-cli-required` preflight result.

## GREEN Evidence

Focused Task 4 command:

```sh
python3 -m unittest -v \
  tests.test_companion_controls.CompanionControlsTests.test_multi_file_cli_uses_workspace_cwd_and_one_process \
  tests.test_companion_controls.CompanionControlsTests.test_single_document_cli_keeps_root_cwd \
  tests.test_companion_controls.CompanionControlsTests.test_multi_file_model_input_uses_compact_workspace_contract \
  tests.test_companion_controls.CompanionControlsTests.test_multi_file_auto_does_not_fall_back_after_cli_failure \
  tests.test_companion_controls.CompanionControlsTests.test_multi_file_openai_only_blocks_before_api_invocation \
  tests.test_companion_controls.CompanionControlsTests.test_multi_file_unavailable_cli_returns_required_error_before_generation \
  tests.test_companion_controls.CompanionControlsTests.test_missing_source_acknowledgement_marks_answer_incomplete \
  tests.test_companion_controls.CompanionControlsTests.test_unread_source_suppresses_generated_card_write_eligibility
```

Result: 8 tests ran in 1.673 seconds; all passed.

Final Companion regression command:

```sh
python3 -m unittest tests.test_companion_controls -q
```

Result: 252 tests ran in 185.493 seconds; all passed.

Source-workspace regression command:

```sh
python3 -m unittest tests.test_source_workspace -q
```

Result: 16 tests ran in 0.034 seconds; all passed.

Static verification:

- `git diff --check`: passed with no output before the implementation commit.
- In-memory AST parsing of `companion.py` and `tests/test_companion_controls.py`: `AST parse OK`.

## Commit

- `df750ee Run one Codex call over selected sources`

## Self-Review

- Confirmed multi-file activation is strictly `len(unique sourceIds) > 1`; zero- and one-source requests retain the existing route.
- Confirmed generation rejects missing conversation/revision bindings, validation errors, ordered source-ID mismatches, and unreadable validated sources before a model call.
- Confirmed `call_codex_cli()` uses the validator's returned `workspacePath`, including an exact-owned legacy fallback path.
- Confirmed multi-file requests issue one `codex exec` process and do not use the legacy transient-startup retry; single-document retry behavior is unchanged.
- Confirmed the command retains `--sandbox read-only` and the multi-file system prompt permits only bounded read inspection.
- Confirmed multi-file model input does not include source-file bodies or call `document_context_for_model()`.
- Confirmed OpenAI-only and unavailable-CLI paths invoke neither Codex nor OpenAI generation, while `auto` invokes only Codex and returns its runtime failure directly.
- Confirmed acknowledgement parsing uses the final `资料读取：` line, ignores unknown IDs, preserves manifest order, and marks unread or absent IDs incomplete.
- Confirmed single-document action responses are not augmented with multi-file eligibility metadata.
- Confirmed the implementation commit contains only the two files authorized for Task 4.

## Concerns

- Task 5 must consume `sourceUsage.complete` or `answerDerivedWritesEligible` to hide answer-derived card and mind-map write controls. Task 4 returns the eligibility boundary but intentionally does not change Web rendering.
- Missing or unread acknowledgements do not trigger an automatic model rerun, as required by the first-release specification.
- Multi-file requests intentionally do not retry the cloud-config startup timeout because a retry would violate the one-shot execution contract.
- Tests exercise the process boundary with a controlled fake Codex executable interface; a live end-to-end workspace read remains part of later integration/release verification.

## Fix Round 1

### Status and Commit

Completed as `21d324e` (`Harden multi-file source acknowledgements`).

Changed files:

- `companion.py`
- `tests/test_companion_controls.py`

### Findings Addressed

- `answerDerivedWritesEligible` now requires all four authoritative conditions: `result.ok` is true, backend exactly `codex-cli`, nonempty answer content beyond the acknowledgement line, and strict complete `sourceUsage`.
- A failed action or `codex-cli-error` cannot become write-eligible even when its text contains a syntactically complete acknowledgement.
- The acknowledgement parser now uses the validated manifest source IDs, accepts exactly one `id=read|unread` entry per source, and never overwrites an earlier status.
- Duplicate IDs, conflicting duplicate statuses, unknown IDs, substring-like unknown IDs, malformed nonempty tokens, missing acknowledgement lines, and missing manifest IDs produce structured `sourceUsage.diagnostics` entries and force `complete=false`.
- Active multi-file execution accepts model answer text only from `--output-last-message`. A zero-exit process with stdout/stderr but no output file returns `codex-cli-error`; stdout/stderr remains diagnostic detail only.
- The existing zero-exit stdout fallback remains available for inactive single-document execution.
- Retryable multi-file startup failures still execute exactly one `codex exec` process and do not enter the legacy retry loop.

### RED Evidence

Command:

```sh
python3 -m unittest -v \
  tests.test_companion_controls.CompanionControlsTests.test_failed_backend_with_complete_acknowledgement_is_not_write_eligible \
  tests.test_companion_controls.CompanionControlsTests.test_answer_derived_write_eligibility_requires_usable_codex_cli_answer \
  tests.test_companion_controls.CompanionControlsTests.test_source_usage_rejects_duplicate_unknown_substring_and_malformed_entries \
  tests.test_companion_controls.CompanionControlsTests.test_multi_file_zero_exit_stdout_error_is_not_promoted_to_answer \
  tests.test_companion_controls.CompanionControlsTests.test_single_document_zero_exit_stdout_fallback_is_unchanged \
  tests.test_companion_controls.CompanionControlsTests.test_multi_file_retryable_startup_failure_uses_one_popen
```

Output:

```text
Ran 6 tests in 0.734s

FAILED (failures=9, errors=1)
```

Observed failures matched the review findings:

- Failed-backend and OpenAI-backed results with complete acknowledgements were marked write-eligible.
- An acknowledgement-only result was marked write-eligible.
- Duplicate, unknown, substring-like unknown, and malformed entries could leave `complete=true`; conflicting duplicates had no diagnostics; valid output had no `diagnostics` field.
- A zero-exit multi-file process promoted `ERROR: authentication failed` from stdout to a successful `codex-cli` answer.
- The single-document stdout compatibility and one-Popen multi-file startup tests already passed in RED, confirming those boundaries before implementation.

### GREEN Evidence

Focused adversarial command: the same 6 tests ran in 0.746 seconds and all passed.

Combined Task 4 command:

```sh
python3 -m unittest -q \
  tests.test_companion_controls.CompanionControlsTests.test_multi_file_cli_uses_workspace_cwd_and_one_process \
  tests.test_companion_controls.CompanionControlsTests.test_single_document_cli_keeps_root_cwd \
  tests.test_companion_controls.CompanionControlsTests.test_multi_file_model_input_uses_compact_workspace_contract \
  tests.test_companion_controls.CompanionControlsTests.test_multi_file_auto_does_not_fall_back_after_cli_failure \
  tests.test_companion_controls.CompanionControlsTests.test_multi_file_openai_only_blocks_before_api_invocation \
  tests.test_companion_controls.CompanionControlsTests.test_multi_file_unavailable_cli_returns_required_error_before_generation \
  tests.test_companion_controls.CompanionControlsTests.test_missing_source_acknowledgement_marks_answer_incomplete \
  tests.test_companion_controls.CompanionControlsTests.test_unread_source_suppresses_generated_card_write_eligibility \
  tests.test_companion_controls.CompanionControlsTests.test_failed_backend_with_complete_acknowledgement_is_not_write_eligible \
  tests.test_companion_controls.CompanionControlsTests.test_answer_derived_write_eligibility_requires_usable_codex_cli_answer \
  tests.test_companion_controls.CompanionControlsTests.test_source_usage_rejects_duplicate_unknown_substring_and_malformed_entries \
  tests.test_companion_controls.CompanionControlsTests.test_multi_file_zero_exit_stdout_error_is_not_promoted_to_answer \
  tests.test_companion_controls.CompanionControlsTests.test_single_document_zero_exit_stdout_fallback_is_unchanged \
  tests.test_companion_controls.CompanionControlsTests.test_multi_file_retryable_startup_failure_uses_one_popen
```

Output:

```text
Ran 14 tests in 2.353s

OK
```

Full Companion regression command:

```sh
python3 -m unittest tests.test_companion_controls -q
```

Output:

```text
Ran 258 tests in 186.165s

OK
```

Static verification:

- `git diff --check`: passed with no output before the implementation commit.
- In-memory AST parsing of `companion.py` and `tests/test_companion_controls.py`: `AST parse OK`.

### Self-Review

- Confirmed parser membership is exact against validated manifest IDs; substring IDs cannot satisfy or overwrite another source.
- Confirmed a duplicate is invalid even when both statuses are identical, and a conflict emits both duplicate and conflict diagnostics.
- Confirmed malformed nonempty tokens and unknown IDs remain visible in diagnostics instead of being silently discarded.
- Confirmed eligibility is computed from the returned action object and its reply, not from coverage alone or a divergent helper argument.
- Confirmed acknowledgement-only text is not treated as usable answer content.
- Confirmed active multi-file execution cannot return stdout/stderr as a successful answer at any exit code.
- Confirmed inactive single-document stdout fallback and its existing retry behavior are unchanged.
- Confirmed the implementation commit is limited to the two Task 4 code/test files.

### Remaining Concerns

- Task 5 must render `sourceUsage.diagnostics` and enforce `answerDerivedWritesEligible`; this round provides the authoritative backend fields but does not alter Web UI.
- The parser continues to use the final `资料读取：` line, consistent with the Task 4 contract; earlier acknowledgement-like prose is ignored.
- Live end-to-end Codex CLI workspace reading remains outside this unit-level fix round.
