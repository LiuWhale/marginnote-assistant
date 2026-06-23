from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


NOTARIZE_PATH = Path(__file__).resolve().parents[1] / "notarize_pkg.py"


class NotarizePkgTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("codex_mn_notarize_pkg", NOTARIZE_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_keychain_profile_credentials_build_notarytool_submit_command(self) -> None:
        module = self.load_module()

        credentials = module.resolve_credentials(
            keychain_profile="CodexNotary",
            apple_id="",
            team_id="",
            password="",
            env={},
        )
        command = module.notarytool_submit_command(Path("/tmp/CodexCompanion.pkg"), credentials)

        self.assertEqual(credentials["mode"], "keychain-profile")
        self.assertEqual(
            command,
            [
                "xcrun",
                "notarytool",
                "submit",
                "/tmp/CodexCompanion.pkg",
                "--keychain-profile",
                "CodexNotary",
                "--wait",
            ],
        )

    def test_apple_id_environment_credentials_build_notarytool_submit_command(self) -> None:
        module = self.load_module()
        env = {
            "APPLE_ID": "dev@example.com",
            "APPLE_TEAM_ID": "TEAM123",
            "APPLE_APP_SPECIFIC_PASSWORD": "app-specific-password",
        }

        credentials = module.resolve_credentials(
            keychain_profile="",
            apple_id="",
            team_id="",
            password="",
            env=env,
        )
        command = module.notarytool_submit_command(Path("/tmp/CodexCompanion.pkg"), credentials)

        self.assertEqual(credentials["mode"], "apple-id")
        self.assertIn("--apple-id", command)
        self.assertIn("dev@example.com", command)
        self.assertIn("--team-id", command)
        self.assertIn("TEAM123", command)
        self.assertIn("--password", command)
        self.assertIn("app-specific-password", command)

    def test_cli_reports_missing_credentials_without_traceback(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / "CodexCompanion.pkg"
            pkg.write_bytes(b"pkg")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                rc = module.main([str(pkg)], env={})

        self.assertEqual(rc, 1)
        self.assertIn("notarytool credentials", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_dry_run_json_reports_submit_staple_and_validate_commands(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / "CodexCompanion.pkg"
            pkg.write_bytes(b"pkg")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = module.main(
                    [str(pkg), "--keychain-profile", "CodexNotary", "--dry-run", "--json"],
                    env={},
                )

        self.assertEqual(rc, 0)
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["dryRun"])
        self.assertEqual(payload["credentialsMode"], "keychain-profile")
        self.assertEqual(payload["submitCommand"][:3], ["xcrun", "notarytool", "submit"])
        self.assertEqual(payload["stapleCommand"][:3], ["xcrun", "stapler", "staple"])
        self.assertEqual(payload["validateCommand"][:3], ["xcrun", "stapler", "validate"])

    def test_dry_run_json_does_not_require_notarytool_credentials(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / "CodexCompanion.pkg"
            pkg.write_bytes(b"pkg")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                rc = module.main([str(pkg), "--dry-run", "--json"], env={})

        self.assertEqual(rc, 0)
        self.assertEqual(stderr.getvalue(), "")
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["dryRun"])
        self.assertEqual(payload["credentialsMode"], "dry-run-no-credentials")
        self.assertIn("notarytool credentials", payload["credentialsWarning"])
        self.assertEqual(payload["submitCommand"][:3], ["xcrun", "notarytool", "submit"])


if __name__ == "__main__":
    unittest.main()
