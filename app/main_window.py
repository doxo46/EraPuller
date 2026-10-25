"""EraPuller — 主窗口：无边框 + 玻璃卡片 + 语言切换 + 拉取状态机"""

import os

from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, QRect, QSettings, Qt, QUrl
from PySide6.QtGui import QAction, QColor, QDesktopServices, QFont, QFontMetrics, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from . import icons
from .github import RepoInfo, parse_github_url
from .i18n import LANGUAGES, lang_label, tr
from .theme import (
    BG_BOTTOM,
    BG_MID,
    BG_TOP,
    CARD_BORDER,
    COLOR_ERROR,
    COLOR_LINK,
    COLOR_SUCCESS,
    COLOR_WARNING,
    QFONT_NAME,
    TEXT_DIM,
    TEXT_MAIN,
    TEXT_SUB,
)
from .widgets import (
    BgGlow,
    CaptionButton,
    GradientButton,
    GradientTitle,
    HoverButton,
    LogView,
    ModernProgressBar,
    SegmentedControl,
    Toast,
    _font,
)
from .workers import PullWorker, RepoInfoWorker

DEFAULT_SAVE_DIR = os.path.join(os.path.expanduser("~"), "Downloads")


def _fmt_count(n: int) -> str:
    if n >= 1000000:
        return f"{n / 1000000:.1f}m"
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(n)


