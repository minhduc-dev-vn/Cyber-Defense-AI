"""
layout.py — Định nghĩa vùng layout của cửa sổ Pygame.

Tính toán Rect cho từng vùng: control panel, graph area, log panel.
Dùng tỷ lệ phần trăm để hỗ trợ responsive.
"""
from __future__ import annotations

import pygame


class Layout:
    """
    Quản lý vị trí và kích thước các vùng UI.

    Cập nhật tự động khi cửa sổ thay đổi kích thước.
    """

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self._compute()

    def update(self, width: int, height: int) -> None:
        """Cập nhật layout khi resize cửa sổ."""
        self.width = width
        self.height = height
        self._compute()

    def _compute(self) -> None:
        """Tính toán Rect cho từng vùng theo tỷ lệ chuẩn."""
        w, h = self.width, self.height

        # Chiều cao các dải ngang
        h_header = int(h * 0.055)
        h_tab = int(h * 0.060)
        h_bottom = int(h * 0.285)
        h_main = h - h_header - h_tab - h_bottom

        # Chiều rộng các cột
        w_left = int(w * 0.17)
        w_right = int(w * 0.22)
        w_center = w - w_left - w_right

        # 1. Header & Tab Bar
        self.header_rect = pygame.Rect(0, 0, w, h_header)
        self.tab_rect = pygame.Rect(0, h_header, w, h_tab)

        # 2. Vùng Main (trái, giữa, phải)
        y_main = h_header + h_tab
        self.control_panel = pygame.Rect(0, y_main, w_left, h_main)
        self.graph_area = pygame.Rect(w_left, y_main, w_center, h_main)
        self.right_panel = pygame.Rect(w_left + w_center, y_main, w_right, h_main)

        # Vùng vẽ đồ thị (bên trong graph_area với margin)
        m = int(w_center * 0.04)  # Margin linh động theo width
        self.graph_inner = pygame.Rect(
            self.graph_area.x + m,
            self.graph_area.y + m,
            self.graph_area.width - 2 * m,
            self.graph_area.height - 2 * m,
        )

        # 3. Vùng Bottom
        y_bottom = h - h_bottom
        
        w_log = int(w * 0.35)
        w_frontier = int(w * 0.25)
        w_result = w - w_log - w_frontier

        self.log_panel = pygame.Rect(0, y_bottom, w_log, h_bottom)
        self.frontier_panel = pygame.Rect(w_log, y_bottom, w_frontier, h_bottom)
        self.result_panel = pygame.Rect(w_log + w_frontier, y_bottom, w_result, h_bottom)
        
        # Overlay stats cũ (có thể không cần dùng nữa do đã có result panel, nhưng giữ lại cho tương thích API tạm thời)
        self.stats_overlay = pygame.Rect(
            self.graph_area.right - 220, self.graph_area.y + 8, 210, 160
        )

    def is_in_graph(self, x: int, y: int) -> bool:
        """Kiểm tra điểm (x, y) có nằm trong vùng đồ thị không."""
        return self.graph_area.collidepoint(x, y)

    def is_in_control(self, x: int, y: int) -> bool:
        return self.control_panel.collidepoint(x, y)

