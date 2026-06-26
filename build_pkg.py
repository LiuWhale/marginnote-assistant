#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_VERSION = "0.4.33"
DEFAULT_ZIP = ROOT / f"release/CodexCompanion-{DEFAULT_VERSION}-latest-dist.zip"
DEFAULT_OUTPUT = ROOT / f"release/CodexCompanion-{DEFAULT_VERSION}-latest.pkg"
ONEDRIVE_DIR = Path.home() / "Library/CloudStorage/OneDrive-个人/Codex Companion"
PACKAGE_IDENTIFIER = "com.codex.marginnote-companion"
SHARED_INSTALL_PARENT = Path("Users/Shared/Codex Companion")
PKGBUILD_FILTERS = [
    r"(^|/)\.DS_Store$",
    r"(^|/)__MACOSX(/|$)",
    r"(^|/)\._[^/]*$",
]


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


def matching_mnaddon_for_zip(zip_path: Path) -> Path | None:
    zip_path = zip_path.expanduser().resolve()
    name = zip_path.name
    candidates: list[Path] = []
    if name.endswith("-latest-dist.zip"):
        candidates.append(zip_path.with_name(name.replace("-latest-dist.zip", "-latest.mnaddon")))
    if name.endswith("-dist.zip"):
        candidates.append(zip_path.with_name(name[: -len("-dist.zip")] + ".mnaddon"))
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def release_manifest_paths(zip_path: Path, pkg_path: Path) -> list[Path]:
    paths = [zip_path]
    mnaddon_path = matching_mnaddon_for_zip(zip_path)
    if mnaddon_path:
        paths.append(mnaddon_path)
    paths.append(pkg_path)
    return paths


def infer_release_version(zip_path: Path) -> str:
    match = re.search(r"CodexCompanion-(\d+\.\d+\.\d+)-", zip_path.name)
    return match.group(1) if match else DEFAULT_VERSION


def default_output_for_zip(zip_path: Path, version: str) -> Path:
    return zip_path.expanduser().resolve().with_name(f"CodexCompanion-{version}-latest.pkg")


def sync_release_artifacts(zip_path: Path, pkg_path: Path, onedrive_dir: Path = ONEDRIVE_DIR) -> dict[str, object]:
    zip_path = zip_path.expanduser().resolve()
    pkg_path = pkg_path.expanduser().resolve()
    onedrive_dir = onedrive_dir.expanduser().resolve()
    onedrive_dir.mkdir(parents=True, exist_ok=True)
    cloud_zip = onedrive_dir / zip_path.name
    cloud_pkg = onedrive_dir / pkg_path.name
    shutil.copy2(zip_path, cloud_zip)
    mnaddon_path = matching_mnaddon_for_zip(zip_path)
    cloud_mnaddon = onedrive_dir / mnaddon_path.name if mnaddon_path else None
    if mnaddon_path and cloud_mnaddon:
        shutil.copy2(mnaddon_path, cloud_mnaddon)
    shutil.copy2(pkg_path, cloud_pkg)
    local_manifest = pkg_path.parent / "SHA256SUMS.txt"
    cloud_manifest = onedrive_dir / "SHA256SUMS.txt"
    write_sha256_manifest(release_manifest_paths(zip_path, pkg_path), local_manifest)
    cloud_manifest_paths = [cloud_zip]
    if cloud_mnaddon:
        cloud_manifest_paths.append(cloud_mnaddon)
    cloud_manifest_paths.append(cloud_pkg)
    write_sha256_manifest(cloud_manifest_paths, cloud_manifest)
    return {
        "onedriveDir": str(onedrive_dir),
        "onedriveZip": str(cloud_zip),
        "onedriveMnaddon": str(cloud_mnaddon) if cloud_mnaddon else "",
        "onedrivePkg": str(cloud_pkg),
        "localManifest": str(local_manifest),
        "onedriveManifest": str(cloud_manifest),
    }


