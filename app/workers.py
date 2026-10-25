"""EraPuller — 后台工作线程：仓库信息获取、Git 克隆、ZIP 快速下载"""

import os
import queue
import re
import shutil
import subprocess
import tempfile
import threading
import urllib.request
import zipfile

from PySide6.QtCore import QThread, Signal

from .github import RepoInfo, RepoError, fetch_repo_info

_P_RECV = re.compile(r"Receiving objects:\s*(\d+)%\s*\((\d+)/(\d+)\)")
_P_CHECK = re.compile(r"Checking out files:\s*(\d+)%")
_P_ENUM = re.compile(r"Enumerating objects:\s*(\d+)%")


class RepoInfoWorker(QThread):
    """解析 URL 后异步获取仓库信息（含头像）。"""

    done = Signal(object)
    failed = Signal(str)

    def __init__(self, owner: str, repo: str, parent=None):
        super().__init__(parent)
        self._owner = owner
        self._repo = repo

    def run(self):
        try:
            info = fetch_repo_info(self._owner, self._repo)
            self.done.emit(info)
        except Exception as e:  # noqa: BLE001
            self.failed.emit(str(e))


class PullWorker(QThread):
    """执行拉取：mode="zip" 走 ZIP 快速下载，mode="git" 走 git clone。"""

    progress = Signal(int)      # 0-100
    log = Signal(str)           # HTML 行
    succeeded = Signal(str)     # 目标文件夹
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, mode: str, url: str, dest: str, info: RepoInfo, branch, parent=None):
        super().__init__(parent)
        self._mode = mode
        self._url = url
        self._dest = dest
        self._info = info
        self._branch = branch
        self._cancel = False
        self._last_log_ts = 0.0
        self._log_count = 0

    def cancel(self):
        self._cancel = True

    # ---------------- 主流程 ----------------
    def run(self):
        try:
            if self._mode == "git":
                path = self._run_git()
            else:
                path = self._run_zip()
            if self._cancel:
                self.cancelled.emit()
            else:
                self.succeeded.emit(path)
        except Exception as e:  # noqa: BLE001
            if self._cancel:
                self.cancelled.emit()
            else:
                self.failed.emit(str(e))

    # ---------------- Git 克隆 ----------------
    def _run_git(self) -> str:
        dest = os.path.join(self._dest, self._info.name)
        if os.path.isdir(dest) and os.listdir(dest):
            dest = self._auto_suffix(dest)
        self.log.emit("<span style='color:#98A2C0'>▍执行 git clone --progress …</span>")
        cmd = ["git", "clone", "--progress"]
        if self._branch:
            cmd += ["-b", self._branch]
        cmd += [self._url, dest]

        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            raise RepoError("git_missing")

        q: "queue.Queue[str | None]" = queue.Queue()

        def reader():
            buf = b""
            while True:
                chunk = proc.stderr.read(8192)
                if not chunk:
                    break
                buf += chunk
                while True:
                    m = re.search(rb"[\r\n]", buf)
                    if not m:
                        break
                    line, buf = buf[: m.start()], buf[m.end():]
                    q.put(line.decode("utf-8", "replace"))
            if buf:
                q.put(buf.decode("utf-8", "replace"))
            q.put(None)

        threading.Thread(target=reader, daemon=True).start()
        self.progress.emit(2)

        while True:
            try:
                line = q.get(timeout=0.2)
            except queue.Empty:
                if self._cancel and proc.poll() is None:
                    try:
                        proc.terminate()
                    except Exception:  # noqa: BLE001
                        pass
                continue
            if line is None:
                break
            if self._cancel and proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:  # noqa: BLE001
                    pass
            self._handle_git_line(line)

        code = proc.wait()
        if self._cancel:
            raise RepoError("cancelled")
        if code != 0:
            raise RepoError(f"git clone 失败（退出码 {code}），请检查地址或网络")
        if not os.path.isdir(dest):
            raise RepoError("克隆完成但未找到目标文件夹")
        self.progress.emit(100)
        self.log.emit("<span style='color:#2EE6A8'>✔ 完整克隆完成</span>")
        return dest

    def _handle_git_line(self, line: str):
        line = line.rstrip()
        if not line.strip():
            return
        m = _P_RECV.search(line)
        if m:
            pct = int(m.group(1))
            self.progress.emit(min(94, 2 + int(pct * 0.66)))
            self._log_throttle(f"<span style='color:#7CCBFF'>▍{line}</span>")
            return
        m = _P_CHECK.search(line)
        if m:
            pct = int(m.group(1))
            self.progress.emit(min(99, 66 + int(pct * 0.33)))
            self._log_throttle(f"<span style='color:#7CCBFF'>▍{line}</span>")
            return
        m = _P_ENUM.search(line)
        if m:
            self.progress.emit(min(2, 2))
            return
        if line.startswith("remote:"):
            self._log_throttle(f"<span style='color:#5E6784'>▍{line}</span>")
            return
        if "Cloning into" in line or "克隆到" in line:
            self.log.emit(f"<span style='color:#C9D4F0'>▍{line}</span>")
            return
        self._log_throttle(f"<span style='color:#98A2C0'>▍{line}</span>")

    # ---------------- ZIP 快速下载 ----------------
    def _run_zip(self) -> str:
        branch = self._branch or self._info.default_branch or "main"
        url = (
            f"https://codeload.github.com/{self._info.owner}/"
            f"{self._info.name}/zip/refs/heads/{branch}"
        )
        self.log.emit(
            f"<span style='color:#98A2C0'>▍下载 {self._info.full_name} @ {branch} …</span>"
        )

        tmp_dir = tempfile.mkdtemp(prefix="erapuller_")
        zip_path = os.path.join(tmp_dir, "src.zip")
        req = urllib.request.Request(
            url, headers={"User-Agent": "EraPuller/1.0 (graphical github puller)"}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                ctype = resp.headers.get("Content-Type", "")
                if ctype.startswith("text/html"):
                    raise RepoError(
                        "下载失败：仓库过大或不存在，请改用「完整克隆 (Git)」模式"
                    )
                total = int(resp.headers.get("Content-Length") or 0)
                done = 0
                with open(zip_path, "wb") as f:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
                        done += len(chunk)
                        if self._cancel:
                            raise RepoError("cancelled")
                        if total:
                            self.progress.emit(min(68, 2 + int(done / total * 66)))
        except RepoError:
            raise
        except Exception as e:  # noqa: BLE001
            raise RepoError(f"network_error ({e})")

        self.log.emit("<span style='color:#2EE6A8'>✔ 下载完成，正在解压…</span>")
        try:
            zf = zipfile.ZipFile(zip_path)
            total_sz = sum(i.file_size for i in zf.infolist()) or 1
            done_sz = 0
            root = None
            for name in zf.namelist():
                if self._cancel:
                    zf.close()
                    raise RepoError("cancelled")
                zf.extract(name, tmp_dir)
                done_sz += zf.getinfo(name).file_size
                self.progress.emit(min(97, 68 + int(done_sz / total_sz * 29)))
                if root is None:
                    top = name.split("/", 1)[0]
                    if top:
                        root = os.path.join(tmp_dir, top)
            zf.close()
        except zipfile.BadZipFile:
            raise RepoError("下载的文件不是有效的 ZIP 压缩包，请重试或改用 Git 模式")

        if not root or not os.path.isdir(root):
            raise RepoError("解压失败：未找到项目目录")

        target = os.path.join(self._dest, self._info.name)
        if os.path.exists(target):
            target = self._auto_suffix(target)
            self.log.emit("<span style='color:#FFB84D'>▍目标文件夹已存在，已自动添加序号</span>")
        shutil.move(root, target)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        self.progress.emit(100)
        self.log.emit("<span style='color:#2EE6A8'>✔ 快速下载完成</span>")
        return target

    # ---------------- 工具 ----------------
    def _auto_suffix(self, path: str) -> str:
        i = 2
        while True:
            cand = f"{path} ({i})"
            if not os.path.exists(cand):
                return cand
            i += 1

    def _log_throttle(self, html: str):
        """进度类日志节流，避免刷屏。"""
        self._log_count += 1
        if self._log_count % 6 == 0:
            self.log.emit(html)
