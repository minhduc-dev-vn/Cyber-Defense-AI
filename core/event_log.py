"""
event_log.py — Quản lý log sự kiện từng bước của thuật toán.

EventLog lưu danh sách message có thể cuộn, xuất text,
và cho UI truy vấn theo bước.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LogEntry:
    """Một dòng log."""
    step: int
    message: str
    level: str = "info"   # "info" | "warn" | "error" | "success"


class EventLog:
    """
    Log sự kiện thuật toán.

    Dùng trong cả thuật toán (ghi) và UI (đọc hiển thị).
    """

    MAX_ENTRIES = 500  # Giới hạn để không tốn RAM

    def __init__(self) -> None:
        self._entries: List[LogEntry] = []
        self._current_step: int = 0

    def clear(self) -> None:
        """Xóa toàn bộ log."""
        self._entries.clear()
        self._current_step = 0

    def log(self, message: str, level: str = "info") -> None:
        """Ghi một dòng log ở bước hiện tại."""
        entry = LogEntry(step=self._current_step, message=message, level=level)
        self._entries.append(entry)
        if len(self._entries) > self.MAX_ENTRIES:
            self._entries.pop(0)

    def info(self, message: str) -> None:
        self.log(message, "info")

    def warn(self, message: str) -> None:
        self.log(message, "warn")

    def error(self, message: str) -> None:
        self.log(message, "error")

    def success(self, message: str) -> None:
        self.log(message, "success")

    def step(self, step_index: int, message: str) -> None:
        """Ghi log với số bước cụ thể."""
        self._current_step = step_index
        self.log(f"[Bước {step_index:03d}] {message}", "info")

    def set_step(self, step_index: int) -> None:
        """Cập nhật bước hiện tại."""
        self._current_step = step_index

    def get_all(self) -> List[LogEntry]:
        """Trả về toàn bộ log."""
        return list(self._entries)

    def get_last_n(self, n: int = 20) -> List[LogEntry]:
        """Trả về n dòng log cuối cùng."""
        return self._entries[-n:]

    def get_entries_for_step(self, step: int) -> List[LogEntry]:
        """Trả về các log entry tại bước step."""
        return [e for e in self._entries if e.step == step]

    def to_text(self) -> str:
        """Xuất toàn bộ log thành text."""
        lines = []
        for entry in self._entries:
            prefix = {
                "info": "ℹ️",
                "warn": "⚠️",
                "error": "❌",
                "success": "✅",
            }.get(entry.level, "•")
            lines.append(f"{prefix} {entry.message}")
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._entries)
