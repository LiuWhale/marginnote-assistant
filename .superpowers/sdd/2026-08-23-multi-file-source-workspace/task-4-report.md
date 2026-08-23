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
