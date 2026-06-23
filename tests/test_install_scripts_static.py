from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT if (PROJECT_ROOT / "install.sh").exists() else PROJECT_ROOT.parent


class InstallScriptStaticTests(unittest.TestCase):
    def test_install_companion_migrates_legacy_launch_agent_before_bootstrap(self) -> None:
        script = (PROJECT_ROOT / "install_companion.sh").read_text(encoding="utf-8")

        self.assertIn("LEGACY_LABEL=", script)
        self.assertIn("LEGACY_PLIST=", script)
        self.assertIn('launchctl bootout "$DOMAIN" "$LEGACY_PLIST"', script)
        self.assertLess(
            script.index('launchctl bootout "$DOMAIN" "$LEGACY_PLIST"'),
            script.index('launchctl bootstrap "$DOMAIN" "$PLIST"'),
        )

    def test_install_scripts_support_dry_run_without_launchctl_or_doctor(self) -> None:
        install_root = (PACKAGE_ROOT / "install.sh").read_text(encoding="utf-8")
        install_companion = (PROJECT_ROOT / "install_companion.sh").read_text(encoding="utf-8")
        install_extension = (PROJECT_ROOT / "install_extension.sh").read_text(encoding="utf-8")
        uninstall_companion = (PROJECT_ROOT / "uninstall_companion.sh").read_text(encoding="utf-8")

        self.assertIn("CODEX_MN_DRY_RUN", install_root)
        self.assertIn("Skipping doctor in dry-run mode", install_root)
        self.assertIn("CODEX_MN_DRY_RUN", install_companion)
        self.assertIn("Dry-run: would bootstrap LaunchAgent", install_companion)
        self.assertLess(
            install_companion.index("Dry-run: would bootstrap LaunchAgent"),
            install_companion.index('launchctl bootout "$DOMAIN" "$LEGACY_PLIST"'),
        )
        self.assertIn("CODEX_MN_DRY_RUN", install_extension)
        self.assertIn("Dry-run: would install MN4 extension", install_extension)
        self.assertIn("CODEX_MN_DRY_RUN", uninstall_companion)
        self.assertIn("Dry-run: would unload LaunchAgent", uninstall_companion)

    def test_root_installers_do_not_require_nested_scripts_to_be_executable(self) -> None:
        install_root = (PACKAGE_ROOT / "install.sh").read_text(encoding="utf-8")
        uninstall_root = (PACKAGE_ROOT / "uninstall.sh").read_text(encoding="utf-8")

        self.assertNotIn('! -x "$COMPANION_SOURCE/install_extension.sh"', install_root)
        self.assertNotIn('! -x "$COMPANION_SOURCE/install_companion.sh"', install_root)
        self.assertIn('/bin/zsh "$COMPANION_SOURCE/install_extension.sh"', install_root)
        self.assertIn('/bin/zsh "$COMPANION_SOURCE/install_companion.sh"', install_root)
        self.assertNotIn('-x "$COMPANION_SOURCE/uninstall_companion.sh"', uninstall_root)
        self.assertIn('/bin/zsh "$COMPANION_SOURCE/uninstall_companion.sh"', uninstall_root)

    def test_refresh_mn_runtime_command_collects_evidence_without_quitting_mn4(self) -> None:
        command = (PACKAGE_ROOT / "Refresh MN Runtime.command").read_text(encoding="utf-8")
        script = (PROJECT_ROOT / "refresh_mn_runtime.py").read_text(encoding="utf-8")

        self.assertIn("refresh_mn_runtime.py", command)
        self.assertIn("request_web_panel_reload", script)
        self.assertIn("request_native_capability_probe", script)
        self.assertIn("--try-addon-url-reload", command)
        self.assertIn("addonReloadAttempts", script)
        self.assertIn("webPanelReloadResult", script)
        self.assertIn("mnRuntime", script)
        self.assertIn("MNRuntimeEvidence", script)
        self.assertIn("nativeApiCapabilities", script)
        self.assertIn("doctor.py", script)
        self.assertIn("reopen the Codex panel", script)
        self.assertNotIn("killall", command + script)
        self.assertNotIn("quit MarginNote", command + script)
        self.assertNotIn("osascript -e 'quit", command + script)

    def test_restart_marginnote_command_is_explicit_and_uses_companion_action(self) -> None:
        command = (PACKAGE_ROOT / "Restart MarginNote 4.command").read_text(encoding="utf-8")

        self.assertIn("restart_marginnote4", command)
        self.assertIn("This will quit and reopen MarginNote 4", command)
        self.assertIn("send_action.py", command)
        self.assertIn("--direct", command)
        self.assertIn("--record", command)
        self.assertNotIn("killall", command)


if __name__ == "__main__":
    unittest.main()
