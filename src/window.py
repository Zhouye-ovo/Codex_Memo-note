"""主窗口：小签（TagTab）——极简桌面标签小组件。

仪表盘同款美术：45% 透黑玻璃 + 深色顶栏 + 5×7 点阵 LED Finish；
黑色胶囊标签列表 + Finish / Unfinished 翻页；学习计划表格独立窗口（可手动关闭、四角缩放）；
主窗四角拖拽缩放；贴边折叠（老 QQ 风格）。
"""
from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRect,
    QRectF,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QCursor,
    QFont,
    QGuiApplication,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSystemTrayIcon,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from datetime import datetime

from . import schedule, skin
from .config import Config
from .store import Item, ItemStore

FONT_FAMILY = "Microsoft YaHei UI"
MONO_FONT = "Consolas"
WINDOW_W = 320
WINDOW_H = 560
MIN_W = 290                 # 宽度下限：保证点阵文字与按钮不重叠、标签可读
MIN_H = 180
MAX_W = 900
MAX_H = 2000
TABLE_MIN_W = 480
TABLE_MIN_H = 240
TABLE_MAX_W = 1600
TABLE_MAX_H = 2000
DRAG_THRESHOLD = 5
TOPBAR_ICON = 26
HANDLE = 14                 # 四角缩放热区

