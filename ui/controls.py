"""Reusable Pygame controls for the dashboard UI."""
from __future__ import annotations

from typing import Callable, List, Optional

import pygame

from ui.theme import (
    COLOR_BTN_ACTIVE,
    COLOR_BTN_DISABLED,
    COLOR_BTN_HOVER,
    COLOR_BTN_NORMAL,
    COLOR_BTN_TEXT,
    COLOR_PANEL_BORDER,
    COLOR_PANEL_HIGHLIGHT,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    draw_text_fit,
    get_font,
)


class Button:
    """Simple clickable button."""

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
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_pressed = self._pressed
            self._pressed = False
            if was_pressed and self.rect.collidepoint(event.pos):
                self.on_click()
                return True
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

        glow_color = self._color or COLOR_BTN_ACTIVE
        if self.enabled:
            for spread, alpha in ((8, 34), (4, 48)):
                glow_rect = self.rect.inflate(spread, spread)
                glow = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(
                    glow,
                    (*glow_color, alpha),
                    glow.get_rect(),
                    border_radius=8 + spread // 2,
                )
                surface.blit(glow, glow_rect.topleft)
        shadow = pygame.Surface((self.rect.width + 4, self.rect.height + 4), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 58))
        surface.blit(shadow, (self.rect.x + 2, self.rect.y + 2))
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        top = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, max(2, self.rect.height // 2))
        top_glow = pygame.Surface((top.width, top.height), pygame.SRCALPHA)
        top_glow.fill((255, 255, 255, 32 if self.enabled else 6))
        surface.blit(top_glow, top.topleft)
        pygame.draw.rect(surface, (82, 146, 205), self.rect, 1, border_radius=6)
        pygame.draw.line(surface, (148, 204, 255), (self.rect.x + 5, self.rect.y + 1), (self.rect.right - 6, self.rect.y + 1), 1)
        draw_text_fit(
            surface,
            self.label,
            self.rect.inflate(-8, 0),
            COLOR_BTN_TEXT if self.enabled else (165, 184, 205),
            size=13,
            bold=self.enabled,
            align="center",
        )


class Dropdown:
    """Dropdown selector."""

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
        if not self.options:
            return ""
        self.selected_index = max(0, min(self.selected_index, len(self.options) - 1))
        return self.options[self.selected_index]

    @property
    def is_open(self) -> bool:
        return self._open

    def close(self) -> None:
        self._open = False
        self._hovered_item = -1

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._open = not self._open
                return True
            if self._open:
                for i, _ in enumerate(self.options):
                    if self._item_rect(i).collidepoint(event.pos):
                        self.selected_index = i
                        self._open = False
                        if self.on_change:
                            self.on_change(i, self.options[i])
                        return True
                self._open = False
        elif event.type == pygame.MOUSEMOTION and self._open:
            self._hovered_item = -1
            for i in range(len(self.options)):
                if self._item_rect(i).collidepoint(event.pos):
                    self._hovered_item = i
        return False

    def _item_rect(self, index: int) -> pygame.Rect:
        return pygame.Rect(self.rect.x, self.rect.bottom + index * self.rect.height, self.rect.width, self.rect.height)

    def menu_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.rect.x,
            self.rect.bottom,
            self.rect.width,
            self.rect.height * len(self.options),
        )

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (4, 13, 24), self.rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, self.rect, 1, border_radius=6)
        pygame.draw.line(surface, COLOR_PANEL_HIGHLIGHT, (self.rect.x + 5, self.rect.y + 1), (self.rect.right - 6, self.rect.y + 1), 1)
        draw_text_fit(surface, self.selected, self.rect.inflate(-34, 0).move(8, 0), COLOR_TEXT_PRIMARY, size=12)
        arrow = "^" if self._open else "v"
        arrow_surf = get_font(12, bold=True).render(arrow, True, COLOR_TEXT_SECONDARY)
        surface.blit(arrow_surf, (self.rect.right - 18, self.rect.centery - arrow_surf.get_height() // 2))

    def draw_menu(self, surface: pygame.Surface) -> None:
        if not self._open:
            return
        menu = self.menu_rect()
        shadow = pygame.Surface((menu.width + 8, menu.height + 8), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 90))
        surface.blit(shadow, (menu.x + 4, menu.y + 4))
        pygame.draw.rect(surface, (4, 13, 24), menu, border_radius=6)
        pygame.draw.rect(surface, (61, 137, 255), menu, 1, border_radius=6)
        for i, opt in enumerate(self.options):
            item_rect = self._item_rect(i)
            bg = (18, 55, 95) if i == self._hovered_item else (4, 13, 24)
            if i == self.selected_index:
                bg = (18, 92, 196)
            inner = item_rect.inflate(-2, -2)
            pygame.draw.rect(surface, bg, inner, border_radius=4)
            draw_text_fit(surface, opt, inner.inflate(-18, 0).move(8, 0), COLOR_TEXT_PRIMARY, size=12)


class TextInput:
    """Tiny text input used for seeds and numeric parameters."""

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
            return self._active
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
        border = (73, 146, 255) if self._active else (43, 74, 108)
        pygame.draw.rect(surface, (4, 13, 24), self.rect, border_radius=6)
        pygame.draw.rect(surface, border, self.rect, 1, border_radius=6)
        draw_text_fit(surface, self.value, self.rect.inflate(-12, 0).move(6, 0), COLOR_TEXT_PRIMARY, size=12)
        if self._active:
            font = get_font(12)
            text_width = min(font.size(self.value)[0], self.rect.width - 18)
            caret_x = self.rect.x + 10 + text_width
            pygame.draw.line(
                surface,
                (130, 190, 255),
                (caret_x, self.rect.y + 8),
                (caret_x, self.rect.bottom - 8),
                1,
            )


class TabBar:
    """Segmented tab bar."""

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
        self._recompute()

    def _recompute(self) -> None:
        gap = 8
        tab_w = (self.rect.width - gap * (len(self.tabs) - 1)) // max(len(self.tabs), 1)
        self._tab_rects = [
            pygame.Rect(self.rect.x + i * (tab_w + gap), self.rect.y, tab_w, self.rect.height)
            for i in range(len(self.tabs))
        ]

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._tab_rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    if self.on_change:
                        self.on_change(i)
                    return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        for i, rect in enumerate(self._tab_rects):
            active = i == self.selected
            bg = (15, 82, 178) if active else (7, 17, 31)
            border = (61, 137, 255) if active else COLOR_PANEL_BORDER
            pygame.draw.rect(surface, bg, rect, border_radius=7)
            pygame.draw.rect(surface, border, rect, 1, border_radius=7)
            draw_text_fit(
                surface,
                self.tabs[i],
                rect.inflate(-12, 0),
                (245, 249, 255) if active else COLOR_TEXT_SECONDARY,
                size=13,
                bold=active,
                align="center",
            )
