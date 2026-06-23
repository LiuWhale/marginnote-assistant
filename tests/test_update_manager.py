from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any


UPDATE_MANAGER_PATH = Path(__file__).resolve().parents[1] / "update_manager.py"


def load_update_manager() -> Any:
    spec = importlib.util.spec_from_file_location("codex_mn_update_manager", UPDATE_MANAGER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UpdateManagerTests(unittest.TestCase):
    def test_public_release_html_parses_latest_zip_without_rest_api(self) -> None:
        module = load_update_manager()
        html = b"""
        <html>
          <body>
            <a href="/LiuWhale/marginnote-assistant/releases/download/v0.4.6/CodexCompanion-0.4.6-latest.pkg">pkg</a>
            <a href="/LiuWhale/marginnote-assistant/releases/download/v0.4.6/CodexCompanion-0.4.6-latest-dist.zip">zip</a>
          </body>
        </html>
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            requested_urls: list[str] = []

            class FakeResponse(BytesIO):
                headers = {"Content-Type": "text/html; charset=utf-8"}

                def __enter__(self) -> "FakeResponse":
                    return self

                def __exit__(self, *args: object) -> None:
                    return None

                def geturl(self) -> str:
                    return "https://github.com/LiuWhale/marginnote-assistant/releases/tag/v0.4.6"

            def fake_urlopen(req: Any, settings: dict[str, Any], timeout: float) -> FakeResponse:
                requested_urls.append(req.full_url)
                return FakeResponse(html)

            old_urlopen = module.urlopen_with_proxy
            module.urlopen_with_proxy = fake_urlopen
            try:
                result = module.check_for_update(
                    root,
                    {"githubRepo": "LiuWhale/marginnote-assistant", "proxyUrl": ""},
                    current_version="0.4.1",
                )
            finally:
                module.urlopen_with_proxy = old_urlopen

        self.assertTrue(result["ok"])
        self.assertTrue(result["available"])
        self.assertEqual(result["latestVersion"], "0.4.6")
        self.assertEqual(result["assetName"], "CodexCompanion-0.4.6-latest-dist.zip")
        self.assertEqual(
            result["downloadUrl"],
            "https://github.com/LiuWhale/marginnote-assistant/releases/download/v0.4.6/CodexCompanion-0.4.6-latest-dist.zip",
        )
        self.assertEqual(requested_urls, ["https://github.com/LiuWhale/marginnote-assistant/releases/latest"])

    def test_public_release_check_fetches_lazy_loaded_expanded_assets(self) -> None:
        module = load_update_manager()
        latest_html = b"""
        <html>
          <body>
            <include-fragment src="https://github.com/LiuWhale/marginnote-assistant/releases/expanded_assets/v0.4.6"></include-fragment>
          </body>
        </html>
        """
        assets_html = b"""
        <html>
          <body>
            <a href="/LiuWhale/marginnote-assistant/releases/download/v0.4.6/CodexCompanion-0.4.6-latest-dist.zip">zip</a>
          </body>
        </html>
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            requested_urls: list[str] = []

            class FakeResponse(BytesIO):
                def __init__(self, payload: bytes, final_url: str) -> None:
                    super().__init__(payload)
                    self._final_url = final_url
                    self.headers = {"Content-Type": "text/html; charset=utf-8"}

                def __enter__(self) -> "FakeResponse":
                    return self

                def __exit__(self, *args: object) -> None:
                    return None

                def geturl(self) -> str:
                    return self._final_url

            def fake_urlopen(req: Any, settings: dict[str, Any], timeout: float) -> FakeResponse:
                requested_urls.append(req.full_url)
                if req.full_url.endswith("/releases/latest"):
                    return FakeResponse(
                        latest_html,
                        "https://github.com/LiuWhale/marginnote-assistant/releases/tag/v0.4.6",
                    )
                if req.full_url.endswith("/releases/expanded_assets/v0.4.6"):
                    return FakeResponse(
                        assets_html,
                        "https://github.com/LiuWhale/marginnote-assistant/releases/expanded_assets/v0.4.6",
                    )
                raise AssertionError(f"unexpected URL: {req.full_url}")

            old_urlopen = module.urlopen_with_proxy
            module.urlopen_with_proxy = fake_urlopen
            try:
                result = module.check_for_update(
                    root,
                    {"githubRepo": "LiuWhale/marginnote-assistant", "proxyUrl": ""},
                    current_version="0.4.1",
                )
            finally:
                module.urlopen_with_proxy = old_urlopen

        self.assertTrue(result["ok"])
        self.assertEqual(result["latestVersion"], "0.4.6")
        self.assertEqual(result["assetName"], "CodexCompanion-0.4.6-latest-dist.zip")
        self.assertEqual(
            requested_urls,
            [
                "https://github.com/LiuWhale/marginnote-assistant/releases/latest",
                "https://github.com/LiuWhale/marginnote-assistant/releases/expanded_assets/v0.4.6",
            ],
        )

    def test_release_metadata_selects_latest_dist_zip_and_compares_version(self) -> None:
        module = load_update_manager()

        release = {
            "tag_name": "v0.4.6",
            "html_url": "https://github.com/LiuWhale/marginnote-assistant/releases/tag/v0.4.6",
            "name": "Codex Companion 0.4.6",
            "body": "Fixes and updater.",
            "assets": [
                {"name": "CodexCompanion-0.4.6-latest.pkg", "browser_download_url": "https://example/pkg"},
                {
                    "name": "CodexCompanion-0.4.6-latest-dist.zip",
                    "browser_download_url": "https://example/CodexCompanion-0.4.6-latest-dist.zip",
                    "size": 42,
                },
            ],
        }

        parsed = module.parse_latest_release(release, current_version="0.4.1", repo="LiuWhale/marginnote-assistant")

        self.assertTrue(parsed["ok"])
        self.assertTrue(parsed["available"])
        self.assertEqual(parsed["repo"], "LiuWhale/marginnote-assistant")
        self.assertEqual(parsed["latestVersion"], "0.4.6")
        self.assertEqual(parsed["currentVersion"], "0.4.1")
        self.assertEqual(parsed["assetName"], "CodexCompanion-0.4.6-latest-dist.zip")
        self.assertEqual(parsed["downloadUrl"], "https://example/CodexCompanion-0.4.6-latest-dist.zip")

    def test_release_metadata_rejects_release_without_installable_zip(self) -> None:
        module = load_update_manager()

        parsed = module.parse_latest_release(
            {"tag_name": "v0.4.6", "assets": [{"name": "CodexCompanion.pkg", "browser_download_url": "https://example/pkg"}]},
            current_version="0.4.1",
            repo="LiuWhale/marginnote-assistant",
        )

        self.assertFalse(parsed["ok"])
        self.assertIn("release zip", parsed["message"])

    def test_validate_release_zip_requires_installable_package_shape(self) -> None:
        module = load_update_manager()
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "CodexCompanion-0.4.6-latest-dist.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("CodexCompanion-0.4.6/install.sh", "#!/bin/zsh\n")
                archive.writestr("CodexCompanion-0.4.6/companion/companion.py", "print('ok')\n")
                archive.writestr("CodexCompanion-0.4.6/extension/codex.mn.assistant/mnaddon.json", "{}\n")

            result = module.validate_release_zip(archive_path)

            self.assertTrue(result["ok"])
            self.assertEqual(result["packageRoot"], "CodexCompanion-0.4.6")
            self.assertEqual(result["installScript"], str(Path(tmp) / "CodexCompanion-0.4.6" / "install.sh"))

    def test_update_status_file_round_trips_install_dry_run(self) -> None:
        module = load_update_manager()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status_path = root / "control" / "update_status.json"

            written = module.write_update_status(
                root,
                {
                    "state": "available",
                    "repo": "LiuWhale/marginnote-assistant",
                    "latestVersion": "0.4.6",
                },
            )
            loaded = json.loads(status_path.read_text(encoding="utf-8"))

            self.assertEqual(written["state"], "available")
            self.assertEqual(loaded["repo"], "LiuWhale/marginnote-assistant")
            self.assertEqual(module.read_update_status(root)["latestVersion"], "0.4.6")

    def test_installing_status_reports_permission_failure_from_install_log(self) -> None:
        module = load_update_manager()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_path = root / "updates" / "install-latest.log"
            log_path.parent.mkdir(parents=True)
            log_path.write_text(
                "Installing Codex Companion for MarginNote 4...\n"
                "rsync: open: Operation not permitted\n",
                encoding="utf-8",
            )
            module.write_update_status(
                root,
                {
                    "ok": True,
                    "state": "installing",
                    "repo": "LiuWhale/marginnote-assistant",
                    "currentVersion": "0.4.2",
                    "latestVersion": "0.4.6",
                    "installLog": str(log_path),
                },
            )

            status = module.read_update_status(root)

        self.assertFalse(status["ok"])
        self.assertEqual(status["state"], "error")
        self.assertIn("权限不足", status["message"])
        self.assertIn("完全磁盘访问", status["message"])

    def test_install_update_stops_before_script_when_extension_target_is_not_writable(self) -> None:
        module = load_update_manager()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_path = root / "updates" / "CodexCompanion-0.4.6-latest-dist.zip"
            archive_path.parent.mkdir(parents=True)
            archive_path.write_text("zip", encoding="utf-8")
            popen_called = False

            def fake_check(root_arg: Path, settings: dict[str, Any], current_version: str) -> dict[str, Any]:
                return {
                    "ok": True,
                    "state": "available",
                    "available": True,
                    "repo": "LiuWhale/marginnote-assistant",
                    "currentVersion": current_version,
                    "latestVersion": "0.4.6",
                    "assetName": "CodexCompanion-0.4.6-latest-dist.zip",
                    "downloadUrl": "https://example/CodexCompanion-0.4.6-latest-dist.zip",
                }

            def fake_download(root_arg: Path, settings: dict[str, Any], update: dict[str, Any]) -> Path:
                return archive_path

            def fake_validate(path: Path) -> dict[str, Any]:
                return {
                    "ok": True,
                    "packageRootPath": str(root / "updates" / "CodexCompanion-0.4.6"),
                    "installScript": str(root / "updates" / "CodexCompanion-0.4.6" / "install.sh"),
                }

            def fake_popen(*args: Any, **kwargs: Any) -> None:
                nonlocal popen_called
                popen_called = True

            old_check = module.check_for_update
            old_download = module.download_asset
            old_validate = module.validate_release_zip
            old_access = getattr(module, "check_extension_write_access", None)
            old_popen = module.subprocess.Popen
            module.check_for_update = fake_check
            module.download_asset = fake_download
            module.validate_release_zip = fake_validate
            module.subprocess.Popen = fake_popen
            try:
                module.check_extension_write_access = lambda: (False, "权限不足：无法写入 MarginNote 扩展目录。")
                result = module.install_update(root, {"githubRepo": "LiuWhale/marginnote-assistant"}, "0.4.6")
            finally:
                module.check_for_update = old_check
                module.download_asset = old_download
                module.validate_release_zip = old_validate
                if old_access is None:
                    delattr(module, "check_extension_write_access")
                else:
                    module.check_extension_write_access = old_access
                module.subprocess.Popen = old_popen

        self.assertFalse(result["ok"])
        self.assertEqual(result["state"], "error")
        self.assertIn("权限不足", result["message"])
        self.assertFalse(popen_called)