# 5×7 点阵字形（仪表盘同款，含英文与数字）
_DOT_5X7 = {
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00100", "01000", "00100", "00010", "00001"),
    "¥": ("10001", "10001", "01110", "11111", "00100", "00100", "00100"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01110"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "N": ("10001", "10011", "10101", "11001", "10001", "10001", "10001"),
    "S": ("01110", "10001", "10000", "01110", "00001", "10001", "01110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}

# 学习计划表格数据（点击格子可划线）
TABLE_HEADERS = ["阶段", "效果", "现在的差距", "现成零件", "作品集产出"]
TABLE_DATA = [
    ["一 · UV/时间家族", "UV 流动", "几乎为零（_Time 参数化）", "采样/swizzle", "案例-UV流动"],
    ["", "遮罩", "多纹理采样 + lerp(A,B,mask)", "Blend 速查", "案例-遮罩"],
    ["", "纹理扭曲", "噪声已入库，直接用", "噪声笔记", "案例-纹理扭曲"],
    ["", "序列帧动画", "① 新知识：行列分块", "hash 随机起始帧", "案例-序列帧"],
    ["", "顶点动画（可提前）", "几乎为零（sin+_Time）", "结构体笔记", "案例-顶点动画"],
    ["二 · 溶解家族", "硬边溶解", "全齐（噪声+clip）", "噪声+clip", "案例-硬边溶解"],
    ["", "软溶解", "双阈值 smoothstep 羽化", "Ramp 边缘配色", "案例-软溶解"],
    ["", "光边溶解", "HDR 边缘色 + Bloom", "HDR/Bloom + Add 混合", "案例-光边溶解（主力）"],
    ["三 · 深度家族", "切边软化/软粒子", "② 新知识：URP 深度采样实战", "深度纹理速查 + UE 原理", "案例-切边软化"],
    ["四 · 压轴", "热扭曲", "③ 新知识：Custom Pass/Renderer Feature", "_CameraOpaqueTexture+噪声", "案例-热扭曲（毕业题）"],
]


class ClickLabel(QLabel):
    clicked = Signal()
    doubleClicked = Signal()
    pressed = Signal(object)
    moved = Signal(object)
    released = Signal(object)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._press_g = None

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_g = event.globalPosition().toPoint()
            self.pressed.emit(self._press_g)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._press_g is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.moved.emit(event.globalPosition().toPoint())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._press_g is not None:
            self._press_g = None
            self.released.emit(event.globalPosition().toPoint())
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)


class DotText(QWidget):
    """5×7 点阵 LED 文字（英文/数字）。"""

    clicked = Signal()

    def __init__(self, text: str = "", clickable: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._text = text
        self._clickable = clickable
        self.setFixedSize(*self.size_hint())
        if clickable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_text(self, text: str) -> None:
        self._text = text
        self.setFixedSize(*self.size_hint())
        self.update()

    def size_hint(self) -> tuple[int, int]:
        return max(1, len(self._text)) * 10, 14

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pitch_x = pitch_y = 2
        dot = 1
        lit = QColor(255, 255, 255) if (self._clickable and self.underMouse()) else QColor(skin.TEXT_MAIN)
        glow = QColor(255, 255, 255, 120) if (self._clickable and self.underMouse()) else QColor(255, 255, 255, 55)
        off = QColor(255, 255, 255, 22)
        x = 0
        for ch in self._text:
            pat = _DOT_5X7.get(ch, _DOT_5X7[" "])
            for row in range(7):
                for col in range(5):
                    if pat[row][col] == "1":
                        p.fillRect(QRectF(x + col * pitch_x - 1, row * pitch_y - 1, dot + 2, dot + 2), glow)
                        p.fillRect(x + col * pitch_x, row * pitch_y, dot, dot, lit)
                    else:
                        p.fillRect(x + col * pitch_x, row * pitch_y, dot, dot, off)
            x += 5 * pitch_x

    def mouseReleaseEvent(self, event) -> None:
        if self._clickable and event.button() == Qt.MouseButton.LeftButton \
                and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class EscapeLineEdit(QLineEdit):
    escapePressed = Signal()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.escapePressed.emit()
        else:
            super().keyPressEvent(event)


class IconButton(QPushButton):
    """顶栏图标按钮：QPainter 线条自绘（仪表盘同款）。"""

    def __init__(self, kind: str, tip: str, size: int = TOPBAR_ICON, parent=None) -> None:
        super().__init__(parent)
        self.kind = kind
        self.setToolTip(tip)
        self.setCheckable(kind in ("pin", "table"))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        if self.isDown():
            p.fillRect(r, QColor(skin.PRESS_BG))
        if self.underMouse():
            p.setPen(QPen(QColor(255, 255, 255, 70), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(QRectF(r).adjusted(0.5, 0.5, -0.5, -0.5), 5, 5)
        color = QColor(skin.STATUS_BLUE) if (self.kind in ("pin", "table") and self.isChecked()) else QColor(skin.TEXT_WEAK2)
        if self.underMouse():
            color = QColor(255, 255, 255)
        self._draw_icon(p, color)

    def _draw_icon(self, p: QPainter, color: QColor) -> None:
        pen = QPen(color, 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        cx, cy = self.width() / 2.0, self.height() / 2.0
        u = self.width() / 6.0
        if self.kind == "table":
            r = QRectF(cx - u, cy - u, 2 * u, 2 * u)
            p.drawRect(r)
            p.drawLine(QPointF(r.left(), cy), QPointF(r.right(), cy))
            p.drawLine(QPointF(cx, r.top()), QPointF(cx, r.bottom()))
        elif self.kind == "fold":
            p.drawLine(QPointF(cx - u, cy - u), QPointF(cx + u, cy))
            p.drawLine(QPointF(cx + u, cy), QPointF(cx - u, cy + u))
        elif self.kind == "pin":
            p.drawLine(QPointF(cx, cy - u), QPointF(cx, cy + u))
            p.drawLine(QPointF(cx - u, cy + u), QPointF(cx + u, cy + u))
            p.setBrush(color)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(cx, cy - u), 1.8, 1.8)
        elif self.kind == "close":
            d = u * 0.85
            p.drawLine(QPointF(cx - d, cy - d), QPointF(cx + d, cy + d))
            p.drawLine(QPointF(cx + d, cy - d), QPointF(cx - d, cy + d))


class CheckDot(QWidget):
    toggled = Signal(bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._done = False
        self.setFixedSize(18, 18)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_done(self, done: bool) -> None:
        self._done = done
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(2, 2, 14, 14)
        if self._done:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(skin.STATUS_GREEN))
            p.drawRoundedRect(r, 4, 4)
            pen = QPen(QColor(255, 255, 255), 2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(QPointF(5, 9), QPointF(8, 12))
            p.drawLine(QPointF(8, 12), QPointF(13, 6))
        else:
            p.setPen(QPen(QColor(255, 255, 255, 110), 1.2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(r)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._done = not self._done
            self.update()
            self.toggled.emit(self._done)
        event.accept()

class EditableLabel(QWidget):
    """双击进入编辑的文本标签。"""

    def __init__(self, text: str, on_commit, size: int = 11,
                 weight: QFont.Weight = QFont.Weight.Normal,
                 color: str = skin.TEXT_MAIN, parent=None,
                 drag_press=None, drag_move=None, drag_release=None) -> None:
        super().__init__(parent)
        self._on_commit = on_commit
        self._cancelled = False
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(0)
        self.label = ClickLabel(text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.label.doubleClicked.connect(self.begin_edit)
        if drag_press:
            self.label.pressed.connect(drag_press)
        if drag_move:
            self.label.moved.connect(drag_move)
        if drag_release:
            self.label.released.connect(drag_release)
        self.edit = EscapeLineEdit(text)
        self.edit.setFixedHeight(26)
        self.edit.setStyleSheet(
            "QLineEdit { background: #151515; color: #F4F4F0;"
            " border: 1px solid rgba(255,255,255,0.22); border-radius: 13px;"
            " padding: 0 10px; font-size: 11px; }"
        )
        self.edit.editingFinished.connect(self._commit)
        self.edit.escapePressed.connect(self._cancel)
        self._lay.addWidget(self.label)
        self._lay.addWidget(self.edit)
        self.edit.hide()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.set_font(size, weight)
        self.set_color(color)

    def set_font(self, size: int, weight: QFont.Weight) -> None:
        f = QFont(FONT_FAMILY, size, weight)
        self.label.setFont(f)
        self.edit.setFont(QFont(FONT_FAMILY, size))

    def set_color(self, color: str) -> None:
        self.label.setStyleSheet(
            f"color: {color}; background: transparent; border: none; padding: 2px 0;"
        )

    def text(self) -> str:
        return self.label.text()

    def begin_edit(self) -> None:
        self._cancelled = False
        self.edit.setText(self.label.text())
        self.edit.selectAll()
        self.label.hide()
        self.edit.show()
        self.edit.setFocus()

    def _commit(self) -> None:
        if not self.edit.isVisible():
            return
        if self._cancelled:
            self._cancelled = False
            self._close_edit()
            return
        self._close_edit()
        t = self.edit.text().strip()
        if t:
            self._on_commit(t)

    def _cancel(self) -> None:
        self._cancelled = True
        self._close_edit()

    def _close_edit(self) -> None:
        self.edit.hide()
        self.label.show()


class ItemChip(QFrame):
    """黑色圆角胶囊标签。"""

    def __init__(self, item: Item, store: ItemStore, on_change,
                 on_drag_press=None, on_drag_move=None, on_drag_release=None,
                 parent=None) -> None:
        super().__init__(parent)
        self.item = item
        self.store = store
        self.on_change = on_change
        self._on_drag_press = on_drag_press
        self._on_drag_move = on_drag_move
        self._on_drag_release = on_drag_release
        self.setFixedHeight(36)
        self.setStyleSheet(
            "ItemChip { background: #0A0A0A; border: 1px solid rgba(255,255,255,0.14);"
            " border-radius: 18px; }"
            " ItemChip:hover { background: #121212; }"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 8, 0)
        lay.setSpacing(8)
        self.check = CheckDot()
        self.check.set_done(item.done)
        self.check.toggled.connect(self._toggle)
        lay.addWidget(self.check)
        self.label = EditableLabel(
            item.title, self._rename, size=11, color=skin.TEXT_MAIN,
            drag_press=self._fwd_press, drag_move=self._fwd_move,
            drag_release=self._fwd_release)
        lay.addWidget(self.label, 1)
        self.btn_del = IconButton("close", "删除标签", size=20)
        self.btn_del.setVisible(False)
        self.btn_del.clicked.connect(self._delete)
        lay.addWidget(self.btn_del)
        self._apply_done_style()

    def enterEvent(self, event) -> None:
        self.btn_del.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.btn_del.setVisible(False)
        super().leaveEvent(event)

    def _apply_done_style(self) -> None:
        self.label.set_color(skin.TEXT_WEAK if self.item.done else skin.TEXT_MAIN)

    def _toggle(self, done: bool) -> None:
        self.store.toggle_item(self.item.id)
        self.store.save()
        self.on_change()

    def _rename(self, title: str) -> None:
        self.store.rename_item(self.item.id, title)
        self.store.save()
        self.on_change()

    def _delete(self) -> None:
        self.store.remove_item(self.item.id)
        self.store.save()
        self.on_change()

    # ---------- 拖拽排序 ----------
    def _fwd_press(self, gpos) -> None:
        if self._on_drag_press:
            self._on_drag_press(self, gpos)

    def _fwd_move(self, gpos) -> None:
        if self._on_drag_move:
            self._on_drag_move(self, gpos)

    def _fwd_release(self, gpos) -> None:
        if self._on_drag_release:
            self._on_drag_release(self, gpos)

    def set_drag_visual(self, on: bool) -> None:
        if on:
            self.setStyleSheet(
                "ItemChip { background: #0A0A0A;"
                " border: 1px solid rgba(78,163,255,190); border-radius: 18px; }"
            )
        else:
            self.setStyleSheet(
                "ItemChip { background: #0A0A0A; border: 1px solid rgba(255,255,255,0.14);"
                " border-radius: 18px; }"
                " ItemChip:hover { background: #121212; }"
            )

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._fwd_press(event.globalPosition().toPoint())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._fwd_move(event.globalPosition().toPoint())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._fwd_release(event.globalPosition().toPoint())
            event.accept()
            return
        super().mouseReleaseEvent(event)


class AddChip(QFrame):
    """虚线胶囊：＋ 添加标签。"""

    def __init__(self, on_add, parent=None) -> None:
        super().__init__(parent)
        self._on_add = on_add
        self.setFixedHeight(36)
        self.setStyleSheet(
            "AddChip { background: rgba(255,255,255,0.03);"
            " border: 1px dashed rgba(255,255,255,0.24); border-radius: 18px; }"
            " AddChip:hover { background: rgba(255,255,255,0.06); }"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 8, 0)
        lay.setSpacing(8)
        self.btn = QPushButton("＋ 添加标签")
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; color: #A1A19A;"
            " font-size: 11px; } QPushButton:hover { color: #F4F4F0; }"
        )
        self.btn.clicked.connect(self._show_edit)
        lay.addWidget(self.btn)
        self.edit = EscapeLineEdit()
        self.edit.setPlaceholderText("回车添加，Esc 取消")
        self.edit.setFixedHeight(26)
        self.edit.setStyleSheet(
            "QLineEdit { background: #151515; color: #F4F4F0;"
            " border: 1px solid rgba(255,255,255,0.22); border-radius: 13px;"
            " padding: 0 10px; font-size: 11px; }"
        )
        self.edit.returnPressed.connect(self._commit)
        self.edit.escapePressed.connect(self._cancel)
        self.edit.hide()
        lay.addWidget(self.edit, 1)

    def _show_edit(self) -> None:
        self.btn.hide()
        self.edit.clear()
        self.edit.show()
        self.edit.setFocus()

    def _cancel(self) -> None:
        self.edit.hide()
        self.btn.show()

    def _commit(self) -> None:
        title = self.edit.text().strip()
        self._cancel()
        if title:
            self._on_add(title)


class CornerHandle(QWidget):
    """四角缩放热区（不可见，鼠标悬停出现缩放光标）。"""

    pressed = Signal(object)
    moved = Signal(object)
    released = Signal(object)

    def __init__(self, corner: str, parent=None) -> None:
        super().__init__(parent)
        self.corner = corner
        self.setFixedSize(HANDLE, HANDLE)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor if corner in ("tl", "br")
                       else Qt.CursorShape.SizeBDiagCursor)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.pressed.emit(event.globalPosition().toPoint())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.moved.emit(event.globalPosition().toPoint())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.released.emit(event.globalPosition().toPoint())
        super().mouseReleaseEvent(event)

class TableWindow(QWidget):
    """学习计划表格独立窗口（可手动关闭、四角缩放、位置记忆）。"""

    closed = Signal()

    def __init__(self, cfg: Config, parent=None) -> None:
        super().__init__(parent)
        self.cfg = cfg
        self._dragging = False
        self._press_global = None
        self._press_win = None
        self._resizing = None
        self._rs_press = None
        self._rs_geo = None
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if cfg.topmost:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.setWindowTitle("学习计划")
        self.setMinimumSize(TABLE_MIN_W, TABLE_MIN_H)
        self.setMaximumSize(TABLE_MAX_W, TABLE_MAX_H)
        sz = cfg.table_size if (isinstance(cfg.table_size, list) and len(cfg.table_size) == 2) else [760, 440]
        self.resize(max(TABLE_MIN_W, min(int(sz[0]), TABLE_MAX_W)),
                    max(TABLE_MIN_H, min(int(sz[1]), TABLE_MAX_H)))
        self._build_ui()
        self._apply_layout()
        self._apply_pos()

    # ---------- UI ----------
    def _build_ui(self) -> None:
        self.title_label = ClickLabel("学习计划")
        f = QFont(FONT_FAMILY, 10, QFont.Weight.Bold)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        self.title_label.setFont(f)
        self.title_label.setStyleSheet(f"color: {skin.TEXT_WEAK2}; background: transparent;")
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.title_label.setParent(self)

        self.btn_close = IconButton("close", "关闭表格", parent=self)
        self.btn_close.clicked.connect(self.close)

        self.table = QTableWidget(len(TABLE_DATA), len(TABLE_HEADERS), self)
        self.table.setHorizontalHeaderLabels(TABLE_HEADERS)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setShowGrid(True)
        self.table.setStyleSheet(
            "QTableWidget { background: transparent; border: none;"
            " gridline-color: rgba(255,255,255,26); color: #F4F4F0; }"
            "QTableWidget::item { background: transparent; border: none; padding: 3px;"
            " font-size: 9px; }"
            "QHeaderView::section { background: #0E0E0E; color: #D4D4CE; border: none;"
            " border-bottom: 1px solid rgba(255,255,255,40); padding: 4px; font-size: 9px; }"
            "QTableCornerButton::section { background: #0E0E0E; border: none; }"
            "QScrollBar:vertical { background: transparent; width: 6px; margin: 2px; }"
            "QScrollBar::handle:vertical { background: rgba(255,255,255,42);"
            " border-radius: 3px; min-height: 24px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
            "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }"
        )
        font = QFont(FONT_FAMILY, 9)
        for r, row in enumerate(TABLE_DATA):
            for c, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setFont(font)
                item.setForeground(QColor(skin.TEXT_MAIN))
                self.table.setItem(r, c, item)
        self.table.itemClicked.connect(self._on_table_click)

        self._handles: dict[str, CornerHandle] = {}
        for corner in ("tl", "tr", "bl", "br"):
            h = CornerHandle(corner, self)
            h.pressed.connect(lambda p, c=corner: self._start_resize(c, p))
            h.moved.connect(lambda p, c=corner: self._do_resize(c, p))
            h.released.connect(lambda p, c=corner: self._end_resize(c))
            self._handles[corner] = h

    def _apply_layout(self) -> None:
        W, H = self.width(), self.height()
        top = skin.TOPBAR_MARGIN
        self.btn_close.move(W - 8 - TOPBAR_ICON, top + (skin.TOPBAR_H - TOPBAR_ICON) // 2)
        tw = self.title_label.fontMetrics().horizontalAdvance(self.title_label.text()) + 4
        self.title_label.setFixedSize(tw, 18)
        self.title_label.move(14, top + (skin.TOPBAR_H - 18) // 2)
        list_top = top + skin.TOPBAR_H + 6
        self.table.setGeometry(8, list_top, W - 16, H - 8 - list_top)
        self._handles["tl"].move(0, 0)
        self._handles["tr"].move(W - HANDLE, 0)
        self._handles["bl"].move(0, H - HANDLE)
        self._handles["br"].move(W - HANDLE, H - HANDLE)

    def _apply_pos(self) -> None:
        screen = QApplication.primaryScreen()
        g = screen.availableGeometry()
        if self.cfg.table_pos:
            x, y = int(self.cfg.table_pos[0]), int(self.cfg.table_pos[1])
            if x < g.left() - self.width() + 60 or x > g.right() - 60 \
                    or y < g.top() - 40 or y > g.bottom() - 40:
                self._center()
            else:
                self.move(x, y)
        else:
            self._center()

    def _center(self) -> None:
        g = QApplication.primaryScreen().availableGeometry()
        self.move(g.left() + (g.width() - self.width()) // 2,
                  g.top() + (g.height() - self.height()) // 2)

    # ---------- 表格交互 ----------
    def _on_table_click(self, item: QTableWidgetItem) -> None:
        f = item.font()
        f.setStrikeOut(not f.strikeOut())
        item.setFont(f)
        item.setForeground(QColor(skin.TEXT_WEAK if f.strikeOut() else skin.TEXT_MAIN))

    # ---------- 四角缩放 ----------
    def _start_resize(self, corner, gpos) -> None:
        self._resizing = corner
        self._rs_press = gpos
        self._rs_geo = self.geometry()

    def _do_resize(self, corner, gpos) -> None:
        if not self._resizing:
            return
        d = gpos - self._rs_press
        x, y, w, h = self._rs_geo.x(), self._rs_geo.y(), self._rs_geo.width(), self._rs_geo.height()
        if corner in ("tl", "bl"):
            w = max(TABLE_MIN_W, min(TABLE_MAX_W, self._rs_geo.width() - d.x()))
            x = self._rs_geo.x() + (self._rs_geo.width() - w)
        else:
            w = max(TABLE_MIN_W, min(TABLE_MAX_W, self._rs_geo.width() + d.x()))
        if corner in ("tl", "tr"):
            h = max(TABLE_MIN_H, min(TABLE_MAX_H, self._rs_geo.height() - d.y()))
            y = self._rs_geo.y() + (self._rs_geo.height() - h)
        else:
            h = max(TABLE_MIN_H, min(TABLE_MAX_H, self._rs_geo.height() + d.y()))
        self.setGeometry(x, y, w, h)

    def _end_resize(self, gpos=None) -> None:
        self._resizing = None
        self.cfg.table_size = [self.width(), self.height()]
        self.cfg.table_pos = [self.x(), self.y()]
        self.cfg.save()

    # ---------- 拖拽移动 ----------
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_global = event.globalPosition().toPoint()
            self._press_win = self.pos()
            self._dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._press_global is not None and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._press_global
            if not self._dragging and delta.manhattanLength() >= DRAG_THRESHOLD:
                self._dragging = True
            if self._dragging:
                self.move(self._press_win + delta)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._dragging:
                self._dragging = False
                self.cfg.table_pos = [self.x(), self.y()]
                self.cfg.save()
            self._press_global = None
            self._press_win = None
        super().mouseReleaseEvent(event)

    # ---------- 绘制 / 事件 ----------
    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), skin.BG_RADIUS, skin.BG_RADIUS)
        p.setClipPath(path)
        p.fillRect(rect, QColor(0, 0, 0, skin.BG_ALPHA))
        W = self.width()
        x0 = 8
        y0 = skin.TOPBAR_MARGIN
        w = W - 16
        h = skin.TOPBAR_H
        p.fillRect(QRectF(x0 + 1, y0 + h, w - 2, 2), QColor(0, 0, 0, 80))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(skin.TOPBAR_BG))
        p.drawRoundedRect(QRectF(x0, y0, w, h), 4, 4)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 46), 1))
        p.drawRoundedRect(QRectF(x0 + 0.5, y0 + 0.5, w - 1, h - 1), 4, 4)
        p.setClipping(False)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_handles"):
            self._apply_layout()

    def closeEvent(self, event) -> None:
        self.cfg.table_size = [self.width(), self.height()]
        self.cfg.table_pos = [self.x(), self.y()]
        self.cfg.save()
        self.closed.emit()
        super().closeEvent(event)

class IndicatorDot(QWidget):
    """工业风峰谷指示灯（红=高峰 / 绿=低谷，低饱和）。"""

    hovered = Signal()
    left = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(14, 14)
        self._trough = True
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_trough(self, on: bool) -> None:
        self._trough = on
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(skin.INDICATOR_RING), 1.5))
        p.setBrush(QColor(18, 20, 24))
        p.drawEllipse(QRectF(1, 1, 12, 12))
        color = QColor(skin.TROUGH_GREEN if self._trough else skin.PEAK_RED)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        p.drawEllipse(QRectF(4, 4, 6, 6))
        p.setBrush(QColor(255, 255, 255, 26))
        p.drawEllipse(QRectF(4.5, 3.8, 5, 2.6))

    def enterEvent(self, event) -> None:
        self.hovered.emit()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.left.emit()
        super().leaveEvent(event)


class CountdownPopup(QWidget):
    """流浪地球工业风倒计时弹窗（纯黑冷灰、红竖线分隔、锐利无光晕）。"""

    def __init__(self, cfg: Config) -> None:
        super().__init__(None)
        self._trough = True
        self._hours = 0
        self._hhmm = "00:00"
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if cfg.topmost:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(300, 112)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(200)
        self._hide_timer.timeout.connect(self._do_hide)

    def set_data(self, trough: bool, hours: int, hhmm: str) -> None:
        self._trough = trough
        self._hours = hours
        self._hhmm = hhmm
        self.update()

    def position_near(self, anchor: QWidget) -> None:
        scr = QGuiApplication.screenAt(anchor.mapToGlobal(QPoint(0, 0))) or QApplication.primaryScreen()
        g = scr.availableGeometry()
        ax = anchor.mapToGlobal(QPoint(0, 0)).x()
        ay = anchor.mapToGlobal(QPoint(0, 0)).y()
        aw, ah = anchor.width(), anchor.height()
        right_space = g.right() - (ax + aw)
        left_space = ax - g.left()
        margin = 8
        if right_space >= self.width() + margin or right_space >= left_space:
            x = ax + aw + margin
        else:
            x = ax - margin - self.width()
        x = max(g.left(), min(x, g.right() - self.width()))
        y = ay + ah - self.height()
        y = max(g.top(), min(y, g.bottom() - self.height()))
        self.move(x, y)

    def schedule_hide(self) -> None:
        self._hide_timer.start()

    def cancel_hide(self) -> None:
        self._hide_timer.stop()

    def _do_hide(self) -> None:
        if self.isVisible() and self.geometry().contains(QCursor.pos()):
            return
        self.hide()

    def enterEvent(self, event) -> None:
        self.cancel_hide()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.schedule_hide()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)
        p.setClipPath(path)
        bg = QColor(skin.POPUP_BG)
        bg.setAlpha(skin.BG_ALPHA)
        p.fillRect(rect, bg)
        p.setClipping(False)

        right = self.width() - 20
        red = QColor(skin.POPUP_RED)
        white = QColor("#FFFFFF")

        f_cn = QFont("SimHei", 18, QFont.Weight.Bold)
        f_title = QFont("SimHei", 20, QFont.Weight.Bold)
        f_num = QFont("Bahnschrift", 44, QFont.Weight.Bold)
        f_en = QFont("Bahnschrift", 11, QFont.Weight.Bold)
        f_en.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)

        title = "距离高峰" if self._trough else "距离低谷期"
        p.setFont(f_title)
        p.setPen(white)
        tw = p.fontMetrics().horizontalAdvance(title)
        p.drawText(QRectF(right - tw, 10, tw, 32),
                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, title)

        y2 = 46
        h2 = 50
        p.setFont(f_cn)
        w_hours_cn = p.fontMetrics().horizontalAdvance("小时")
        p.setPen(white)
        p.drawText(QRectF(right - w_hours_cn, y2, w_hours_cn, h2),
                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "小时")
        x = right - w_hours_cn - 12
        x -= 2
        p.setPen(QPen(red, 2))
        p.drawLine(QPointF(x, y2 + 8), QPointF(x, y2 + h2 - 8))
        x -= 12
        p.setFont(f_num)
        p.setPen(red)
        num = str(self._hours)
        w_num = p.fontMetrics().horizontalAdvance(num)
        x -= w_num
        p.drawText(QRectF(x, y2 - 4, w_num, h2),
                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, num)
        x -= 12
        x -= 2
        p.setPen(QPen(red, 2))
        p.drawLine(QPointF(x, y2 + 8), QPointF(x, y2 + h2 - 8))
        x -= 12
        p.setFont(f_cn)
        p.setPen(white)
        w_left = p.fontMetrics().horizontalAdvance("还剩")
        x -= w_left
        p.drawText(QRectF(x, y2, w_left, h2),
                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "还剩")

        tail = "PEAK" if self._trough else "TROUGH"
        en = f"REMAINING {self._hhmm} UNTIL {tail}"
        p.setFont(f_en)
        p.setPen(white)
        ew = p.fontMetrics().horizontalAdvance(en)
        p.drawText(QRectF(right - ew, 90, ew, 18),
                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, en)


