# Task 2 Report: Stable Source Candidates and Extracted Text Links

## Status

Completed and committed as `2ca9dc1` (`Resolve stable multi-file source candidates`).

## Files

- `source_registry.py`
- `companion.py`
- `tests/test_source_registry.py`
- `tests/test_companion_controls.py`

## RED

Command:

```sh
python3 -m unittest tests.test_source_registry tests.test_companion_controls.CompanionControlsTests.test_source_workspace_candidates_include_only_resolvable_files -v
```

Output: 5 tests ran; the stable-ID test failed because explicit-source IDs changed with list order, and the candidate test errored because `source_workspace_candidates` was absent.

Command:

```sh
python3 -m unittest tests.test_companion_controls.CompanionControlsTests.test_source_text_artifact_reuses_page_aware_pdf_cache tests.test_companion_controls.CompanionControlsTests.test_source_text_artifact_reuses_utf8_text_file -v
```

Output: 2 tests ran; both errored because `source_text_artifact` was absent.

## GREEN

Command:

```sh
python3 -m unittest tests.test_source_registry tests.test_companion_controls.CompanionControlsTests.test_source_workspace_candidates_include_only_resolvable_files tests.test_companion_controls.CompanionControlsTests.test_source_text_artifact_reuses_page_aware_pdf_cache tests.test_companion_controls.CompanionControlsTests.test_source_text_artifact_reuses_utf8_text_file -v
```

Output: 7 tests ran, all passed.

Command:

```sh
python3 -m unittest tests.test_source_registry tests.test_companion_controls -q
```

Output: 238 tests ran in 175.947s, all passed.

Command:

```sh
python3 -m unittest tests.test_source_workspace -q
```

Output: 10 tests ran, all passed.

## Self-Review

- `stable_source_id()` uses the required SHA-256 kind-and-identity form. File-backed registry entries use canonical paths; MarginNote metadata uses `topicid|bookmd5|documentTitle`.
- Candidate aggregation admits only canonical readable regular files. It includes cache-backed current and available MarginNote documents, uploads, explicit document paths, and explicitly selected files under configured search roots. Search roots themselves are never candidates.
- PDF artifacts reuse `ensure_pdf_text_cache()`, preserve page markers and the existing truncation wording, and write only Companion-owned UTF-8 files under `control/source-text/`. UTF-8 text files are linked from their original path without a duplicate artifact.
- Existing Source Registry schemas and actions were not changed. Task 1's `source_workspace.py` descriptor interface was not modified.

## Concerns

- This task intentionally exposes helpers only. Read-only action dispatch, conversation persistence, queue revision binding, and the source-picker UI remain Task 3 and Task 5 work.
- A standalone `py_compile` check could not create `__pycache__` in the sandbox. The full 238-test suite imports and executes both modified modules successfully.
