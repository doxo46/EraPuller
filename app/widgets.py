"""EraPuller — 自定义控件：标题栏 / 渐变按钮 / 分段切换 / 进度条 / Toast 等"""

import math

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
    QTimer,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import icons
from .theme import (
    ACCENT_A,
    ACCENT_B,
    ACCENT_C,
    CARD_BORDER,
    COLOR_ERROR,
    COLOR_SUCCESS,
    COLOR_WARNING,
    CSS_FONT,
    QFONT_NAME,
    RADIUS,
    TEXT_DIM,
    TEXT_MAIN,
    TEXT_SUB,
    gradient_css,
)

_CURSOR_POINTING = Qt.CursorShape.PointingHandCursor


def _font(pixel: int, bold: bool = False) -> QFont:
    f = QFont(QFONT_NAME)
    f.setPixelSize(pixel)
    f.setBold(bold)
    return f


# ============================================================ 通用悬浮按钮
class HoverButton(QPushButton):
    """半透明胶囊按钮：悬浮高亮、按下加深。"""

    def __init__(self, text: str = "", icon=None, parent=None):
        super().__init__(text, parent)
        self._hover = False
        self._pressed = False
        self._icon = icon
        self._icon_size = 16
        self.setCursor(_CURSOR_POINTING)
        self.setFixedHeight(38)
        self.setMouseTracking(True)

    def set_icon(self, icon, size: int = 16):
        self._icon = icon
        self._icon_size = size
        self.update()

    def enterEvent(self, e):
        self._hover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self._pressed = False
        self.update()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.update()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        radius = min(11, r.height() / 2)
        if not self.isEnabled():
            p.setBrush(QColor(28, 35, 56))
            p.setPen(QPen(QColor(255, 255, 255, 18), 1))
        else:
            bg = QColor(255, 255, 255, 110 if self._hover else 60)
            p.setBrush(bg)
            bd = QColor(255, 255, 255, 200 if self._hover else 90)
            p.setPen(QPen(bd, 1))
        p.drawRoundedRect(r, radius, radius)
        if self._pressed:
            p.setBrush(QColor(0, 0, 0, 40))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(r, radius, radius)
        # 图标 + 文字
        draw_x = r.left()
        tw = 0
        fm = QFontMetrics(self.font())
        text = self.text()
        if text:
            tw = fm.horizontalAdvance(text)
        content_w = (self._icon_size + 6 if self._icon else 0) + tw
        x = r.center().x() - content_w / 2
        y = r.center().y()
        if self._icon:
            self._icon.paint(p, QRectF(x, y - self._icon_size / 2, self._icon_size, self._icon_size).toRect())
            x += self._icon_size + 6
        if text:
            col = TEXT_MAIN if self.isEnabled() else TEXT_DIM
            p.setPen(QColor(col))
            p.setFont(self.font())
            p.drawText(QRectF(x, r.top(), tw, r.height()).toRect(), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
        p.end()


class CaptionButton(QWidget):
    """标题栏窗口控制按钮（最小化/最大化/关闭）。"""

    clicked = Signal()

    def __init__(self, kind: str, parent=None):
        super().__init__(parent)
        self._kind = kind
        self._hover = False
        self.setFixedSize(46, 46)
        self.setCursor(_CURSOR_POINTING)

    def enterEvent(self, e):
        self._hover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self.update()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._hover = True
            self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.rect().contains(e.position().toPoint()):
            self.clicked.emit()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect())
        if self._hover:
            if self._kind == "close":
                p.setBrush(QColor(255, 92, 122, 200))
            else:
                p.setBrush(QColor(255, 255, 255, 26))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(r, 8, 8)
        color = "#FFFFFF" if self._hover else "#98A2C0"
        c = r.center()
        pen = QPen(QColor(color), 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        s = 11.0
        if self._kind == "min":
            p.drawLine(QPointF(c.x() - s, c.y()), QPointF(c.x() + s, c.y()))
        elif self._kind == "max":
            p.drawRoundedRect(QRectF(c.x() - s * 0.72, c.y() - s * 0.72, s * 1.44, s * 1.44), 2.5, 2.5)
        elif self._kind == "restore":
            p.drawRoundedRect(QRectF(c.x() - s * 0.62, c.y() - s * 0.25, s * 1.2, s * 1.2), 2.5, 2.5)
            p.setOpacity(0.55)
            p.drawRoundedRect(QRectF(c.x() - s * 0.9, c.y() - s * 0.62, s * 1.2, s * 1.2), 2.5, 2.5)
        elif self._kind == "close":
            p.drawLine(QPointF(c.x() - s * 0.62, c.y() - s * 0.62), QPointF(c.x() + s * 0.62, c.y() + s * 0.62))
            p.drawLine(QPointF(c.x() + s * 0.62, c.y() - s * 0.62), QPointF(c.x() - s * 0.62, c.y() + s * 0.62))
        p.end()


# ============================================================ 渐变主按钮
class GradientButton(QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._hover = False
        self._pressed = False
        self._icon = None
        self.setCursor(_CURSOR_POINTING)
        self.setFixedHeight(50)
        self.setMouseTracking(True)
        self.setFont(_font(16, True))

    def set_icon(self, icon):
        self._icon = icon
        self.update()

    def enterEvent(self, e):
        self._hover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self._pressed = False
        self.update()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.update()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        radius = min(13, r.height() / 2)
        path = QPainterPath()
        path.addRoundedRect(r, radius, radius)

        if not self.isEnabled():
            p.setBrush(QColor(33, 41, 66))
            p.setPen(QPen(QColor(255, 255, 255, 14), 1))
            p.drawPath(path)
            p.setPen(QColor(110, 120, 150))
            p.setFont(self.font())
            p.drawText(r.toRect(), Qt.AlignmentFlag.AlignCenter, self.text())
            p.end()
            return

        # 悬浮光晕
        if self._hover and not self._pressed:
            glow = QRadialGradient(r.center(), r.width() * 0.62)
            glow.setColorAt(0.0, QColor(70, 190, 255, 70))
            glow.setColorAt(1.0, QColor(70, 190, 255, 0))
            p.setBrush(glow)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(r).adjusted(-7, -7, 7, 7), radius + 7, radius + 7)

        grad = QLinearGradient(r.left(), r.top(), r.right(), r.bottom())
        grad.setColorAt(0.0, ACCENT_A)
        grad.setColorAt(0.45, QColor(70, 150, 255))
        grad.setColorAt(1.0, ACCENT_B)
        p.setBrush(grad)
        p.setPen(QPen(QColor(255, 255, 255, 60 if not self._hover else 130), 1))
        p.drawPath(path)

        if self._pressed:
            p.setBrush(QColor(0, 0, 0, 60))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(path)
        # 顶部高光
        hi = QLinearGradient(0, r.top(), 0, r.center().y())
        hi.setColorAt(0.0, QColor(255, 255, 255, 70))
        hi.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(hi)
        p.setPen(Qt.PenStyle.NoPen)
        hp = QPainterPath()
        hp.addRoundedRect(QRectF(r).adjusted(3, 2, -3, -r.height() * 0.45), radius, radius)
        p.drawPath(hp)

        # 图标 + 文字
        p.setPen(QColor("#FFFFFF"))
        p.setFont(self.font())
        fm = QFontMetrics(self.font())
        text = self.text()
        tw = fm.horizontalAdvance(text)
        icon_w = 22 if self._icon else 0
        total = icon_w + (8 if self._icon else 0) + tw
        x = r.center().x() - total / 2
        y = r.center().y()
        if self._icon:
            self._icon.paint(p, QRectF(x, y - 11, 22, 22).toRect())
            x += 30
        p.drawText(QRectF(x, r.top(), tw, r.height()).toRect(), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
        p.end()


# ============================================================ 分段切换器
class SegmentedControl(QWidget):
    changed = Signal(int)

    def __init__(self, items, parent=None):
        super().__init__(parent)
        self._items = list(items)
        self._cur = 0
        self._from = 0
        self._t = 1.0
        self.setCursor(_CURSOR_POINTING)
        self.setFixedHeight(42)
        self.setMinimumWidth(360)
        fm = QFontMetrics(_font(13, True))
        w = sum(fm.horizontalAdvance(t) for t in self._items) + 44 * len(self._items) + 8
        self.setMinimumWidth(max(360, w))
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(240)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(lambda v: self._on_anim(v))

    def _on_anim(self, v):
        self._t = float(v)
        self.update()

    def set_current(self, i: int, animate: bool = True):
        i = max(0, min(len(self._items) - 1, i))
        if i == self._cur:
            return
        self._from = self._cur
        self._cur = i
        if animate:
            self._anim.stop()
            self._anim.setStartValue(0.0)
            self._anim.setEndValue(1.0)
            self._anim.start()
        else:
            self._t = 1.0
            self.update()
        self.changed.emit(self._cur)

    def current(self) -> int:
        return self._cur

    def mousePressEvent(self, e):
        n = len(self._items)
        if n == 0:
            return
        i = int(e.position().x() / (self.width() / n))
        i = max(0, min(n - 1, i))
        if i != self._cur:
            self.set_current(i)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        radius = min(12, r.height() / 2)
        p.setBrush(QColor(255, 255, 255, 16))
        p.setPen(QPen(QColor(255, 255, 255, 30), 1))
        p.drawRoundedRect(r, radius, radius)

        n = len(self._items)
        if n == 0:
            p.end()
            return
        w = r.width() / n
        x0 = r.left() + (self._from + (self._cur - self._from) * self._t) * w
        ind = QRectF(x0 + 4, r.top() + 4, w - 8, r.height() - 8)
        grad = QLinearGradient(ind.left(), ind.top(), ind.right(), ind.bottom())
        grad.setColorAt(0.0, QColor(0, 229, 255))
        grad.setColorAt(1.0, QColor(124, 77, 255))
        p.setBrush(grad)
        p.setPen(QPen(QColor(255, 255, 255, 50), 1))
        p.drawRoundedRect(ind, min(10, ind.height() / 2), min(10, ind.height() / 2))

        for i, item in enumerate(self._items):
            cell = QRectF(r.left() + i * w, r.top(), w, r.height())
            selected = (i == self._cur)
            p.setFont(_font(13, True))
            p.setPen(QColor("#FFFFFF") if selected else QColor(TEXT_SUB))
            p.drawText(cell.toRect(), Qt.AlignmentFlag.AlignCenter, item)
        p.end()


# ============================================================ 动态进度条
class ModernProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._indet = False
        self._phase = 0.0
        self.setFixedHeight(14)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    def set_value(self, v: int):
        self._indet = False
        self._value = max(0, min(100, int(v)))
        self.update()

    def set_indeterminate(self, on: bool):
        self._indet = on
        self.update()

    def _tick(self):
        self._phase += 0.018
        self.update()

    def showEvent(self, e):
        self._timer.start()
        super().showEvent(e)

    def hideEvent(self, e):
        self._timer.stop()
        super().hideEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0, 1, 0, -1)
        radius = r.height() / 2
        p.setBrush(QColor(255, 255, 255, 16))
        p.setPen(QPen(QColor(255, 255, 255, 26), 1))
        p.drawRoundedRect(r, radius, radius)

        if self._indet:
            band_w = r.width() * 0.36
            pos = (self._phase * (r.width() + band_w)) % (r.width() + band_w) - band_w
            grad = QLinearGradient(pos, 0, pos + band_w, 0)
            grad.setColorAt(0.0, QColor(0, 229, 255, 40))
            grad.setColorAt(0.5, QColor(120, 150, 255, 210))
            grad.setColorAt(1.0, QColor(124, 77, 255, 40))
            p.setBrush(grad)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(pos, r.top() + 2, band_w, r.height() - 4), radius, radius)
        elif self._value > 0:
            fw = r.width() * self._value / 100
            fr = QRectF(r.left(), r.top(), fw, r.height())
            grad = QLinearGradient(fr.left(), 0, fr.right(), 0)
            grad.setColorAt(0.0, ACCENT_A)
            grad.setColorAt(1.0, ACCENT_B)
            p.setBrush(grad)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(fr, radius, radius)
            # 流光
            shine_x = (self._phase * (fw + 40)) % (fw + 40) - 40
            sg = QLinearGradient(shine_x, 0, shine_x + 40, 0)
            sg.setColorAt(0.0, QColor(255, 255, 255, 0))
            sg.setColorAt(0.5, QColor(255, 255, 255, 160))
            sg.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setBrush(sg)
            p.setPen(Qt.PenStyle.NoPen)
            path = QPainterPath()
            path.addRoundedRect(fr, radius, radius)
            p.drawPath(path)
        p.end()


