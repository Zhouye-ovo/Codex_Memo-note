"""配置读写：config.json 位于项目根目录（G 盘，不写 C 盘）。"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")

EDGES = ("left", "right", "top", "bottom")


@dataclass
class Config:
    pos: list | None = None          # [x, y] 主窗
    size: list | None = None         # [w, h] 主窗
    topmost: bool = True
    dock_edge: str | None = None     # left/right/top/bottom
    table_pos: list | None = None    # [x, y] 表格窗
    table_size: list | None = None   # [w, h] 表格窗

    @classmethod
    def load(cls) -> "Config":
        cfg = cls()
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            cfg.pos = data.get("pos")
            sz = data.get("size")
            if isinstance(sz, list) and len(sz) == 2:
                cfg.size = [int(sz[0]), int(sz[1])]
            cfg.topmost = bool(data.get("topmost", True))
            edge = data.get("dock_edge")
            cfg.dock_edge = edge if edge in EDGES else None
            tpos = data.get("table_pos")
            if isinstance(tpos, list) and len(tpos) == 2:
                cfg.table_pos = [int(tpos[0]), int(tpos[1])]
            tsz = data.get("table_size")
            if isinstance(tsz, list) and len(tsz) == 2:
                cfg.table_size = [int(tsz[0]), int(tsz[1])]
        except (FileNotFoundError, ValueError, TypeError, OSError):
            pass
        return cfg

    def save(self) -> None:
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, ensure_ascii=False, indent=2)
        except OSError:
            pass