def shell_single_quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


def render_postinstall_script(installer_root: str, embedded_zip_name: str = "CodexCompanion.zip") -> str:
    quoted_root = shell_single_quote(installer_root)
    quoted_parent = shell_single_quote(str(Path(installer_root).parent))
    quoted_zip_name = shell_single_quote(embedded_zip_name)
    return f"""#!/bin/zsh
set -euo pipefail

INSTALLER_ROOT={quoted_root}
INSTALLER_PARENT={quoted_parent}
EMBEDDED_ZIP_NAME={quoted_zip_name}
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ZIP_PATH="$SCRIPT_DIR/$EMBEDDED_ZIP_NAME"
CONSOLE_USER="$(/usr/bin/stat -f %Su /dev/console)"

if [[ -z "$CONSOLE_USER" || "$CONSOLE_USER" == "root" || "$CONSOLE_USER" == "loginwindow" ]]; then
  echo "Codex Companion installer could not find an active desktop user." >&2
  exit 1
fi

CONSOLE_HOME="$(/usr/bin/dscl . -read "/Users/$CONSOLE_USER" NFSHomeDirectory | /usr/bin/awk '{{print $2}}')"
if [[ -z "$CONSOLE_HOME" || ! -d "$CONSOLE_HOME" ]]; then
  echo "Codex Companion installer could not resolve home for $CONSOLE_USER." >&2
  exit 1
fi

if [[ ! -f "$ZIP_PATH" ]]; then
  echo "Codex Companion installer payload is missing $EMBEDDED_ZIP_NAME." >&2
  exit 1
fi

/bin/rm -rf "$INSTALLER_ROOT"
/bin/mkdir -p "$INSTALLER_PARENT"
/usr/bin/unzip -q "$ZIP_PATH" -d "$INSTALLER_PARENT"

if [[ ! -f "$INSTALLER_ROOT/install.sh" ]]; then
  echo "Codex Companion installer payload is missing install.sh at $INSTALLER_ROOT." >&2
  exit 1
fi

/usr/bin/sudo -u "$CONSOLE_USER" \\
  HOME="$CONSOLE_HOME" \\
  CODEX_MN_INSTALLER_PKG=1 \\
  /bin/zsh -lc "cd {quoted_root} && /bin/zsh ./install.sh"
"""


def package_root_from_extract(extract_dir: Path) -> Path:
    roots = [path for path in extract_dir.iterdir() if path.is_dir() and path.name.startswith("CodexCompanion-")]
    if len(roots) != 1:
        raise RuntimeError(f"expected one CodexCompanion package root, found {len(roots)}")
    return roots[0]


def ignore_metadata_names(directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name == ".DS_Store" or name.startswith("._") or name == "__MACOSX"}


def extract_release_zip(zip_path: Path, extract_dir: Path) -> Path:
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(extract_dir)
    return package_root_from_extract(extract_dir)


def stage_pkg_payload(package_root: Path, payload_root: Path) -> Path:
    shared_root = payload_root / SHARED_INSTALL_PARENT / package_root.name
    shared_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(package_root, shared_root, ignore=ignore_metadata_names)
    return Path("/") / SHARED_INSTALL_PARENT / package_root.name


def write_pkg_scripts(scripts_dir: Path, installer_root: Path, zip_path: Path) -> Path:
    scripts_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(zip_path, scripts_dir / "CodexCompanion.zip")
    postinstall = scripts_dir / "postinstall"
    postinstall.write_text(render_postinstall_script(str(installer_root)), encoding="utf-8")
    postinstall.chmod(0o755)
    clear_extended_attributes(scripts_dir)
    return postinstall


def pkgbuild_environment() -> dict[str, str]:
    env = os.environ.copy()
    env["COPYFILE_DISABLE"] = "1"
    return env