# ============================================================ 动态背景光晕
class BgGlow(QWidget):
    """缓慢漂移的极光光晕，营造灵动氛围。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._tick)

    def _tick(self):
        self._t += 0.008
        self.update()

    def showEvent(self, e):
        self._timer.start()
        super().showEvent(e)

    def hideEvent(self, e):
        self._timer.stop()
        super().hideEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        cx1 = w * (0.22 + 0.06 * math.sin(self._t * 1.3))
        cy1 = h * (0.16 + 0.05 * math.cos(self._t * 1.1))
        r1 = w * 0.42
        g1 = QRadialGradient(QPointF(cx1, cy1), r1)
        g1.setColorAt(0.0, QColor(0, 229, 255, 26))
        g1.setColorAt(1.0, QColor(0, 229, 255, 0))
        p.setBrush(g1)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx1, cy1), r1, r1)

        cx2 = w * (0.82 - 0.06 * math.sin(self._t * 1.05))
        cy2 = h * (0.34 + 0.05 * math.cos(self._t * 0.9))
        r2 = w * 0.38
        g2 = QRadialGradient(QPointF(cx2, cy2), r2)
        g2.setColorAt(0.0, QColor(124, 77, 255, 30))
        g2.setColorAt(1.0, QColor(124, 77, 255, 0))
        p.setBrush(g2)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx2, cy2), r2, r2)
        p.end()


# ============================================================ 渐变标题
class GradientTitle(QLabel):
    def __init__(self, text: str = "", size: int = 30, parent=None):
        super().__init__(text, parent)
        self._size = size
        self.setFont(_font(size, True))

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect())
        # 柔和投影
        p.setPen(QPen(QColor(0, 0, 0, 90), 0))
        p.setFont(_font(self._size, True))
        fm = QFontMetrics(self.font())
        text = self.text()
        tw = fm.horizontalAdvance(text)
        x = r.center().x() - tw / 2
        y = r.center().y() + fm.ascent() / 2 - fm.descent() / 2 - 1
        grad = QLinearGradient(x, 0, x + tw, 0)
        grad.setColorAt(0.0, QColor(0, 229, 255))
        grad.setColorAt(0.55, QColor(110, 170, 255))
        grad.setColorAt(1.0, QColor(190, 120, 255))
        p.setBrush(grad)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawText(QPointF(x + 1, y + 2), text)
        p.setPen(QPen(grad, 0))
        p.drawText(QPointF(x, y), text)
        p.end()


# ============================================================ Toast 通知
class Toast(QLabel):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setFont(_font(13, False))
        self.hide()
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(220)

    def show_message(self, text: str, kind: str = "info", duration: int = 2600):
        colors = {
            "info": "#98A2C0",
            "success": "#2EE6A8",
            "error": "#FF5C7A",
            "warning": "#FFB84D",
        }
        c = colors.get(kind, colors["info"])
        self.setText(text)
        self.setStyleSheet(
            f"""
            QLabel {{
                background: rgba(16,22,44,0.96);
                border: 1px solid {c}66;
                border-radius: 10px;
                color: {c};
                padding: 9px 18px;
                font-size: 13px;
            }}
            """
        )
        self.adjustSize()
        parent = self.parentWidget()
        if parent:
            w = min(self.width(), parent.width() - 60)
            x = parent.width() / 2 - w / 2
            y = parent.height() - self.height() - 70
            self.setGeometry(int(x), int(y), int(w), self.height())
            self.setWordWrap(self.width() >= parent.width() - 100)
        self._fade.stop()
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self._fade.stop()
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.start()
        QTimer.singleShot(duration, self._fade_out)

    def _fade_out(self):
        self._fade.stop()
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(0.0)
        self._fade.finished.connect(self.hide)
        self._fade.start()


# ============================================================ 日志视图
class LogView(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LogView")
        self.setReadOnly(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.document().setMaximumBlockCount(600)
        self.append_html("<span style='color:#5E6784'>▍日志就绪</span>")

    def append_html(self, html: str):
        self.append(html)
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())
