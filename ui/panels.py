"""Left control panel for the modern dashboard UI."""
from __future__ import annotations

from typing import Callable, Optional

import pygame

from core.constants import SPEED_OPTIONS
from core.state import AppState
from ui.controls import Button, Dropdown
from ui.theme import (
    COLOR_EDGE_DEFAULT,
    COLOR_NODE_HACKER,
    COLOR_NODE_SERVER,
    COLOR_PANEL_BORDER,
    COLOR_PANEL_HIGHLIGHT,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    draw_panel,
    draw_text_fit,
    get_font,
    get_node_color,
)


GROUPS = [
    "Tìm kiếm mù",
    "Tìm kiếm có phí",
    "Tìm kiếm cục bộ",
    "CSP - Ràng buộc",
    "Môi trường phức tạp",
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

ALGO_LABELS = {
    "BFS": "BFS - Tìm theo chiều rộng",
    "DFS": "DFS - Tìm theo chiều sâu",
    "UCS": "UCS - Chi phí đều",
    "Greedy": "Greedy - Tham lam",
    "A*": "A* - Tìm kiếm A sao",
    "IDA*": "IDA* - Lặp sâu A sao",
    "Simple HC": "Leo đồi đơn giản",
    "Steepest HC": "Leo đồi dốc nhất",
    "Sim. Annealing": "Ủ nhiệt mô phỏng",
    "Backtracking": "Quay lui",
    "Fwd Checking": "Kiểm tra tiến",
    "Min-Conflicts": "Xung đột tối thiểu",
    "Belief Unobs.": "Niềm tin không quan sát",
    "Belief Partial": "Niềm tin quan sát một phần",
    "AND-OR": "Tìm kiếm AND-OR",
    "Minimax": "Minimax",
    "Alpha-Beta": "Cắt tỉa Alpha-Beta",
    "Expectimax": "Expectimax",
}

MAP_LABELS = {
    "pathfinding_basic": "Map 1 - Tìm đường cơ bản",
    "weighted_network": "Map 2 - Mạng có trọng số",
    "defense_optimization": "Map 3 - Tối ưu phòng thủ",
    "csp_segmentation": "Map 4 - Phân vùng CSP",
    "belief_hidden": "Map 5 - Mạng ẩn",
    "belief_partial": "Map 6 - Quan sát một phần",
    "adversarial_game": "Map 7 - Đối kháng",
}


def algo_label(name: str) -> str:
    return ALGO_LABELS.get(name, name)


def map_label(name: str) -> str:
    return MAP_LABELS.get(name, name)


SPEED_KEYS = list(SPEED_OPTIONS.keys())


class ControlPanel:
    """Dashboard sidebar with algorithm, map and playback controls."""

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
        self._algo_buttons: list[Button] = []
        self._speed_buttons: list[Button] = []
        self._build_widgets()

    def _build_widgets(self) -> None:
        x = self.rect.x + 14
        w = self.rect.width - 28
        y = self.rect.y + 36
        group = self.app_state.selected_group_index
        algos = GROUP_ALGOS[group]
        maps = GROUP_MAPS[group]
        try:
            map_index = maps.index(self.app_state.selected_map_name)
        except ValueError:
            map_index = 0

        self.algo_dropdown = Dropdown(
            pygame.Rect(x, y, w, 30),
            [algo_label(name) for name in algos],
            selected_index=min(self.app_state.selected_algo_index, len(algos) - 1),
            on_change=self._on_algo_change_internal,
        )
        y += 38

        self._algo_buttons = []
        btn_gap = 8
        btn_w = (w - btn_gap * 2) // 3
        for idx, label in enumerate(algos[:3]):
            self._algo_buttons.append(
                Button(
                    pygame.Rect(x + idx * (btn_w + btn_gap), y, btn_w, 30),
                    label,
                    lambda i=idx, n=label: self._select_algo_button(i, n),
                    color=(16, 94, 200) if idx == self.app_state.selected_algo_index else (7, 17, 31),
                )
            )
        content_bottom = self.rect.bottom - 12
        controls_total_h = 156
        self._controls_y = max(y + 184, content_bottom - controls_total_h)

        self._map_y = y + 44
        y = self._map_y + 32
        self.map_dropdown = Dropdown(
            pygame.Rect(x, y, w, 30),
            [map_label(name) for name in maps],
            selected_index=map_index,
            on_change=self._on_map_change_internal,
        )
        mini_y = y + 36
        mini_h = max(76, self._controls_y - mini_y - 18)
        self._mini_rect = pygame.Rect(x, mini_y, w, mini_h)

        cy = self._controls_y + 28
        small_gap = 6
        cmd_w = (w - small_gap * 3) // 4
        self.btn_start = Button(pygame.Rect(x, cy, cmd_w, 30), "Chạy", self._on_start, color=(35, 170, 83))
        self.btn_pause = Button(pygame.Rect(x + (cmd_w + small_gap), cy, cmd_w, 30), "Dừng", self._on_pause, color=(204, 155, 24))
        self.btn_step = Button(pygame.Rect(x + 2 * (cmd_w + small_gap), cy, cmd_w, 30), "Bước", self._on_step, color=(32, 101, 218))
        self.btn_reset = Button(pygame.Rect(x + 3 * (cmd_w + small_gap), cy, cmd_w, 30), "Đặt lại", self._on_reset, color=(198, 51, 50))

        self._speed_buttons = []
        speed_y = cy + 56
        speed_w = (w - small_gap * 3) // 4
        for idx, key in enumerate(SPEED_KEYS):
            self._speed_buttons.append(
                Button(
                    pygame.Rect(x + idx * (speed_w + small_gap), speed_y, speed_w, 26),
                    key,
                    lambda k=key: self._set_speed(k),
                    color=(16, 94, 200) if key == self.app_state.speed_key else (7, 17, 31),
                )
            )

        self.btn_compare = None
        if self._on_compare:
            self.btn_compare = Button(
                pygame.Rect(x, speed_y + 38, w, 28),
                "So sánh nhóm",
                self._on_compare,
                color=(9, 31, 55),
            )

    def _select_algo_button(self, idx: int, name: str) -> None:
        self.app_state.selected_algo_index = idx
        self.algo_dropdown.selected_index = idx
        if self._on_algo_change:
            self._on_algo_change(idx, name)
        self._build_widgets()

    def _on_group_change(self, idx: int) -> None:
        self.app_state.selected_group_index = idx
        self.app_state.selected_algo_index = 0
        if self._on_algo_change:
            self._on_algo_change(0, GROUP_ALGOS[idx][0])
        if self._on_map_change:
            self._on_map_change(0, GROUP_MAPS[idx][0])
        self._build_widgets()

    def _on_algo_change_internal(self, idx: int, name: str) -> None:
        self.app_state.selected_algo_index = idx
        if self._on_algo_change:
            group = self.app_state.selected_group_index
            self._on_algo_change(idx, GROUP_ALGOS[group][idx])
        self._build_widgets()

    def _on_map_change_internal(self, idx: int, name: str) -> None:
        if self._on_map_change:
            group = self.app_state.selected_group_index
            self._on_map_change(idx, GROUP_MAPS[group][idx])

    def _set_speed(self, key: str) -> None:
        self.app_state.speed_key = key
        self._build_widgets()

    def handle_event(self, event: pygame.event.Event) -> bool:
        consumed = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.algo_dropdown.rect.collidepoint(event.pos):
                self.map_dropdown.close()
                return self.algo_dropdown.handle_event(event)
            if self.map_dropdown.rect.collidepoint(event.pos):
                self.algo_dropdown.close()
                return self.map_dropdown.handle_event(event)
            if self.algo_dropdown.is_open or self.map_dropdown.is_open:
                consumed = False
                if self.algo_dropdown.is_open:
                    consumed |= self.algo_dropdown.handle_event(event)
                if self.map_dropdown.is_open:
                    consumed |= self.map_dropdown.handle_event(event)
                return True
        if event.type == pygame.MOUSEMOTION:
            if self.algo_dropdown.is_open:
                consumed |= self.algo_dropdown.handle_event(event)
            if self.map_dropdown.is_open:
                consumed |= self.map_dropdown.handle_event(event)
            if consumed:
                return True
        consumed |= self.algo_dropdown.handle_event(event)
        consumed |= self.map_dropdown.handle_event(event)
        for button in self._algo_buttons:
            consumed |= button.handle_event(event)
        for button in self._speed_buttons:
            consumed |= button.handle_event(event)
        for button in (self.btn_start, self.btn_pause, self.btn_step, self.btn_reset):
            consumed |= button.handle_event(event)
        if self.btn_compare:
            consumed |= self.btn_compare.handle_event(event)
        return consumed

    def draw(self, surface: pygame.Surface) -> None:
        draw_panel(surface, self.rect)
        self._draw_section(surface, 1, "CHỌN THUẬT TOÁN", self.rect.y + 14)
        self.algo_dropdown.draw(surface)
        for button in self._algo_buttons:
            button.draw(surface)

        self._draw_divider(surface, self._map_y - 10)
        self._draw_section(surface, 2, "CHỌN BẢN ĐỒ", self._map_y)
        self.map_dropdown.draw(surface)
        self._draw_mini_map(surface)

        self._draw_divider(surface, self._controls_y - 10)
        self._draw_section(surface, 3, "ĐIỀU KHIỂN", self._controls_y)
        for button in (self.btn_start, self.btn_pause, self.btn_step, self.btn_reset):
            button.draw(surface)
        speed_label = get_font(11).render("Tốc độ mô phỏng", True, COLOR_TEXT_SECONDARY)
        surface.blit(speed_label, (self.rect.x + 14, self._speed_buttons[0].rect.y - 18))
        for button in self._speed_buttons:
            button.draw(surface)
        if self.btn_compare:
            self.btn_compare.draw(surface)
        self.algo_dropdown.draw_menu(surface)
        self.map_dropdown.draw_menu(surface)

    def _draw_section(self, surface: pygame.Surface, index: int, title: str, y: int) -> None:
        font = get_font(13, bold=True)
        color = (116, 195, 255)
        text = font.render(f"{index}. {title}", True, color)
        surface.blit(text, (self.rect.x + 14, y))

    def _draw_divider(self, surface: pygame.Surface, y: int) -> None:
        pygame.draw.line(surface, (12, 28, 45), (self.rect.x + 1, y), (self.rect.right - 2, y), 1)
        pygame.draw.line(surface, COLOR_PANEL_HIGHLIGHT, (self.rect.x + 14, y + 1), (self.rect.right - 14, y + 1), 1)

    def _draw_mini_map(self, surface: pygame.Surface) -> None:
        rect = self._mini_rect
        pygame.draw.rect(surface, (5, 15, 29), rect, border_radius=7)
        pygame.draw.rect(surface, (43, 74, 108), rect, 1, border_radius=7)
        map_data = self.app_state.map_data
        if not map_data:
            return
        nodes = map_data.graph.get_all_nodes()
        if not nodes:
            return
        min_x = min(node.position[0] for node in nodes)
        max_x = max(node.position[0] for node in nodes)
        min_y = min(node.position[1] for node in nodes)
        max_y = max(node.position[1] for node in nodes)
        span_x = max(1, max_x - min_x)
        span_y = max(1, max_y - min_y)
        scale = min((rect.width - 36) / span_x, (rect.height - 26) / span_y)

        def pos(node_id: str) -> tuple[int, int]:
            node = map_data.graph.get_node(node_id)
            assert node is not None
            x = rect.x + 18 + int((node.position[0] - min_x) * scale)
            y = rect.y + 13 + int((node.position[1] - min_y) * scale)
            return x, y

        for edge in map_data.graph.get_all_edges():
            pygame.draw.line(surface, COLOR_EDGE_DEFAULT, pos(edge.source), pos(edge.target), 1)
        for node in nodes:
            color = COLOR_NODE_HACKER if node.id == map_data.hacker_start else get_node_color(node.kind)
            if node.id in map_data.goal_nodes:
                color = COLOR_NODE_SERVER
            pygame.draw.circle(surface, color, pos(node.id), 5)
