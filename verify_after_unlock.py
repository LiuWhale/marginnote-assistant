#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


HOME = Path.home()
ROOT = Path(os.environ.get("CODEX_MN_COMPANION_HOME", HOME / ".codex/marginnote-assistant")).expanduser()
EXT_DIR = HOME / "Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant"
DB_PATH = HOME / "Library/Containers/QReader.MarginStudy.easy/Data/Library/Private Documents/MN4NotebookDatabase/0/MarginNotes.sqlite"
EVENTS_PATH = ROOT / "events.jsonl"
QUEUE_DIR = ROOT / "queue"
COMPANION = "http://127.0.0.1:48761"


def shell(args: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, capture_output=True)


def is_screen_locked() -> bool:
    proc = shell(["ioreg", "-n", "Root", "-d1"])
    return "CGSSessionScreenIsLocked\"=Yes" in proc.stdout or "CGSSessionScreenIsLocked\" = Yes" in proc.stdout


def plugin_versions() -> tuple[str, str]:
    manifest_version = ""
    try:
        manifest_version = json.loads((EXT_DIR / "mnaddon.json").read_text(encoding="utf-8")).get("version", "")
    except Exception:
        pass
    main_version = ""
    try:
        text = (EXT_DIR / "main.js").read_text(encoding="utf-8")
        match = re.search(r"PluginVersion\s*=\s*'([^']+)'", text)
        main_version = match.group(1) if match else ""
    except Exception:
        pass
    return manifest_version, main_version


def read_defaults(key: str) -> str:
    proc = shell(["/usr/bin/defaults", "read", "QReader.MarginStudy.easy", key])
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip().strip('"')


def current_mn_context() -> tuple[str, str]:
    return read_defaults("mindbooks_lasttopicid"), read_defaults("mindbooks_lastbookmd5")


def http_json(method: str, path: str, payload: dict | None = None, timeout: float = 8) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(COMPANION + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def recent_events(limit: int = 80) -> list[dict]:
    if not EVENTS_PATH.exists():
        return []
    out: list[dict] = []
    for line in EVENTS_PATH.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def count_title(topic_id: str, title: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            """
            select count(*)
              from ZBOOKNOTE
             where ZTOPICID=?
               and ZNOTETITLE like ?
            """,
            (topic_id, f"{title}%"),
        ).fetchone()
        return int(row[0])
    finally:
        conn.close()


def queue_files() -> list[str]:
    if not QUEUE_DIR.exists():
        return []
    return sorted(path.name for path in QUEUE_DIR.glob("*.jsonl"))


def main() -> int:
    manifest_version, main_version = plugin_versions()
    print(f"plugin manifest version: {manifest_version or 'unknown'}")
    print(f"plugin main.js version:  {main_version or 'unknown'}")

    try:
        health = http_json("GET", "/health")
        print(f"companion health:        {health.get('ok')} - {health.get('message')}")
    except Exception as exc:
        print(f"companion health:        FAILED - {exc}")
        return 2

    locked = is_screen_locked()
    print(f"screen locked:           {locked}")
    if locked:
        print("解锁 Mac 后打开任意带 PDF 的 MarginNote notebook，再重新运行本脚本。")
        return 3

    topic_id, book_md5 = current_mn_context()
    if not topic_id or not book_md5:
        print("没有读取到当前 MarginNote topic/book。请先在 MN4 中打开一个带 PDF 的 notebook。")
        return 3

    shell(["open", f"marginnote4app://notebook/{topic_id}"])
    time.sleep(8)
    latest = recent_events(20)
    latest_version = latest[-1].get("pluginVersion") if latest else ""
    latest_event = latest[-1].get("event") if latest else ""
    print(f"latest plugin event:     {latest_event or 'none'} / {latest_version or 'unknown'}")
    if latest_version != main_version:
        print("当前 MN4 还没有加载最新插件。请退出并重开 MN4 后再运行。")
        return 4

    title = f"Codex Assistant 验证卡片 {time.strftime('%Y%m%d-%H%M%S')}"
    body = (
        "## Codex Assistant 验证\n\n"
        "如果你在 MarginNote 脑图中看到这张卡片，说明 Companion -> MN4 插件 -> "
        "MN 原生卡片创建链路已经跑通。"
    )
    payload = {
        "topicid": topic_id,
        "bookmd5": book_md5,
        "command": {
            "ok": True,
            "message": "Codex Assistant 验证卡片已推送。",
            "reply": "这是解锁后验收脚本生成的唯一标题诊断卡片。",
            "cards": [{"title": title, "body": body}],
        },
    }
    result = http_json("POST", "/marginnote/enqueue", payload)
    print(f"enqueue:                 {result.get('ok')} - {title}")
    print(f"queue files before wait: {', '.join(queue_files()) or 'none'}")

    deadline = time.time() + 30
    seen = 0
    while time.time() < deadline:
        time.sleep(2)
        seen = count_title(topic_id, title)
        if seen:
            break

    events = recent_events(60)
    names = [event.get("event") for event in events]
    print(f"created card count:      {seen}")
    print(f"queue files after wait:  {', '.join(queue_files()) or 'none'}")
    print(
        "event evidence:          "
        + ", ".join(name for name in ["pollCallback", "commandsReceived", "handleResponse", "createCardsFinished", "commandsAcked"] if name in names)
    )
    return 0 if seen else 5


if __name__ == "__main__":
    sys.exit(main())
