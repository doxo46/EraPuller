"""E2E 功能验证：真实解析 + ZIP 下载 + Git 克隆"""

import os
import sys
import time
import traceback

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_e2e_log.txt")


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


with open(LOG, "w", encoding="utf-8") as f:
    f.write("start e2e\n")

try:
    from PySide6.QtWidgets import QApplication

    app = QApplication([])
    app.setStyle("Fusion")
    from app.main_window import MainWindow

    win = MainWindow()
    win.show()
    app.processEvents()

    # 1) 解析真实仓库
    win._url_input.setText("https://github.com/octocat/Hello-World")
    win._on_parse()
    deadline = time.time() + 40
    while time.time() < deadline:
        app.processEvents()
        if win._repo_info is not None:
            break
        time.sleep(0.05)
    log("info: " + (win._repo_info.full_name if win._repo_info else "FAILED"))
    assert win._repo_info, "repo info not fetched"

    # 2) ZIP 模式拉取
    zip_dest = os.path.join(os.environ.get("TEMP", "."), "erapuller_e2e_zip")
    win._seg.set_current(0)
    win._path_input.setText(zip_dest)

    win._on_pull()
    deadline = time.time() + 90
    while time.time() < deadline:
        app.processEvents()
        if win._pull_worker is None or not win._pull_worker.isRunning():
            break
        time.sleep(0.05)
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()
    log("zip target: " + str(win._target_path))
    log("zip toast: " + win._toast.text())
    log("zip log: " + win._log.toPlainText()[-400:].replace("\n", " | "))
    target = win._target_path
    if target and os.path.isdir(target):
        log("zip files: " + str(sorted(os.listdir(target))[:8]))
        assert os.path.exists(os.path.join(target, "README"))
    else:
        raise AssertionError("zip pull failed")

    # 3) Git 模式拉取
    git_dest = os.path.join(os.environ.get("TEMP", "."), "erapuller_e2e_git")
    win._seg.set_current(1)
    win._path_input.setText(git_dest)
    win._on_pull()
    deadline = time.time() + 90
    while time.time() < deadline:
        app.processEvents()
        if win._pull_worker is None or not win._pull_worker.isRunning():
            break
        time.sleep(0.05)
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()
    gtarget = win._target_path
    log("git target: " + str(gtarget))
    log("git toast: " + win._toast.text())
    log("git log: " + win._log.toPlainText()[-400:].replace("\n", " | "))
    if gtarget and os.path.isdir(os.path.join(gtarget, ".git")):
        log("git ok: .git exists")
    else:
        raise AssertionError("git pull failed")

    log("E2E PASS")
except Exception:
    log("EXC: " + traceback.format_exc())
