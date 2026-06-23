#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_PACKAGE = ROOT / "release/CodexCompanion-0.4.12-latest-dist.zip"

REQUIRED_SUFFIXES = [
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
    "assets/cover.png",
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
    "companion/companion.py",
    "companion/runtime_config.py",
    "companion/doctor.py",
    "companion/install_companion.sh",
    "companion/install_extension.sh",
    "extension/codex.mn.assistant/main.js",
    "extension/codex.mn.assistant/mnaddon.json",
]

PRIVATE_NAMES = {
    "companion/.env",
    "companion/companion_settings.json",
    "companion/events.jsonl",
    "companion/goal.json",
    "companion/companion.pid",
}
PRIVATE_PARTS = (
    "companion/uploads/",
    "companion/queue/",
    "companion/drafts/",
    "companion/release/",
    "companion/logs/",
    "companion/control/",
    "companion/backups/",
    "companion/sessions/",
)

MARKERS = {
    "README.md": "Codex Companion for MarginNote 4",
    "CHANGELOG.md": "## 0.4.12 - 2026-06-23",
    "LICENSE": "MIT License",
    "README-FIRST.txt": "Double-click: Install Codex Companion.command",
    "Install Codex Companion.command": "install.sh",
    "Uninstall Codex Companion.command": "uninstall.sh",
    "Collect Native Highlight Evidence.command": "--collect-native-highlight-evidence",
    "Collect Single Document Acceptance.command": "single_document_acceptance.py",
    "Collect Cross-Machine Evidence.command": "--collect-cross-machine-evidence",
    "Refresh MN Runtime.command": "refresh_mn_runtime.py",
    "Restart MarginNote 4.command": "restart_marginnote4",
    "Build Signed Package.command": "--auto-sign",
    "Notarize Package.command": "notarize_pkg.py",
    "Prepare Release Handoff.command": "prepare_release_handoff.py",
    "release_acceptance.py": "Run final release acceptance gates",
    "single_document_acceptance.py": "codex-companion-single-document-acceptance-v1",
    "build_pkg.py": "PACKAGE_IDENTIFIER = \"com.codex.marginnote-companion\"",
    "notarize_pkg.py": "notarytool submit",
    "prepare_release_handoff.py": "Prepare a Codex Companion release handoff bundle",
    "companion/install_companion.sh": "LEGACY_LABEL=\"com.liuwhale.codex-marginnote-assistant\"",
    "companion/runtime_config.py": "DEFAULT_RUNTIME_SETTINGS",
    "companion/doctor.py": "installable clean zip",
    "extension/codex.mn.assistant/main.js": "appendSelectionPopupMenuActions",
}


@dataclass
class SmokeResult:
    ok: bool
    package: str
    sha256: str
    file_count: int
    missing: list[str]
    bad_entries: list[str]
    missing_markers: list[str]
    problems: list[str]
    sha256_manifest: dict[str, object] | None = None


def read_sha256_manifest(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) >= 2:
            entries[parts[-1]] = parts[0]
    return entries


def inspect_sidecar_sha256_manifest(package: Path, expected_sha256: str) -> dict[str, object]:
    manifest = package.parent / "SHA256SUMS.txt"
    payload: dict[str, object] = {
        "path": str(manifest),
        "exists": manifest.exists(),
        "packageName": package.name,
        "expectedSha256": expected_sha256,
        "manifestSha256": "",
        "matches": False,
    }
    if not manifest.exists():
        return payload
    try:
        entries = read_sha256_manifest(manifest)
    except Exception as exc:
        payload["error"] = str(exc)
        return payload
    observed = entries.get(package.name, "")
    payload["manifestSha256"] = observed
    payload["matches"] = observed == expected_sha256
    payload["entryCount"] = len(entries)
    return payload


def suffixes(names: list[str]) -> list[str]:
    return [name.split("/", 1)[1] for name in names if "/" in name]