def _make_card() -> QFrame:
    card = QFrame()
    card.setObjectName("Card")
    card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    lay = QVBoxLayout(card)
    lay.setContentsMargins(20, 18, 20, 18)
    lay.setSpacing(12)
    return card


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._settings = QSettings("EraPuller", "EraPuller")
        self._lang = os.environ.get("ERAPULLER_LANG") or self._settings.value("lang", "zh_CN")
        if self._lang not in LANGUAGES:
            self._lang = "zh_CN"

        self._repo_info: RepoInfo | None = None
        self._parsed = None
        self._info_worker: RepoInfoWorker | None = None
        self._pull_worker: PullWorker | None = None
        self._target_path = ""
        self._maximized = False
        self._resize_state = None

        self.setWindowTitle(tr(self._lang, "app_title"))
        self.setWindowIcon(icons.app_logo())
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumSize(980, 660)

        self._build_ui()
        self._retranslate()
        self._restore_geometry()
        self._fade_in()

    # ================================================== UI 构建
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)

        # 外壳：圆角 + 阴影
        self._shell = QFrame()
        self._shell.setObjectName("Shell")
        self._shell.setStyleSheet(
            f"""
            QFrame#Shell {{
                background: qlineargradient(x1:0, y1:0, x2:0.6, y2:1,
                    stop:0 {BG_TOP}, stop:0.5 {BG_MID}, stop:1 {BG_BOTTOM});
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 18px;
            }}
            """
        )
        self._shadow = QGraphicsDropShadowEffect(self._shell)
        self._shadow.setBlurRadius(48)
        self._shadow.setOffset(0, 10)
        self._shadow.setColor(QColor(0, 0, 0, 190))
        self._shell.setGraphicsEffect(self._shadow)
        root.addWidget(self._shell)

        shell_lay = QVBoxLayout(self._shell)
        shell_lay.setContentsMargins(0, 0, 0, 0)
        shell_lay.setSpacing(0)

        # ---------- 标题栏 ----------
        title_bar = QWidget()
        title_bar.setFixedHeight(48)
        tb = QHBoxLayout(title_bar)
        tb.setContentsMargins(16, 0, 8, 0)
        tb.setSpacing(8)

        logo = QLabel()
        logo.setPixmap(icons.app_logo().pixmap(24, 24))
        tb.addWidget(logo)
        self._tb_title = QLabel()
        self._tb_title.setFont(_font(14, True))
        self._tb_title.setStyleSheet(f"color:{TEXT_MAIN};")
        tb.addWidget(self._tb_title)
        tb.addStretch(1)

        # 语言按钮
        self._lang_btn = HoverButton()
        self._lang_btn.setFixedSize(0, 0)
        self._lang_menu_btn = HoverButton("")
        self._lang_menu_btn.set_icon(icons.globe_icon(), 15)
        self._lang_menu = QMenu(self)
        for code in LANGUAGES:
            act = QAction(LANGUAGES[code]["label"], self._lang_menu)
            act.setCheckable(True)
            act.setChecked(code == self._lang)
            act.triggered.connect(lambda _=False, c=code: self._set_lang(c))
            self._lang_menu.addAction(act)
        self._lang_menu_btn.setMenu(self._lang_menu)
        self._lang_menu_btn.setText(lang_label(self._lang))
        tb.addWidget(self._lang_menu_btn)

        self._btn_min = CaptionButton("min")
        self._btn_max = CaptionButton("max")
        self._btn_close = CaptionButton("close")
        self._btn_min.clicked.connect(self.showMinimized)
        self._btn_max.clicked.connect(self._toggle_max)
        self._btn_close.clicked.connect(self.close)
        tb.addWidget(self._btn_min)
        tb.addWidget(self._btn_max)
        tb.addWidget(self._btn_close)

        shell_lay.addWidget(title_bar)

        # ---------- 内容区（光晕垫底 + 内容叠放） ----------
        content_area = QWidget()
        grid = QGridLayout(content_area)
        grid.setContentsMargins(0, 0, 0, 0)
        self._bg = BgGlow(content_area)
        grid.addWidget(self._bg, 0, 0)
        content = QWidget()
        grid.addWidget(content, 0, 0)
        shell_lay.addWidget(content_area, 1)

        lay = QVBoxLayout(content)
        lay.setContentsMargins(34, 14, 34, 22)
        lay.setSpacing(14)

        # ---------- 标题区 ----------
        self._hero = GradientTitle(tr(self._lang, "app_title"), 30)
        lay.addWidget(self._hero)
        self._tagline = QLabel()
        self._tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._tagline.setStyleSheet(f"color:{TEXT_SUB}; font-size:13px;")
        lay.addWidget(self._tagline)
        lay.addSpacing(2)

        # ---------- URL 卡片 ----------
        self._url_card = _make_card()
        url_row = QHBoxLayout()
        url_row.setContentsMargins(0, 0, 0, 0)
        url_row.setSpacing(10)
        self._url_input = QLineEdit()
        self._url_input.setObjectName("UrlInput")
        self._url_input.setPlaceholderText(tr(self._lang, "url_placeholder"))
        self._url_input.setFixedHeight(46)
        paste_act = self._url_input.addAction(
            icons.clipboard_icon(18), QLineEdit.ActionPosition.TrailingPosition
        )
        paste_act.triggered.connect(self._paste_url)
        paste_act.setToolTip(tr(self._lang, "paste_tip"))
        self._url_input.returnPressed.connect(self._on_parse)
        url_row.addWidget(self._url_input, 1)
        self._parse_btn = HoverButton(tr(self._lang, "parse"))
        self._parse_btn.set_icon(icons.refresh_icon(), 16)
        self._parse_btn.clicked.connect(self._on_parse)
        self._parse_btn.setToolTip(tr(self._lang, "parse_tip"))
        url_row.addWidget(self._parse_btn)
        self._url_card.layout().addLayout(url_row)
        lay.addWidget(self._url_card)

        # ---------- 仓库信息卡片 ----------
        self._repo_card = _make_card()
        repo_row = QHBoxLayout()
        repo_row.setContentsMargins(0, 0, 0, 0)
        repo_row.setSpacing(16)
        self._avatar = QLabel()
        self._avatar.setFixedSize(56, 56)
        self._avatar.setPixmap(self._default_avatar(56))
        repo_row.addWidget(self._avatar, 0, Qt.AlignmentFlag.AlignTop)
        info_col = QVBoxLayout()
        info_col.setSpacing(4)
        name_row = QHBoxLayout()
        name_row.setSpacing(10)
        self._repo_name = QLabel()
        self._repo_name.setFont(_font(17, True))
        self._repo_name.setStyleSheet(f"color:{TEXT_MAIN};")
        name_row.addWidget(self._repo_name)
        self._repo_branch = QLabel()
        self._repo_branch.setStyleSheet(
            f"color:#8BE9FF; background:rgba(0,229,255,0.10); border-radius:8px; padding:2px 9px; font-size:11px;"
        )
        name_row.addWidget(self._repo_branch)
        name_row.addStretch(1)
        info_col.addLayout(name_row)
        self._repo_full = QLabel()
        self._repo_full.setStyleSheet(f"color:{COLOR_LINK.name()}; font-size:12px;")
        self._repo_full.setCursor(Qt.CursorShape.PointingHandCursor)
        self._repo_full.mousePressEvent = lambda e: self._open_github()
        info_col.addWidget(self._repo_full)
        self._repo_desc = QLabel()
        self._repo_desc.setWordWrap(True)
        self._repo_desc.setStyleSheet(f"color:{TEXT_SUB}; font-size:13px;")
        info_col.addWidget(self._repo_desc)
        self._repo_chips = QLabel()
        self._repo_chips.setStyleSheet("font-size:12px;")
        info_col.addWidget(self._repo_chips)
        repo_row.addLayout(info_col, 1)
        self._repo_card.layout().addLayout(repo_row)
        self._repo_card.hide()
        lay.addWidget(self._repo_card)

        # ---------- 选项卡片 ----------
        self._opts_card = _make_card()
        opts = self._opts_card.layout()

        mode_row = QHBoxLayout()
        mode_row.setSpacing(14)
        self._seg = SegmentedControl([tr(self._lang, "mode_zip"), tr(self._lang, "mode_git")])
        self._seg.changed.connect(self._on_mode_changed)
        mode_row.addWidget(self._seg)
        self._mode_desc = QLabel()
        self._mode_desc.setWordWrap(True)
        self._mode_desc.setStyleSheet(f"color:{TEXT_DIM}; font-size:12px;")
        mode_row.addWidget(self._mode_desc, 1)
        opts.addLayout(mode_row)

        save_row = QHBoxLayout()
        save_row.setSpacing(10)
        save_lbl = QLabel()
        save_lbl.setObjectName("SaveLabel")
        save_lbl.setStyleSheet(f"color:{TEXT_SUB}; font-size:13px;")
        self._save_lbl = save_lbl
        save_row.addWidget(save_lbl)
        self._path_input = QLineEdit()
        self._path_input.setObjectName("PathInput")
        self._path_input.setFixedHeight(38)
        self._path_input.setText(self._settings.value("last_dir", DEFAULT_SAVE_DIR))
        save_row.addWidget(self._path_input, 1)
        self._browse_btn = HoverButton()
        self._browse_btn.set_icon(icons.folder_icon(), 15)
        self._browse_btn.setText("…")
        self._browse_btn.setFixedWidth(70)
        self._browse_btn.clicked.connect(self._browse_dir)
        save_row.addWidget(self._browse_btn)
        opts.addLayout(save_row)
        lay.addWidget(self._opts_card)

        # ---------- 主按钮 ----------
        self._pull_btn = GradientButton(tr(self._lang, "pull"))
        self._pull_btn.set_icon(icons.download_icon(20))
        self._pull_btn.clicked.connect(self._on_pull)
        lay.addWidget(self._pull_btn)

        # ---------- 进度卡片 ----------
        self._prog_card = _make_card()
        pc = self._prog_card.layout()
        bar_row = QHBoxLayout()
        bar_row.setSpacing(12)
        self._prog_bar = ModernProgressBar()
        bar_row.addWidget(self._prog_bar, 1)
        self._pct_label = QLabel("0%")
        self._pct_label.setStyleSheet(f"color:{TEXT_SUB}; font-size:12px;")
        self._pct_label.setFixedWidth(44)
        self._pct_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        bar_row.addWidget(self._pct_label)
        pc.addLayout(bar_row)

        status_row = QHBoxLayout()
        status_row.setSpacing(10)
        self._run_status = QLabel()
        self._run_status.setStyleSheet(f"color:{TEXT_SUB}; font-size:12px;")
        status_row.addWidget(self._run_status, 1)
        self._cancel_btn = HoverButton(tr(self._lang, "cancel"))
        self._cancel_btn.clicked.connect(self._on_cancel)
        self._cancel_btn.hide()
        status_row.addWidget(self._cancel_btn)
        self._open_btn = HoverButton()
        self._open_btn.set_icon(icons.open_icon(), 15)
        self._open_btn.setText(tr(self._lang, "open_folder"))
        self._open_btn.clicked.connect(self._open_target)
        self._open_btn.setEnabled(False)
        status_row.addWidget(self._open_btn)
        self._copy_btn = HoverButton()
        self._copy_btn.set_icon(icons.copy_icon(), 15)
        self._copy_btn.setText(tr(self._lang, "copy_path"))
        self._copy_btn.clicked.connect(self._copy_target)
        self._copy_btn.setEnabled(False)
        status_row.addWidget(self._copy_btn)
        pc.addLayout(status_row)

        self._log_toggle = HoverButton(tr(self._lang, "log_hide"))
        self._log_toggle.setFixedHeight(30)
        self._log_toggle.clicked.connect(self._toggle_log)
        self._log_toggle.hide()
        pc.addWidget(self._log_toggle)
        self._log = LogView()
        self._log.setMinimumHeight(110)
        self._log.setMaximumHeight(150)
        pc.addWidget(self._log)
        self._prog_card.hide()
        lay.addWidget(self._prog_card)

        # ---------- 底栏 ----------
        footer = QHBoxLayout()
        footer.setContentsMargins(4, 0, 4, 0)
        self._status_dot = QLabel()
        self._status_dot.setPixmap(icons.dot_pixmap(9, "#2EE6A8"))
        footer.addWidget(self._status_dot)
        self._status_label = QLabel()
        self._status_label.setStyleSheet(f"color:{TEXT_DIM}; font-size:12px;")
        footer.addWidget(self._status_label)
        footer.addStretch(1)
        self._footer_hint = QLabel()
        self._footer_hint.setStyleSheet(f"color:{TEXT_DIM}; font-size:12px;")
        footer.addWidget(self._footer_hint)
        lay.addLayout(footer)

        # 标题栏拖拽
        title_bar.mousePressEvent = self._tb_press
        title_bar.mouseMoveEvent = self._tb_move
        title_bar.mouseReleaseEvent = self._tb_release
        title_bar.mouseDoubleClickEvent = lambda e: self._toggle_max()

        self._toast = Toast(self)

    # ================================================== 语言
    def _set_lang(self, code: str):
        if code == self._lang:
            return
        self._lang = code
        self._settings.setValue("lang", code)
        for act in self._lang_menu.actions():
            act.setChecked(act.text() == LANGUAGES[code]["label"])
        self._lang_menu_btn.setText(lang_label(code))
        self._retranslate()

    def _retranslate(self):
        t = lambda k: tr(self._lang, k)
        title = t("app_title")
        self.setWindowTitle(title)
        self._tb_title.setText(title)
        self._hero.setText(title)
        self._tagline.setText(t("tagline"))
        self._url_input.setPlaceholderText(t("url_placeholder"))
        self._parse_btn.setText(t("parse"))
        self._parse_btn.setToolTip(t("parse_tip"))
        self._mode_desc.setText(t("mode_zip_desc") if self._seg.current() == 0 else t("mode_git_desc"))
        self._save_lbl.setText(t("save_to"))
        self._browse_btn.setToolTip(t("browse_tip"))
        self._pull_btn.setText(t("pull"))
        self._cancel_btn.setText(t("cancel"))
        self._open_btn.setText(t("open_folder"))
        self._copy_btn.setText(t("copy_path"))
        self._log_toggle.setText(t("log_hide") if self._log.isVisible() else t("log_show"))
        self._status_label.setText(t("status_ready"))
        self._footer_hint.setText(t("footer_hint"))
        if not self._log.isVisible() and not self._log_toggle.isVisible() and not self._prog_card.isVisible():
            pass
        self._url_input.setToolTip(t("paste_tip"))
        # 仓库卡片
        if self._repo_info:
            self._render_repo_card()

    # ================================================== 仓库信息
    def _paste_url(self):
        text = QApplication.clipboard().text().strip()
        if text:
            self._url_input.setText(text)
            self._url_input.setFocus()

    def _on_parse(self):
        if self._info_worker or (self._pull_worker and self._pull_worker.isRunning()):
            return
        raw = self._url_input.text().strip()
        if not raw:
            self._toast.show_message(tr(self._lang, "empty_url"), "warning")
            return
        parsed = parse_github_url(raw)
        if not parsed:
            self._toast.show_message(tr(self._lang, "url_invalid"), "error")
            return
        owner, repo, branch = parsed
        self._parsed = (owner, repo, branch)
        self._repo_info = None
        self._repo_card.hide()
        self._set_status(tr(self._lang, "fetch_info_loading"), "#7CCBFF")
        self._parse_btn.setEnabled(False)
        self._parse_btn.setText(tr(self._lang, "parsing"))
        self._info_worker = RepoInfoWorker(owner, repo, self)
        self._info_worker.done.connect(self._on_info_done)
        self._info_worker.failed.connect(self._on_info_failed)
        self._info_worker.start()

    def _on_info_done(self, info: RepoInfo):
        self._info_worker = None
        self._parse_btn.setEnabled(True)
        self._parse_btn.setText(tr(self._lang, "parse"))
        self._repo_info = info
        self._render_repo_card()
        self._repo_card.show()
        self._set_status(tr(self._lang, "status_ready"))
        self._toast.show_message(
            f"{tr(self._lang, 'repo_loaded')} · {info.full_name}", "success", 2200
        )

    def _on_info_failed(self, msg: str):
        self._info_worker = None
        self._parse_btn.setEnabled(True)
        self._parse_btn.setText(tr(self._lang, "parse"))
        text = self._translate_error(msg)
        self._set_status(tr(self._lang, "status_ready"))
        # 信息失败仍允许拉取（用解析出的 owner/repo）
        if self._parsed:
            self._repo_info = RepoInfo(owner=self._parsed[0], name=self._parsed[1])
        self._toast.show_message(f"{tr(self._lang, 'url_parse_failed')}{text}", "warning", 3600)

    def _translate_error(self, msg: str) -> str:
        t = lambda k: tr(self._lang, k)
        m = {
            "repo_not_found": t("repo_not_found"),
            "rate_limited": t("rate_limited"),
            "network_error": t("network_error"),
            "git_missing": t("git_missing"),
            "cancelled": t("cancelled_msg"),
        }
        for k, v in m.items():
            if msg.startswith(k):
                rest = msg[len(k):].strip(" ()")
                return v + (f" ({rest})" if rest else "")
        return msg

    def _render_repo_card(self):
        info = self._repo_info
        if not info:
            return
        t = lambda k: tr(self._lang, k)
        self._repo_name.setText(info.name)
        self._repo_branch.setText(f"{t('default_branch')}: {info.default_branch}")
        self._repo_full.setText(f"https://github.com/{info.full_name}  ↗")
        self._repo_desc.setText(info.description or t("repo_desc_empty"))
        chips = []
        chips.append(f"<span style='color:#FFD24D'>★</span> <b>{_fmt_count(info.stars)}</b> <span style='color:{TEXT_DIM}'>star</span>")
        chips.append(f"<span style='color:#8BE9FF'>⎇</span> <b>{_fmt_count(info.forks)}</b> <span style='color:{TEXT_DIM}'>fork</span>")
        if info.language:
            chips.append(f"<span style='color:#7CE7A8'>●</span> {info.language}")
        if info.license_name:
            chips.append(f"<span style='color:{TEXT_SUB}'>◈ {info.license_name}</span>")
        self._repo_chips.setText("&nbsp;&nbsp;&nbsp;".join(chips))
        self._repo_chips.setTextFormat(Qt.TextFormat.RichText)
        if info.avatar_bytes:
            self._avatar.setPixmap(self._rounded_pixmap(info.avatar_bytes, 56))
        else:
            self._avatar.setPixmap(self._default_avatar(56))

    # ================================================== 拉取
    def _on_mode_changed(self, i: int):
        t = lambda k: tr(self._lang, k)
        self._mode_desc.setText(t("mode_zip_desc") if i == 0 else t("mode_git_desc"))

    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(self, tr(self._lang, "browse"), self._path_input.text())
        if d:
            self._path_input.setText(d)

    def _on_pull(self):
        if self._pull_worker and self._pull_worker.isRunning():
            return
        raw = self._url_input.text().strip()
        parsed = parse_github_url(raw) or self._parsed
        if not parsed:
            self._toast.show_message(tr(self._lang, "empty_url"), "warning")
            return
        owner, repo, branch = parsed
        dest = self._path_input.text().strip()
        if not dest:
            self._toast.show_message(tr(self._lang, "dest_invalid"), "error")
            return
        if not os.path.isdir(dest):
            try:
                os.makedirs(dest, exist_ok=True)
                self._toast.show_message(f"{tr(self._lang, 'dest_created')}{dest}", "info", 2000)
            except OSError:
                self._toast.show_message(tr(self._lang, "dest_invalid"), "error")
                return
        self._settings.setValue("last_dir", dest)

        info = self._repo_info or RepoInfo(owner=owner, name=repo)
        if info.default_branch == "main" and branch:
            info.default_branch = branch
        mode = "zip" if self._seg.current() == 0 else "git"

        self._target_path = ""
        self._open_btn.setEnabled(False)
        self._copy_btn.setEnabled(False)
        self._prog_card.show()
        self._log_toggle.show()
        self._log.clear()
        self._prog_bar.set_value(0)
        self._pct_label.setText("0%")
        self._set_busy(True)
        self._set_status(
            tr(self._lang, "downloading" if mode == "zip" else "clone_running"), "#7CCBFF"
        )

        self._pull_worker = PullWorker(mode, raw, dest, info, branch, self)
        self._pull_worker.progress.connect(self._on_progress)
        self._pull_worker.log.connect(self._log.append_html)
        self._pull_worker.succeeded.connect(self._on_pull_success)
        self._pull_worker.failed.connect(self._on_pull_failed)
        self._pull_worker.cancelled.connect(self._on_pull_cancelled)
        self._pull_worker.start()

    def _on_progress(self, v: int):
        self._prog_bar.set_value(v)
        self._pct_label.setText(f"{v}%")

    def _on_pull_success(self, path: str):
        self._target_path = path
        self._prog_bar.set_value(100)
        self._pct_label.setText("100%")
        self._set_busy(False)
        self._open_btn.setEnabled(True)
        self._copy_btn.setEnabled(True)
        self._set_status(tr(self._lang, "success_title"), "#2EE6A8")
        self._toast.show_message(f"{tr(self._lang, 'success_msg')}\n{path}", "success", 4200)

    def _on_pull_failed(self, msg: str):
        self._prog_bar.set_indeterminate(False)
        text = self._translate_error(msg)
        self._set_busy(False)
        self._set_status(tr(self._lang, "status_ready"))
        self._toast.show_message(text, "error", 4200)

    def _on_pull_cancelled(self):
        self._prog_bar.set_indeterminate(False)
        self._set_busy(False)
        self._set_status(tr(self._lang, "cancelled"))
        self._toast.show_message(tr(self._lang, "cancelled_msg"), "warning", 2600)

    def _on_cancel(self):
        if self._pull_worker and self._pull_worker.isRunning():
            self._cancel_btn.setEnabled(False)
            self._cancel_btn.setText("…")
            self._pull_worker.cancel()

    def _set_busy(self, busy: bool):
        self._cancel_btn.setVisible(busy)
        self._cancel_btn.setEnabled(busy)
        if busy:
            self._cancel_btn.setText(tr(self._lang, "cancel"))
        self._pull_btn.setEnabled(not busy)
        self._parse_btn.setEnabled(not busy)
        self._url_input.setEnabled(not busy)
        self._seg.setEnabled(not busy)
        self._browse_btn.setEnabled(not busy)
        self._path_input.setEnabled(not busy)
        self._log_toggle.setText(tr(self._lang, "log_show") if not self._log.isVisible() else tr(self._lang, "log_hide"))

    def _toggle_log(self):
        if self._log.isVisible():
            self._log.hide()
            self._log_toggle.setText(tr(self._lang, "log_show"))
        else:
            self._log.show()
            self._log_toggle.setText(tr(self._lang, "log_hide"))

    def _open_target(self):
        if self._target_path and os.path.isdir(self._target_path):
            os.startfile(self._target_path)  # noqa: S606

    def _copy_target(self):
        QApplication.clipboard().setText(self._target_path)
        self._toast.show_message(tr(self._lang, "path_copied"), "success", 2000)

    def _open_github(self):
        if self._repo_info:
            QDesktopServices.openUrl(QUrl(f"https://github.com/{self._repo_info.full_name}"))

    # ================================================== 状态
    def _set_status(self, text: str, color: str = "#98A2C0"):
        self._status_label.setText(text)
        self._status_label.setStyleSheet(f"color:{color}; font-size:12px;")
        try:
            self._status_dot.setPixmap(icons.dot_pixmap(9, color))
        except Exception:  # noqa: BLE001
            pass

    # ================================================== 窗口控制
    def _tb_press(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            e.accept()

    def _tb_move(self, e):
        if self._drag_pos is not None and e.buttons() & Qt.MouseButton.LeftButton:
            if self._maximized:
                return
            self.move(e.globalPosition().toPoint() - self._drag_pos)
            e.accept()

    def _tb_release(self, e):
        self._drag_pos = None

    def _toggle_max(self):
        if self._maximized:
            self.showNormal()
            self._maximized = False
            self._btn_max._kind = "max"
            self._apply_rounded(True)
        else:
            self.showMaximized()
            self._maximized = True
            self._btn_max._kind = "restore"
            self._apply_rounded(False)
        self._btn_max.update()

    def _apply_rounded(self, rounded: bool):
        m = 10 if rounded else 0
        self.layout().setContentsMargins(m, m, m, m)
        radius = "18px" if rounded else "0px"
        self._shell.setStyleSheet(
            f"""
            QFrame#Shell {{
                background: qlineargradient(x1:0, y1:0, x2:0.6, y2:1,
                    stop:0 {BG_TOP}, stop:0.5 {BG_MID}, stop:1 {BG_BOTTOM});
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: {radius};
            }}
            """
        )
        self._shadow.setEnabled(rounded)

    def _fade_in(self):
        self.setWindowOpacity(0.0)
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(280)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _restore_geometry(self):
        g = self._settings.value("geometry")
        if g and isinstance(g, QRect) and g.width() >= self.minimumWidth():
            self.setGeometry(g)

    # ================================================== 头像
    def _default_avatar(self, size: int) -> QPixmap:
        pm = QPixmap(size, size)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(36, 46, 78))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRect(0, 0, size, size), size / 3, size / 3)
        p.setPen(QColor(120, 140, 190))
        f = QFont(QFONT_NAME)
        f.setPixelSize(int(size * 0.42))
        f.setBold(True)
        p.setFont(f)
        p.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "▦")
        p.end()
        return pm

    def _rounded_pixmap(self, data: bytes, size: int) -> QPixmap:
        pm = QPixmap()
        pm.loadFromData(data)
        if pm.isNull():
            return self._default_avatar(size)
        pm = pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        out = QPixmap(size, size)
        out.fill(Qt.GlobalColor.transparent)
        p = QPainter(out)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRect(0, 0, size, size), size / 3, size / 3)
        p.setClipPath(path)
        p.drawPixmap(QRect(0, 0, size, size), pm)
        p.end()
        return out

    # ================================================== 关闭与退出
    def closeEvent(self, e):
        running = (self._pull_worker and self._pull_worker.isRunning()) or (
            self._info_worker and self._info_worker.isRunning()
        )
        if running:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Warning)
            box.setWindowTitle(tr(self._lang, "exit_title"))
            box.setText(tr(self._lang, "exit_question"))
            yes = box.addButton(tr(self._lang, "close"), QMessageBox.ButtonRole.AcceptRole)
            no = box.addButton(tr(self._lang, "cancel"), QMessageBox.ButtonRole.RejectRole)
            box.setDefaultButton(no)
            box.exec()
            if box.clickedButton() is not yes:
                e.ignore()
                return
            if self._pull_worker:
                self._pull_worker.cancel()
                self._pull_worker.wait(3000)
        if not self._maximized:
            self._settings.setValue("geometry", self.geometry())
        e.accept()
