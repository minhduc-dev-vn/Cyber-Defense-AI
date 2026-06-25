"""
panels.py — Bảng điều khiển bên trái (Control Panel).

Gồm: tab nhóm thuật toán, dropdown chọn algo/map,
nút Start/Pause/Step/Reset, speed, seed, params.
"""
from __future__ import annotations

from typing import Callable, List, Optional

import pygame

from core.constants import SPEED_OPTIONS, MAP_NAMES, CONTROL_PANEL_WIDTH
from core.state import AppState
from ui.theme import (
    get_font,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_BTN_ACTIVE,
)
from ui.controls import Button, Dropdown, TextInput, TabBar


# Danh sách nhóm và thuật toán
GROUPS = [
    "1. Tìm kiếm mù",
    "2. Heuristic",
    "3. Local Search",
    "4. CSP",
    "5. Env phức tạp",
    "6. Đối kháng",
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
    Bảng điều khiển bên trái.

    Callbacks:
      on_start, on_pause, on_step, on_reset, on_compare
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
        self.app_state = app_state

        self._on_start = on_start
        self._on_pause = on_pause
        self._on_step = on_step
        self._on_reset = on_reset
        self._on_compare = on_compare
        self._on_algo_change = on_algo_change
        self._on_map_change = on_map_change

        self._build_widgets()

    def _build_widgets(self) -> None:
        x = self.rect.x + 8
        w = self.rect.width - 16
        y = self.rect.y + 8

        # Tab nhóm
        self.tab_bar = TabBar(
            pygame.Rect(x, y, w, 28),
            ["G1", "G2", "G3", "G4", "G5", "G6"],
            selected=self.app_state.selected_group_index,
            on_change=self._on_group_change,
        )
        y += 34

        # Nhãn nhóm
        self._group_label_y = y
        y += 18

        # Dropdown thuật toán
        self._algo_label_y = y
        y += 16
        group = self.app_state.selected_group_index
        self.algo_dropdown = Dropdown(
            pygame.Rect(x, y, w, 24),
            GROUP_ALGOS[group],
            selected_index=self.app_state.selected_algo_index,
            on_change=self._on_algo_change_internal,
        )
        y += 30

        # Dropdown map
        self._map_label_y = y
        y += 16
        maps = GROUP_MAPS[group]
        self.map_dropdown = Dropdown(
            pygame.Rect(x, y, w, 24),
            maps,
            selected_index=0,
            on_change=self._on_map_change_internal,
        )
        y += 36

        # Nút Start/Pause
        half = (w - 4) // 2
        self.btn_start = Button(
            pygame.Rect(x, y, half, 30),
            "▶ Start",
            self._on_start,
            color=(40, 160, 80),
        )
        self.btn_pause = Button(
            pygame.Rect(x + half + 4, y, half, 30),
            "⏸ Pause",
            self._on_pause,
            color=(160, 120, 30),
        )
        y += 36

        # Nút Step/Reset
        self.btn_step = Button(
            pygame.Rect(x, y, half, 30),
            "→ Step",
            self._on_step,
            color=(40, 80, 160),
        )
        self.btn_reset = Button(
            pygame.Rect(x + half + 4, y, half, 30),
            "↺ Reset",
            self._on_reset,
            color=(140, 40, 40),
        )
        y += 40

        # Speed
        self._speed_label_y = y
        y += 16
        self.speed_dropdown = Dropdown(
            pygame.Rect(x, y, w, 24),
            SPEED_KEYS,
            selected_index=SPEED_KEYS.index(self.app_state.speed_key),
            on_change=self._on_speed_change,
        )
        y += 32

        # Seed
        self._seed_label_y = y
        y += 16
        self.seed_input = TextInput(
            pygame.Rect(x, y, w, 24),
            "Seed",
            str(self.app_state.random_seed),
            max_len=8,
        )
        y += 34

        # Compare
        if self._on_compare:
            self.btn_compare = Button(
                pygame.Rect(x, y, w, 28),
                "📊 So sánh nhóm",
                self._on_compare,
                color=(60, 60, 120),
            )
            y += 36
        else:
            self.btn_compare = None

        # Hiển thị chi tiết
        self.btn_details = Button(
            pygame.Rect(x, y, w, 28),
            "🔍 Chi tiết",
            self._toggle_details,
            color=(50, 70, 100),
        )
        y += 36

        self._extra_y = y  # Vị trí bắt đầu vẽ params bổ sung

    def _on_group_change(self, idx: int) -> None:
        self.app_state.selected_group_index = idx
        self.app_state.selected_algo_index = 0
        # Rebuild algo/map dropdowns
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
        consumed = False
        consumed |= self.tab_bar.handle_event(event)
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
        # Nền panel
        pygame.draw.rect(surface, COLOR_PANEL_BG, self.rect)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, self.rect, 1)

        # Tiêu đề
        font_title = get_font(14, bold=True)
        title = font_title.render("🛡️ Cyber Defense AI", True, (180, 210, 255))
        surface.blit(title, (self.rect.x + 8, self.rect.y + 4 + 8 + 34 - 30))

        font_lbl = get_font(11)

        # Tab bar
        self.tab_bar.draw(surface)

        # Label nhóm
        group = self.app_state.selected_group_index
        group_name = GROUPS[group]
        grp_surf = font_lbl.render(group_name, True, (160, 190, 240))
        surface.blit(grp_surf, (self.rect.x + 8, self._group_label_y))

        # Label + dropdown thuật toán
        surface.blit(font_lbl.render("Thuật toán:", True, COLOR_TEXT_SECONDARY), (self.rect.x + 8, self._algo_label_y))
        self.algo_dropdown.draw(surface)

        # Label + dropdown map
        surface.blit(font_lbl.render("Bản đồ:", True, COLOR_TEXT_SECONDARY), (self.rect.x + 8, self._map_label_y))
        self.map_dropdown.draw(surface)

        # Nút điều khiển
        self.btn_start.draw(surface)
        self.btn_pause.draw(surface)
        self.btn_step.draw(surface)
        self.btn_reset.draw(surface)

        # Speed
        surface.blit(font_lbl.render("Tốc độ:", True, COLOR_TEXT_SECONDARY), (self.rect.x + 8, self._speed_label_y))
        self.speed_dropdown.draw(surface)

        # Seed
        surface.blit(font_lbl.render("Random Seed:", True, COLOR_TEXT_SECONDARY), (self.rect.x + 8, self._seed_label_y))
        self.seed_input.draw(surface)

        # Compare / Details
        if self.btn_compare:
            self.btn_compare.draw(surface)
        self.btn_details.draw(surface)

        # Legend màu sắc
        self._draw_legend(surface)

    def _draw_legend(self, surface: pygame.Surface) -> None:
        """Vẽ legend màu sắc nhỏ ở cuối panel."""
        font = get_font(10)
        from core.constants import (
            COLOR_FRONTIER, COLOR_EXPLORED, COLOR_CURRENT,
            COLOR_FINAL_PATH, COLOR_NODE_HACKER, COLOR_NODE_SERVER,
        )
        items = [
            (COLOR_NODE_HACKER, "Hacker"),
            (COLOR_NODE_SERVER, "Server/DB"),
            (COLOR_FRONTIER, "Frontier"),
            (COLOR_EXPLORED, "Explored"),
            (COLOR_CURRENT, "Hiện tại"),
            (COLOR_FINAL_PATH, "Đường đi"),
        ]
        x = self.rect.x + 6
        y = self.rect.bottom - len(items) * 16 - 6
        for color, label in items:
            pygame.draw.circle(surface, color, (x + 6, y + 7), 5)
            lbl_surf = font.render(label, True, COLOR_TEXT_SECONDARY)
            surface.blit(lbl_surf, (x + 14, y + 1))
            y += 15
