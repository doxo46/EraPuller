"""EraPuller — 全局主题：配色、字体与 QSS 样式表"""

from PySide6.QtGui import QColor

# ---------- 色板 ----------
BG_TOP = "#0A0E1D"
BG_MID = "#0D1428"
BG_BOTTOM = "#131C36"

CARD_BG = "rgba(255,255,255,0.045)"
CARD_BG_HOVER = "rgba(255,255,255,0.06)"
CARD_BORDER = "rgba(255,255,255,0.09)"

ACCENT_A = QColor(0, 229, 255)      # 星芒青
ACCENT_B = QColor(124, 77, 255)     # 极光紫
ACCENT_C = QColor(255, 61, 129)     # 霓虹玫红

TEXT_MAIN = "#E9EEFB"
TEXT_SUB = "#98A2C0"
TEXT_DIM = "#5E6784"

COLOR_SUCCESS = QColor(46, 230, 168)
COLOR_ERROR = QColor(255, 92, 122)
COLOR_WARNING = QColor(255, 184, 77)
COLOR_LINK = QColor(110, 190, 255)

RADIUS = 14

CSS_FONT = '"Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", "PingFang SC", sans-serif'
QFONT_NAME = "Microsoft YaHei UI"
CSS_MONO = '"Cascadia Mono", "Consolas", "Courier New", monospace'


def gradient_css(c1: str, c2: str) -> str:
    return f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c1}, stop:1 {c2})"


def build_qss() -> str:
    return f"""
* {{
    font-family: {CSS_FONT};
    outline: none;
}}
QWidget {{
    color: {TEXT_MAIN};
}}

/* ---------- 卡片 ---------- */
QFrame#Card {{
    background: {CARD_BG};
    border: 1px solid {CARD_BORDER};
    border-radius: {RADIUS}px;
}}

/* ---------- 输入框 ---------- */
QLineEdit#UrlInput {{
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 12px;
    padding: 0 16px;
    color: {TEXT_MAIN};
    font-size: 14px;
    selection-background-color: {ACCENT_B.name()};
    selection-color: #FFFFFF;
}}
QLineEdit#UrlInput:hover {{
    border-color: rgba(255,255,255,0.18);
}}
QLineEdit#UrlInput:focus {{
    border: 1px solid {gradient_css("#00E5FF", "#7C4DFF")};
    background: rgba(255,255,255,0.075);
}}
QLineEdit#UrlInput::placeholder {{ color: {TEXT_DIM}; }}

QLineEdit#PathInput {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 0 12px;
    color: {TEXT_SUB};
    font-size: 12px;
}}
QLineEdit#PathInput:hover {{ border-color: rgba(255,255,255,0.16); }}
QLineEdit#PathInput:focus {{ border-color: rgba(0,229,255,0.55); color: {TEXT_MAIN}; }}

/* ---------- 日志视图 ---------- */
QTextEdit#LogView {{
    background: rgba(4,8,18,0.55);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    color: {TEXT_SUB};
    font-family: {CSS_MONO};
    font-size: 12px;
    padding: 8px 10px;
    selection-background-color: {ACCENT_B.name()};
}}

/* ---------- 菜单 ---------- */
QMenu {{
    background: #141B31;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 10px;
    padding: 6px;
}}
QMenu::item {{
    padding: 7px 26px 7px 12px;
    border-radius: 7px;
    color: {TEXT_MAIN};
    font-size: 13px;
}}
QMenu::item:selected {{
    background: {gradient_css("#0FD8FF", "#7C4DFF")};
    color: #FFFFFF;
}}
QMenu::item:disabled {{ color: {TEXT_DIM}; }}
QMenu::separator {{
    height: 1px;
    background: rgba(255,255,255,0.08);
    margin: 4px 8px;
}}

/* ---------- 滚动条 ---------- */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: rgba(255,255,255,0.14);
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: rgba(255,255,255,0.26); }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

/* ---------- 提示气泡 ---------- */
QToolTip {{
    background: #1A2240;
    color: {TEXT_MAIN};
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 12px;
}}

/* ---------- 消息框 ---------- */
QMessageBox {{
    background: #101730;
}}
QMessageBox QLabel {{ color: {TEXT_MAIN}; font-size: 13px; }}
QMessageBox QPushButton {{
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 8px;
    padding: 6px 18px;
    color: {TEXT_MAIN};
    font-size: 13px;
}}
QMessageBox QPushButton:hover {{ background: rgba(255,255,255,0.14); }}
QMessageBox QPushButton:pressed {{ background: rgba(255,255,255,0.05); }}
"""
