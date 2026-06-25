"""
layout.py — Định nghĩa vùng layout của cửa sổ Pygame.

Tính toán Rect cho từng vùng: control panel, graph area, log panel.
"""
from __future__ import annotations

import pygame
from core.constants import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    CONTROL_PANEL_WIDTH,
    LOG_PANEL_HEIGHT,
    GRAPH_AREA_MARGIN,
)


class Layout:
    """
    Quản lý vị trí và kích thước các vùng UI.

    Cập nhật tự động khi cửa sổ thay đổi kích thước.
    """

    def __init__(self, width: int = WINDOW_WIDTH, height: int = WINDOW_HEIGHT) -> None:
        self.width = width
        self.height = height
        self._compute()

    def update(self, width: int, height: int) -> None:
        """Cập nhật layout khi resize cửa sổ."""
        self.width = width
        self.height = height
        self._compute()

    def _compute(self) -> None:
        """Tính toán Rect cho từng vùng."""
        w, h = self.width, self.height

        # Bảng điều khiển bên trái
        self.control_panel = pygame.Rect(0, 0, CONTROL_PANEL_WIDTH, h)

        # Vùng bên phải (đồ thị + log)
        right_x = CONTROL_PANEL_WIDTH
        right_w = w - CONTROL_PANEL_WIDTH

        # Panel log phía dưới
        log_y = h - LOG_PANEL_HEIGHT
        self.log_panel = pygame.Rect(right_x, log_y, right_w, LOG_PANEL_HEIGHT)

        # Vùng đồ thị chính
        graph_h = h - LOG_PANEL_HEIGHT
        self.graph_area = pygame.Rect(right_x, 0, right_w, graph_h)

        # Vùng vẽ đồ thị (bên trong với margin)
        m = GRAPH_AREA_MARGIN
        self.graph_inner = pygame.Rect(
            right_x + m, m,
            right_w - 2 * m,
            graph_h - 2 * m,
        )

        # Stats ở góc trên phải trong graph_area
        self.stats_overlay = pygame.Rect(
            right_x + right_w - 220, 8, 210, 160
        )

    def is_in_graph(self, x: int, y: int) -> bool:
        """Kiểm tra điểm (x, y) có nằm trong vùng đồ thị không."""
        return self.graph_area.collidepoint(x, y)

    def is_in_control(self, x: int, y: int) -> bool:
        return self.control_panel.collidepoint(x, y)