def clear_extended_attributes(path: Path) -> None:
    xattr = shutil.which("xattr")
    if not xattr:
        return
    subprocess.run([xattr, "-cr", str(path)], text=True, capture_output=True, check=False, env=pkgbuild_environment())
    for item in [path, *path.rglob("*")]:
        if not item.exists() and not item.is_symlink():
            continue
        listed = subprocess.run(
            [xattr, str(item)],
            text=True,
            capture_output=True,
            check=False,
            env=pkgbuild_environment(),
        )
        for attr in listed.stdout.splitlines():
            attr = attr.strip()
            if attr:
                subprocess.run([xattr, "-d", attr, str(item)], text=True, capture_output=True, check=False, env=pkgbuild_environment())


def run_command(cmd: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        check=False,
        env=pkgbuild_environment(),
    )
    if completed.returncode != 0:
        detail = "\n".join(
            part
            for part in (
                "command failed: " + " ".join(cmd),
                completed.stdout.strip(),
                completed.stderr.strip(),
            )
            if part
        )
        raise RuntimeError(detail)
    return {
        "command": cmd,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
    }


def parse_developer_id_installer_identities(output: str) -> list[str]:
    identities: list[str] = []
    for line in output.splitlines():
        if "Developer ID Installer:" not in line:
            continue
        parts = line.split('"')
        if len(parts) >= 3:
            identity = parts[1].strip()
        else:
            identity = line.strip()
        if identity.startswith("Developer ID Installer:") and identity not in identities:
            identities.append(identity)
    return identities


def find_developer_id_installer_identities() -> list[str]:
    completed = subprocess.run(
        ["security", "find-identity", "-v", "-p", "basic"],
        text=True,
        capture_output=True,
        check=False,
        env=pkgbuild_environment(),
    )
    return parse_developer_id_installer_identities(completed.stdout + completed.stderr)


def resolve_sign_identity(sign_identity: str, auto_sign: bool) -> str:
    if sign_identity:
        return sign_identity
    if not auto_sign:
        return ""
    identities = find_developer_id_installer_identities()
    if len(identities) == 1:
        return identities[0]
    if not identities:
        raise RuntimeError(
            "No Developer ID Installer identity was found in the current keychain. "
            "Install an Apple Developer ID Installer certificate or pass --sign-identity explicitly."
        )
    formatted = "\n".join(f"  - {identity}" for identity in identities)
    raise RuntimeError(
        "Multiple Developer ID Installer identities were found. "
        "Pass --sign-identity with one of:\n" + formatted
    )


def strip_pkg_appledouble(pkg_path: Path, output_path: Path | None = None) -> list[str]:
    pkg_path = pkg_path.expanduser().resolve()
    target_path = (output_path or pkg_path).expanduser().resolve()
    removed: list[str] = []
    with tempfile.TemporaryDirectory(prefix="codex-companion-pkg-clean-") as tmp:
        tmp_path = Path(tmp)
        expanded = tmp_path / "expanded"
        cleaned = tmp_path / "cleaned.pkg"
        run_command(["/usr/sbin/pkgutil", "--expand", str(pkg_path), str(expanded)])
        for item in sorted(expanded.rglob("._*")):
            removed.append(str(item.relative_to(expanded)))
            item.unlink()
        run_command(["/usr/sbin/pkgutil", "--flatten", str(expanded), str(cleaned)])
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path == pkg_path:
            shutil.move(str(cleaned), str(pkg_path))
        else:
            shutil.copy2(cleaned, target_path)
    return removed


