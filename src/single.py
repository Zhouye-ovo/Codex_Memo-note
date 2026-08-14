"""单实例保护：命名互斥体 + 命名事件（纯 ctypes，不写 C 盘）。

- 第一个实例创建互斥体；后续实例发现已存在 → 触发命名事件后退出。
- 第一个实例轮询事件，收到请求就把窗口调出来。
- 互斥/事件名称带 GoalTab 前缀，与仪表盘项目完全隔离。
"""
from __future__ import annotations

import ctypes

MUTEX_NAME = "Local\\GoalTab_TagTab_SingleInstance"
EVENT_NAME = "Local\\GoalTab_TagTab_ShowEvent"
ERROR_ALREADY_EXISTS = 183
WAIT_OBJECT_0 = 0
EVENT_MODIFY_STATE = 0x0002

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_mutex = None
_event = None


def ensure_single_instance() -> bool:
    """True = 本进程是唯一实例；False = 已有实例（已请求其显示），应直接退出。"""
    global _mutex, _event
    _mutex = _kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        _kernel32.SetLastError(0)
        ev = _kernel32.OpenEventW(EVENT_MODIFY_STATE, False, EVENT_NAME)
        if ev:
            _kernel32.SetEvent(ev)
            _kernel32.CloseHandle(ev)
        return False
    _event = _kernel32.CreateEventW(None, False, False, EVENT_NAME)
    return True


def poll_show_request() -> bool:
    """有“显示窗口”请求时返回 True（事件为自动复位，消费后自动清除）。"""
    if not _event:
        return False
    return _kernel32.WaitForSingleObject(_event, 0) == WAIT_OBJECT_0