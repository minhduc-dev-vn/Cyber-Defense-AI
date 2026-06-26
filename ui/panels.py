"""
panels.py — Bảng điều khiển bên trái (Control Panel) và thanh Tab ngang.
"""
from __future__ import annotations

from typing import Callable, List, Optional

import pygame

from core.constants import SPEED_OPTIONS, MAP_NAMES
from core.state import AppState
from ui.theme import (
    get_font,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_BG,
)
from ui.controls import Button, Dropdown, TextInput, TabBar


GROUPS = [
    "Tìm kiếm mù",
    "Tìm kiếm có phí",
    "Tìm kiếm cục bộ",
    "Môi trường phức tạp",
    "CSP - Ràng buộc",
    "Môi trường đối kháng",
]

GROUP_ALGOS = [
    ["BFS", "DFS", "UCS"],
    ["Greedy", "A*", "IDA*"],
    ["Simple HC", "Steepest HC", "Sim. Annealing"],
    ["Backtracking", "Fwd Checking", "Min-Conflicts"],
    ["Belief Unobs.", "Belief Partial", "AND-OR"],
    ["Minimax", "Alpha-Beta", "Expectimax"],
]

GROUP_MAPS = [
    ["pathfinding_basic", "weighted_network"],
    ["weighted_network", "pathfinding_basic"],
    ["defense_optimization"],
    ["csp_segmentation"],
    ["belief_hidden", "belief_partial"],
    ["adversarial_game"],
]

SPEED_KEYS = list(SPEED_OPTIONS.keys())


