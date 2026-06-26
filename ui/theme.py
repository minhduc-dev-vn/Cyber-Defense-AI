"""
theme.py — Màu sắc, font và style nhất quán cho toàn bộ UI.

Import từ constants.py để tránh trùng lặp định nghĩa.
"""
from __future__ import annotations

import pygame
from core.constants import (
    COLOR_BG,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_LOG,
    COLOR_TEXT_WARNING,
    COLOR_TEXT_ERROR,
    COLOR_TEXT_SUCCESS,
    COLOR_BTN_NORMAL,
    COLOR_BTN_HOVER,
    COLOR_BTN_ACTIVE,
    COLOR_BTN_DISABLED,
    COLOR_BTN_TEXT,
    COLOR_NODE_DEFAULT,
    COLOR_NODE_HACKER,
    COLOR_NODE_SERVER,
    COLOR_NODE_DATABASE,
    COLOR_NODE_FIREWALL,
    COLOR_NODE_IDS,
    COLOR_NODE_ROUTER,
    COLOR_NODE_SWITCH,
    COLOR_NODE_PC,
    COLOR_FRONTIER,
    COLOR_EXPLORED,
    COLOR_CURRENT,
    COLOR_FINAL_PATH,
    COLOR_BLOCKED,
    COLOR_EDGE_DEFAULT,
    COLOR_EDGE_FINAL,
    COLOR_EDGE_BLOCKED,
    CSP_ZONE_COLORS,
)


# Re-export để các module UI chỉ import từ theme
__all__ = [
    "get_font",
    "get_node_color",
    "COLOR_BG",
    "COLOR_PANEL_BG",
    "COLOR_PANEL_BORDER",
    "COLOR_TEXT_PRIMARY",
    "COLOR_TEXT_SECONDARY",
    "COLOR_TEXT_LOG",
    "COLOR_TEXT_WARNING",
    "COLOR_TEXT_ERROR",
    "COLOR_TEXT_SUCCESS",
    "COLOR_BTN_NORMAL",
    "COLOR_BTN_HOVER",
    "COLOR_BTN_ACTIVE",
    "COLOR_BTN_DISABLED",
    "COLOR_BTN_TEXT",
    "COLOR_FRONTIER",
    "COLOR_EXPLORED",
    "COLOR_CURRENT",
    "COLOR_FINAL_PATH",
    "COLOR_BLOCKED",
    "COLOR_EDGE_DEFAULT",
    "COLOR_EDGE_FINAL",
    "COLOR_EDGE_BLOCKED",
    "CSP_ZONE_COLORS",
]

# Cache fonts để không tải lại nhiều lần
_font_cache: dict[tuple[str, int], pygame.font.Font] = {}
_UI_SCALE: float = 1.0

def set_ui_scale(scale: float) -> None:
    global _UI_SCALE
    _UI_SCALE = scale

def get_font(size: int = 14, bold: bool = False) -> pygame.font.Font:
    """
    Trả về pygame.font.Font với kích thước cho trước, có nhân với UI_SCALE.
    
    Ưu tiên dùng font hệ thống 'Segoe UI' (Windows) hoặc fallback sang SysFont.
    """
    scaled_size = max(10, int(size * _UI_SCALE))
    key = (("bold" if bold else "normal"), scaled_size)
    if key not in _font_cache:
        try:
            name = "segoeuib" if bold else "segoeui"
            font = pygame.font.SysFont(name, scaled_size)
        except Exception:
            font = pygame.font.SysFont("arial", scaled_size, bold=bold)
        _font_cache[key] = font
    return _font_cache[key]


# Ánh xạ kind → màu node mặc định
_KIND_COLORS: dict[str, tuple[int, int, int]] = {
    "pc": COLOR_NODE_PC,
    "router": COLOR_NODE_ROUTER,
    "switch": COLOR_NODE_SWITCH,
    "firewall": COLOR_NODE_FIREWALL,
    "ids": COLOR_NODE_IDS,
    "server": COLOR_NODE_SERVER,
    "database": COLOR_NODE_DATABASE,
}


def get_node_color(kind: str, state: str = "default") -> tuple[int, int, int]:
    """
    Trả về màu node theo loại và trạng thái thuật toán.

    state: "default" | "hacker" | "frontier" | "explored" | "current" | "final" | "blocked"
    """
    if state == "blocked":
        return COLOR_BLOCKED
    if state == "hacker":
        return COLOR_NODE_HACKER
    if state == "frontier":
        return COLOR_FRONTIER
    if state == "explored":
        return COLOR_EXPLORED
    if state == "current":
        return COLOR_CURRENT
    if state == "final":
        return COLOR_FINAL_PATH
    return _KIND_COLORS.get(kind, COLOR_NODE_DEFAULT)
