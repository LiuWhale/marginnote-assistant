#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import error, request
from urllib.parse import quote


DEFAULT_URL = "http://127.0.0.1:48761"
ROOT = Path(__file__).resolve().parent
DEFAULT_NEXT_STEP_EN = "reopen the Codex panel or restart MarginNote 4, then click Refresh MN capability."
DEFAULT_ADDON_ID = "codex.mn.assistant"
CURRENT_PLUGIN_VERSION = "0.4.29"
MN_RUNTIME_EVIDENCE_SCHEMA = "codex-companion-mn-runtime-v1"


def read_default(key: str) -> str:
    try:
        result = subprocess.run(
            ["/usr/bin/defaults", "read", "QReader.MarginStudy.easy", key],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip().strip('"')


def companion_url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + path


def addon_reload_urls(addon_id: str) -> list[str]:
    encoded = quote(str(addon_id or DEFAULT_ADDON_ID).strip() or DEFAULT_ADDON_ID, safe="._-")
    candidates = [
        f"marginnote4app://addon/{encoded}/enable",
        f"marginnote4app://addon/{encoded}/load",
        f"marginnote4app://addon/{encoded}/reload",
        f"marginnote4app://addon/{encoded}/open",
        f"marginnote4app://addon/{encoded}?enable=1",
        f"marginnote4app://addon/{encoded}?action=load",
        f"marginnote4app://addon/{encoded}?action=reload",
    ]
    return list(dict.fromkeys(candidates))


def open_addon_reload_url(url: str) -> dict[str, Any]:
    result = subprocess.run(
        ["/usr/bin/open", url],
        check=False,
        capture_output=True,
        text=True,
        timeout=8,
    )
    return {
        "returncode": result.returncode,
        "stdout": (result.stdout or "")[-1000:],
        "stderr": (result.stderr or "")[-1000:],
    }


def try_addon_url_reload(
    addon_id: str,
    *,
    open_url=open_addon_reload_url,
    pause=time.sleep,
    interval: float = 1.0,
) -> list[dict[str, Any]]:
    attempts: list[dict[str, Any]] = []
    for url in addon_reload_urls(addon_id):
        try:
            result = open_url(url)
        except Exception as exc:
            result = {"returncode": None, "stdout": "", "stderr": str(exc)}
        returncode = result.get("returncode")
        attempts.append(
            {
                "method": "open-url",
                "url": url,
                "ok": returncode == 0,
                "returncode": returncode,
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
            }
        )
        pause(interval)
    return attempts


def get_json(base_url: str, path: str, timeout: int = 10) -> dict[str, Any]:
    req = request.Request(
        companion_url(base_url, path),
        headers={"Accept": "application/json"},
        method="GET",
    )
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(base_url: str, path: str, payload: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        companion_url(base_url, path),
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def status_or_error(base_url: str) -> dict[str, Any]:
    try:
        return get_json(base_url, "/status")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"ok": False, "error": f"HTTP {exc.code}: {body[:1000]}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def find_doctor_script() -> Path | None:
    candidates = [
        ROOT / "doctor.py",
        ROOT / "companion/doctor.py",
        Path.home() / ".codex/marginnote-assistant/doctor.py",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def run_doctor(timeout: int = 30) -> dict[str, Any]:
    script = find_doctor_script()
    if script is None:
        return {
            "doctorFound": False,
            "doctorReturnCode": None,
            "doctorStdout": "",
            "doctorStderr": "doctor.py not found",
        }
    result = subprocess.run(
        ["/usr/bin/python3", str(script)],
        cwd=str(script.parent),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return {
        "doctorFound": True,
        "doctorPath": str(script),
        "doctorReturnCode": result.returncode,
        "doctorStdout": result.stdout[-12000:],
        "doctorStderr": result.stderr[-4000:],
    }


def latest_native_event_ts(status: dict[str, Any]) -> str:
    runtime = status.get("mnRuntime") if isinstance(status.get("mnRuntime"), dict) else {}
    native_ts = str(runtime.get("latestNativeEventTs") or "")
    if native_ts:
        return native_ts
    caps = status.get("nativeApiCapabilities") if isinstance(status.get("nativeApiCapabilities"), dict) else {}
    return str(caps.get("event_ts") or "")


def latest_web_event_ts(status: dict[str, Any]) -> str:
    runtime = status.get("mnRuntime") if isinstance(status.get("mnRuntime"), dict) else {}
    return str(runtime.get("latestWebEventTs") or "")


def wait_for_runtime_refresh(
    base_url: str,
    previous_native_ts: str,
    timeout: int,
    interval: float,
    previous_web_ts: str = "",
) -> dict[str, Any]:
    deadline = time.time() + timeout
    last_status: dict[str, Any] = {}
    while time.time() < deadline:
        last_status = status_or_error(base_url)
        runtime = last_status.get("mnRuntime") if isinstance(last_status.get("mnRuntime"), dict) else {}
        if bool(runtime.get("ready")):
            return last_status
        current_native_ts = latest_native_event_ts(last_status)
        current_web_ts = latest_web_event_ts(last_status)
        if current_native_ts and current_native_ts != previous_native_ts:
            return last_status
        if current_web_ts and current_web_ts != previous_web_ts:
            return last_status
        time.sleep(interval)
    return last_status or status_or_error(base_url)


def collect_queued_command_ids(results: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    for result in results:
        if not isinstance(result, dict) or not result.get("ok"):
            continue
        queued = result.get("queued") if isinstance(result.get("queued"), dict) else {}
        command_id = str(queued.get("id") or "").strip()
        if command_id and command_id not in ids:
            ids.append(command_id)
    return ids


def cleanup_unprocessed_native_commands(
    base_url: str,
    topic_id: str,
    book_md5: str,
    command_ids: list[str],
    *,
    post=post_json,
) -> dict[str, Any]:
    ids = [str(command_id).strip() for command_id in command_ids if str(command_id).strip()]
    if not ids:
        return {"ok": True, "skipped": True, "reason": "no queued command ids"}
    if not topic_id:
        return {"ok": False, "skipped": True, "reason": "missing topicid", "ids": ids}
    payload = {
        "topicid": topic_id,
        "notebookid": topic_id,
        "bookmd5": book_md5,
        "docmd5": book_md5,
        "ids": ids,
        "source": "refresh_mn_runtime.py",
    }
    try:
        result = post(base_url, "/marginnote/ack", payload)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "payload": payload}
    if isinstance(result, dict):
        return result
    return {"ok": False, "error": "invalid ack response", "response": result}


def write_evidence(payload: dict[str, Any], output: Path | None) -> Path:
    target = output
    if target is None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = Path.home() / "Desktop" / f"CodexCompanion-MNRuntimeEvidence-{stamp}.json"
    target = target.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh MarginNote runtime capability reporting and collect Codex Companion evidence."
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="Companion base URL.")
    parser.add_argument("--topicid", default="", help="MarginNote notebook/topic id.")
    parser.add_argument("--bookmd5", default="", help="MarginNote document md5.")
    parser.add_argument("--timeout", type=int, default=45, help="Seconds to wait for a refreshed MN runtime event.")
    parser.add_argument("--interval", type=float, default=2.0, help="Polling interval while waiting for runtime evidence.")
    parser.add_argument("--output", default="", help="Evidence JSON path. Defaults to Desktop.")
    parser.add_argument("--try-addon-url-reload", action="store_true", help="Try non-destructive marginnote4app://addon reload URLs before probing.")
    parser.add_argument("--addon-id", default=DEFAULT_ADDON_ID, help="MarginNote addon id used by --try-addon-url-reload.")
    parser.add_argument(
        "--leave-queued-commands",
        action="store_true",
        help="Do not ack diagnostic native commands created by this script when MN4 does not consume them before timeout.",
    )
    args = parser.parse_args()

    topic_id = args.topicid or read_default("mindbooks_lasttopicid")
    book_md5 = args.bookmd5 or read_default("mindbooks_lastbookmd5")

    status_before = status_or_error(args.url)
    if not status_before.get("ok"):
        payload = {
            "schema": MN_RUNTIME_EVIDENCE_SCHEMA,
            "generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
            "pluginVersion": CURRENT_PLUGIN_VERSION,
            "ok": False,
            "message": "Codex Companion 未运行或 /status 不可用。",
            "error": status_before.get("error", ""),
            "nextStep": "启动本地 Companion 服务后重试；如果 MN4 面板已打开，先关闭并重新打开面板。",
            "nextStepEnglish": DEFAULT_NEXT_STEP_EN,
            "statusBefore": status_before,
        }
        evidence_path = write_evidence(payload, Path(args.output) if args.output else None)
        print("Codex Companion status unavailable.")
        print(f"Evidence: {evidence_path}")
        return 1

    previous_native_ts = latest_native_event_ts(status_before)
    previous_web_ts = latest_web_event_ts(status_before)
    addon_reload_attempts: list[dict[str, Any]] = []
    if args.try_addon_url_reload:
        addon_reload_attempts = try_addon_url_reload(
            args.addon_id,
            interval=min(max(args.interval, 0.2), 2.0),
        )

    web_reload_payload = {
        "action": "request_web_panel_reload",
        "topicid": topic_id,
        "notebookid": topic_id,
        "bookmd5": book_md5,
        "docmd5": book_md5,
        "source": "refresh_mn_runtime.py",
    }
    if topic_id:
        try:
            web_panel_reload_result = post_json(args.url, "/marginnote/action", web_reload_payload)
        except Exception as exc:
            web_panel_reload_result = {"ok": False, "error": str(exc), "payload": web_reload_payload}
    else:
        web_panel_reload_result = {
            "ok": False,
            "message": "缺少 topicid，无法请求 MN4 插件重新加载 Codex 面板。",
            "payload": web_reload_payload,
        }

    probe_payload = {
        "action": "request_native_capability_probe",
        "topicid": topic_id,
        "notebookid": topic_id,
        "bookmd5": book_md5,
        "docmd5": book_md5,
        "source": "refresh_mn_runtime.py",
    }

    try:
        probe_result = post_json(args.url, "/marginnote/action", probe_payload)
    except Exception as exc:
        probe_result = {"ok": False, "error": str(exc), "payload": probe_payload}

    status_after = wait_for_runtime_refresh(args.url, previous_native_ts, args.timeout, args.interval, previous_web_ts)
    runtime = status_after.get("mnRuntime") if isinstance(status_after.get("mnRuntime"), dict) else {}
    native_caps = status_after.get("nativeApiCapabilities") if isinstance(status_after.get("nativeApiCapabilities"), dict) else {}
    doctor_result = run_doctor()

    ready = bool(runtime.get("ready"))
    queued_command_ids = collect_queued_command_ids([web_panel_reload_result, probe_result])
    cleanup_result: dict[str, Any] = {"ok": True, "skipped": True, "reason": "runtime ready or cleanup disabled"}
    if not ready and not args.leave_queued_commands:
        cleanup_result = cleanup_unprocessed_native_commands(args.url, topic_id, book_md5, queued_command_ids)
    payload = {
        "schema": MN_RUNTIME_EVIDENCE_SCHEMA,
        "generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "pluginVersion": str(runtime.get("pluginVersion") or native_caps.get("pluginVersion") or CURRENT_PLUGIN_VERSION),
        "ok": ready,
        "message": "MN4 runtime is ready." if ready else "MN4 runtime evidence collected, but runtime is not fully ready.",
        "nextStep": runtime.get("nextStep") or "重新打开 Codex 面板；如果仍旧，重启 MarginNote 4 后再点“刷新MN能力”。",
        "nextStepEnglish": DEFAULT_NEXT_STEP_EN,
        "topicid": topic_id,
        "bookmd5": book_md5,
        "statusBefore": status_before,
        "addonReloadAttempts": addon_reload_attempts,
        "webPanelReloadResult": web_panel_reload_result,
        "probeResult": probe_result,
        "cleanupQueuedCommandIds": queued_command_ids,
        "cleanupResult": cleanup_result,
        "statusAfter": status_after,
        "mnRuntime": runtime,
        "nativeApiCapabilities": native_caps,
        "doctor": doctor_result,
    }
    evidence_path = write_evidence(payload, Path(args.output) if args.output else None)

    print(payload["message"])
    print(f"mnRuntime.ready={ready}")
    print(f"nativeApiCapabilities.available={bool(native_caps.get('available'))}")
    print(f"doctorReturnCode={doctor_result.get('doctorReturnCode')}")
    print(f"Evidence: {evidence_path}")
    if not ready:
        print(f"Next step: {payload['nextStep']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
