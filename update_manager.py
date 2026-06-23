#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import zipfile
from html import unescape
from pathlib import Path
from typing import Any
from urllib import error, parse, request

from runtime_config import DEFAULT_RUNTIME_SETTINGS, sanitize_github_repo, sanitize_proxy_url


UPDATE_STATUS_RELATIVE = Path("control/update_status.json")
UPDATES_DIR_NAME = "updates"
GITHUB_API = "https://api.github.com/repos/{repo}/releases/latest"
GITHUB_LATEST_PAGE = "https://github.com/{repo}/releases/latest"


def now_text() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def version_key(value: Any) -> tuple[int, ...]:
    text = str(value or "").strip().lstrip("vV")
    parts = [int(item) for item in re.findall(r"\d+", text)]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:6])


def compare_versions(left: Any, right: Any) -> int:
    left_key = version_key(left)
    right_key = version_key(right)
    if left_key > right_key:
        return 1
    if left_key < right_key:
        return -1
    return 0


def clean_version(value: Any) -> str:
    text = str(value or "").strip()
    if text.startswith(("v", "V")):
        text = text[1:]
    match = re.search(r"\d+(?:\.\d+){0,5}", text)
    return match.group(0) if match else text


def write_update_status(root: Path, data: dict[str, Any]) -> dict[str, Any]:
    status = dict(data)
    status.setdefault("updatedAt", now_text())
    target = root / UPDATE_STATUS_RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return status


def read_update_status(root: Path) -> dict[str, Any]:
    target = root / UPDATE_STATUS_RELATIVE
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    return {
        "ok": bool(data.get("ok", False)),
        "state": str(data.get("state") or "unknown"),
        "repo": sanitize_github_repo(data.get("repo")),
        "currentVersion": str(data.get("currentVersion") or ""),
        "latestVersion": str(data.get("latestVersion") or ""),
        "available": bool(data.get("available", False)),
        "assetName": str(data.get("assetName") or ""),
        "downloadUrl": str(data.get("downloadUrl") or ""),
        "releaseUrl": str(data.get("releaseUrl") or ""),
        "message": str(data.get("message") or "尚未检查更新。"),
        "updatedAt": str(data.get("updatedAt") or ""),
        "archivePath": str(data.get("archivePath") or ""),
        "installLog": str(data.get("installLog") or ""),
    }


def select_release_asset(assets: Any, latest_version: str) -> dict[str, Any] | None:
    if not isinstance(assets, list):
        return None
    candidates: list[dict[str, Any]] = []
    for item in assets:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        url = str(item.get("browser_download_url") or "")
        if not name.lower().endswith(".zip") or not url:
            continue
        candidates.append(item)
    if not candidates:
        return None

    def score(item: dict[str, Any]) -> tuple[int, str]:
        name = str(item.get("name") or "")
        lower = name.lower()
        points = 0
        if "codexcompanion" in lower:
            points += 10
        if latest_version and latest_version in name:
            points += 8
        if "latest" in lower:
            points += 4
        if lower.endswith("-dist.zip") or "-dist" in lower:
            points += 3
        return (points, name)

    return sorted(candidates, key=score, reverse=True)[0]


def parse_latest_release(release: dict[str, Any], current_version: str, repo: str) -> dict[str, Any]:
    tag = str(release.get("tag_name") or release.get("name") or "").strip()
    latest_version = clean_version(tag)
    asset = select_release_asset(release.get("assets"), latest_version)
    if not latest_version:
        return {
            "ok": False,
            "state": "error",
            "available": False,
            "repo": repo,
            "currentVersion": current_version,
            "latestVersion": "",
            "message": "GitHub release 缺少版本号。",
        }
    if not asset:
        return {
            "ok": False,
            "state": "error",
            "available": False,
            "repo": repo,
            "currentVersion": current_version,
            "latestVersion": latest_version,
            "message": "GitHub latest release 没有可安装的 release zip。",
            "releaseUrl": str(release.get("html_url") or ""),
        }
    available = compare_versions(latest_version, current_version) > 0
    return {
        "ok": True,
        "state": "available" if available else "current",
        "available": available,
        "repo": repo,
        "currentVersion": current_version,
        "latestVersion": latest_version,
        "assetName": str(asset.get("name") or ""),
        "downloadUrl": str(asset.get("browser_download_url") or ""),
        "releaseUrl": str(release.get("html_url") or ""),
        "releaseNotes": str(release.get("body") or "")[:2000],
        "assetSize": int(asset.get("size") or 0),
        "message": f"发现新版本 {latest_version}。" if available else f"当前已是最新版本 {current_version}。",
    }


def absolute_github_url(repo: str, href: str) -> str:
    href = unescape(str(href or "").strip())
    if href.startswith(("https://", "http://")):
        return href
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return "https://github.com" + href
    return parse.urljoin(f"https://github.com/{repo}/releases/", href)