def build_pkg(
    zip_path: Path,
    output_path: Path,
    version: str,
    sign_identity: str = "",
    auto_sign: bool = False,
    dry_run: bool = False,
    sync_onedrive: bool = True,
    onedrive_dir: Path = ONEDRIVE_DIR,
) -> dict[str, object]:
    zip_path = zip_path.expanduser().resolve()
    output_path = output_path.expanduser().resolve()
    if not zip_path.exists():
        raise FileNotFoundError(f"release zip not found: {zip_path}")
    with tempfile.TemporaryDirectory(prefix="codex-companion-pkg-") as tmp:
        tmp_path = Path(tmp)
        extract_dir = tmp_path / "extract"
        scripts_dir = tmp_path / "scripts"
        extract_dir.mkdir()
        package_root = extract_release_zip(zip_path, extract_dir)
        installer_root = Path("/") / SHARED_INSTALL_PARENT / package_root.name
        postinstall = write_pkg_scripts(scripts_dir, installer_root, zip_path)
        component_pkg = tmp_path / "component.pkg"
        resolved_identity = resolve_sign_identity(sign_identity, auto_sign)
        result: dict[str, object] = {
            "ok": True,
            "zip": str(zip_path),
            "output": str(output_path),
            "packageRoot": package_root.name,
            "installerRoot": str(installer_root),
            "postinstall": postinstall.read_text(encoding="utf-8"),
            "signed": bool(resolved_identity),
            "signIdentity": resolved_identity,
            "dryRun": dry_run,
        }
        if dry_run:
            return result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        run_command(
            [
                "/usr/bin/pkgbuild",
                "--nopayload",
                "--scripts",
                str(scripts_dir),
                "--identifier",
                PACKAGE_IDENTIFIER,
                "--version",
                version,
            ]
            + [str(component_pkg)]
        )
        removed_metadata = strip_pkg_appledouble(component_pkg)
        product_cmd = [
            "/usr/bin/productbuild",
            "--package",
            str(component_pkg),
            "--identifier",
            PACKAGE_IDENTIFIER,
            "--version",
            version,
        ]
        if resolved_identity:
            product_cmd.extend(["--sign", resolved_identity])
        product_cmd.append(str(output_path))
        run_command(product_cmd)
        if not resolved_identity:
            removed_metadata.extend(strip_pkg_appledouble(output_path))
        result["created"] = output_path.exists()
        result["size"] = output_path.stat().st_size if output_path.exists() else 0
        result["removedAppleDouble"] = removed_metadata
        if output_path.exists() and zip_path.exists():
            if sync_onedrive:
                result["releaseSync"] = sync_release_artifacts(zip_path, output_path, onedrive_dir)
            else:
                write_sha256_manifest(release_manifest_paths(zip_path, output_path), output_path.parent / "SHA256SUMS.txt")
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a macOS pkg wrapper for Codex Companion.")
    parser.add_argument("zip", nargs="?", default=str(DEFAULT_ZIP), help="CodexCompanion release zip.")
    parser.add_argument("--output", default="", help="Output .pkg path. Defaults to the matching release latest pkg.")
    parser.add_argument("--version", default="", help="pkg version string. Defaults to the version inferred from the release zip.")
    parser.add_argument("--sign-identity", default="", help="Developer ID Installer identity for productbuild --sign.")
    parser.add_argument("--auto-sign", action="store_true", help="Use the single Developer ID Installer identity found in the current keychain.")
    parser.add_argument("--dry-run", action="store_true", help="Stage payload and scripts without invoking pkgbuild/productbuild.")
    parser.add_argument("--no-sync-onedrive", action="store_true", help="Do not mirror the pkg and SHA256SUMS.txt into the OneDrive release folder.")
    parser.add_argument("--json", action="store_true", help="Print JSON result.")
    args = parser.parse_args()

    try:
        zip_path = Path(args.zip)
        version = args.version or infer_release_version(zip_path)
        output_path = Path(args.output) if args.output else default_output_for_zip(zip_path, version)
        result = build_pkg(
            zip_path,
            output_path,
            version,
            sign_identity=args.sign_identity,
            auto_sign=args.auto_sign,
            dry_run=args.dry_run,
            sync_onedrive=not args.no_sync_onedrive,
        )
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["output"])
        print(f"installerRoot={result['installerRoot']}")
        print(f"signed={result['signed']}")
        print(f"dryRun={result['dryRun']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
