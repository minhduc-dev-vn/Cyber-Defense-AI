"""
utils.py — Hàm tiện ích dùng chung trong project.
"""
from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple


def reconstruct_path(parent: dict[str, Optional[str]], goal: str) -> List[str]:
    """
    Tái tạo đường đi từ dict parent.

    parent[node] = node cha trong cây tìm kiếm.
    parent[start] = None.
    """
    path = []
    current: Optional[str] = goal
    while current is not None:
        path.append(current)
        current = parent.get(current)
    path.reverse()
    return path


def distance_2d(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
    """Khoảng cách Euclidean giữa 2 điểm 2D."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def clamp(value: float, lo: float, hi: float) -> float:
    """Kẹp giá trị trong khoảng [lo, hi]."""
    return max(lo, min(hi, value))


def lerp_color(
    c1: Tuple[int, int, int],
    c2: Tuple[int, int, int],
    t: float,
) -> Tuple[int, int, int]:
    """Nội suy tuyến tính giữa 2 màu RGB."""
    t = clamp(t, 0.0, 1.0)
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def make_seeded_random(seed: int) -> random.Random:
    """Tạo đối tượng random với seed cố định (tái lập được)."""
    return random.Random(seed)


def format_path(path: List[str]) -> str:
    """Định dạng đường đi thành chuỗi."""
    if not path:
        return "(không có đường)"
    return " → ".join(path)


def format_cost(cost: float) -> str:
    """Định dạng chi phí."""
    if cost == float("inf"):
        return "∞"
    return f"{cost:.2f}"


def truncate(text: str, max_len: int = 50) -> str:
    """Cắt ngắn chuỗi nếu quá dài."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def wrap_text(text: str, max_chars_per_line: int) -> List[str]:
    """Ngắt text thành nhiều dòng theo giới hạn ký tự."""
    words = text.split()
    lines: List[str] = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars_per_line:
            current = (current + " " + word).strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
