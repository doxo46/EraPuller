"""EraPuller — GitHub 地址解析与仓库信息获取"""

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from urllib.parse import urlparse


class RepoError(Exception):
    """业务层错误，message 直接面向用户展示。"""


@dataclass
class RepoInfo:
    owner: str
    name: str
    full_name: str = ""
    description: str = ""
    stars: int = 0
    forks: int = 0
    language: str = ""
    license_name: str = ""
    default_branch: str = "main"
    avatar_url: str = ""
    avatar_bytes: bytes = field(default=b"", repr=False)
    updated_at: str = ""

    def __post_init__(self):
        if not self.full_name:
            self.full_name = f"{self.owner}/{self.name}"


_OWNER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")
_REPO_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def parse_github_url(raw: str):
    """解析各种形态的 GitHub 地址，返回 (owner, repo, branch) 或 None。

    支持：
      https://github.com/owner/repo
      https://github.com/owner/repo.git
      https://github.com/owner/repo/tree/feature/x
      git@github.com:owner/repo.git
      github.com/owner/repo
      owner/repo
    """
    s = (raw or "").strip()
    if not s:
        return None
    s = s.rstrip("/")
    if s.endswith(".git"):
        s = s[:-4]

    path = None
    if s.startswith("git@"):
        if ":" not in s:
            return None
        host, path = s.split(":", 1)
        if "github.com" not in host:
            return None
    elif "://" in s:
        u = urlparse(s)
        if "github.com" not in (u.netloc or ""):
            return None
        path = u.path.lstrip("/")
    else:
        if "/" not in s:
            return None
        path = s  # 允许直接输入 owner/repo

    parts = [p for p in path.split("/") if p]
    if len(parts) < 2:
        return None
    owner, repo = parts[0], parts[1]
    branch = None
    if "tree" in parts[2:]:
        idx = parts.index("tree")
        if idx + 1 < len(parts):
            branch = "/".join(parts[idx + 1:])
    if not _OWNER_RE.match(owner) or not _REPO_RE.match(repo):
        return None
    return owner, repo, branch


def _http_get_json(url: str, timeout: int = 12) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "EraPuller/1.0 (graphical github puller)",
            "Accept": "application/vnd.github+json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RepoError("repo_not_found")
        if e.code in (403, 429):
            raise RepoError("rate_limited")
        raise RepoError(f"network_error ({e.code})")
    except urllib.error.URLError as e:
        raise RepoError(f"network_error ({e.reason})")
    except Exception as e:  # noqa: BLE001
        raise RepoError(f"network_error ({e})")


def fetch_repo_info(owner: str, repo: str) -> RepoInfo:
    data = _http_get_json(f"https://api.github.com/repos/{owner}/{repo}")
    lic = data.get("license") or {}
    info = RepoInfo(
        owner=owner,
        name=repo,
        full_name=data.get("full_name") or f"{owner}/{repo}",
        description=(data.get("description") or "").strip(),
        stars=data.get("stargazers_count") or 0,
        forks=data.get("forks_count") or 0,
        language=data.get("language") or "",
        license_name=lic.get("spdx_id") or "",
        default_branch=data.get("default_branch") or "main",
        avatar_url=(data.get("owner") or {}).get("avatar_url") or "",
        updated_at=data.get("pushed_at") or "",
    )
    if info.avatar_url:
        try:
            req = urllib.request.Request(
                info.avatar_url, headers={"User-Agent": "EraPuller/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                info.avatar_bytes = resp.read()
        except Exception:  # noqa: BLE001
            info.avatar_bytes = b""
    return info
