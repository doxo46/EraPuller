"""EraPuller — 程序入口"""

import os
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from app import __version__
from app.icons import app_logo
from app.main_window import MainWindow
from app.theme import QFONT_NAME, build_qss


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("EraPuller")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("EraPuller")
    app.setStyle("Fusion")
    app.setFont(QFont(QFONT_NAME, 10))
    app.setStyleSheet(build_qss())
    app.setWindowIcon(app_logo())

    win = MainWindow()
    win.show()

    # 开发/CI 辅助：环境变量触发截图与演示数据（对普通用户不可见）
    demo_url = os.environ.get("ERAPULLER_DEMO_URL")
    if demo_url:
        win._url_input.setText(demo_url)
        win._on_parse()
    demo_pull = os.environ.get("ERAPULLER_DEMO_PULL")
    if demo_pull:
        import tempfile

        win._seg.set_current(0)
        win._path_input.setText(os.path.join(tempfile.gettempdir(), "erapuller_demo"))

        def _try_pull():
            if win._repo_info is None:
                QTimer.singleShot(600, _try_pull)
                return
            win._on_pull()

        QTimer.singleShot(600, _try_pull)
    shot = os.environ.get("ERAPULLER_SHOT")
    if shot:
        def _do_shot():
            win.grab().save(shot)
            app.quit()
        QTimer.singleShot(4500, _do_shot)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