def parse_public_release_html(html_text: str, final_url: str, repo: str) -> dict[str, Any]:
    tag = ""
    tag_match = re.search(r"/releases/tag/([^/?#]+)", final_url)
    if tag_match:
        tag = parse.unquote(tag_match.group(1))
    assets: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for match in re.finditer(r"""href\s*=\s*(['"])(.*?)\1""", html_text, flags=re.IGNORECASE | re.DOTALL):
        href = unescape(match.group(2))
        if "/releases/download/" not in href:
            continue
        asset_url = absolute_github_url(repo, href)
        parsed = parse.urlparse(asset_url)
        if not parsed.path.lower().endswith(".zip"):
            continue
        if asset_url in seen_urls:
            continue
        seen_urls.add(asset_url)
        if not tag:
            download_tag = re.search(r"/releases/download/([^/]+)/", parsed.path)
            if download_tag:
                tag = parse.unquote(download_tag.group(1))
        assets.append(
            {
                "name": Path(parse.unquote(parsed.path)).name,
                "browser_download_url": asset_url,
                "size": 0,
            }
        )
    release_url = f"https://github.com/{repo}/releases/tag/{parse.quote(tag, safe='')}" if tag else final_url
    return {
        "tag_name": tag,
        "html_url": release_url,
        "assets": assets,
        "body": "",
    }


def urlopen_with_proxy(req: request.Request, settings: dict[str, Any], timeout: float):
    proxy_url = sanitize_proxy_url(settings.get("proxyUrl", ""))
    if not proxy_url:
        return request.urlopen(req, timeout=timeout)
    opener = request.build_opener(request.ProxyHandler({"http": proxy_url, "https": proxy_url}))
    return opener.open(req, timeout=timeout)


def fetch_latest_release_from_public_page(settings: dict[str, Any], repo: str) -> dict[str, Any]:
    page_url = GITHUB_LATEST_PAGE.format(repo=repo)
    req = request.Request(
        page_url,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": "CodexCompanionUpdater/1.0",
        },
        method="GET",
    )
    with urlopen_with_proxy(req, settings, timeout=20) as resp:
        raw = resp.read()
        final_url = getattr(resp, "geturl", lambda: page_url)()
    html_text = raw.decode("utf-8", errors="replace")
    release = parse_public_release_html(html_text, str(final_url or page_url), repo)
    tag = str(release.get("tag_name") or "")
    if tag and not release.get("assets"):
        assets_url = f"https://github.com/{repo}/releases/expanded_assets/{parse.quote(tag, safe='')}"
        assets_req = request.Request(
            assets_url,
            headers={
                "Accept": "text/html,*/*",
                "User-Agent": "CodexCompanionUpdater/1.0",
            },
            method="GET",
        )
        with urlopen_with_proxy(assets_req, settings, timeout=20) as assets_resp:
            assets_raw = assets_resp.read()
        expanded_release = parse_public_release_html(
            assets_raw.decode("utf-8", errors="replace"),
            str(release.get("html_url") or final_url or page_url),
            repo,
        )
        if expanded_release.get("assets"):
            release["assets"] = expanded_release["assets"]
    if not release.get("tag_name"):
        raise ValueError("GitHub release 页面缺少版本号。")
    if not release.get("assets"):
        raise ValueError("GitHub release 页面没有找到可安装 zip。")
    return release


def fetch_latest_release_from_api(settings: dict[str, Any], repo: str) -> dict[str, Any]:
    api_url = GITHUB_API.format(repo=repo)
    req = request.Request(
        api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "CodexCompanionUpdater/1.0",
        },
        method="GET",
    )
    with urlopen_with_proxy(req, settings, timeout=20) as resp:
        release = json.loads(resp.read().decode("utf-8"))
    if not isinstance(release, dict):
        raise ValueError("GitHub 返回不是 release 对象。")
    return release


def check_for_update(root: Path, settings: dict[str, Any], current_version: str) -> dict[str, Any]:
    repo = sanitize_github_repo(settings.get("githubRepo"))
    try:
        release = fetch_latest_release_from_public_page(settings, repo)
    except Exception as exc:
        page_error = str(exc)
        try:
            release = fetch_latest_release_from_api(settings, repo)
        except error.HTTPError as api_exc:
            detail = api_exc.read().decode("utf-8", errors="replace")[:500]
            result = {
                "ok": False,
                "state": "error",
                "available": False,
                "repo": repo,
                "currentVersion": current_version,
                "message": f"检查更新失败：公开 release 页面不可用（{page_error}）；GitHub API HTTP {api_exc.code}。{detail}",
            }
            return write_update_status(root, result)
        except Exception as api_exc:
            result = {
                "ok": False,
                "state": "error",
                "available": False,
                "repo": repo,
                "currentVersion": current_version,
                "message": f"检查更新失败：公开 release 页面不可用（{page_error}）；GitHub API 也不可用（{api_exc}）。",
            }
            return write_update_status(root, result)
    return write_update_status(root, parse_latest_release(release, current_version, repo))


