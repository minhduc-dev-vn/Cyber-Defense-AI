"""Responsive dashboard layout for the Pygame UI."""
from __future__ import annotations

import pygame

from core.constants import WINDOW_HEIGHT, WINDOW_WIDTH


class Layout:
    """Computes all dashboard regions used by the UI layer."""

    def __init__(self, width: int = WINDOW_WIDTH, height: int = WINDOW_HEIGHT) -> None:
        self.width = width
        self.height = height
        self._compute()

    def update(self, width: int, height: int) -> None:
        self.width = max(1024, width)
        self.height = max(680, height)
        self._compute()

    def _compute(self) -> None:
        w, h = self.width, self.height
        margin = 10
        gap = 10

        self.title_bar = pygame.Rect(0, 0, w, 44)
        self.top_tabs = pygame.Rect(margin, 52, w - 2 * margin, 50)

        content_top = self.top_tabs.bottom + gap
        content_bottom = h - margin
        bottom_h = max(158, min(210, int(h * 0.22)))
        main_h = content_bottom - content_top - bottom_h - gap

        left_w = max(270, min(330, int(w * 0.18)))
        right_w = max(280, min(330, int(w * 0.20)))
        center_w = w - (2 * margin + left_w + right_w + 2 * gap)
        if center_w < 480:
            right_w = max(240, right_w - (480 - center_w))
            center_w = w - (2 * margin + left_w + right_w + 2 * gap)

        self.control_panel = pygame.Rect(margin, content_top, left_w, main_h)
        self.graph_area = pygame.Rect(self.control_panel.right + gap, content_top, center_w, main_h)
        self.right_panel = pygame.Rect(self.graph_area.right + gap, content_top, right_w, main_h)

        bottom_y = self.graph_area.bottom + gap
        bottom_w = w - 2 * margin
        log_w = max(420, min(620, int(bottom_w * 0.38)))
        self.log_panel = pygame.Rect(margin, bottom_y, log_w, bottom_h)
        self.stats_overlay = pygame.Rect(self.log_panel.right + gap, bottom_y, w - self.log_panel.right - margin, bottom_h)
        self.graph_inner = self.graph_area.inflate(-24, -46)

    def is_in_graph(self, x: int, y: int) -> bool:
        return self.graph_area.collidepoint(x, y)

    def is_in_control(self, x: int, y: int) -> bool:
        return self.control_panel.collidepoint(x, y)
