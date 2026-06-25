"""
controls.py — Các widget điều khiển: Button, Dropdown, Slider, TextInput.

Tất cả widget tự vẽ lên surface và xử lý sự kiện Pygame.
"""
from __future__ import annotations

from typing import Callable, List, Optional

import pygame

from ui.theme import (
    get_font,
    COLOR_BTN_NORMAL,
    COLOR_BTN_HOVER,
    COLOR_BTN_ACTIVE,
    COLOR_BTN_DISABLED,
    COLOR_BTN_TEXT,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)


class Button:
    """Nút bấm đơn giản."""

    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        on_click: Callable[[], None],
        enabled: bool = True,
        tooltip: str = "",
        color: Optional[tuple[int, int, int]] = None,
    ) -> None:
        self.rect = rect
        self.label = label
        self.on_click = on_click
        self.enabled = enabled
        self.tooltip = tooltip
        self._color = color
        self._hovered = False
        self._pressed = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Xử lý sự kiện. Trả về True nếu được click."""
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressed and self.rect.collidepoint(event.pos):
                self._pressed = False
                self.on_click()
                return True
            self._pressed = False
        return False

    def draw(self, surface: pygame.Surface) -> None:
        if not self.enabled:
            color = COLOR_BTN_DISABLED
        elif self._pressed:
            color = COLOR_BTN_ACTIVE
        elif self._hovered:
            color = COLOR_BTN_HOVER
        else:
            color = self._color or COLOR_BTN_NORMAL

        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, self.rect, 1, border_radius=6)

        font = get_font(13, bold=self._pressed)
        text_surf = font.render(self.label, True, COLOR_BTN_TEXT if self.enabled else (100, 100, 120))
        tw, th = text_surf.get_size()
        cx, cy = self.rect.center
        surface.blit(text_surf, (cx - tw // 2, cy - th // 2))


class Dropdown:
    """Dropdown chọn một trong nhiều option."""

    def __init__(
        self,
        rect: pygame.Rect,
        options: List[str],
        selected_index: int = 0,
        on_change: Optional[Callable[[int, str], None]] = None,
    ) -> None:
        self.rect = rect
        self.options = options
        self.selected_index = selected_index
        self.on_change = on_change
        self._open = False
        self._hovered_item = -1

    @property
    def selected(self) -> str:
        if self.options:
            return self.options[self.selected_index]
        return ""

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._open = not self._open
                return True
            if self._open:
                # Kiểm tra click vào item dropdown
                for i, opt in enumerate(self.options):
                    item_rect = self._item_rect(i)
                    if item_rect.collidepoint(event.pos):
                        self.selected_index = i
                        self._open = False
                        if self.on_change:
                            self.on_change(i, opt)
                        return True
                self._open = False
        elif event.type == pygame.MOUSEMOTION and self._open:
            self._hovered_item = -1
            for i in range(len(self.options)):
                if self._item_rect(i).collidepoint(event.pos):
                    self._hovered_item = i
        return False

    def _item_rect(self, index: int) -> pygame.Rect:
        return pygame.Rect(
            self.rect.x,
            self.rect.bottom + index * self.rect.height,
            self.rect.width,
            self.rect.height,
        )

    def draw(self, surface: pygame.Surface) -> None:
        # Nền dropdown
        pygame.draw.rect(surface, COLOR_PANEL_BG, self.rect, border_radius=5)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, self.rect, 1, border_radius=5)

        font = get_font(12)
        label = self.selected[:28] + ("…" if len(self.selected) > 28 else "")
        text_surf = font.render(label, True, COLOR_TEXT_PRIMARY)
        surface.blit(text_surf, (self.rect.x + 6, self.rect.centery - text_surf.get_height() // 2))

        # Mũi tên
        arrow = "▲" if self._open else "▼"
        arr_surf = font.render(arrow, True, COLOR_TEXT_SECONDARY)
        surface.blit(arr_surf, (self.rect.right - 20, self.rect.centery - arr_surf.get_height() // 2))

        # Danh sách options
        if self._open:
            for i, opt in enumerate(self.options):
                ir = self._item_rect(i)
                bg = (60, 80, 130) if i == self._hovered_item else (35, 40, 60)
                if i == self.selected_index:
                    bg = (40, 120, 80)
                pygame.draw.rect(surface, bg, ir)
                pygame.draw.rect(surface, COLOR_PANEL_BORDER, ir, 1)
                opt_surf = font.render(opt[:28], True, COLOR_TEXT_PRIMARY)
                surface.blit(opt_surf, (ir.x + 6, ir.centery - opt_surf.get_height() // 2))


class TextInput:
    """Ô nhập text đơn giản."""

    def __init__(
        self,
        rect: pygame.Rect,
        label: str = "",
        initial: str = "",
        max_len: int = 10,
    ) -> None:
        self.rect = rect
        self.label = label
        self.value = initial
        self.max_len = max_len
        self._active = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self._active:
            if event.key == pygame.K_BACKSPACE:
                self.value = self.value[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                self._active = False
            elif len(self.value) < self.max_len and event.unicode.isprintable():
                self.value += event.unicode
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        border_color = (80, 140, 220) if self._active else COLOR_PANEL_BORDER
        pygame.draw.rect(surface, (28, 32, 50), self.rect, border_radius=4)
        pygame.draw.rect(surface, border_color, self.rect, 1, border_radius=4)
        font = get_font(12)
        val_surf = font.render(self.value, True, COLOR_TEXT_PRIMARY)
        surface.blit(val_surf, (self.rect.x + 5, self.rect.centery - val_surf.get_height() // 2))


class TabBar:
    """Thanh tab chọn nhóm thuật toán."""

    def __init__(
        self,
        rect: pygame.Rect,
        tabs: List[str],
        selected: int = 0,
        on_change: Optional[Callable[[int], None]] = None,
    ) -> None:
        self.rect = rect
        self.tabs = tabs
        self.selected = selected
        self.on_change = on_change
        tab_w = rect.width // max(len(tabs), 1)
        self._tab_rects = [
            pygame.Rect(rect.x + i * tab_w, rect.y, tab_w, rect.height)
            for i in range(len(tabs))
        ]

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, tr in enumerate(self._tab_rects):
                if tr.collidepoint(event.pos):
                    self.selected = i
                    if self.on_change:
                        self.on_change(i)
                    return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        font = get_font(11)
        for i, (tr, tab) in enumerate(zip(self._tab_rects, self.tabs)):
            active = (i == self.selected)
            bg = (50, 90, 160) if active else (30, 36, 56)
            pygame.draw.rect(surface, bg, tr)
            pygame.draw.rect(surface, COLOR_PANEL_BORDER, tr, 1)
            text_surf = font.render(tab, True, (240, 245, 255) if active else COLOR_TEXT_SECONDARY)
            tw, th = text_surf.get_size()
            surface.blit(text_surf, (tr.centerx - tw // 2, tr.centery - th // 2))
