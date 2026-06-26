"""Scrollable algorithm log panel."""
from __future__ import annotations

from typing import List

import pygame

from core.event_log import EventLog, LogEntry
from ui.theme import (
    COLOR_TEXT_ERROR,
    COLOR_TEXT_LOG,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_SUCCESS,
    COLOR_TEXT_WARNING,
    draw_panel,
    get_font,
)


class LogView:
    """Draws algorithm log entries."""

    LINE_HEIGHT = 20

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self._scroll = 0
        self._entries: List[LogEntry] = []

    def update(self, log: EventLog) -> None:
        self._entries = log.get_all()
        max_visible = max(1, (self.rect.height - 42) // self.LINE_HEIGHT)
        if len(self._entries) > max_visible:
            self._scroll = len(self._entries) - max_visible

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.rect.collidepoint(pygame.mouse.get_pos()):
            return
        if event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, self._scroll - event.y * 2)

    def draw(self, surface: pygame.Surface) -> None:
        draw_panel(surface, self.rect, "Nhật ký thuật toán")
        clip = pygame.Rect(self.rect.x + 12, self.rect.y + 40, self.rect.width - 24, self.rect.height - 48)
        old_clip = surface.get_clip()
        surface.set_clip(clip)
        font = get_font(12)
        visual_lines: list[tuple[LogEntry, str, bool]] = []
        text_width = clip.width - 22
        for entry in self._entries:
            wrapped = self._wrap_text(entry.message, font, text_width)
            for line_idx, line in enumerate(wrapped):
                visual_lines.append((entry, line, line_idx == 0))

        max_visible = max(1, clip.height // self.LINE_HEIGHT)
        if len(visual_lines) > max_visible:
            start = max(0, len(visual_lines) - max_visible - max(0, self._scroll - max(0, len(self._entries) - max_visible)))
        else:
            start = 0
        visible = visual_lines[start:start + max_visible]
        for i, (entry, line, is_first_line) in enumerate(visible):
            y = clip.y + i * self.LINE_HEIGHT
            if i % 2 == 0:
                stripe = pygame.Rect(clip.x - 4, y - 1, clip.width + 8, self.LINE_HEIGHT)
                stripe_surf = pygame.Surface((stripe.width, stripe.height), pygame.SRCALPHA)
                stripe_surf.fill((255, 255, 255, 8))
                surface.blit(stripe_surf, stripe.topleft)
            color = {
                "info": COLOR_TEXT_PRIMARY,
                "warn": COLOR_TEXT_WARNING,
                "error": COLOR_TEXT_ERROR,
                "success": COLOR_TEXT_SUCCESS,
            }.get(entry.level, COLOR_TEXT_LOG)
            marker = {
                "info": ">",
                "warn": "!",
                "error": "x",
                "success": "+",
            }.get(entry.level, "-")
            marker_text = marker if is_first_line else " "
            surface.blit(font.render(marker_text, True, COLOR_TEXT_SECONDARY), (clip.x, y))
            surface.blit(font.render(line, True, color), (clip.x + 18, y))
        surface.set_clip(old_clip)

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        words = str(text).split(" ")
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if font.size(candidate)[0] <= max_width:
                current = candidate
                continue
            if current:
                lines.append(current)
            while font.size(word)[0] > max_width and len(word) > 1:
                cut = len(word)
                while cut > 1 and font.size(word[:cut])[0] > max_width:
                    cut -= 1
                lines.append(word[:cut])
                word = word[cut:]
            current = word
        if current:
            lines.append(current)
        return lines or [""]
