from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "extension/codex.mn.assistant"
MAIN_PATH = ROOT / "main.js"
APP_PATH = ROOT / "web/app.js"
PANEL_CONTROLLER_PATH = ROOT / "CodexWebPanelController.js"
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
        self.panel_controller = PANEL_CONTROLLER_PATH.read_text(encoding="utf-8")

    def test_web_panel_injects_action_token_before_document_context(self) -> None:
        send_context = self.panel_controller.split(
            "CodexWebPanelController.prototype.sendContextToWeb", 1
        )[1].split("\nCodexWebPanelController.prototype.promptText", 1)[0]

        self.assertIn("this.callPanel('setActionToken'", send_context)
        self.assertIn("this.callPanel('setContext'", send_context)
        self.assertLess(
            send_context.index("this.callPanel('setActionToken'"),
            send_context.index("this.callPanel('setContext'"),
        )

        self.assertIn("function setWebActionToken", self.app)
        self.assertIn("setActionToken: function(payload)", self.app)
        token_helper = function_body(self.app, "setWebActionToken", "renderContext")
        node = shutil.which("node")
        if node is None:
            self.fail("node is required to execute the Web token injection test")
        script = f"""
var webActionToken = '';
{token_helper}
setWebActionToken('a'.repeat(64));
if (webActionToken !== 'a'.repeat(64)) throw new Error('valid token was not installed');
setWebActionToken('invalid');
if (webActionToken !== 'a'.repeat(64)) throw new Error('invalid token replaced the valid token');
"""
        result = subprocess.run([node, "-e", script], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_native_token_readers_use_the_existing_margin_note_base64_api(self) -> None:
        self.assertIn("function codexDecodeBase64Ascii", self.panel_controller)
        self.assertIn("function codexReadAsciiFile", self.panel_controller)
        self.assertIn("NSData.dataWithContentsOfFile(path)", self.panel_controller)
        self.assertIn("data.base64Encoding()", self.panel_controller)
        self.assertIn("/web-action-token", self.panel_controller)
        self.assertIn("codexReadAsciiFile(candidates[i])", self.panel_controller)
        self.assertIn("function codexDecodeBase64Ascii", self.main)
        self.assertIn("function codexReadAsciiFile", self.main)
        self.assertIn("NSData.dataWithContentsOfFile(path)", self.main)
        self.assertIn("data.base64Encoding()", self.main)
        self.assertIn("/web-action-token", self.main)
        self.assertIn("codexReadAsciiFile(candidates[i])", self.main)

        decoder = function_body(self.panel_controller, "codexDecodeBase64Ascii", "codexReadAsciiFile")
        node = shutil.which("node")
        if node is None:
            self.fail("node is required to execute the native token decoder test")
        script = f"""
function codexSafeString(value) {{ return value === null || value === undefined ? '' : String(value); }}
{decoder}
const token = '0123456789abcdef'.repeat(4) + '\\n';
const encoded = Buffer.from(token, 'ascii').toString('base64');
if (codexDecodeBase64Ascii(encoded) !== token) throw new Error('ASCII token decode failed');
if (codexDecodeBase64Ascii('not base64!') !== '') throw new Error('invalid base64 was accepted');
"""
        result = subprocess.run([node, "-e", script], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_local_extension_token_survives_home_directory_lookup_failure(self) -> None:
        token_reader = function_body(
            self.panel_controller,
            "codexCompanionActionToken",
            "codexUrlString",
        )
        node = shutil.which("node")
        if node is None:
            self.fail("node is required to execute the native token lookup fallback test")
        script = f"""
function codexSafeString(value) {{ return value === null || value === undefined ? '' : String(value); }}
function codexReadAsciiFile(path) {{ return path.endsWith('/web-action-token') ? 'a'.repeat(64) : ''; }}
function NSHomeDirectory() {{ throw new Error('unsupported bridge global'); }}
{token_reader}
if (codexCompanionActionToken('/extension') !== 'a'.repeat(64)) {{
  throw new Error('local extension token was lost when home lookup failed');
}}
"""
        result = subprocess.run([node, "-e", script], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_web_panel_reports_token_injection_without_exposing_the_token(self) -> None:
        send_context = self.panel_controller.split(
            "CodexWebPanelController.prototype.sendContextToWeb", 1
        )[1].split("\nCodexWebPanelController.prototype.promptText", 1)[0]

        self.assertIn("webPanelContextInjected", send_context)
        self.assertIn("tokenAvailable", send_context)
        self.assertIn("tokenLength", send_context)
        self.assertIn("mainPathAvailable", send_context)
        self.assertIn("mainPathValue", send_context)
        self.assertIn("localTokenFileExists", send_context)
        self.assertIn("localTokenDataLength", send_context)
        self.assertIn("localTokenBase64Length", send_context)
        self.assertIn("localTokenDecodedLength", send_context)
        self.assertIn("localTokenDecodedValid", send_context)
        self.assertIn("lastTokenDiagnosticSignature", send_context)
        diagnostic = send_context.split("webPanelContextInjected", 1)[1]
        self.assertNotIn("token: actionToken", diagnostic)

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

    def test_native_draft_read_uses_authenticated_action_post_instead_of_plain_nsdata_url(self) -> None:
        action_headers = function_body(self.main, "companionActionRequestHeaders", "isExplicitTrue")
        write_draft = self.main.split(
            "CodexAssistantAddon.prototype.writeDraft", 1
        )[1].split("\n  CodexAssistantAddon.prototype.handleCompanionResponse", 1)[0]

        self.assertIn("url === CompanionURL", action_headers)
        self.assertIn("action: 'draft_get'", write_draft)
        self.assertIn("draftId: draftId", write_draft)
        self.assertIn("postJSON(CompanionURL", write_draft)
        self.assertIn(", true);", write_draft)
        self.assertNotIn(
            "NSData.dataWithContentsOfURL(NSURL.URLWithString(url))",
            write_draft,
        )

    def test_native_draft_read_diagnostics_report_metadata_without_token_value(self) -> None:
        write_draft = self.main.split(
            "CodexAssistantAddon.prototype.writeDraft", 1
        )[1].split("\n  CodexAssistantAddon.prototype.handleCompanionResponse", 1)[0]

        self.assertIn("nativeDraftReadRequestPrepared", write_draft)
        self.assertIn("nativeDraftReadRequestFinished", write_draft)
        for marker in ["tokenAvailable", "tokenLength", "statusCode", "dataLength", "error"]:
            self.assertIn(marker, write_draft)
        self.assertNotIn("token: draftReadToken", write_draft)

    def test_native_json_parsing_uses_nsdata_length_instead_of_js_truthiness(self) -> None:
        parse_json = function_body(self.main, "parseJSONData", "rawStringFromData")
        raw_string = function_body(self.main, "rawStringFromData", "previewData")
        write_draft = self.main.split(
            "CodexAssistantAddon.prototype.writeDraftResponse", 1
        )[1].split("\n  CodexAssistantAddon.prototype.handleCompanionResponse", 1)[0]

        self.assertIn("if (isNil(data)) return null", parse_json)
        self.assertIn("if (isNil(data)) return ''", raw_string)
        self.assertIn("!isNil(error)", write_draft)
        self.assertIn("byteLengthOfData(data) <= 0", write_draft)
        self.assertNotIn("error || !data", write_draft)

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
