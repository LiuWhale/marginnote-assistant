from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "extension/codex.mn.assistant"
MAIN_PATH = ROOT / "main.js"
APP_PATH = ROOT / "web/app.js"
LOOPBACK_ORIGIN = "http://127.0.0.1:48761"


def function_body(source: str, name: str, next_name: str) -> str:
    marker = f"function {name}"
    start = source.find(marker)
    if start < 0:
        raise AssertionError(f"missing {marker}")
    end = source.find(f"function {next_name}", start + len(marker))
    if end < 0:
        raise AssertionError(f"missing function {next_name} after {name}")
    return source[start:end]


class ExtensionTokenRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.main = MAIN_PATH.read_text(encoding="utf-8")
        self.app = APP_PATH.read_text(encoding="utf-8")

    def test_native_main_keeps_generic_event_and_ack_routes_tokenless(self) -> None:
        generic_headers = function_body(self.main, "companionRequestHeaders", "companionActionRequestHeaders")
        post_json = function_body(self.main, "postJSON", "createPanelController")
        post_event = self.main.split("CodexAssistantAddon.prototype.postEvent", 1)[1].split(
            "CodexAssistantAddon.prototype.uploadPdfToCompanion", 1
        )[0]
        ack_commands = self.main.split("CodexAssistantAddon.prototype.ackCommands", 1)[1].split(
            "function aiEditObjectRefFromDraft", 1
        )[0]

        self.assertNotIn("companionActionToken", generic_headers)
        self.assertIn("authenticated === true", post_json)
        self.assertIn("companionActionRequestHeaders(url)", post_json)
        self.assertNotIn(", true)", post_event)
        self.assertNotIn(", true)", ack_commands)

    def test_native_main_only_reads_token_for_explicit_exact_action_url(self) -> None:
        self.assertIn("function companionActionRequestHeaders", self.main)
        if "function companionActionRequestHeaders" not in self.main:
            return
        action_headers = function_body(self.main, "companionActionRequestHeaders", "isExplicitTrue")
        call_action = self.main.split("CodexAssistantAddon.prototype.callCompanion", 1)[1].split(
            "CodexAssistantAddon.prototype.postEvent", 1
        )[0]
        upload_action = self.main.split("CodexAssistantAddon.prototype.uploadPdfToCompanion", 1)[1].split(
            "CodexAssistantAddon.prototype.appendSelectionPopupMenuActions", 1
        )[0]

        self.assertIn("url === CompanionURL", action_headers)
        self.assertIn("companionActionToken()", action_headers)
        self.assertIn("companionActionRequestHeaders(CompanionURL)", call_action)
        self.assertIn("postJSON(CompanionURL, ctx, 30,", upload_action)
        self.assertIn(", true);", upload_action)

    def test_web_token_authorizer_is_gated_by_literal_loopback_origin(self) -> None:
        self.assertIn("function isLiteralLoopbackCompanionUrl", self.app)
        if "function isLiteralLoopbackCompanionUrl" not in self.app:
            return
        gate = function_body(self.app, "isLiteralLoopbackCompanionUrl", "authorizeCompanionRequest")
        authorizer = function_body(self.app, "authorizeCompanionRequest", "postCompanion")

        self.assertIn(f"'{LOOPBACK_ORIGIN}/'", gate)
        self.assertIn("isLiteralLoopbackCompanionUrl(url)", authorizer)
        self.assertNotIn("companionUrl", authorizer)

    def test_web_token_authorizer_never_inherits_custom_url(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.fail("node is required to execute the Web token routing test")

        try:
            gate = function_body(self.app, "isLiteralLoopbackCompanionUrl", "authorizeCompanionRequest")
            authorizer = function_body(self.app, "authorizeCompanionRequest", "postCompanion")
        except AssertionError as exc:
            self.fail(str(exc))

        script = f"""
const webActionToken = 'a'.repeat(64);
{gate}
{authorizer}
function headersFor(url) {{
  const headers = {{}};
  authorizeCompanionRequest({{setRequestHeader: (name, value) => headers[name] = value}}, url);
  return headers;
}}
const cases = {{
  '{LOOPBACK_ORIGIN}/marginnote/action': true,
  '{LOOPBACK_ORIGIN}/marginnote/draft': true,
  'https://127.0.0.1:48761/marginnote/action': false,
  'http://127.0.0.1:48762/marginnote/action': false,
  'http://localhost:48761/marginnote/action': false,
  'http://127.0.0.1.evil.test:48761/marginnote/action': false,
  'http://user@127.0.0.1:48761/marginnote/action': false,
  'http://127.0.0.1:48761@evil.test/marginnote/action': false,
  'http://custom.example.test/marginnote/action': false
}};
for (const [url, expected] of Object.entries(cases)) {{
  const actual = Object.prototype.hasOwnProperty.call(headersFor(url), 'X-Codex-Action-Token');
  if (actual !== expected) throw new Error(url + ': expected ' + expected + ', got ' + actual);
}}
"""
        result = subprocess.run([node, "-e", script], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
