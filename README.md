# 小签 TagTab

> 极简桌面标签小组件：把「标签 / 小目标」钉在桌面上，随时勾选进度；FINISH / UNFINISHED 点阵 LED 一键翻页；学习计划表格独立窗口；拖到屏幕边缘自动折叠成小签（老 QQ 贴边风格）。

## 功能特性

- 扁平标签列表：新增（虚线胶囊“＋ 添加标签”）、勾选完成、双击改名、悬停删除、上下拖拽排序（松手即存）
- FINISH ↔ UNFINISHED 翻页：完成项自动移入已完成页，取消勾选回到未完成页
- 学习计划表格（独立窗口）：点击格子文字划线标记 / 恢复；四角缩放；位置尺寸自动记忆
- 主窗四角缩放 + 贴边折叠：拖到屏幕边缘自动吸附成小签，悬停/点击弹出
- 单实例保护：重复启动自动把已有窗口调出来
- 峰谷指示灯 + 倒计时弹窗：左下角工业指示灯（红=DeepSeek 高峰 / 绿=低谷），悬停显示距下一次低谷/高峰的剩余时间（流浪地球工业风排版）
- 美术沿用 DeepSeek 仪表盘项目：45% 透黑玻璃 + 深色顶栏 + 5×7 点阵 LED + 黑色胶囊

## 技术栈

Python 3.11 + PySide6（Qt6），UI 全部 QPainter 自绘，无外部素材。

## 运行（全部在 G 盘，不写 C 盘）

```powershell
cd /d G:\Codex_FXLearn
python -m venv .venv
.\.venv\Scripts\python -m pip install --cache-dir G:\Codex_FXLearn\.pip-cache -r requirements.txt
.\.venv\Scripts\python main.py
```

> 已有 `G:\Codex_desktop-pet\.venv` 时可直接复用：
> `G:\Codex_desktop-pet\.venv\Scripts\python.exe main.py`

## 数据文件

- `items.json`：标签数据（旧版 `goals.json` 启动时自动迁移为扁平格式）
- `config.json`：主窗 / 表格窗的位置、尺寸、贴边、置顶（自动生成，不入库）

## 操作速览

- 顶栏按钮：表格 / 贴边折叠 / 置顶 / 收进托盘
- 双击文字改名；悬停胶囊显示删除；按住上下拖拽排序
- 四角拖拽缩放；拖到屏幕边缘自动贴边，悬停弹出

## 冒烟测试

```powershell
.\.venv\Scripts\python main.py --smoke
```