class ControlPanel:
    """
    Bảng điều khiển bên trái (chia thành các card) + Thanh tab ngang trên cùng.
    """

    def __init__(
        self,
        rect: pygame.Rect,
        app_state: AppState,
        on_start: Callable,
        on_pause: Callable,
        on_step: Callable,
        on_reset: Callable,
        on_compare: Optional[Callable] = None,
        on_algo_change: Optional[Callable] = None,
        on_map_change: Optional[Callable] = None,
    ) -> None:
        self.rect = rect
        self.tab_rect = pygame.Rect(0, 0, 0, 0)  # Sẽ được set qua _build_widgets
        self.app_state = app_state

        self._on_start = on_start
        self._on_pause = on_pause
        self._on_step = on_step
        self._on_reset = on_reset
        self._on_compare = on_compare
        self._on_algo_change = on_algo_change
        self._on_map_change = on_map_change

    def _build_widgets(self) -> None:
        """Được gọi từ app.py sau khi Layout tính toán xong rect."""
        from ui.app import App # hacky way to get layout but let's assume it's passed or we'll get it from rect
        
        # We need the tab_rect, but wait, app.py calls `self.control_panel.rect = layout.control_panel`. 
        # I should add a method to pass tab_rect.
        pass

    def set_rects(self, control_rect: pygame.Rect, tab_rect: pygame.Rect) -> None:
        self.rect = control_rect
        self.tab_rect = tab_rect
        
        # 1. Tab Bar
        self.tab_bar = TabBar(
            self.tab_rect,
            GROUPS,
            selected=self.app_state.selected_group_index,
            on_change=self._on_group_change,
        )

        # 2. Các control trong Left Panel
        pad = int(self.rect.width * 0.06)
        x = self.rect.x + pad
        w = self.rect.width - 2 * pad
        y = self.rect.y + pad

        self.cards: list[tuple[pygame.Rect, str]] = []

        # Card 1: CHỌN THUẬT TOÁN
        self.cards.append((pygame.Rect(x, y, w, 70), "1. CHỌN THUẬT TOÁN"))
        group = self.app_state.selected_group_index
        self.algo_dropdown = Dropdown(
            pygame.Rect(x + 10, y + 30, w - 20, 26),
            GROUP_ALGOS[group],
            selected_index=self.app_state.selected_algo_index,
            on_change=self._on_algo_change_internal,
        )
        y += 85

        # Card 2: CHỌN BẢN ĐỒ
        self.cards.append((pygame.Rect(x, y, w, 70), "2. CHỌN BẢN ĐỒ"))
        maps = GROUP_MAPS[group]
        self.map_dropdown = Dropdown(
            pygame.Rect(x + 10, y + 30, w - 20, 26),
            maps,
            selected_index=0,
            on_change=self._on_map_change_internal,
        )
        y += 85

        # Card 3: THIẾT LẬP
        self.cards.append((pygame.Rect(x, y, w, 130), "3. THIẾT LẬP"))
        cy = y + 30
        
        self.btn_details = Button(
            pygame.Rect(x + 10, cy, w - 20, 26),
            "Hiển thị chi tiết / Compare",
            self._toggle_details,
            color=(50, 70, 100),
        )
        cy += 34
        
        self.speed_dropdown = Dropdown(
            pygame.Rect(x + 10, cy, w - 20, 26),
            SPEED_KEYS,
            selected_index=SPEED_KEYS.index(self.app_state.speed_key),
            on_change=self._on_speed_change,
        )
        cy += 34
        
        self.seed_input = TextInput(
            pygame.Rect(x + 10, cy, w - 20, 26),
            "Seed",
            str(self.app_state.random_seed),
            max_len=8,
        )
        y += 145

        # Card 4: ĐIỀU KHIỂN
        self.cards.append((pygame.Rect(x, y, w, 120), "4. ĐIỀU KHIỂN"))
        cy = y + 30
        bw = (w - 28) // 4
        self.btn_start = Button(pygame.Rect(x + 10, cy, bw, 32), "Start", self._on_start, color=(40, 160, 80))
        self.btn_pause = Button(pygame.Rect(x + 10 + bw + 2, cy, bw, 32), "Pause", self._on_pause, color=(160, 120, 30))
        self.btn_step = Button(pygame.Rect(x + 10 + 2*bw + 4, cy, bw, 32), "Step", self._on_step, color=(40, 80, 160))
        self.btn_reset = Button(pygame.Rect(x + 10 + 3*bw + 6, cy, bw, 32), "Reset", self._on_reset, color=(160, 50, 50))
        cy += 44
        
        if self._on_compare:
            self.btn_compare = Button(
                pygame.Rect(x + 10, cy, w - 20, 30),
                "So sánh nhóm",
                self._on_compare,
                color=(60, 60, 120),
            )
        else:
            self.btn_compare = None


    def _on_group_change(self, idx: int) -> None:
        self.app_state.selected_group_index = idx
        self.app_state.selected_algo_index = 0
        group = idx
        self.algo_dropdown.options = GROUP_ALGOS[group]
        self.algo_dropdown.selected_index = 0
        maps = GROUP_MAPS[group]
        self.map_dropdown.options = maps
        self.map_dropdown.selected_index = 0
        if self._on_algo_change:
            self._on_algo_change(0, GROUP_ALGOS[group][0])
        if self._on_map_change:
            self._on_map_change(0, maps[0])

    def _on_algo_change_internal(self, idx: int, name: str) -> None:
        self.app_state.selected_algo_index = idx
        if self._on_algo_change:
            self._on_algo_change(idx, name)

    def _on_map_change_internal(self, idx: int, name: str) -> None:
        if self._on_map_change:
            self._on_map_change(idx, name)

    def _on_speed_change(self, idx: int, key: str) -> None:
        self.app_state.speed_key = key

    def _toggle_details(self) -> None:
        self.app_state.show_details = not self.app_state.show_details

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not hasattr(self, 'tab_bar'):
            return False
            
        consumed = False
        consumed |= self.tab_bar.handle_event(event)
        
        # Check active drops first because they hover over everything
        if self.algo_dropdown._open:
            if self.algo_dropdown.handle_event(event): return True
        if self.map_dropdown._open:
            if self.map_dropdown.handle_event(event): return True
        if self.speed_dropdown._open:
            if self.speed_dropdown.handle_event(event): return True
            
        consumed |= self.algo_dropdown.handle_event(event)
        consumed |= self.map_dropdown.handle_event(event)
        consumed |= self.btn_start.handle_event(event)
        consumed |= self.btn_pause.handle_event(event)
        consumed |= self.btn_step.handle_event(event)
        consumed |= self.btn_reset.handle_event(event)
        consumed |= self.speed_dropdown.handle_event(event)
        consumed |= self.seed_input.handle_event(event)
        if self.btn_compare:
            consumed |= self.btn_compare.handle_event(event)
        consumed |= self.btn_details.handle_event(event)
        return consumed

    def draw(self, surface: pygame.Surface) -> None:
        if not hasattr(self, 'tab_bar'):
            return
            
        # Nền panel trái
        pygame.draw.rect(surface, COLOR_PANEL_BG, self.rect)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, self.rect, 1)

        # Thanh tab ngang (đặt ở trên cùng)
        self.tab_bar.draw(surface)

        font_lbl = get_font(12, bold=True)
        
        # Vẽ các thẻ (cards)
        for cr, title in self.cards:
            pygame.draw.rect(surface, (20, 26, 40), cr, border_radius=6)
            pygame.draw.rect(surface, COLOR_PANEL_BORDER, cr, 1, border_radius=6)
            ts = font_lbl.render(title, True, (160, 190, 240))
            surface.blit(ts, (cr.x + 10, cr.y + 8))

        # Các components trong thẻ
        self.btn_details.draw(surface)
        self.seed_input.draw(surface)
        
        self.btn_start.draw(surface)
        self.btn_pause.draw(surface)
        self.btn_step.draw(surface)
        self.btn_reset.draw(surface)

        if self.btn_compare:
            self.btn_compare.draw(surface)

        # Dropdown vẽ sau cùng để popup nằm trên
        self.speed_dropdown.draw(surface)
        self.map_dropdown.draw(surface)
        self.algo_dropdown.draw(surface)

