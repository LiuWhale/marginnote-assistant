# MarginNote API Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce a replaceable MarginNote API adapter with URL API Gateway support so future card, mindmap, and transaction operations can target native JSB or `url-api-marginnote` through one backend contract.

**Architecture:** Add a standalone Python adapter module that builds and validates URL API Gateway requests without coupling to UI or model generation. Companion owns settings/env persistence and exposes read-only status/probe actions. This phase does not replace the existing native write path; it makes URL API a first-class optional backend.

**Tech Stack:** Python 3 standard library, existing `.env` settings flow, existing Companion `/marginnote/action`, `unittest`.

---

## Files

- Create: `marginnote_api_adapter.py`  
  URL API request building, x-success/x-error callback URL generation, secret redaction, backend status, optional opener wrapper.

- Modify: `runtime_config.py`  
  Add `mnApiBackend` with `auto/native/url_api`, plus secret sanitization helper.

- Modify: `companion.py`  
  Save/clear `MN_URL_API_SECRET`, expose status fields, add `mn_api_status` and `mn_url_api_build_request` actions.

- Create: `tests/test_marginnote_api_adapter.py`  
  Unit tests for URL construction, secret redaction, bad action rejection, and status.

- Modify: `tests/test_runtime_config.py` and `tests/test_companion_controls.py`  
  Cover new settings and action contracts.

## Acceptance

- URL API request builder emits `marginnote4app://addon/api?...` with `requestId`, `action`, `secret`, encoded JSON `payload`, `x-success`, and `x-error`.
- Secret is never returned in status or action response except inside the actual URL request intended for opening.
- Companion status reports `mnApiBackend`, `mnUrlApiConfigured`, and adapter availability.
- Read-only actions can report adapter status and build a redacted request preview.
- Full test suite remains green.

