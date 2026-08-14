"""小签 TagTab：极简桌面标签小组件入口。"""
from __future__ import annotations

import os
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from src.config import Config
from src.single import ensure_single_instance, poll_show_request
from src.store import ItemStore
from src.window import MainWindow


def _on_show_request(win: MainWindow) -> None:
    if poll_show_request():
        if win._docked:
            win._reveal()
        else:
            win.show()
            win.raise_()
        if win._docked:
            win._dock_timer.start()


def main() -> None:
    # --smoke：自动化冒烟测试（offscreen，不弹窗、不碰 C 盘）
    if "--smoke" in sys.argv:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication(sys.argv)
        win = MainWindow(Config.load(), ItemStore.load())
        win.show()
        app.processEvents()
        print("smoke ok")
        return

    # --snapshot [路径] [--edit]：离屏渲染窗口自截图，用于自查界面
    if "--snapshot" in sys.argv:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication(sys.argv)
        win = MainWindow(Config.load(), ItemStore.load())
        win.show()
        app.processEvents()
        idx = sys.argv.index("--snapshot")
        path = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else "snapshot.png"
        if "--edit" in sys.argv:
            for chip in win._chips:
                chip.label.begin_edit()
                break
            app.processEvents()
        win.grab().save(path)
        print("snapshot saved:", path)
        return
    if not ensure_single_instance():
        return

    app = QApplication(sys.argv)
    app.setApplicationName("TagTab")
    cfg = Config.load()
    store = ItemStore.load()
    win = MainWindow(cfg, store)
    win.show()
    show_timer = QTimer()
    show_timer.timeout.connect(lambda: _on_show_request(win))
    show_timer.start(600)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
