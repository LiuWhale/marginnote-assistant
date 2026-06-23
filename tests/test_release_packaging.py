from __future__ import annotations

import contextlib
import io
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
import hashlib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT if (PROJECT_ROOT / "install.sh").exists() else PROJECT_ROOT.parent
PACKAGE_RELEASE_PATH = PROJECT_ROOT / "package_release.py"
PKG_BUILDER_PATH = PACKAGE_ROOT / "build_pkg.py"


class ReleasePackagingTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("codex_mn_package_release", PACKAGE_RELEASE_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_release_excludes_private_env_but_keeps_example_template(self) -> None:
        module = self.load_module()

        self.assertIn(".env", module.COMPANION_EXCLUDES)
        self.assertNotIn(".env.example", module.COMPANION_EXCLUDES)

    def test_release_excludes_package_root_installers_from_nested_companion_copy(self) -> None:
        module = self.load_module()

        self.assertIn("install.sh", module.COMPANION_EXCLUDES)
        self.assertIn("uninstall.sh", module.COMPANION_EXCLUDES)
        self.assertIn("Install Codex Companion.command", module.COMPANION_EXCLUDES)
        self.assertIn("Uninstall Codex Companion.command", module.COMPANION_EXCLUDES)
        self.assertIn("Collect Native Highlight Evidence.command", module.COMPANION_EXCLUDES)
        self.assertIn("Collect Cross-Machine Evidence.command", module.COMPANION_EXCLUDES)
        self.assertIn("Restart MarginNote 4.command", module.COMPANION_EXCLUDES)
        self.assertIn("Build Signed Package.command", module.COMPANION_EXCLUDES)
        self.assertIn("Notarize Package.command", module.COMPANION_EXCLUDES)
        self.assertIn("build_pkg.py", module.COMPANION_EXCLUDES)
        self.assertIn("notarize_pkg.py", module.COMPANION_EXCLUDES)
        self.assertIn(".git", module.COMPANION_EXCLUDES)
        self.assertIn("extension", module.COMPANION_EXCLUDES)
        self.assertIn("updates", module.COMPANION_EXCLUDES)

    def test_release_keeps_acceptance_script_in_nested_companion_for_packaged_tests(self) -> None:
        module = self.load_module()

        self.assertNotIn("release_acceptance.py", module.COMPANION_EXCLUDES)
        self.assertNotIn("update_manager.py", module.COMPANION_EXCLUDES)

    def test_release_places_first_run_scripts_at_package_root(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            package_root = Path(tmp) / "CodexCompanion-test"
            root.mkdir()
            package_root.mkdir()
            for name in (
                "README.md",
                "CHANGELOG.md",
                "LICENSE",
                "README-FIRST.txt",
                "install.sh",
                "uninstall.sh",
                "Install Codex Companion.command",
                "Uninstall Codex Companion.command",
                "Collect Native Highlight Evidence.command",
                "Collect Single Document Acceptance.command",
                "Collect Cross-Machine Evidence.command",
                "Refresh MN Runtime.command",
                "Restart MarginNote 4.command",
                "Build Signed Package.command",
                "Notarize Package.command",
                "Prepare Release Handoff.command",
                "release_smoke_test.py",
                "release_acceptance.py",
                "single_document_acceptance.py",
                "build_pkg.py",
                "notarize_pkg.py",
                "prepare_release_handoff.py",
            ):
                (root / name).write_text(f"{name}\n", encoding="utf-8")

            module.ROOT = root
            module.copy_root_files(package_root)

            for name in (
                "README.md",
                "CHANGELOG.md",
                "LICENSE",
                "README-FIRST.txt",
                "install.sh",
                "uninstall.sh",
                "Install Codex Companion.command",
                "Uninstall Codex Companion.command",
                "Collect Native Highlight Evidence.command",
                "Collect Single Document Acceptance.command",
                "Collect Cross-Machine Evidence.command",
                "Refresh MN Runtime.command",
                "Restart MarginNote 4.command",
                "Build Signed Package.command",
                "Notarize Package.command",
                "Prepare Release Handoff.command",
                "release_smoke_test.py",
                "release_acceptance.py",
                "single_document_acceptance.py",
                "build_pkg.py",
                "notarize_pkg.py",
                "prepare_release_handoff.py",
            ):
                self.assertEqual((package_root / name).read_text(encoding="utf-8"), f"{name}\n")

    def test_release_writes_external_sha256_manifest(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "CodexCompanion-test-dist.zip"
            second = Path(tmp) / "CodexCompanion-test.pkg"
            first.write_bytes(b"zip")
            second.write_bytes(b"pkg")
            target = Path(tmp) / "SHA256SUMS.txt"

            module.write_sha256_manifest([first, second], target)

            text = target.read_text(encoding="utf-8")
            self.assertIn(hashlib.sha256(b"zip").hexdigest() + "  CodexCompanion-test-dist.zip", text)
            self.assertIn(hashlib.sha256(b"pkg").hexdigest() + "  CodexCompanion-test.pkg", text)

    def test_release_smoke_requires_evidence_commands(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "codex_mn_release_smoke_require_evidence",
            PACKAGE_ROOT / "release_smoke_test.py",
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        self.assertIn("Collect Native Highlight Evidence.command", module.REQUIRED_SUFFIXES)
        self.assertIn("Collect Single Document Acceptance.command", module.REQUIRED_SUFFIXES)
        self.assertIn("Collect Cross-Machine Evidence.command", module.REQUIRED_SUFFIXES)
        self.assertIn("Refresh MN Runtime.command", module.REQUIRED_SUFFIXES)
        self.assertIn("Restart MarginNote 4.command", module.REQUIRED_SUFFIXES)
        self.assertIn("Build Signed Package.command", module.REQUIRED_SUFFIXES)
        self.assertIn("Notarize Package.command", module.REQUIRED_SUFFIXES)
        self.assertIn("Prepare Release Handoff.command", module.REQUIRED_SUFFIXES)
        self.assertIn("README.md", module.REQUIRED_SUFFIXES)
        self.assertIn("CHANGELOG.md", module.REQUIRED_SUFFIXES)
        self.assertIn("LICENSE", module.REQUIRED_SUFFIXES)
        self.assertIn("assets/cover.png", module.REQUIRED_SUFFIXES)
        self.assertIn("single_document_acceptance.py", module.REQUIRED_SUFFIXES)
        self.assertIn("notarize_pkg.py", module.REQUIRED_SUFFIXES)
        self.assertIn("prepare_release_handoff.py", module.REQUIRED_SUFFIXES)
        self.assertEqual(
            module.MARKERS["Collect Native Highlight Evidence.command"],
            "--collect-native-highlight-evidence",
        )
        self.assertEqual(
            module.MARKERS["Collect Single Document Acceptance.command"],
            "single_document_acceptance.py",
        )
        self.assertEqual(
            module.MARKERS["Collect Cross-Machine Evidence.command"],
            "--collect-cross-machine-evidence",
        )
        self.assertEqual(module.MARKERS["Refresh MN Runtime.command"], "refresh_mn_runtime.py")
        self.assertEqual(module.MARKERS["Restart MarginNote 4.command"], "restart_marginnote4")
        self.assertEqual(module.MARKERS["Build Signed Package.command"], "--auto-sign")
        self.assertEqual(module.MARKERS["Notarize Package.command"], "notarize_pkg.py")
        self.assertEqual(module.MARKERS["Prepare Release Handoff.command"], "prepare_release_handoff.py")
        self.assertEqual(
            module.MARKERS["single_document_acceptance.py"],
            "codex-companion-single-document-acceptance-v1",
        )
        self.assertEqual(module.MARKERS["notarize_pkg.py"], "notarytool submit")
        self.assertEqual(
            module.MARKERS["prepare_release_handoff.py"],
            "Prepare a Codex Companion release handoff bundle",
        )

    def test_release_smoke_fails_when_sidecar_sha256_manifest_mismatches_zip(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "codex_mn_release_smoke_sha256",
            PACKAGE_ROOT / "release_smoke_test.py",
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "CodexCompanion-test-dist.zip"
            with zipfile.ZipFile(package, "w") as archive:
                for suffix in module.REQUIRED_SUFFIXES:
                    marker = module.MARKERS.get(suffix, "ok")
                    archive.writestr(f"CodexCompanion-test/{suffix}", marker)
            (Path(tmp) / "SHA256SUMS.txt").write_text(
                "0" * 64 + "  CodexCompanion-test-dist.zip\n",
                encoding="utf-8",
            )

            result = module.inspect_package(package)

            self.assertFalse(result.ok)
            self.assertIn("sha256 manifest mismatch", "\n".join(result.problems))

    def test_pkg_builder_parses_developer_id_installer_identities(self) -> None:
        spec = importlib.util.spec_from_file_location("codex_mn_build_pkg_signing", PKG_BUILDER_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        output = '\n'.join(
            [
                '  1) 0123456789ABCDEF "Apple Development: Someone (ABCDE12345)"',
                '  2) FEDCBA9876543210 "Developer ID Installer: Example Team (ABCDE12345)"',
                '  3) 1111111111111111 "Developer ID Application: Example Team (ABCDE12345)"',
                '     3 valid identities found',
            ]
        )

        identities = module.parse_developer_id_installer_identities(output)

        self.assertEqual(identities, ["Developer ID Installer: Example Team (ABCDE12345)"])

    def test_pkg_builder_writes_external_sha256_manifest(self) -> None:
        spec = importlib.util.spec_from_file_location("codex_mn_build_pkg_checksums", PKG_BUILDER_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / "CodexCompanion-test-dist.zip"
            pkg_path = Path(tmp) / "CodexCompanion-test.pkg"
            zip_path.write_bytes(b"zip")
            pkg_path.write_bytes(b"pkg")
            target = Path(tmp) / "SHA256SUMS.txt"

            module.write_sha256_manifest([zip_path, pkg_path], target)

            text = target.read_text(encoding="utf-8")
            self.assertIn(hashlib.sha256(b"zip").hexdigest() + "  CodexCompanion-test-dist.zip", text)
            self.assertIn(hashlib.sha256(b"pkg").hexdigest() + "  CodexCompanion-test.pkg", text)

    def test_pkg_builder_syncs_pkg_and_manifest_to_onedrive(self) -> None:
        spec = importlib.util.spec_from_file_location("codex_mn_build_pkg_onedrive_sync", PKG_BUILDER_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zip_path = root / "CodexCompanion-test-latest-dist.zip"
            pkg_path = root / "CodexCompanion-test-latest.pkg"
            cloud = root / "OneDrive/Codex Companion"
            zip_path.write_bytes(b"zip")
            pkg_path.write_bytes(b"pkg")

            result = module.sync_release_artifacts(zip_path, pkg_path, cloud)

            self.assertEqual(result["onedrivePkg"], str((cloud / pkg_path.name).resolve()))
            self.assertEqual((cloud / zip_path.name).read_bytes(), b"zip")
            self.assertEqual((cloud / pkg_path.name).read_bytes(), b"pkg")
            self.assertEqual((root / "SHA256SUMS.txt").read_text(), (cloud / "SHA256SUMS.txt").read_text())
            self.assertIn(hashlib.sha256(b"pkg").hexdigest() + "  " + pkg_path.name, (cloud / "SHA256SUMS.txt").read_text())

    def test_pkg_builder_main_reports_signing_errors_without_traceback(self) -> None:
        spec = importlib.util.spec_from_file_location("codex_mn_build_pkg_cli_error", PKG_BUILDER_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        def fail_build(*args, **kwargs):
            raise RuntimeError("No Developer ID Installer identity was found")

        module.build_pkg = fail_build
        old_argv = sys.argv[:]
        sys.argv = ["build_pkg.py", "--auto-sign"]
        stderr = io.StringIO()
        try:
            with contextlib.redirect_stderr(stderr):
                rc = module.main()
        finally:
            sys.argv = old_argv

        self.assertEqual(rc, 1)
        self.assertIn("No Developer ID Installer identity was found", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_pkg_builder_json_stdout_stays_parseable_when_pkg_tools_are_noisy(self) -> None:
        spec = importlib.util.spec_from_file_location("codex_mn_build_pkg_json_stdout", PKG_BUILDER_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        class Completed:
            stdout = ""
            stderr = ""
            returncode = 0

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zip_path = root / "CodexCompanion-test-dist.zip"
            output_path = root / "CodexCompanion-test.pkg"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("CodexCompanion-test/install.sh", "#!/bin/zsh\necho install\n")

            old_argv = sys.argv[:]
            old_run = module.subprocess.run
            old_which = module.shutil.which
            old_strip = module.strip_pkg_appledouble

            def fake_run(cmd, *args, **kwargs):
                if not kwargs.get("capture_output"):
                    print(f"{Path(cmd[0]).name}: noisy build log")
                if cmd[0] == "/usr/bin/productbuild":
                    Path(cmd[-1]).write_bytes(b"pkg")
                return Completed()

            sys.argv = [
                "build_pkg.py",
                str(zip_path),
                "--output",
                str(output_path),
                "--no-sync-onedrive",
                "--json",
            ]
            module.subprocess.run = fake_run
            module.shutil.which = lambda name: None
            module.strip_pkg_appledouble = lambda *args, **kwargs: []
            stdout = io.StringIO()
            try:
                with contextlib.redirect_stdout(stdout):
                    rc = module.main()
            finally:
                sys.argv = old_argv
                module.subprocess.run = old_run
                module.shutil.which = old_which
                module.strip_pkg_appledouble = old_strip

        self.assertEqual(rc, 0)
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["output"], str(output_path.resolve()))

    def test_pkg_builder_postinstall_runs_user_install_for_console_user(self) -> None:
        spec = importlib.util.spec_from_file_location("codex_mn_build_pkg", PKG_BUILDER_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        script = module.render_postinstall_script("/Users/Shared/Codex Companion/CodexCompanion-test")

        self.assertIn("/dev/console", script)
        self.assertIn("NFSHomeDirectory", script)
        self.assertIn("CodexCompanion.zip", script)
        self.assertIn("/usr/bin/unzip", script)
        self.assertIn("CODEX_MN_INSTALLER_PKG=1", script)
        self.assertIn("/bin/zsh ./install.sh", script)
        self.assertNotIn("HOME=/var/root", script)

    def test_pkg_builder_disables_appledouble_metadata(self) -> None:
        spec = importlib.util.spec_from_file_location("codex_mn_build_pkg_metadata", PKG_BUILDER_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        env = module.pkgbuild_environment()

        self.assertEqual(env["COPYFILE_DISABLE"], "1")
        self.assertTrue(callable(module.clear_extended_attributes))
        self.assertTrue(any(r"\._" in pattern for pattern in module.PKGBUILD_FILTERS))
        self.assertTrue(any("DS_Store" in pattern for pattern in module.PKGBUILD_FILTERS))

    def test_pkg_payload_staging_rewrites_files_without_xattrs(self) -> None:
        spec = importlib.util.spec_from_file_location("codex_mn_build_pkg_plaincopy", PKG_BUILDER_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        if not module.shutil.which("xattr"):
            self.skipTest("xattr is not available")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "CodexCompanion-test"
            payload = Path(tmp) / "payload"
            root.mkdir()
            source = root / "install.sh"
            source.write_text("#!/bin/zsh\necho ok\n", encoding="utf-8")
            set_xattr = subprocess.run(
                ["xattr", "-w", "com.codex.test", "1", str(source)],
                text=True,
                capture_output=True,
                check=False,
            )
            if set_xattr.returncode != 0:
                self.skipTest("could not write test xattr")

            module.stage_pkg_payload(root, payload)
            staged = payload / "Users/Shared/Codex Companion/CodexCompanion-test/install.sh"
            listed = subprocess.run(["xattr", "-l", str(staged)], text=True, capture_output=True, check=False)

            self.assertEqual(staged.read_text(encoding="utf-8"), "#!/bin/zsh\necho ok\n")
            self.assertNotIn("com.codex.test", listed.stdout + listed.stderr)

    @unittest.skipUnless(Path("/usr/bin/pkgbuild").exists(), "pkgbuild is not available")
    def test_pkg_builder_strips_appledouble_from_flat_pkg_scripts(self) -> None:
        spec = importlib.util.spec_from_file_location("codex_mn_build_pkg_strip", PKG_BUILDER_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            scripts = tmp_path / "scripts"
            scripts.mkdir()
            postinstall = scripts / "postinstall"
            postinstall.write_text("#!/bin/zsh\necho ok\n", encoding="utf-8")
            postinstall.chmod(0o755)
            component = tmp_path / "component.pkg"
            dirty = tmp_path / "dirty.pkg"
            cleaned = tmp_path / "cleaned.pkg"

            subprocess.run(
                [
                    "/usr/bin/pkgbuild",
                    "--nopayload",
                    "--scripts",
                    str(scripts),
                    "--identifier",
                    "com.codex.test",
                    "--version",
                    "1",
                    str(component),
                ],
                check=True,
                env=module.pkgbuild_environment(),
                capture_output=True,
            )
            subprocess.run(
                [
                    "/usr/bin/productbuild",
                    "--package",
                    str(component),
                    "--identifier",
                    "com.codex.test",
                    "--version",
                    "1",
                    str(dirty),
                ],
                check=True,
                env=module.pkgbuild_environment(),
                capture_output=True,
            )

            module.strip_pkg_appledouble(dirty, cleaned)

            expanded = tmp_path / "expanded"
            subprocess.run(["/usr/sbin/pkgutil", "--expand", str(cleaned), str(expanded)], check=True)
            appledouble = [path for path in expanded.rglob("._*")]

            self.assertEqual(appledouble, [])

    def test_readme_first_points_to_unified_installer(self) -> None:
        text = (PACKAGE_ROOT / "README-FIRST.txt").read_text(encoding="utf-8")

        self.assertIn("Double-click: Install Codex Companion.command", text)
        self.assertIn("Run: ./install.sh", text)
        self.assertIn("Double-click: Uninstall Codex Companion.command", text)
        self.assertIn("Collect Native Highlight Evidence.command", text)
        self.assertIn("Collect Cross-Machine Evidence.command", text)
        self.assertIn("Notarize Package.command", text)
        self.assertIn("Run: ./uninstall.sh", text)
        self.assertNotIn("companion/install_extension.sh", text)

    def test_release_smoke_test_accepts_installable_zip(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "codex_mn_release_smoke_test",
            PACKAGE_ROOT / "release_smoke_test.py",
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "CodexCompanion-test.zip"
            entries = {
                "CodexCompanion-test/README.md": "Codex Companion for MarginNote 4\n",
                "CodexCompanion-test/CHANGELOG.md": "## 0.4.7 - 2026-06-23\n",
                "CodexCompanion-test/LICENSE": "MIT License\n",
                "CodexCompanion-test/assets/cover.png": b"\x89PNG\r\n\x1a\n",
                "CodexCompanion-test/README-FIRST.txt": "Double-click: Install Codex Companion.command\n",
                "CodexCompanion-test/install.sh": "#!/bin/zsh\n",
                "CodexCompanion-test/uninstall.sh": "#!/bin/zsh\n",
                "CodexCompanion-test/Install Codex Companion.command": "#!/bin/zsh\n./install.sh\n",
                "CodexCompanion-test/Uninstall Codex Companion.command": "#!/bin/zsh\n./uninstall.sh\n",
                "CodexCompanion-test/Collect Native Highlight Evidence.command": "#!/bin/zsh\n--collect-native-highlight-evidence\n",
                "CodexCompanion-test/Collect Single Document Acceptance.command": "#!/bin/zsh\nsingle_document_acceptance.py\n",
                "CodexCompanion-test/Collect Cross-Machine Evidence.command": "#!/bin/zsh\n--collect-cross-machine-evidence\n",
                "CodexCompanion-test/Refresh MN Runtime.command": "#!/bin/zsh\nrefresh_mn_runtime.py\n",
                "CodexCompanion-test/Restart MarginNote 4.command": "#!/bin/zsh\nrestart_marginnote4\n",
                "CodexCompanion-test/Build Signed Package.command": "#!/bin/zsh\n--auto-sign\n",
                "CodexCompanion-test/Notarize Package.command": "#!/bin/zsh\nnotarize_pkg.py\n",
                "CodexCompanion-test/Prepare Release Handoff.command": "#!/bin/zsh\nprepare_release_handoff.py\n",
                "CodexCompanion-test/release_smoke_test.py": "print('smoke')\n",
                "CodexCompanion-test/release_acceptance.py": "Run final release acceptance gates\n",
                "CodexCompanion-test/single_document_acceptance.py": "codex-companion-single-document-acceptance-v1\n",
                "CodexCompanion-test/build_pkg.py": "PACKAGE_IDENTIFIER = \"com.codex.marginnote-companion\"\n",
                "CodexCompanion-test/notarize_pkg.py": "notarytool submit\n",
                "CodexCompanion-test/prepare_release_handoff.py": "Prepare a Codex Companion release handoff bundle\n",
                "CodexCompanion-test/companion/companion.py": "print('ok')\n",
                "CodexCompanion-test/companion/runtime_config.py": "DEFAULT_RUNTIME_SETTINGS = {}\n",
                "CodexCompanion-test/companion/doctor.py": "installable clean zip\n",
                "CodexCompanion-test/companion/refresh_mn_runtime.py": "MNRuntimeEvidence\n",
                "CodexCompanion-test/companion/install_companion.sh": "LEGACY_LABEL=\"com.liuwhale.codex-marginnote-assistant\"\n",
                "CodexCompanion-test/companion/install_extension.sh": "#!/bin/zsh\n",
                "CodexCompanion-test/extension/codex.mn.assistant/main.js": "appendSelectionPopupMenuActions\n",
                "CodexCompanion-test/extension/codex.mn.assistant/mnaddon.json": "{}\n",
            }
            with zipfile.ZipFile(package, "w") as archive:
                for name, content in entries.items():
                    archive.writestr(name, content)

            result = module.inspect_package(package)

            self.assertTrue(result.ok, result.problems)
            self.assertEqual(result.bad_entries, [])

    def test_release_smoke_test_runs_install_dry_run_from_zip(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "codex_mn_release_smoke_test_dry_run",
            PACKAGE_ROOT / "release_smoke_test.py",
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "CodexCompanion-test.zip"
            entries = {
                "CodexCompanion-test/README-FIRST.txt": "Double-click: Install Codex Companion.command\n",
                "CodexCompanion-test/install.sh": "#!/bin/zsh\n[[ \"${CODEX_MN_DRY_RUN:-0}\" == \"1\" ]] || exit 8\ntouch \"$CODEX_MN_COMPANION_HOME/install-dry-run-ok\"\n",
                "CodexCompanion-test/uninstall.sh": "#!/bin/zsh\n[[ \"${CODEX_MN_DRY_RUN:-0}\" == \"1\" ]] || exit 9\ntouch \"$CODEX_MN_COMPANION_HOME/uninstall-dry-run-ok\"\n",
                "CodexCompanion-test/Install Codex Companion.command": "#!/bin/zsh\n./install.sh\n",
                "CodexCompanion-test/Uninstall Codex Companion.command": "#!/bin/zsh\n./uninstall.sh\n",
                "CodexCompanion-test/Collect Native Highlight Evidence.command": "#!/bin/zsh\n--collect-native-highlight-evidence\n",
                "CodexCompanion-test/Collect Single Document Acceptance.command": "#!/bin/zsh\nsingle_document_acceptance.py\n",
                "CodexCompanion-test/Collect Cross-Machine Evidence.command": "#!/bin/zsh\n--collect-cross-machine-evidence\n",
                "CodexCompanion-test/Refresh MN Runtime.command": "#!/bin/zsh\nrefresh_mn_runtime.py\n",
                "CodexCompanion-test/Restart MarginNote 4.command": "#!/bin/zsh\nrestart_marginnote4\n",
                "CodexCompanion-test/Build Signed Package.command": "#!/bin/zsh\n--auto-sign\n",
                "CodexCompanion-test/Notarize Package.command": "#!/bin/zsh\nnotarize_pkg.py\n",
                "CodexCompanion-test/Prepare Release Handoff.command": "#!/bin/zsh\nprepare_release_handoff.py\n",
                "CodexCompanion-test/release_smoke_test.py": "print('smoke')\n",
                "CodexCompanion-test/release_acceptance.py": "Run final release acceptance gates\n",
                "CodexCompanion-test/single_document_acceptance.py": "codex-companion-single-document-acceptance-v1\n",
                "CodexCompanion-test/build_pkg.py": "PACKAGE_IDENTIFIER = \"com.codex.marginnote-companion\"\n",
                "CodexCompanion-test/notarize_pkg.py": "notarytool submit\n",
                "CodexCompanion-test/prepare_release_handoff.py": "Prepare a Codex Companion release handoff bundle\n",
                "CodexCompanion-test/companion/companion.py": "print('ok')\n",
                "CodexCompanion-test/companion/doctor.py": "installable clean zip\n",
                "CodexCompanion-test/companion/refresh_mn_runtime.py": "MNRuntimeEvidence\n",
                "CodexCompanion-test/companion/install_companion.sh": "LEGACY_LABEL=\"com.liuwhale.codex-marginnote-assistant\"\n",
                "CodexCompanion-test/companion/install_extension.sh": "#!/bin/zsh\n",
                "CodexCompanion-test/extension/codex.mn.assistant/main.js": "appendSelectionPopupMenuActions\n",
                "CodexCompanion-test/extension/codex.mn.assistant/mnaddon.json": "{}\n",
            }
            with zipfile.ZipFile(package, "w") as archive:
                for name, content in entries.items():
                    archive.writestr(name, content)

            result = module.run_install_dry_run(package)

            self.assertTrue(result["ok"], result)
            self.assertEqual(result["installReturnCode"], 0)
            self.assertEqual(result["uninstallReturnCode"], 0)


if __name__ == "__main__":
    unittest.main()