def inspect_package(path: Path) -> SmokeResult:
    path = path.expanduser()
    problems: list[str] = []
    if not path.exists():
        return SmokeResult(False, str(path), "", 0, REQUIRED_SUFFIXES[:], [], list(MARKERS), ["package does not exist"])

    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        suffix_list = suffixes(names)
        missing = [item for item in REQUIRED_SUFFIXES if item not in suffix_list]
        bad_entries = [
            item
            for item in suffix_list
            if item in PRIVATE_NAMES or any(part in item for part in PRIVATE_PARTS)
        ]
        missing_markers: list[str] = []
        for suffix, marker in MARKERS.items():
            matched = False
            for name in names:
                if not name.endswith("/" + suffix):
                    continue
                text = archive.read(name).decode("utf-8", errors="replace")
                if marker in text:
                    matched = True
                    break
            if not matched:
                missing_markers.append(suffix)

    sha256_manifest = inspect_sidecar_sha256_manifest(path, digest)
    if sha256_manifest.get("exists") and not sha256_manifest.get("matches"):
        problems.append("sha256 manifest mismatch")
    if missing:
        problems.append("missing required files: " + ", ".join(missing))
    if bad_entries:
        problems.append(f"private runtime entries found: {len(bad_entries)}")
    if missing_markers:
        problems.append("missing content markers: " + ", ".join(missing_markers))

    return SmokeResult(
        ok=not problems,
        package=str(path),
        sha256=digest,
        file_count=len(names),
        missing=missing,
        bad_entries=bad_entries,
        missing_markers=missing_markers,
        problems=problems,
        sha256_manifest=sha256_manifest,
    )


def package_root_from_extract(extract_dir: Path) -> Path:
    roots = [path for path in extract_dir.iterdir() if path.is_dir() and path.name.startswith("CodexCompanion-")]
    if len(roots) != 1:
        raise RuntimeError(f"expected one CodexCompanion package root, found {len(roots)}")
    return roots[0]


def run_script(script: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/zsh", str(script)],
        cwd=str(script.parent),
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def run_install_dry_run(path: Path) -> dict[str, object]:
    path = path.expanduser()
    with tempfile.TemporaryDirectory(prefix="codex-companion-dry-run-") as tmp:
        tmp_path = Path(tmp)
        extract_dir = tmp_path / "extract"
        fake_home = tmp_path / "home"
        companion_home = fake_home / ".codex/marginnote-assistant"
        extract_dir.mkdir()
        companion_home.mkdir(parents=True)
        fake_home.mkdir(exist_ok=True)
        with zipfile.ZipFile(path) as archive:
            archive.extractall(extract_dir)
        package_root = package_root_from_extract(extract_dir)
        env = os.environ.copy()
        env.update(
            {
                "HOME": str(fake_home),
                "CODEX_MN_COMPANION_HOME": str(companion_home),
                "CODEX_MN_DRY_RUN": "1",
            }
        )
        install = run_script(package_root / "install.sh", env)
        uninstall = run_script(package_root / "uninstall.sh", env)
        return {
            "ok": install.returncode == 0 and uninstall.returncode == 0,
            "packageRoot": str(package_root),
            "fakeHome": str(fake_home),
            "installReturnCode": install.returncode,
            "uninstallReturnCode": uninstall.returncode,
            "installStdout": install.stdout[-2000:],
            "installStderr": install.stderr[-2000:],
            "uninstallStdout": uninstall.stdout[-2000:],
            "uninstallStderr": uninstall.stderr[-2000:],
            "installedCompanionPy": (companion_home / "companion.py").exists(),
            "renderedLaunchAgent": (fake_home / "Library/LaunchAgents/com.codex.paper-companion.plist").exists(),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run offline checks against a Codex Companion release zip.")
    parser.add_argument("package", nargs="?", default=str(DEFAULT_PACKAGE), help="Release zip to inspect.")
    parser.add_argument("--install-dry-run", action="store_true", help="Extract to a temporary HOME and run install/uninstall in dry-run mode.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    result = inspect_package(Path(args.package))
    dry_run = run_install_dry_run(Path(args.package)) if result.ok and args.install_dry_run else None
    ok = result.ok and (dry_run is None or bool(dry_run.get("ok")))
    if args.json:
        payload = result.__dict__.copy()
        payload["ok"] = ok
        if dry_run is not None:
            payload["installDryRun"] = dry_run
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        status = "OK" if ok else "FAIL"
        print(f"[{status}] {result.package}")
        print(f"sha256={result.sha256}")
        print(f"files={result.file_count}")
        if result.problems:
            for problem in result.problems:
                print(f"- {problem}")
        if dry_run is not None:
            print(f"installDryRun={dry_run.get('ok')}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
