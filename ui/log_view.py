"""
log_view.py — Vùng hiển thị log thuật toán có thể cuộn.
"""
from __future__ import annotations

from typing import List

import pygame

from core.event_log import EventLog, LogEntry
from ui.theme import (
    get_font,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_TEXT_LOG,
    COLOR_TEXT_WARNING,
    COLOR_TEXT_ERROR,
    COLOR_TEXT_SUCCESS,
    COLOR_TEXT_SECONDARY,
)


class LogView:
    """Vẽ log sự kiện vào một Rect."""

    LINE_HEIGHT = 16

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self._scroll = 0  # dòng bắt đầu hiển thị
        self._entries: List[LogEntry] = []

    def update(self, log: EventLog) -> None:
        """Cập nhật entries từ EventLog. Tự động cuộn xuống cuối."""
        self._entries = log.get_all()
        max_visible = (self.rect.height - 30) // self.LINE_HEIGHT
        if len(self._entries) > max_visible:
            self._scroll = len(self._entries) - max_visible

    def handle_event(self, event: pygame.event.Event) -> None:
        """Xử lý cuộn chuột trong log panel."""
        if not self.rect.collidepoint(pygame.mouse.get_pos()):
            return
        if event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, self._scroll - event.y * 2)

    def draw(self, surface: pygame.Surface) -> None:
        # Nền panel
        pygame.draw.rect(surface, COLOR_PANEL_BG, self.rect)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, self.rect, 1)

        # Tiêu đề
        font_title = get_font(12, bold=True)
        title_surf = font_title.render("📋 Log thuật toán", True, COLOR_TEXT_SECONDARY)
        surface.blit(title_surf, (self.rect.x + 8, self.rect.y + 6))

        # Clip vùng vẽ
        clip = pygame.Rect(
            self.rect.x + 4,
            self.rect.y + 24,
            self.rect.width - 8,
            self.rect.height - 28,
        )
        surface.set_clip(clip)

        font = get_font(11)
        max_visible = clip.height // self.LINE_HEIGHT
        visible = self._entries[self._scroll: self._scroll + max_visible]

        for i, entry in enumerate(visible):
            color = {
                "info": COLOR_TEXT_LOG,
                "warn": COLOR_TEXT_WARNING,
                "error": COLOR_TEXT_ERROR,
                "success": COLOR_TEXT_SUCCESS,
            }.get(entry.level, COLOR_TEXT_LOG)

            y = clip.y + i * self.LINE_HEIGHT
            text = entry.message[:120]  # giới hạn độ dài dòng
            text_surf = font.render(text, True, color)
            surface.blit(text_surf, (clip.x, y))

        surface.set_clip(None)
