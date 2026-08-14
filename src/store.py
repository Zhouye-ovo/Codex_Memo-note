"""标签数据：items.json 读写（扁平列表，无层级；旧 goals.json 自动迁移）。"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS_PATH = os.path.join(PROJECT_ROOT, "items.json")
LEGACY_PATH = os.path.join(PROJECT_ROOT, "goals.json")


@dataclass
class Item:
    id: str
    title: str
    done: bool = False


class ItemStore:
    def __init__(self, items: list[Item] | None = None) -> None:
        self.items = items or []
        self.path = ITEMS_PATH

    # ---------- 序列化 ----------
    @classmethod
    def load(cls, path: str = ITEMS_PATH) -> "ItemStore":
        data = None
        for p in (path, LEGACY_PATH):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                break
            except (FileNotFoundError, ValueError, OSError):
                continue
        items: list[Item] = []
        if isinstance(data, dict):
            raw = data.get("items")
            if isinstance(raw, list):
                for it in raw:
                    items.append(cls._make_item(it))
            else:
                # 旧格式迁移：goals → children 平铺，丢弃组名
                for g in data.get("goals", []):
                    for s in g.get("children", []):
                        items.append(cls._make_item(s))
        return cls(items)

    @staticmethod
    def _make_item(raw) -> Item:
        return Item(str(raw.get("id") or uuid.uuid4().hex[:8]),
                    str(raw.get("title", "")),
                    bool(raw.get("done", False)))

    def save(self, path: str | None = None) -> None:
        try:
            with open(path or self.path, "w", encoding="utf-8") as f:
                json.dump({"items": [asdict(i) for i in self.items]}, f,
                          ensure_ascii=False, indent=2)
        except OSError:
            pass

    # ---------- 操作 ----------
    def add_item(self, title: str) -> Item:
        it = Item(id=uuid.uuid4().hex[:8], title=title)
        self.items.append(it)
        return it

    def remove_item(self, item_id: str) -> None:
        self.items = [i for i in self.items if i.id != item_id]

    def rename_item(self, item_id: str, title: str) -> None:
        it = self.find_item(item_id)
        if it:
            it.title = title

    def toggle_item(self, item_id: str) -> None:
        it = self.find_item(item_id)
        if it:
            it.done = not it.done

    def find_item(self, item_id: str) -> Item | None:
        return next((i for i in self.items if i.id == item_id), None)