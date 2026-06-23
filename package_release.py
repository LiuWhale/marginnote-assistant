#!/usr/bin/env python3
from __future__ import annotations

import os
import hashlib
import shutil
import sys
import time
import zipfile
from pathlib import Path


HOME = Path.home()
ROOT = Path(os.environ.get("CODEX_MN_COMPANION_HOME", HOME / ".codex/marginnote-assistant")).expanduser()
SOURCE_EXT_DIR = ROOT / "extension/codex.mn.assistant"
LIVE_EXT_DIR = HOME / "Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant"
EXT_DIR = SOURCE_EXT_DIR if SOURCE_EXT_DIR.is_dir() else LIVE_EXT_DIR
ONEDRIVE_DIR = HOME / "Library/CloudStorage/OneDrive-个人/Codex Companion"
RELEASE_DIR = ROOT / "release"
ROOT_FILES = [
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
]

COMPANION_EXCLUDES = {
    ".DS_Store",
    ".git",
    ".env",
    "__pycache__",
    "logs",
    "sessions",
    "queue",
    "uploads",
    "control",
    "drafts",
    "backups",
    "release",
    "updates",
    "extension",
    "events.jsonl",
    "companion.pid",
    "companion_settings.json",
    "goal.json",
    "mn4_screenshot.png",
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
    "build_pkg.py",
    "notarize_pkg.py",
    "prepare_release_handoff.py",
}
EXTENSION_EXCLUDES = {".DS_Store", "__MACOSX"}


def ignore_names(excludes: set[str]):
    def _ignore(directory: str, names: list[str]) -> set[str]:
        ignored: set[str] = set()
        for name in names:
            if name in excludes or name.endswith(".pyc") or name.startswith("._"):
                ignored.add(name)
        return ignored

    return _ignore


def zip_dir(source: Path, target: Path) -> None:
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_dir() or path.name.startswith("._"):
                continue
            archive.write(path, path.relative_to(source.parent))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_sha256_manifest(paths: list[Path], target: Path) -> None:
    lines = []
    for path in paths:
        if path.exists() and path.is_file():
            lines.append(f"{sha256_file(path)}  {path.name}")
    target.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def copy_root_files(package_root: Path) -> None:
    for name in ROOT_FILES:
        source = ROOT / name
        if not source.exists():
            raise FileNotFoundError(f"Missing package root file: {source}")
        shutil.copy2(source, package_root / name)


def copy_public_assets(package_root: Path) -> None:
    assets = ROOT / "assets"
    if assets.exists():
        shutil.copytree(assets, package_root / "assets", ignore=ignore_names({".DS_Store", "__pycache__"}))


def main() -> int:
    version = sys.argv[1] if len(sys.argv) > 1 else "0.4.11"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    package_name = f"CodexCompanion-{version}-{stamp}-dist.zip"
    latest_name = f"CodexCompanion-{version}-latest-dist.zip"
    package_path = RELEASE_DIR / package_name
    latest_path = RELEASE_DIR / latest_name

    if not EXT_DIR.is_dir():
        raise SystemExit(f"Missing MarginNote extension directory: {EXT_DIR}")

    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    ONEDRIVE_DIR.mkdir(parents=True, exist_ok=True)

    stage = RELEASE_DIR / f"stage.py.{os.getpid()}"
    if stage.exists():
        shutil.rmtree(stage)
    package_root = stage / f"CodexCompanion-{version}"
    try:
        (package_root / "companion").mkdir(parents=True)
        (package_root / "extension").mkdir(parents=True)
        shutil.copytree(EXT_DIR, package_root / "extension/codex.mn.assistant", ignore=ignore_names(EXTENSION_EXCLUDES))
        shutil.copytree(ROOT, package_root / "companion", dirs_exist_ok=True, ignore=ignore_names(COMPANION_EXCLUDES))
        copy_root_files(package_root)
        copy_public_assets(package_root)
        zip_dir(package_root, package_path)
        shutil.copy2(package_path, latest_path)
        shutil.copy2(package_path, ONEDRIVE_DIR / package_name)
        shutil.copy2(latest_path, ONEDRIVE_DIR / latest_name)
        write_sha256_manifest([package_path, latest_path], RELEASE_DIR / "SHA256SUMS.txt")
        write_sha256_manifest(
            [ONEDRIVE_DIR / package_name, ONEDRIVE_DIR / latest_name],
            ONEDRIVE_DIR / "SHA256SUMS.txt",
        )
        shutil.copy2(ROOT / "README.md", ONEDRIVE_DIR / "README.md")
        shutil.copy2(ROOT / "CHANGELOG.md", ONEDRIVE_DIR / "CHANGELOG.md")
        shutil.copy2(ROOT / "LICENSE", ONEDRIVE_DIR / "LICENSE")
        assets_target = ONEDRIVE_DIR / "assets"
        if assets_target.exists():
            shutil.rmtree(assets_target)
        if (ROOT / "assets").exists():
            shutil.copytree(ROOT / "assets", assets_target, ignore=ignore_names({".DS_Store", "__pycache__"}))
        docs_target = ONEDRIVE_DIR / "docs"
        if docs_target.exists():
            shutil.rmtree(docs_target)
        shutil.copytree(ROOT / "docs", docs_target, ignore=ignore_names({".DS_Store", "__pycache__"}))
    finally:
        if stage.exists():
            shutil.rmtree(stage)

    print(package_path)
    print(latest_path)
    print(ONEDRIVE_DIR / latest_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
