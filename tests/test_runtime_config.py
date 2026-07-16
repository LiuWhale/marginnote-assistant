from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


RUNTIME_CONFIG_PATH = Path(__file__).resolve().parents[1] / "runtime_config.py"


def load_runtime_config():
    spec = importlib.util.spec_from_file_location("codex_companion_runtime_config", RUNTIME_CONFIG_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeConfigTests(unittest.TestCase):
    def test_default_profile_is_codex_cli_gpt56_following_codex_config(self) -> None:
        config = load_runtime_config()

        self.assertEqual(config.DEFAULT_RUNTIME_SETTINGS["model"], "gpt-5.6-sol")
        self.assertEqual(config.DEFAULT_RUNTIME_SETTINGS["speed"], "codex_config")
        self.assertEqual(config.DEFAULT_RUNTIME_SETTINGS["reasoningEffort"], "codex_config")
        self.assertEqual(config.CODEX_CLI_SERVICE_TIERS["codex_config"], "")
        self.assertEqual(config.CODEX_CLI_SERVICE_TIERS["priority"], "priority")
        self.assertIn("xhigh", config.REASONING_EFFORTS)
        self.assertIn("ultra", config.REASONING_EFFORTS)
        self.assertEqual(config.CODEX_CLI_TIMEOUTS["codex_config"], 90)
        self.assertEqual(config.MODEL_PRESETS[0]["id"], "gpt-5.6-sol")
        self.assertIn("gpt-5.6-terra", [item["id"] for item in config.MODEL_PRESETS])
        self.assertIn("gpt-5.6-luna", [item["id"] for item in config.MODEL_PRESETS])

    def test_sanitizes_model_proxy_context_and_custom_buttons(self) -> None:
        config = load_runtime_config()

        self.assertEqual(config.DEFAULT_RUNTIME_SETTINGS["githubRepo"], "LiuWhale/marginnote-assistant")
        self.assertEqual(config.DEFAULT_RUNTIME_SETTINGS["mnApiBackend"], "auto")
        self.assertEqual(config.sanitize_model("bad model name", "fallback-model"), "fallback-model")
        self.assertEqual(config.sanitize_model("gpt-5.6", "fallback-model"), "gpt-5.6-sol")
        self.assertEqual(config.sanitize_model("gpt-5.6-sol", "fallback-model"), "gpt-5.6-sol")
        self.assertEqual(config.sanitize_model("gpt-5.6-terra", "fallback-model"), "gpt-5.6-terra")
        self.assertEqual(config.sanitize_model("gpt-5.6-luna", "fallback-model"), "gpt-5.6-luna")
        self.assertEqual(config.sanitize_speed("priority"), "priority")
        self.assertEqual(config.sanitize_speed("deep"), "codex_config")
        self.assertEqual(config.sanitize_reasoning_effort("xhigh"), "xhigh")
        self.assertEqual(config.sanitize_reasoning_effort("deep"), "high")
        self.assertEqual(config.sanitize_reasoning_effort("unknown"), "codex_config")
        self.assertEqual(config.sanitize_proxy_url("ftp://127.0.0.1:7890"), "")
        self.assertEqual(config.sanitize_proxy_url("http://127.0.0.1:7890"), "http://127.0.0.1:7890")
        self.assertEqual(config.sanitize_github_repo("LiuWhale/marginnote-assistant"), "LiuWhale/marginnote-assistant")
        self.assertEqual(
            config.sanitize_github_repo("https://github.com/LiuWhale/marginnote-assistant"),
            "LiuWhale/marginnote-assistant",
        )
        self.assertEqual(config.sanitize_github_repo("bad repo name"), "LiuWhale/marginnote-assistant")
        self.assertEqual(config.sanitize_mn_api_backend("url_api"), "url_api")
        self.assertEqual(config.sanitize_mn_api_backend("bad"), "auto")
        self.assertEqual(config.sanitize_mn_url_api_secret("mnsec_test_secret_123"), "mnsec_test_secret_123")
        self.assertEqual(config.sanitize_mn_url_api_secret("bad secret with spaces"), "")
        self.assertEqual(config.sanitize_default_context_scope("全文"), "document")
        self.assertEqual(config.sanitize_default_context_scope("unknown"), "auto")
        self.assertEqual(
            config.sanitize_custom_buttons(
                [
                    {"title": "问", "action": "chat", "prompt": "解释", "showOnMain": True},
                    {"title": "坏", "action": "delete_everything", "prompt": "bad"},
                ]
            ),
            [{"title": "问", "action": "chat", "prompt": "解释", "showOnMain": True}],
        )


if __name__ == "__main__":
    unittest.main()
