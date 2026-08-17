"""DeepSeek 峰谷时段计算（北京时间：高峰 09:00-12:00 / 14:00-18:00，其余为低谷）。"""
from __future__ import annotations

import math
from datetime import datetime, timedelta


def _minutes(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute


def is_trough(dt: datetime) -> bool:
    """True = 当前处于低谷期。"""
    m = _minutes(dt)
    return not ((9 * 60 <= m < 12 * 60) or (14 * 60 <= m < 18 * 60))


def next_trough_start(dt: datetime) -> datetime:
    """下一个低谷期开始时间（12:00 或 18:00）。"""
    m = _minutes(dt)
    if m < 12 * 60:
        return dt.replace(hour=12, minute=0, second=0, microsecond=0)
    if m < 18 * 60:
        return dt.replace(hour=18, minute=0, second=0, microsecond=0)
    return dt.replace(hour=12, minute=0, second=0, microsecond=0) + timedelta(days=1)


def next_peak_start(dt: datetime) -> datetime:
    """下一个高峰开始时间（09:00 或 14:00）。"""
    m = _minutes(dt)
    if m < 9 * 60:
        return dt.replace(hour=9, minute=0, second=0, microsecond=0)
    if m < 14 * 60:
        return dt.replace(hour=14, minute=0, second=0, microsecond=0)
    return dt.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)


def remaining_to(target: datetime, now: datetime | None = None) -> tuple[int, str]:
    """返回 (向上取整的小时数, 精确到分钟并向上取整的 HH:MM)。"""
    now = now or datetime.now()
    secs = max(0, int((target - now).total_seconds()))
    hours = math.ceil(secs / 3600)
    mins = math.ceil(secs / 60)
    return hours, f"{mins // 60:02d}:{mins % 60:02d}"