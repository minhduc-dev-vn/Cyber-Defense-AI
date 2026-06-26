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

# Modern dashboard palette. These aliases intentionally override the older
# constants inside the UI layer only; algorithm/core code is untouched.
COLOR_BG = (3, 9, 17)
COLOR_PANEL_BG = (7, 18, 32)
COLOR_PANEL_BORDER = (35, 58, 82)
COLOR_ACCENT = (116, 195, 255)
COLOR_ACCENT_SOFT = (69, 128, 205)
COLOR_PANEL_HIGHLIGHT = (72, 124, 170)
COLOR_TEXT_PRIMARY = (252, 254, 255)
COLOR_TEXT_SECONDARY = (220, 235, 252)
COLOR_TEXT_LOG = (232, 244, 255)
COLOR_TEXT_WARNING = (255, 219, 96)
COLOR_TEXT_ERROR = (255, 104, 104)
COLOR_TEXT_SUCCESS = (92, 246, 145)
COLOR_BTN_NORMAL = (8, 24, 42)
COLOR_BTN_HOVER = (15, 47, 78)
COLOR_BTN_ACTIVE = (15, 83, 170)
COLOR_BTN_DISABLED = (26, 34, 48)
COLOR_BTN_TEXT = (255, 255, 255)
COLOR_EDGE_DEFAULT = (184, 200, 220)
COLOR_EDGE_FINAL = (255, 110, 78)
COLOR_EDGE_BLOCKED = (72, 83, 101)
COLOR_NODE_HACKER = (255, 72, 72)
COLOR_NODE_SERVER = (172, 88, 255)
COLOR_NODE_DATABASE = (178, 84, 245)
COLOR_NODE_FIREWALL = (255, 166, 23)
COLOR_NODE_IDS = (46, 133, 255)
COLOR_NODE_ROUTER = (78, 221, 105)
COLOR_NODE_SWITCH = (83, 213, 112)
COLOR_NODE_PC = (94, 228, 115)
COLOR_NODE_DEFAULT = (82, 159, 255)
COLOR_FRONTIER = (255, 154, 29)
COLOR_EXPLORED = (128, 144, 164)
COLOR_CURRENT = (255, 235, 58)
COLOR_FINAL_PATH = (255, 95, 65)
COLOR_BLOCKED = (74, 87, 105)


# Re-export để các module UI chỉ import từ theme
__all__ = [
    "get_font",
    "get_node_color",
    "COLOR_BG",
    "COLOR_PANEL_BG",
    "COLOR_PANEL_BORDER",
    "COLOR_ACCENT",
    "COLOR_ACCENT_SOFT",
    "COLOR_PANEL_HIGHLIGHT",
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
FONT_SIZE_BOOST = 3


def get_font(size: int = 14, bold: bool = False) -> pygame.font.Font:
    """
    Trả về pygame.font.Font với kích thước cho trước.

    Ưu tiên dùng font hệ thống 'Segoe UI' (Windows) hoặc fallback sang SysFont.
    """
    display_size = max(12, size + FONT_SIZE_BOOST)
    key = (("bold" if bold else "normal"), display_size)
    if key not in _font_cache:
        font = None
        for name in ("Segoe UI", "Tahoma", "Arial"):
            try:
                font = pygame.font.SysFont(name, display_size, bold=bold)
                if font:
                    break
            except Exception:
                continue
        if font is None:
            font = pygame.font.SysFont(None, display_size, bold=bold)
        _font_cache[key] = font
    return _font_cache[key]


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, title: str | None = None) -> None:
    """Draw a glassy dashboard panel."""
    bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    bg.fill((6, 16, 29, 236))
    for i in range(min(40, rect.height)):
        alpha = max(0, 28 - i // 2)
        pygame.draw.line(bg, (29, 69, 105, alpha), (1, i), (rect.width - 2, i))
    surface.blit(bg, rect.topleft)
    pygame.draw.rect(surface, COLOR_PANEL_BORDER, rect, 1, border_radius=6)
    pygame.draw.line(surface, COLOR_PANEL_HIGHLIGHT, (rect.x + 1, rect.y + 1), (rect.right - 2, rect.y + 1), 1)
    pygame.draw.line(surface, (11, 27, 43), (rect.x + 2, rect.bottom - 2), (rect.right - 3, rect.bottom - 2), 1)
    if title:
        font = get_font(13, bold=True)
        title_surf = font.render(title.upper(), True, COLOR_ACCENT)
        surface.blit(title_surf, (rect.x + 14, rect.y + 12))


def draw_text_fit(
    surface: pygame.Surface,
    text: str,
    rect: pygame.Rect,
    color: tuple[int, int, int] = COLOR_TEXT_PRIMARY,
    size: int = 13,
    bold: bool = False,
    align: str = "left",
) -> None:
    """Draw text clipped to rect, reducing size and truncating if needed."""
    if rect.width <= 0 or rect.height <= 0:
        return
    text = str(text)
    font_size = max(10, size)
    while font_size >= 10:
        font = get_font(font_size, bold=bold)
        surf = font.render(text, True, color)
        if surf.get_width() <= rect.width:
            break
        font_size -= 1
    if surf.get_width() > rect.width:
        ellipsis = "..."
        clipped = text
        while clipped and font.render(clipped + ellipsis, True, color).get_width() > rect.width:
            clipped = clipped[:-1]
        text = clipped + ellipsis if clipped else ellipsis
        surf = font.render(text, True, color)
    x = rect.x
    if align == "center":
        x = rect.centerx - surf.get_width() // 2
    elif align == "right":
        x = rect.right - surf.get_width()
    old_clip = surface.get_clip()
    surface.set_clip(rect)
    surface.blit(surf, (x, rect.centery - surf.get_height() // 2))
    surface.set_clip(old_clip)


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