class MainWindow(QWidget):
    def __init__(self, cfg: Config, store: ItemStore) -> None:
        super().__init__()
        self.cfg = cfg
        self.store = store
        self.view = "todo"              # todo / done
        self._chips: list[ItemChip] = []
        self._table_win: TableWindow | None = None
        self._dragging = False
        self._press_global = None
        self._press_win = None
        self._resizing = None
        self._rs_press = None
        self._rs_geo = None
        self._quitting = False
        self._drag_chip = None
        self._drag_g0 = None
        self._drag_active = False

        self._edge = cfg.dock_edge
        self._docked = cfg.dock_edge is not None
        self._revealed = False

        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if cfg.topmost:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.setWindowTitle("小签")
        self.setMinimumSize(MIN_W, MIN_H)
        self.setMaximumSize(MAX_W, MAX_H)
        sz = cfg.size if (isinstance(cfg.size, list) and len(cfg.size) == 2) else [WINDOW_W, WINDOW_H]
        self.resize(max(MIN_W, min(int(sz[0]), MAX_W)), max(MIN_H, min(int(sz[1]), MAX_H)))

        self._anim = QPropertyAnimation(self, b"geometry")
        self._dock_timer = QTimer(self)
        self._dock_timer.setInterval(150)
        self._dock_timer.timeout.connect(self._poll_dock)

        self.dot = IndicatorDot(self)
        self.dot.hovered.connect(self._show_popup)
        self.dot.left.connect(self._schedule_popup_hide)
        self.popup = CountdownPopup(self.cfg)
        self.schedule_timer = QTimer(self)
        self.schedule_timer.setInterval(30000)
        self.schedule_timer.timeout.connect(self._refresh_schedule)
        self.schedule_timer.start()

        self._build_ui()
        self._apply_layout()
        self._refresh()
        self._refresh_schedule()
        self._apply_pos()
        if QApplication.platformName() != "offscreen":
            self._setup_tray()
            if self._docked:
                self._dock_timer.start()

    # ---------- UI ----------
    def _build_ui(self) -> None:
        self.title_label = ClickLabel("小签")
        f = QFont(FONT_FAMILY, 10, QFont.Weight.Bold)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        self.title_label.setFont(f)
        self.title_label.setStyleSheet(f"color: {skin.TEXT_WEAK2}; background: transparent;")
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.title_label.setParent(self)

        self.finish_label = DotText("FINISH", clickable=True, parent=self)
        self.finish_label.clicked.connect(self._toggle_view)

        self.btn_table = IconButton("table", "学习计划表格", parent=self)
        self.btn_fold = IconButton("fold", "贴边折叠 / 弹出", parent=self)
        self.btn_pin = IconButton("pin", "置顶：开/关", parent=self)
        self.btn_close = IconButton("close", "收进托盘", parent=self)
        self.btn_table.clicked.connect(self._toggle_table)
        self.btn_fold.clicked.connect(self._toggle_fold)
        self.btn_pin.clicked.connect(self.toggle_topmost)
        self.btn_close.clicked.connect(self.toggle_visible)
        self.btn_pin.setChecked(self.cfg.topmost)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.viewport().setAutoFillBackground(False)
        self.scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollBar:vertical { background: transparent; width: 6px; margin: 2px; }"
            "QScrollBar::handle:vertical { background: rgba(255,255,255,42);"
            " border-radius: 3px; min-height: 24px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
            "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }"
        )
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        self._chips_layout = QVBoxLayout(body)
        self._chips_layout.setContentsMargins(0, 0, 0, 0)
        self._chips_layout.setSpacing(skin.CHIP_GAP)
        self._chips_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(body)

        self.empty_hint = QLabel("", self.scroll.viewport())
        self.empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_hint.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.empty_hint.setStyleSheet(f"color: {skin.TEXT_WEAK}; background: transparent; font-size: 11px;")
        self.empty_hint.hide()

        self.add_chip = AddChip(self._add_item, self)
        self.add_chip.hide()

        self._handles: dict[str, CornerHandle] = {}
        for corner in ("tl", "tr", "bl", "br"):
            h = CornerHandle(corner, self)
            h.pressed.connect(lambda p, c=corner: self._start_resize(c, p))
            h.moved.connect(lambda p, c=corner: self._do_resize(c, p))
            h.released.connect(lambda p, c=corner: self._end_resize(c))
            self._handles[corner] = h

    def _apply_layout(self) -> None:
        W, H = self.width(), self.height()
        top = skin.TOPBAR_MARGIN
        x = W - 8 - TOPBAR_ICON
        for b in (self.btn_close, self.btn_pin, self.btn_fold, self.btn_table):
            b.move(x, top + (skin.TOPBAR_H - TOPBAR_ICON) // 2)
            x -= 30
        tw = self.title_label.fontMetrics().horizontalAdvance(self.title_label.text()) + 4
        self.title_label.setFixedSize(tw, 18)
        self.title_label.move(14, top + (skin.TOPBAR_H - 18) // 2)
        fw, fh = self.finish_label.size_hint()
        self.finish_label.setFixedSize(fw, fh)
        self.finish_label.move(14 + tw + 14, top + (skin.TOPBAR_H - fh) // 2)
        list_top = top + skin.TOPBAR_H + 6
        self.scroll.setGeometry(8, list_top, W - 16, H - 8 - list_top)
        self.empty_hint.setGeometry(self.scroll.viewport().rect())
        self.dot.move(12, H - 8 - self.dot.height())
        self.dot.raise_()
        self._handles["tl"].move(0, 0)
        self._handles["tr"].move(W - HANDLE, 0)
        self._handles["bl"].move(0, H - HANDLE)
        self._handles["br"].move(W - HANDLE, H - HANDLE)

    def _refresh(self) -> None:
        while self._chips_layout.count():
            item = self._chips_layout.takeAt(0)
            w = item.widget()
            if w is not None and w is not self.add_chip:
                w.deleteLater()
        self._chips.clear()
        visible = [it for it in self.store.items if (it.done) == (self.view == "done")]
        for it in visible:
            chip = ItemChip(it, self.store, self._refresh,
                            self._drag_press, self._drag_move, self._drag_release)
            self._chips.append(chip)
            self._chips_layout.addWidget(chip)
        if self.view == "todo":
            self._chips_layout.addWidget(self.add_chip)
            self.add_chip.show()
            if not visible:
                self.empty_hint.setText("都完成啦，去 Finish 看看")
                self.empty_hint.show()
                self.empty_hint.raise_()
            else:
                self.empty_hint.hide()
        else:
            self.add_chip.hide()
            if not visible:
                self.empty_hint.setText("还没有已完成的标签")
                self.empty_hint.show()
                self.empty_hint.raise_()
            else:
                self.empty_hint.hide()
        self.finish_label.set_text("UNFINISHED" if self.view == "done" else "FINISH")
        self.empty_hint.setGeometry(self.scroll.viewport().rect())

    # ---------- 拖拽排序 ----------
    def _drag_press(self, chip, gpos) -> None:
        self._drag_chip = chip
        self._drag_g0 = gpos
        self._drag_active = False

    def _drag_move(self, chip, gpos) -> None:
        if chip is not self._drag_chip:
            return
        if not self._drag_active:
            d = gpos - self._drag_g0
            if d.manhattanLength() < 8 or abs(d.y()) <= abs(d.x()):
                return
            self._drag_active = True
            chip.set_drag_visual(True)
        before = 0
        for c in self._chips:
            if c is chip:
                continue
            r = c.mapToGlobal(QPoint(0, 0))
            if gpos.y() > r.y() + c.height() // 2:
                before += 1
        cur = self._chips.index(chip)
        if before == cur:
            return
        self._chips.pop(cur)
        self._chips.insert(before, chip)
        self._chips_layout.removeWidget(chip)
        self._chips_layout.insertWidget(before, chip)
        item = chip.item
        items = self.store.items
        cur_s = items.index(item)
        items.pop(cur_s)
        disp = 0
        ins = len(items)
        for i, it in enumerate(items):
            if (it.done) == (self.view == "done"):
                if disp == before:
                    ins = i
                    break
                disp += 1
        items.insert(ins, item)
        self.store.save()

    def _drag_release(self, chip, gpos) -> None:
        if chip is self._drag_chip:
            self._drag_chip = None
            self._drag_active = False
            chip.set_drag_visual(False)

    # ---------- 峰谷倒计时 ----------
    def _refresh_schedule(self) -> None:
        now = datetime.now()
        trough = schedule.is_trough(now)
        self.dot.set_trough(trough)
        target = schedule.next_peak_start(now) if trough else schedule.next_trough_start(now)
        hours, hhmm = schedule.remaining_to(target, now)
        self.popup.set_data(trough, hours, hhmm)

    def _show_popup(self) -> None:
        self._refresh_schedule()
        self.popup.position_near(self)
        self.popup.show()
        self.popup.raise_()
        self.popup.cancel_hide()

    def _schedule_popup_hide(self) -> None:
        self.popup.schedule_hide()

    def moveEvent(self, event) -> None:
        super().moveEvent(event)
        if hasattr(self, "popup") and self.popup.isVisible():
            self.popup.position_near(self)

    # ---------- 表格独立窗口 ----------
    def _toggle_table(self) -> None:
        if self._table_win is None:
            self._table_win = TableWindow(self.cfg)
            self._table_win.closed.connect(self._on_table_closed)
        if self._table_win.isVisible():
            self._table_win.hide()
            self.btn_table.setChecked(False)
        else:
            self._table_win.show()
            self._table_win.raise_()
            self.btn_table.setChecked(True)

    def _on_table_closed(self) -> None:
        self.btn_table.setChecked(False)

    # ---------- 视图 / 数据 ----------
    def _toggle_view(self) -> None:
        self.view = "done" if self.view == "todo" else "todo"
        self._refresh()

    def _add_item(self, title: str) -> None:
        self.store.add_item(title)
        self.store.save()
        self._refresh()

    def toggle_topmost(self) -> None:
        self.cfg.topmost = not self.cfg.topmost
        self.btn_pin.setChecked(self.cfg.topmost)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.cfg.topmost)
        self.show()
        if self._table_win is not None:
            self._table_win.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.cfg.topmost)
            if self._table_win.isVisible():
                self._table_win.show()
        self.popup.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.cfg.topmost)
        self.cfg.save()
    # ---------- 四角缩放 ----------
    def _start_resize(self, corner, gpos) -> None:
        self._resizing = corner
        self._rs_press = gpos
        self._rs_geo = self.geometry()
        if self._docked:
            self._docked = False
            self._revealed = False
            self._dock_timer.stop()
            self.cfg.dock_edge = None

    def _do_resize(self, corner, gpos) -> None:
        if not self._resizing:
            return
        d = gpos - self._rs_press
        x, y, w, h = self._rs_geo.x(), self._rs_geo.y(), self._rs_geo.width(), self._rs_geo.height()
        if corner in ("tl", "bl"):
            w = max(MIN_W, min(MAX_W, self._rs_geo.width() - d.x()))
            x = self._rs_geo.x() + (self._rs_geo.width() - w)
        else:
            w = max(MIN_W, min(MAX_W, self._rs_geo.width() + d.x()))
        if corner in ("tl", "tr"):
            h = max(MIN_H, min(MAX_H, self._rs_geo.height() - d.y()))
            y = self._rs_geo.y() + (self._rs_geo.height() - h)
        else:
            h = max(MIN_H, min(MAX_H, self._rs_geo.height() + d.y()))
        self.setGeometry(x, y, w, h)

    def _end_resize(self, gpos=None) -> None:
        self._resizing = None
        self.cfg.size = [self.width(), self.height()]
        self.cfg.pos = [self.x(), self.y()]
        self.cfg.save()

    # ---------- 贴边折叠 ----------
    def _screen_for(self, pos=None):
        p = pos if pos is not None else QCursor.pos()
        return QGuiApplication.screenAt(p) or QApplication.primaryScreen()

    def _edge_distances(self, screen):
        g = screen.availableGeometry()
        x, y, w, h = self.x(), self.y(), self.width(), self.height()
        return {
            "left": x - g.left(),
            "right": g.right() - (x + w),
            "top": y - g.top(),
            "bottom": g.bottom() - (y + h),
        }

    def _nearest_edge(self, screen):
        d = self._edge_distances(screen)
        edge = min(d, key=d.get)
        return edge, d[edge]

    def _animate_to(self, x: int, y: int, ms: int) -> None:
        self._anim.stop()
        self._anim.setDuration(ms)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.setStartValue(self.geometry())
        self._anim.setEndValue(QRect(x, y, self.width(), self.height()))
        self._anim.start()

    def _dock(self, edge: str, animate: bool = True) -> None:
        screen = self._screen_for()
        g = screen.availableGeometry()
        x, y = self.x(), self.y()
        if edge == "left":
            x = g.left() - (self.width() - skin.TAB_WIDTH)
        elif edge == "right":
            x = g.right() - skin.TAB_WIDTH + 1
        elif edge == "top":
            y = g.top() - (self.height() - skin.TAB_WIDTH)
        else:
            y = g.bottom() - skin.TAB_WIDTH + 1
        # 只钳制与贴边方向垂直的坐标轴（贴边方向允许窗口主体移出屏幕）
        if edge in ("left", "right"):
            y = max(g.top(), min(y, g.bottom() - self.height() + 1))
        else:
            x = max(g.left(), min(x, g.right() - self.width() + 1))
        self._edge = edge
        self._docked = True
        self._revealed = False
        self.cfg.dock_edge = edge
        self.cfg.pos = [x, y]
        self.cfg.save()
        if animate:
            self._animate_to(x, y, skin.DOCK_MS)
        else:
            self.move(x, y)
        self._dock_timer.start()

    def _reveal(self, animate: bool = True) -> None:
        if not self._docked:
            return
        screen = self._screen_for()
        g = screen.availableGeometry()
        x, y = self.x(), self.y()
        if self._edge == "left":
            x = g.left()
        elif self._edge == "right":
            x = g.right() - self.width() + 1
        elif self._edge == "top":
            y = g.top()
        else:
            y = g.bottom() - self.height() + 1
        self._revealed = True
        if animate:
            self._animate_to(x, y, skin.REVEAL_MS)
        else:
            self.move(x, y)
        self.cfg.pos = [x, y]
        self.cfg.save()

    def _poll_dock(self) -> None:
        if not self._docked or self._dragging:
            return
        pos = QCursor.pos()
        scr = self._screen_for(pos)
        g = scr.availableGeometry()
        if self._edge == "left":
            strip = QRect(g.left(), self.y(), skin.TAB_WIDTH + 10, self.height())
        elif self._edge == "right":
            strip = QRect(g.right() - skin.TAB_WIDTH - 9, self.y(), skin.TAB_WIDTH + 10, self.height())
        elif self._edge == "top":
            strip = QRect(self.x(), g.top(), self.width(), skin.TAB_WIDTH + 10)
        else:
            strip = QRect(self.x(), g.bottom() - skin.TAB_WIDTH - 9, self.width(), skin.TAB_WIDTH + 10)
        inside_win = self.geometry().contains(pos)
        if self._revealed:
            if not inside_win and not strip.contains(pos):
                self._dock(self._edge)
        elif inside_win or strip.contains(pos):
            self._reveal()

    def _toggle_fold(self) -> None:
        if self._docked and not self._revealed:
            self._reveal()
        elif self._docked:
            self._dock(self._edge)
        else:
            edge, _ = self._nearest_edge(self._screen_for())
            self._dock(edge)

    # ---------- 位置 / 拖拽 ----------
    def _apply_pos(self) -> None:
        if self.cfg.dock_edge:
            return
        screen = QApplication.primaryScreen()
        g = screen.availableGeometry()
        if self.cfg.pos:
            x, y = int(self.cfg.pos[0]), int(self.cfg.pos[1])
            if x < g.left() - self.width() + 40 or x > g.right() - 40 \
                    or y < g.top() - 40 or y > g.bottom() - 40:
                self._center()
            else:
                self.move(x, y)
        else:
            self._center()

    def _center(self) -> None:
        g = QApplication.primaryScreen().availableGeometry()
        self.move(g.left() + (g.width() - self.width()) // 2,
                  g.top() + (g.height() - self.height()) // 2)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._docked and not self._revealed:
                self._reveal()
                return
            self._press_global = event.globalPosition().toPoint()
            self._press_win = self.pos()
            self._dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._press_global is not None and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._press_global
            if not self._dragging:
                if delta.manhattanLength() >= DRAG_THRESHOLD:
                    self._dragging = True
                    if self._docked:
                        self._docked = False
                        self._revealed = False
                        self._dock_timer.stop()
                        self.cfg.dock_edge = None
            if self._dragging:
                self.move(self._press_win + delta)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._dragging:
                self._dragging = False
                screen = self._screen_for()
                edge, dist = self._nearest_edge(screen)
                if dist <= skin.DOCK_SNAP:
                    self._dock(edge)
                else:
                    self.cfg.pos = [self.x(), self.y()]
                    self.cfg.save()
            self._press_global = None
            self._press_win = None
        super().mouseReleaseEvent(event)

    # ---------- 托盘 ----------
    def _make_icon(self) -> QIcon:
        pm = QPixmap(64, 64)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(skin.STATUS_BLUE))
        p.drawRoundedRect(QRectF(6, 6, 52, 52), 12, 12)
        pen = QPen(QColor(255, 255, 255), 4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(18, 33), QPointF(28, 43))
        p.drawLine(QPointF(28, 43), QPointF(47, 23))
        p.end()
        return QIcon(pm)

    def _setup_tray(self) -> None:
        self.tray = QSystemTrayIcon(self._make_icon(), self)
        self.tray.setToolTip("小签")
        menu = QMenu()
        menu.addAction("显示 / 隐藏", self.toggle_visible)
        menu.addSeparator()
        menu.addAction("退出", self._quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger,
                      QSystemTrayIcon.ActivationReason.DoubleClick):
            self.toggle_visible()

    def toggle_visible(self) -> None:
        if self.isVisible():
            self._dock_timer.stop()
            if self._table_win is not None:
                self._table_win.hide()
            self.popup.hide()
            self.hide()
        else:
            self.show()
            if self._docked:
                self._dock_timer.start()

    def _quit(self) -> None:
        self._quitting = True
        self._dock_timer.stop()
        if self._table_win is not None:
            self._table_win.close()
        self.popup.close()
        self.cfg.pos = [self.x(), self.y()]
        self.cfg.save()
        self.store.save()
        QApplication.instance().quit()

    # ---------- 绘制 / 事件 ----------
    def _draw_topbar(self, p: QPainter) -> None:
        W = self.width()
        x0 = 8
        y0 = skin.TOPBAR_MARGIN
        w = W - 16
        h = skin.TOPBAR_H
        p.fillRect(QRectF(x0 + 1, y0 + h, w - 2, 2), QColor(0, 0, 0, 80))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(skin.TOPBAR_BG))
        p.drawRoundedRect(QRectF(x0, y0, w, h), 4, 4)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 46), 1))
        p.drawRoundedRect(QRectF(x0 + 0.5, y0 + 0.5, w - 1, h - 1), 4, 4)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), skin.BG_RADIUS, skin.BG_RADIUS)
        p.setClipPath(path)
        p.fillRect(rect, QColor(0, 0, 0, skin.BG_ALPHA))
        self._draw_topbar(p)
        p.setClipping(False)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_handles"):
            self._apply_layout()

    def closeEvent(self, event) -> None:
        if not self._quitting:
            self.hide()
            event.ignore()
            return
        self.cfg.pos = [self.x(), self.y()]
        self.cfg.save()
        super().closeEvent(event)