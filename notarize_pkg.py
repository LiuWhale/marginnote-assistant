#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_PKG = ROOT / "release/CodexCompanion-0.4.0-latest.pkg"


def resolve_credentials(
    keychain_profile: str = "",
    apple_id: str = "",
    team_id: str = "",
    password: str = "",
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    env = env if env is not None else os.environ
    profile = (
        keychain_profile
        or env.get("NOTARYTOOL_KEYCHAIN_PROFILE", "")
        or env.get("CODEX_MN_NOTARYTOOL_KEYCHAIN_PROFILE", "")
    ).strip()
    if profile:
        return {"mode": "keychain-profile", "args": ["--keychain-profile", profile]}

    resolved_apple_id = (apple_id or env.get("APPLE_ID", "")).strip()
    resolved_team_id = (team_id or env.get("APPLE_TEAM_ID", "")).strip()
    resolved_password = (password or env.get("APPLE_APP_SPECIFIC_PASSWORD", "")).strip()
    if resolved_apple_id and resolved_team_id and resolved_password:
        return {
            "mode": "apple-id",
            "args": [
                "--apple-id",
                resolved_apple_id,
                "--team-id",
                resolved_team_id,
                "--password",
                resolved_password,
            ],
        }

    raise RuntimeError(
        "Missing notarytool credentials. Provide --keychain-profile, set NOTARYTOOL_KEYCHAIN_PROFILE, "
        "or set APPLE_ID, APPLE_TEAM_ID, and APPLE_APP_SPECIFIC_PASSWORD."
    )


def notarytool_submit_command(pkg_path: Path, credentials: dict[str, Any], wait: bool = True) -> list[str]:
    # Smoke marker: notarytool submit
    command = ["xcrun", "notarytool", "submit", str(pkg_path)]
    command.extend([str(item) for item in credentials.get("args", [])])
    if wait:
        command.append("--wait")
    return command


def stapler_staple_command(pkg_path: Path) -> list[str]:
    return ["xcrun", "stapler", "staple", str(pkg_path)]


def stapler_validate_command(pkg_path: Path) -> list[str]:
    return ["xcrun", "stapler", "validate", str(pkg_path)]


def spctl_assess_command(pkg_path: Path) -> list[str]:
    return ["spctl", "-a", "-vv", "-t", "install", str(pkg_path)]


def run_command(command: list[str], timeout: float = 1800) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-6000:],
        "stderr": completed.stderr[-6000:],
        "ok": completed.returncode == 0,
    }


def notarize_pkg(
    pkg_path: Path,
    credentials: dict[str, Any],
    dry_run: bool = False,
    run_spctl: bool = True,
) -> dict[str, Any]:
    pkg_path = pkg_path.expanduser().resolve()
    if not pkg_path.exists():
        raise FileNotFoundError(f"pkg not found: {pkg_path}")

    submit_command = notarytool_submit_command(pkg_path, credentials)
    staple_command = stapler_staple_command(pkg_path)
    validate_command = stapler_validate_command(pkg_path)
    spctl_command = spctl_assess_command(pkg_path)
    result: dict[str, Any] = {
        "ok": False,
        "pkg": str(pkg_path),
        "dryRun": dry_run,
        "credentialsMode": credentials.get("mode", ""),
        "credentialsWarning": credentials.get("warning", ""),
        "submitCommand": submit_command,
        "stapleCommand": staple_command,
        "validateCommand": validate_command,
        "spctlCommand": spctl_command,
    }
    if dry_run:
        result["ok"] = True
        return result

    submit = run_command(submit_command)
    result["submit"] = submit
    if not submit["ok"]:
        return result

    staple = run_command(staple_command, timeout=300)
    result["staple"] = staple
    if not staple["ok"]:
        return result

    validate = run_command(validate_command, timeout=60)
    result["validate"] = validate
    if run_spctl:
        spctl = run_command(spctl_command, timeout=60)
        result["spctl"] = spctl
    else:
        result["spctl"] = {"ok": True, "skipped": True}

    result["ok"] = bool(result["validate"].get("ok") and result["spctl"].get("ok"))
    return result


def print_text(result: dict[str, Any]) -> None:
    print("pkg:", result.get("pkg"))
    print("credentials:", result.get("credentialsMode"))
    if result.get("dryRun"):
        print("dryRun: true")
        print("submit:", " ".join(result.get("submitCommand", [])))
        print("staple:", " ".join(result.get("stapleCommand", [])))
        print("validate:", " ".join(result.get("validateCommand", [])))
        return
    print("notarization:", "OK" if result.get("ok") else "FAILED")
    for key in ("submit", "staple", "validate", "spctl"):
        item = result.get(key)
        if isinstance(item, dict):
            print(f"{key}: rc={item.get('returncode')}, ok={item.get('ok')}")


def main(argv: list[str] | None = None, env: dict[str, str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Submit, staple, and validate a Codex Companion pkg notarization.")
    parser.add_argument("pkg", nargs="?", default=str(DEFAULT_PKG), help="Signed pkg to notarize.")
    parser.add_argument("--keychain-profile", default="", help="notarytool keychain profile.")
    parser.add_argument("--apple-id", default="", help="Apple ID email for notarytool.")
    parser.add_argument("--team-id", default="", help="Apple Developer Team ID for notarytool.")
    parser.add_argument("--password", default="", help="App-specific password for notarytool.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned commands without contacting Apple.")
    parser.add_argument("--skip-spctl", action="store_true", help="Skip Gatekeeper install assessment after stapling.")
    parser.add_argument("--json", action="store_true", help="Print JSON result.")
    args = parser.parse_args(argv)

    try:
        try:
            credentials = resolve_credentials(
                keychain_profile=args.keychain_profile,
                apple_id=args.apple_id,
                team_id=args.team_id,
                password=args.password,
                env=env,
            )
        except RuntimeError as credential_error:
            if not args.dry_run:
                raise
            credentials = {
                "mode": "dry-run-no-credentials",
                "args": [],
                "warning": str(credential_error),
            }
        result = notarize_pkg(
            Path(args.pkg),
            credentials,
            dry_run=args.dry_run,
            run_spctl=not args.skip_spctl,
        )
    except (FileNotFoundError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
