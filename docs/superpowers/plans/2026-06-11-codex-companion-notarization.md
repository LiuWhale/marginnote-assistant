# Codex Companion Notarization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add notarization tooling and hard release gates for the Codex Companion macOS pkg.

**Architecture:** Keep pkg building in `build_pkg.py`, add focused notarization orchestration in `notarize_pkg.py`, and make `doctor.py` plus `release_acceptance.py` prove signature and notarization separately.

**Tech Stack:** Python stdlib, macOS `xcrun notarytool`, `xcrun stapler`, `spctl`, `pkgutil`, zsh release commands.

---

### Task 1: Tests for Release Package Contents

**Files:**
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/tests/test_release_packaging.py`

- [ ] Add assertions that `Notarize Package.command` and `notarize_pkg.py` are copied to the release root.
- [ ] Add assertions that nested companion copies exclude the root notarization command and script.
- [ ] Add smoke marker assertions for `notarytool submit` and `notarize_pkg.py`.
- [ ] Run `python3 -m unittest tests.test_release_packaging` and verify the new assertions fail before implementation.

### Task 2: Tests for Notarization CLI

**Files:**
- Create: `/Users/liuwhale/.codex/marginnote-assistant/tests/test_notarize_pkg.py`
- Create: `/Users/liuwhale/.codex/marginnote-assistant/notarize_pkg.py`

- [ ] Test that keychain-profile credentials produce a `xcrun notarytool submit <pkg> --keychain-profile <profile> --wait` command.
- [ ] Test that Apple ID environment variables produce `--apple-id`, `--team-id`, and `--password` arguments.
- [ ] Test that missing credentials produce a user-facing error without traceback.
- [ ] Run `python3 -m unittest tests.test_notarize_pkg` and verify it fails because `notarize_pkg.py` is missing or incomplete.

### Task 3: Tests for Doctor and Acceptance Gates

**Files:**
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/tests/test_doctor_checks.py`
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/tests/test_release_acceptance.py`

- [ ] Add a doctor test where a signed nopayload pkg fails `xcrun stapler validate`; expected detail includes `not notarized`.
- [ ] Add a doctor test where signature, nopayload, stapler, and spctl all pass; expected status is OK and evidence records notarization.
- [ ] Add an acceptance test where signed-only blocks `notarized_pkg` but passes `signed_pkg`.
- [ ] Update the all-pass acceptance test to require notarized evidence.
- [ ] Run the focused tests and verify they fail before implementation.

### Task 4: Implement Notarization Support

**Files:**
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/package_release.py`
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/release_smoke_test.py`
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/release_acceptance.py`
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/doctor.py`
- Create: `/Users/liuwhale/.codex/marginnote-assistant/notarize_pkg.py`
- Create: `/Users/liuwhale/.codex/marginnote-assistant/Notarize Package.command`

- [ ] Add root packaging entries and companion excludes for the new notarization files.
- [ ] Implement `notarize_pkg.py` with dry-run, JSON output, keychain-profile credentials, env credentials, submit, staple, validate, and spctl assessment.
- [ ] Add `Notarize Package.command` as a double-click wrapper that finds a nearby pkg and calls `notarize_pkg.py`.
- [ ] Add syntax checks for the new Python and zsh files.
- [ ] Extend doctor and acceptance gates for notarization evidence.

### Task 5: Documentation and Verification

**Files:**
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/README-FIRST.txt`
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/README.md`
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/docs/RELEASE_CHECKLIST.md`
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/docs/RELEASE_STATUS_MATRIX.md`
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/docs/CURRENT_RELEASE_AUDIT.md`

- [ ] Document that signing and notarization require Apple Developer credentials.
- [ ] Re-run focused tests, full unit tests, py_compile, zsh syntax checks, package release, smoke test, build pkg dry-run, and final acceptance.
- [ ] Report real blockers, including missing local Developer ID identity and missing notarized pkg, without marking the release complete.

