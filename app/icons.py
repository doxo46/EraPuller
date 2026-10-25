"""EraPuller — 程序化图标绘制（无需任何图片资源）"""

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)


def _canvas(size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    return pm


def _pen(color: str, width: float = 2.0) -> QPen:
    p = QPen(QColor(color), width)
    p.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return p


def clipboard_icon(size: int = 18, color: str = "#E9EEFB") -> QIcon:
    pm = _canvas(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    p.setPen(_pen(color, max(1.4, s * 0.11)))
    # 顶部夹子
    p.drawRoundedRect(QRectF(s * 0.34, s * 0.13, s * 0.32, s * 0.22), s * 0.06, s * 0.06)
    # 板身
    p.drawRoundedRect(QRectF(s * 0.22, s * 0.26, s * 0.56, s * 0.56), s * 0.09, s * 0.09)
    p.drawLine(QPointF(s * 0.36, s * 0.48), QPointF(s * 0.64, s * 0.48))
    p.drawLine(QPointF(s * 0.36, s * 0.60), QPointF(s * 0.55, s * 0.60))
    p.end()
    return QIcon(pm)


def refresh_icon(size: int = 18, color: str = "#E9EEFB") -> QIcon:
    pm = _canvas(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    pen = _pen(color, max(1.4, s * 0.1))
    p.setPen(pen)
    rect = QRectF(s * 0.22, s * 0.22, s * 0.56, s * 0.56)
    p.drawArc(rect, 25 * 16, 300 * 16)
    # 箭头
    tri = QPolygonF(
        [
            QPointF(s * 0.74, s * 0.20),
            QPointF(s * 0.88, s * 0.40),
            QPointF(s * 0.64, s * 0.38),
        ]
    )
    p.setBrush(QColor(color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPolygon(tri)
    p.end()
    return QIcon(pm)


def folder_icon(size: int = 18, color: str = "#E9EEFB") -> QIcon:
    pm = _canvas(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    p.setPen(_pen(color, max(1.4, s * 0.1)))
    path = QPainterPath()
    path.moveTo(s * 0.18, s * 0.30)
    path.lineTo(s * 0.44, s * 0.30)
    path.lineTo(s * 0.54, s * 0.40)
    path.lineTo(s * 0.82, s * 0.40)
    path.lineTo(s * 0.82, s * 0.70)
    path.lineTo(s * 0.18, s * 0.70)
    path.closeSubpath()
    p.drawPath(path)
    p.end()
    return QIcon(pm)


def globe_icon(size: int = 18, color: str = "#E9EEFB") -> QIcon:
    pm = _canvas(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    pen = _pen(color, max(1.3, s * 0.1))
    p.setPen(pen)
    p.drawEllipse(QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64))
    p.drawEllipse(QRectF(s * 0.38, s * 0.18, s * 0.24, s * 0.64))
    p.drawLine(QPointF(s * 0.18, s * 0.5), QPointF(s * 0.82, s * 0.5))
    p.end()
    return QIcon(pm)


def download_icon(size: int = 18, color: str = "#E9EEFB") -> QIcon:
    pm = _canvas(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    p.setPen(_pen(color, max(1.4, s * 0.11)))
    p.drawLine(QPointF(s * 0.5, s * 0.16), QPointF(s * 0.5, s * 0.58))
    p.drawLine(QPointF(s * 0.34, s * 0.42), QPointF(s * 0.5, s * 0.58))
    p.drawLine(QPointF(s * 0.66, s * 0.42), QPointF(s * 0.5, s * 0.58))
    p.drawLine(QPointF(s * 0.24, s * 0.74), QPointF(s * 0.76, s * 0.74))
    p.end()
    return QIcon(pm)


def open_icon(size: int = 18, color: str = "#E9EEFB") -> QIcon:
    pm = _canvas(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    p.setPen(_pen(color, max(1.4, s * 0.11)))
    # 箭头朝右上方（打开）
    p.drawLine(QPointF(s * 0.28, s * 0.72), QPointF(s * 0.72, s * 0.28))
    p.drawLine(QPointF(s * 0.42, s * 0.28), QPointF(s * 0.72, s * 0.28))
    p.drawLine(QPointF(s * 0.72, s * 0.28), QPointF(s * 0.72, s * 0.58))
    p.end()
    return QIcon(pm)


def check_icon(size: int = 18, color: str = "#2EE6A8") -> QIcon:
    pm = _canvas(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    p.setPen(_pen(color, max(1.6, s * 0.13)))
    p.drawLine(QPointF(s * 0.22, s * 0.54), QPointF(s * 0.42, s * 0.74))
    p.drawLine(QPointF(s * 0.42, s * 0.74), QPointF(s * 0.80, s * 0.30))
    p.end()
    return QIcon(pm)


def copy_icon(size: int = 18, color: str = "#E9EEFB") -> QIcon:
    pm = _canvas(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    p.setPen(_pen(color, max(1.3, s * 0.1)))
    p.drawRoundedRect(QRectF(s * 0.26, s * 0.26, s * 0.48, s * 0.48), s * 0.08, s * 0.08)
    p.setOpacity(0.45)
    p.drawRoundedRect(QRectF(s * 0.42, s * 0.14, s * 0.44, s * 0.42), s * 0.08, s * 0.08)
    p.end()
    return QIcon(pm)


def external_icon(size: int = 18, color: str = "#6EBEFF") -> QIcon:
    pm = _canvas(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    p.setPen(_pen(color, max(1.3, s * 0.1)))
    p.drawRoundedRect(QRectF(s * 0.16, s * 0.16, s * 0.68, s * 0.68), s * 0.1, s * 0.1)
    p.drawLine(QPointF(s * 0.44, s * 0.44), QPointF(s * 0.66, s * 0.34))
    p.drawLine(QPointF(s * 0.52, s * 0.34), QPointF(s * 0.66, s * 0.34))
    p.drawLine(QPointF(s * 0.66, s * 0.34), QPointF(s * 0.66, s * 0.48))
    p.end()
    return QIcon(pm)


def close_icon(size: int = 14, color: str = "#E9EEFB") -> QIcon:
    pm = _canvas(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    p.setPen(_pen(color, max(1.4, s * 0.11)))
    p.drawLine(QPointF(s * 0.25, s * 0.25), QPointF(s * 0.75, s * 0.75))
    p.drawLine(QPointF(s * 0.75, s * 0.25), QPointF(s * 0.25, s * 0.75))
    p.end()
    return QIcon(pm)


def min_icon(size: int = 14, color: str = "#E9EEFB") -> QIcon:
    pm = _canvas(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    p.setPen(_pen(color, max(1.4, s * 0.11)))
    p.drawLine(QPointF(s * 0.24, s * 0.5), QPointF(s * 0.76, s * 0.5))
    p.end()
    return QIcon(pm)


def max_icon(size: int = 14, color: str = "#E9EEFB") -> QIcon:
    pm = _canvas(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    p.setPen(_pen(color, max(1.4, s * 0.11)))
    p.drawRoundedRect(QRectF(s * 0.24, s * 0.24, s * 0.52, s * 0.52), s * 0.08, s * 0.08)
    p.end()
    return QIcon(pm)


def restore_icon(size: int = 14, color: str = "#E9EEFB") -> QIcon:
    pm = _canvas(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    p.setPen(_pen(color, max(1.4, s * 0.11)))
    p.drawRoundedRect(QRectF(s * 0.20, s * 0.38, s * 0.42, s * 0.42), s * 0.07, s * 0.07)
    p.setOpacity(0.55)
    p.drawRoundedRect(QRectF(s * 0.38, s * 0.20, s * 0.42, s * 0.42), s * 0.07, s * 0.07)
    p.end()
    return QIcon(pm)


def app_logo(size: int = 96) -> QIcon:
    """品牌图标：青色→紫色渐变圆角方块 + 白色下载箭头。"""
    pm = _canvas(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    rect = QRectF(0, 0, s, s)
    path = QPainterPath()
    r = s * 0.24
    path.addRoundedRect(rect, r, r)
    grad = QLinearGradient(0, 0, s, s)
    grad.setColorAt(0.0, QColor(0, 229, 255))
    grad.setColorAt(0.55, QColor(72, 140, 255))
    grad.setColorAt(1.0, QColor(124, 77, 255))
    p.fillPath(path, grad)
    # 高光
    hi = QLinearGradient(0, 0, 0, s * 0.6)
    hi.setColorAt(0.0, QColor(255, 255, 255, 90))
    hi.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.fillPath(path, hi)
    white = QColor("#FFFFFF")
    pen = _pen("#FFFFFF", max(2.2, s * 0.055))
    p.setPen(pen)
    p.drawLine(QPointF(s * 0.5, s * 0.26), QPointF(s * 0.5, s * 0.60))
    p.drawLine(QPointF(s * 0.36, s * 0.46), QPointF(s * 0.5, s * 0.60))
    p.drawLine(QPointF(s * 0.64, s * 0.46), QPointF(s * 0.5, s * 0.60))
    p.setPen(QPen(white, max(2.2, s * 0.05)))
    p.drawLine(QPointF(s * 0.26, s * 0.72), QPointF(s * 0.74, s * 0.72))
    p.end()
    return QIcon(pm)


def dot_pixmap(size: int = 10, color: str = "#2EE6A8") -> QPixmap:
    pm = _canvas(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QRectF(1, 1, size - 2, size - 2))
    p.end()
    return pm
