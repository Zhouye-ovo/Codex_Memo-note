"""皮肤常量：仪表盘同款配色（DeepSeek 表盘风）。换肤只改本文件。"""
from PySide6.QtGui import QColor

# ---------- 背景：透黑玻璃（45% 不透明度） ----------
BG_ALPHA = 115                      # 45% 黑底
BG_RADIUS = 16
BG_GRAD_TOP = "#080808"
BG_GRAD_BOTTOM = "#0D0D0D"

# ---------- 顶栏（仪表盘同款） ----------
TOPBAR_H = 34
TOPBAR_MARGIN = 4
TOPBAR_BG = "#0E0E0E"

# ---------- 文字（仪表盘暖白灰阶） ----------
TEXT_STRONG = "#FFFFFF"
TEXT_MAIN = "#F4F4F0"
TEXT_LABEL = "#D4D4CE"
TEXT_MID = "#A1A19A"
TEXT_WEAK2 = "#B2B2AC"
TEXT_WEAK = "#7A7A74"

# ---------- 状态色 ----------
STATUS_BLUE = "#4EA3FF"
STATUS_RED = "#FF3B30"
STATUS_GREEN = "#00D084"

# ---------- 胶囊标签 ----------
CHIP_BG = "#0A0A0A"
CHIP_BG_HOVER = "#121212"
CHIP_BORDER = "rgba(255,255,255,0.14)"
CHIP_RADIUS = 18
CHIP_GAP = 8

# ---------- 描边 / 反馈 ----------
BORDER_STRONG = "rgba(255,255,255,0.35)"
BORDER_MED = "rgba(255,255,255,0.18)"
BORDER_WEAK = "rgba(255,255,255,0.08)"
PRESS_BG = "#151515"
HOVER_BG = "rgba(255,255,255,0.07)"

# ---------- 点阵 ----------
DOT_LIT = "#FFFFFF"
DOT_OFF = "rgba(255,255,255,0.10)"

# ---------- 贴边 ----------
TAB_WIDTH = 8
DOCK_SNAP = 20
REVEAL_MS = 180
DOCK_MS = 220

# ---------- 峰谷指示灯 / 倒计时弹窗 ----------
PEAK_RED = "#B05248"          # 低饱和红（高峰）
TROUGH_GREEN = "#4E8A63"      # 低饱和绿（低谷）
POPUP_RED = "#C4504A"         # 弹窗强调红
POPUP_BG = "#0A0B0D"          # 纯黑冷灰底
INDICATOR_RING = "#282B2F"    # 指示灯金属环