def safe_zip_members(archive: zipfile.ZipFile) -> list[str]:
    names = archive.namelist()
    for name in names:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe zip member: {name}")
    return names


def validate_release_zip(archive_path: Path) -> dict[str, Any]:
    archive_path = Path(archive_path).expanduser()
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            names = safe_zip_members(archive)
            top_levels = sorted({Path(name).parts[0] for name in names if Path(name).parts})
            if len(top_levels) != 1:
                return {"ok": False, "message": "release zip 必须只有一个顶层目录。"}
            package_root_name = top_levels[0]
            required = {
                f"{package_root_name}/install.sh",
                f"{package_root_name}/companion/companion.py",
                f"{package_root_name}/extension/codex.mn.assistant/mnaddon.json",
            }
            missing = sorted(required - set(names))
            if missing:
                return {"ok": False, "message": "release zip 缺少安装文件：" + ", ".join(missing)}
            target_root = archive_path.parent / package_root_name
            if target_root.exists():
                shutil.rmtree(target_root)
            archive.extractall(archive_path.parent)
    except Exception as exc:
        return {"ok": False, "message": f"release zip 校验失败：{exc}"}
    install_script = archive_path.parent / package_root_name / "install.sh"
    return {
        "ok": True,
        "message": "release zip 结构有效。",
        "packageRoot": package_root_name,
        "packageRootPath": str(archive_path.parent / package_root_name),
        "installScript": str(install_script),
    }


def download_asset(root: Path, settings: dict[str, Any], update: dict[str, Any]) -> Path:
    url = str(update.get("downloadUrl") or "")
    name = str(update.get("assetName") or "CodexCompanion-latest-dist.zip")
    if not url:
        raise ValueError("更新缺少下载地址。")
    target_dir = root / UPDATES_DIR_NAME
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / re.sub(r"[^A-Za-z0-9._-]+", "-", name)
    if url.startswith("file://"):
        shutil.copy2(Path(url[7:]).expanduser(), target)
        return target
    req = request.Request(url, headers={"User-Agent": "CodexCompanionUpdater/1.0"}, method="GET")
    with urlopen_with_proxy(req, settings, timeout=120) as resp, target.open("wb") as handle:
        shutil.copyfileobj(resp, handle)
    return target


def install_update(root: Path, settings: dict[str, Any], current_version: str) -> dict[str, Any]:
    update = check_for_update(root, settings, current_version)
    if not update.get("ok"):
        return update
    if not update.get("available"):
        return update
    write_update_status(root, {**update, "state": "downloading", "message": "正在下载更新包。"})
    try:
        archive_path = download_asset(root, settings, update)
    except Exception as exc:
        return write_update_status(root, {**update, "ok": False, "state": "error", "message": f"下载更新失败：{exc}"})
    validation = validate_release_zip(archive_path)
    if not validation.get("ok"):
        return write_update_status(root, {**update, **validation, "state": "error", "archivePath": str(archive_path)})
    if os.environ.get("CODEX_MN_UPDATE_DRY_RUN") == "1":
        return write_update_status(
            root,
            {
                **update,
                "state": "ready",
                "archivePath": str(archive_path),
                "packageRootPath": validation.get("packageRootPath", ""),
                "message": "更新包已下载并通过校验（dry-run，未安装）。",
            },
        )
    log_path = root / UPDATES_DIR_NAME / "install-latest.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["CODEX_MN_COMPANION_HOME"] = str(root)
    with log_path.open("ab") as log:
        subprocess.Popen(
            ["/bin/zsh", str(validation["installScript"])],
            cwd=str(Path(str(validation["packageRootPath"]))),
            env=env,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
    return write_update_status(
        root,
        {
            **update,
            "state": "installing",
            "archivePath": str(archive_path),
            "packageRootPath": validation.get("packageRootPath", ""),
            "installLog": str(log_path),
            "message": "已开始安装更新。安装完成后请重新打开 Codex 面板，必要时重启 MarginNote 4。",
        },
    )


if __name__ == "__main__":
    home = Path(os.environ.get("CODEX_MN_COMPANION_HOME", Path.home() / ".codex/marginnote-assistant")).expanduser()
    settings = {"githubRepo": DEFAULT_RUNTIME_SETTINGS["githubRepo"], "proxyUrl": ""}
    print(json.dumps(check_for_update(home, settings, "0.0.0"), ensure_ascii=False, indent=2))
