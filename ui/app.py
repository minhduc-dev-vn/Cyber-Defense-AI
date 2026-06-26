"""
app.py - Main Pygame application for Cyber Defense AI.

The UI stays separate from algorithm logic: algorithms only yield StepEvent
objects, while this module handles playback, logging, stats, and controls.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Iterator, Optional

import pygame

from core.constants import FPS, SPEED_OPTIONS, WINDOW_HEIGHT, WINDOW_WIDTH
from core.map_loader import MapData, MapLoadError, load_map
from core.models import AlgorithmMetrics, AlgorithmResult, StepEvent
from core.state import AlgorithmRunState, AppState
from ui.graph_view import GraphView
from ui.layout import Layout
from ui.log_view import LogView
from ui.node_art import draw_network_node
from ui.panels import ControlPanel, GROUPS, GROUP_MAPS, algo_label, map_label
from ui.stats_view import StatsView
from ui.theme import (
    COLOR_BG,
    COLOR_BLOCKED,
    COLOR_CURRENT,
    COLOR_EDGE_DEFAULT,
    COLOR_FRONTIER,
    COLOR_NODE_FIREWALL,
    COLOR_NODE_HACKER,
    COLOR_NODE_IDS,
    COLOR_NODE_SERVER,
    COLOR_PANEL_BORDER,
    COLOR_TEXT_ERROR,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_SUCCESS,
    COLOR_ACCENT,
    COLOR_ACCENT_SOFT,
    COLOR_PANEL_HIGHLIGHT,
    draw_panel,
    draw_text_fit,
    get_font,
    get_node_color,
)


NODE_KIND_LABELS = {
    "pc": "Máy trạm",
    "router": "Bộ định tuyến",
    "switch": "Bộ chuyển mạch",
    "firewall": "Tường lửa",
    "ids": "IDS",
    "server": "Máy chủ",
    "database": "Cơ sở dữ liệu",
}


class App:
    """Pygame application shell for the Cyber Defense AI simulator."""

    TITLE = "Cyber Defense AI - Trình mô phỏng phòng thủ mạng AI"

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(self.TITLE)
        self.screen = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT),
            pygame.RESIZABLE,
        )
        self.clock = pygame.time.Clock()

        self.state = AppState()
        self.state.run_state = AlgorithmRunState()
        self.layout = Layout(WINDOW_WIDTH, WINDOW_HEIGHT)

        self._map_data: Optional[MapData] = None
        self._load_map("pathfinding_basic")

        self.graph_view = GraphView(self.layout.graph_area, self.state)
        if self._map_data:
            self.graph_view.set_graph(self._map_data.graph)

        self.log_view = LogView(self.layout.log_panel)
        self.stats_view = StatsView(self.layout.stats_overlay)

        self.control_panel = ControlPanel(
            self.layout.control_panel,
            self.state,
            on_start=self._on_start,
            on_pause=self._on_pause,
            on_step=self._on_step,
            on_reset=self._on_reset,
            on_compare=self._on_compare,
            on_algo_change=self._on_algo_change,
            on_map_change=self._on_map_change,
        )

        self._step_gen: Optional[Iterator[StepEvent]] = None
        self._last_auto_step: float = 0.0
        self._toast: str = ""
        self._toast_until: float = 0.0

    def _load_map(self, map_name: str) -> bool:
        maps_dir = Path(__file__).parent.parent / "maps"
        path = maps_dir / f"{map_name}.json"
        try:
            self._map_data = load_map(path)
            self.state.map_data = self._map_data
            self.state.selected_map_name = map_name
            self._show_toast(f"Đã tải bản đồ: {map_label(map_name)}")
            return True
        except MapLoadError as exc:
            self._show_toast(f"Tải bản đồ thất bại: {exc}", duration=4.0)
            return False

    def _show_toast(self, msg: str, duration: float = 2.5) -> None:
        self._toast = msg
        self._toast_until = time.time() + duration

    def _on_start(self) -> None:
        run = self.state.run_state
        if run.status == "ready":
            self._build_step_gen()
        if run.status in ("ready", "paused"):
            run.status = "running"

    def _on_pause(self) -> None:
        run = self.state.run_state
        if run.status == "running":
            run.status = "paused"

    def _on_step(self) -> None:
        run = self.state.run_state
        if run.status == "ready":
            self._build_step_gen()
            run.status = "paused"
        if run.status in ("paused", "ready"):
            self._do_one_step()

    def _on_reset(self) -> None:
        self.state.run_state.reset()
        self._step_gen = None
        self.state.selected_node = None
        self.state.compare_mode = False
        self.state.compare_results.clear()
        self.log_view.update(self.state.run_state.log)

    def _on_compare(self) -> None:
        if not self._map_data:
            self._show_toast("Chưa tải bản đồ")
            return

        group = self.state.selected_group_index
        if group not in (0, 1, 2, 3, 4, 5):
            self._show_toast("So sánh đã sẵn sàng cho nhóm 1-6")
            return

        self._step_gen = None
        run = self.state.run_state
        run.reset()

        results = self._run_compare_algorithms(group)
        self.state.compare_results = results
        self.state.compare_mode = True
        run.algorithm_name = "So sánh"
        run.status = "success" if results and all(r.success for r in results) else "failure"
        run.metrics = results[0].metrics if results else None

        table = self._format_compare_log(results)
        for line in table.splitlines():
            run.log.log(line, "info")
        self.log_view.update(run.log)
        self._show_toast("Đã hoàn tất so sánh")

    def _on_algo_change(self, idx: int, name: str) -> None:
        self._on_reset()

    def _on_map_change(self, idx: int, name: str) -> None:
        if self._load_map(name) and self._map_data:
            self.graph_view.set_graph(self._map_data.graph)
        self._on_reset()

    def _algorithm_step_runner(self, group: int, algo_idx: int) -> tuple[str, Callable]:
        if group == 0:
            if algo_idx == 0:
                from algorithms.uninformed.bfs import solve_steps
                return "BFS", solve_steps
            if algo_idx == 1:
                from algorithms.uninformed.dfs import solve_steps
                return "DFS", solve_steps
            from algorithms.uninformed.ucs import solve_steps
            return "UCS", solve_steps

        if group == 1:
            if algo_idx == 0:
                from algorithms.informed.greedy_search import solve_steps
                return "Greedy", solve_steps
            if algo_idx == 1:
                from algorithms.informed.astar import solve_steps
                return "A*", solve_steps
            from algorithms.informed.idastar import solve_steps
            return "IDA*", solve_steps

        if group == 2:
            if algo_idx == 0:
                from algorithms.local_search.simple_hill_climbing import solve_steps
                return "Simple HC", solve_steps
            if algo_idx == 1:
                from algorithms.local_search.steepest_hill_climbing import solve_steps
                return "Steepest HC", solve_steps
            from algorithms.local_search.simulated_annealing import solve_steps
            return "Simulated Annealing", solve_steps

        if group == 3:
            if algo_idx == 0:
                from algorithms.csp.backtracking import solve_steps
                return "Backtracking", solve_steps
            if algo_idx == 1:
                from algorithms.csp.forward_checking import solve_steps
                return "Forward Checking", solve_steps
            from algorithms.csp.min_conflicts import solve_steps
            return "Min-Conflicts", solve_steps

        if group == 4:
            if algo_idx == 0:
                from algorithms.complex_environment.belief_unobservable import solve_steps
                return "Belief Unobservable", solve_steps
            if algo_idx == 1:
                from algorithms.complex_environment.belief_partial_observable import solve_steps
                return "Belief Partial", solve_steps
            from algorithms.complex_environment.and_or_graph import solve_steps
            return "AND-OR", solve_steps

        if group == 5:
            if algo_idx == 0:
                from algorithms.adversarial.minimax import solve_steps
                return "Minimax", solve_steps
            if algo_idx == 1:
                from algorithms.adversarial.alpha_beta import solve_steps
                return "Alpha-Beta", solve_steps
            from algorithms.adversarial.expectimax import solve_steps
            return "Expectimax", solve_steps

        raise ValueError(f"Group {group + 1} is not implemented yet")

    def _algorithm_run_specs(self, group: int) -> list[tuple[str, Callable]]:
        if group == 0:
            from algorithms.uninformed import bfs, dfs, ucs
            return [("BFS", bfs.run), ("DFS", dfs.run), ("UCS", ucs.run)]
        if group == 1:
            from algorithms.informed import astar, greedy_search, idastar
            return [
                ("Greedy", greedy_search.run),
                ("A*", astar.run),
                ("IDA*", idastar.run),
            ]
        if group == 2:
            from algorithms.local_search import (
                simple_hill_climbing,
                simulated_annealing,
                steepest_hill_climbing,
            )
            return [
                ("Simple HC", simple_hill_climbing.run),
                ("Steepest HC", steepest_hill_climbing.run),
                ("Sim. Annealing", simulated_annealing.run),
            ]
        if group == 3:
            from algorithms.csp import backtracking, forward_checking, min_conflicts
            return [
                ("Backtracking", backtracking.run),
                ("Forward Checking", forward_checking.run),
                ("Min-Conflicts", min_conflicts.run),
            ]
        if group == 4:
            from algorithms.complex_environment import (
                and_or_graph,
                belief_partial_observable,
                belief_unobservable,
            )
            return [
                ("Belief Unobs.", belief_unobservable.run),
                ("Belief Partial", belief_partial_observable.run),
                ("AND-OR", and_or_graph.run),
            ]
        if group == 5:
            from algorithms.adversarial import alpha_beta, expectimax, minimax
            return [
                ("Minimax", minimax.run),
                ("Alpha-Beta", alpha_beta.run),
                ("Expectimax", expectimax.run),
            ]
        return []

    def _run_compare_algorithms(self, group: int) -> list[AlgorithmResult]:
        assert self._map_data is not None
        graph = self._map_data.graph
        start = self._map_data.hacker_start
        goals = self._map_data.goal_nodes
        results: list[AlgorithmResult] = []
        seed = self._current_seed()
        for expected_name, run_func in self._algorithm_run_specs(group):
            if group == 2 and expected_name == "Sim. Annealing":
                result = run_func(
                    graph,
                    start,
                    goals,
                    seed=seed,
                    t0=self.state.sa_t0,
                    alpha=self.state.sa_alpha,
                    tmin=self.state.sa_tmin,
                    max_steps=min(self.state.sa_max_steps, 120),
                )
            elif group == 3 and expected_name == "Min-Conflicts":
                result = run_func(graph, start, goals, seed=seed, max_steps=300)
            elif group == 4:
                result = run_func(graph, start, goals, metadata=self._map_data.metadata)
            elif group == 5:
                result = run_func(graph, start, goals, depth=self.state.game_depth)
            else:
                result = run_func(graph, start, goals)
            result.metrics.algorithm = expected_name
            results.append(result)
        return results

    def _format_compare_log(self, results: list[AlgorithmResult]) -> str:
        """Format compare rows for the Vietnamese UI log."""
        header = (
            f"{'Thuật toán':<28} | {'Đạt':>5} | {'Đường':>6} | {'Chi phí':>10} | "
            f"{'Mở rộng':>9} | {'Biên max':>9} | {'Thời gian':>10}"
        )
        rows = [header, "-" * len(header)]
        for result in results:
            metrics = result.metrics
            path_len = max(0, len(metrics.path) - 1)
            rows.append(
                f"{algo_label(metrics.algorithm):<28} | "
                f"{'Có' if metrics.success else 'Không':>5} | "
                f"{path_len:>6} | "
                f"{metrics.total_cost:>10.2f} | "
                f"{metrics.nodes_expanded:>9} | "
                f"{metrics.max_frontier_size:>9} | "
                f"{metrics.time_ms:>8.2f}ms"
            )
        return "\n".join(rows)

    def _build_step_gen(self) -> None:
        run = self.state.run_state
        run.reset()
        self.state.compare_mode = False
        self.state.compare_results.clear()

        if not self._map_data:
            self._show_toast("Chưa tải bản đồ")
            return

        group = self.state.selected_group_index
        algo_idx = self.state.selected_algo_index
        try:
            name, solve_steps = self._algorithm_step_runner(group, algo_idx)
        except ValueError:
            self._show_toast(f"Nhóm {group + 1} sẽ được bổ sung sau")
            run.status = "ready"
            return

        run.algorithm_name = name
        seed = self._current_seed()
        if group == 2 and algo_idx == 2:
            self._step_gen = solve_steps(
                self._map_data.graph,
                self._map_data.hacker_start,
                self._map_data.goal_nodes,
                seed=seed,
                t0=self.state.sa_t0,
                alpha=self.state.sa_alpha,
                tmin=self.state.sa_tmin,
                max_steps=self.state.sa_max_steps,
            )
        elif group == 3 and algo_idx == 2:
            self._step_gen = solve_steps(
                self._map_data.graph,
                self._map_data.hacker_start,
                self._map_data.goal_nodes,
                seed=seed,
                max_steps=300,
            )
        elif group == 4:
            self._step_gen = solve_steps(
                self._map_data.graph,
                self._map_data.hacker_start,
                self._map_data.goal_nodes,
                metadata=self._map_data.metadata,
            )
        elif group == 5:
            self._step_gen = solve_steps(
                self._map_data.graph,
                self._map_data.hacker_start,
                self._map_data.goal_nodes,
                depth=self.state.game_depth,
            )
        else:
            self._step_gen = solve_steps(
                self._map_data.graph,
                self._map_data.hacker_start,
                self._map_data.goal_nodes,
            )
        run.log.clear()
        run.status = "ready"

    def _current_seed(self) -> int:
        value = self.state.random_seed
        self.state.random_seed = value
        return value

    def _do_one_step(self) -> bool:
        run = self.state.run_state
        if self._step_gen is None:
            self._build_step_gen()
            if self._step_gen is None:
                return False

        try:
            step = next(self._step_gen)
        except StopIteration:
            if run.status == "running":
                run.status = "failure"
            self._step_gen = None
            return False

        run.steps.append(step)
        run.current_step_index = len(run.steps) - 1
        run.metrics = self._metrics_from_step(step, success=(step.event_type == "found"))
        run.log.log(step.message, "success" if step.event_type == "found" else "info")
        self.log_view.update(run.log)

        if step.event_type == "found":
            run.status = "success"
            self._step_gen = None
            self._show_toast(f"{algo_label(step.algorithm)} đã hoàn tất")
            return False

        if self._is_failure_step(step):
            run.status = "failure"
            run.metrics = self._metrics_from_step(step, success=False)
            self._step_gen = None
            self._show_toast(f"{algo_label(step.algorithm)} thất bại")
            return False

        return True

    def _is_failure_step(self, step: StepEvent) -> bool:
        if step.event_type == "failure":
            return True
        message = step.message.lower()
        return (
            "khong tim thay" in message
            or "khÃ´ng tÃ¬m tháº¥y" in message
            or "không tìm thấy" in message
            or "no path" in message
            or "no finite heuristic" in message
        )

    def _metrics_from_step(self, step: StepEvent, success: bool) -> AlgorithmMetrics:
        return AlgorithmMetrics(
            algorithm=step.algorithm,
            success=success,
            path=list(step.path),
            total_cost=step.total_cost,
            nodes_expanded=step.nodes_expanded,
            nodes_generated=step.nodes_generated,
            max_frontier_size=step.max_frontier_size,
            num_steps=step.step_index + 1,
            extra=dict(step.data),
        )

    def run(self) -> None:
        running = True
        while running:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.layout.update(*event.size)
                    self._rebuild_views()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        if self.state.run_state.status == "running":
                            self._on_pause()
                        else:
                            self._on_start()
                    elif event.key == pygame.K_s:
                        self._on_step()
                    elif event.key == pygame.K_r:
                        self._on_reset()

                self.control_panel.handle_event(event)
                self._handle_top_nav_event(event)
                self.graph_view.handle_event(event)
                self.log_view.handle_event(event)

            run = self.state.run_state
            if run.status == "running":
                delay = SPEED_OPTIONS.get(self.state.speed_key, 0.6)
                now = time.time()
                if now - self._last_auto_step >= delay:
                    self._last_auto_step = now
                    if not self._do_one_step() and run.status == "running":
                        run.status = "failure"

            self.render_frame()
            pygame.display.flip()

        pygame.quit()

    def render_frame(self) -> None:
        """Render one complete UI frame onto the current screen surface."""
        run = self.state.run_state
        self.screen.fill(COLOR_BG)
        self._draw_header()
        self._draw_top_nav()

        current_step = run.current_step
        hacker_pos = self._map_data.hacker_start if self._map_data else ""
        goals = self._map_data.goal_nodes if self._map_data else []
        self.graph_view.draw(
            self.screen,
            current_step,
            hacker_pos,
            goals,
            graph=self._map_data.graph if self._map_data else None,
        )

        self.stats_view.draw(
            self.screen,
            step=current_step,
            metrics=run.metrics,
            status=run.status,
            show_details=self.state.show_details,
            compare_results=self.state.compare_results if self.state.compare_mode else None,
        )

        self.control_panel.draw(self.screen)
        self.log_view.draw(self.screen)
        self._draw_right_panel()
        self._draw_toast()
        if self._map_data:
            self._draw_map_title()

    def _rebuild_views(self) -> None:
        self.graph_view.rect = self.layout.graph_area
        self.log_view.rect = self.layout.log_panel
        self.stats_view.rect = self.layout.stats_overlay
        self.control_panel.rect = self.layout.control_panel
        self.control_panel._build_widgets()

    def _handle_top_nav_event(self, event: pygame.event.Event) -> bool:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        for idx, rect in enumerate(self._top_nav_rects()):
            if rect.collidepoint(event.pos):
                if idx == self.state.selected_group_index:
                    return True
                self.state.selected_group_index = idx
                self.state.selected_algo_index = 0
                map_name = GROUP_MAPS[idx][0]
                if self._load_map(map_name) and self._map_data:
                    self.graph_view.set_graph(self._map_data.graph)
                self._on_reset()
                self.control_panel._build_widgets()
                return True
        return False

    def _top_nav_rects(self) -> list[pygame.Rect]:
        rect = self.layout.top_tabs
        gap = 10
        tab_w = (rect.width - gap * (len(GROUPS) - 1)) // len(GROUPS)
        return [
            pygame.Rect(rect.x + i * (tab_w + gap), rect.y + 5, tab_w, rect.height - 10)
            for i in range(len(GROUPS))
        ]

    def _draw_header(self) -> None:
        rect = self.layout.title_bar
        pygame.draw.rect(self.screen, (2, 7, 14), rect)
        pygame.draw.line(self.screen, (25, 45, 65), (0, rect.bottom - 1), (rect.right, rect.bottom - 1), 1)
        shield = pygame.Rect(18, 10, 22, 22)
        pygame.draw.polygon(
            self.screen,
            (21, 66, 117),
            [(shield.centerx, shield.y), (shield.right, shield.y + 6), (shield.right - 3, shield.bottom - 4), (shield.centerx, shield.bottom), (shield.x + 3, shield.bottom - 4), (shield.x, shield.y + 6)],
        )
        pygame.draw.polygon(
            self.screen,
            (220, 238, 255),
            [(shield.centerx, shield.y + 5), (shield.centerx + 5, shield.y + 10), (shield.centerx + 2, shield.y + 10), (shield.centerx + 2, shield.y + 17), (shield.centerx - 2, shield.y + 17), (shield.centerx - 2, shield.y + 10), (shield.centerx - 5, shield.y + 10)],
        )
        title_font = get_font(16, bold=True)
        sub_font = get_font(15)
        title = title_font.render("Cyber Defense AI", True, COLOR_TEXT_PRIMARY)
        self.screen.blit(title, (52, 12))
        subtitle = sub_font.render("- Mô phỏng thuật toán AI", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(subtitle, (52 + title.get_width() + 8, 13))

    def _draw_top_nav(self) -> None:
        rect = self.layout.top_tabs
        draw_panel(self.screen, rect)
        for idx, tab_rect in enumerate(self._top_nav_rects()):
            active = idx == self.state.selected_group_index
            bg = (13, 73, 155) if active else (4, 13, 24)
            border = (59, 138, 246) if active else (31, 53, 76)
            if active:
                for spread, alpha in ((8, 42), (4, 58)):
                    glow_rect = tab_rect.inflate(spread, spread)
                    glow = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                    pygame.draw.rect(glow, (55, 142, 255, alpha), glow.get_rect(), border_radius=8)
                    self.screen.blit(glow, glow_rect.topleft)
            pygame.draw.rect(self.screen, bg, tab_rect, border_radius=6)
            top = pygame.Surface((tab_rect.width, max(2, tab_rect.height // 2)), pygame.SRCALPHA)
            top.fill((110, 184, 255, 64 if active else 22))
            self.screen.blit(top, tab_rect.topleft)
            pygame.draw.rect(self.screen, border, tab_rect, 1, border_radius=6)
            pygame.draw.line(self.screen, COLOR_PANEL_HIGHLIGHT if not active else (168, 216, 255), (tab_rect.x + 6, tab_rect.y + 1), (tab_rect.right - 7, tab_rect.y + 1), 1)
            icon_rect = pygame.Rect(tab_rect.x + 22, tab_rect.centery - 12, 24, 24)
            pygame.draw.circle(self.screen, (13, 39, 68) if active else (8, 24, 42), icon_rect.center, 12)
            pygame.draw.circle(self.screen, (192, 222, 255) if active else (135, 155, 176), icon_rect.center, 11, 1)
            self._draw_nav_icon(idx, icon_rect, COLOR_TEXT_PRIMARY if active else COLOR_TEXT_SECONDARY)
            draw_text_fit(
                self.screen,
                GROUPS[idx],
                pygame.Rect(tab_rect.x + 54, tab_rect.y, tab_rect.width - 62, tab_rect.height),
                COLOR_TEXT_PRIMARY if active else COLOR_TEXT_SECONDARY,
                size=13,
                bold=True,
            )

    def _draw_nav_icon(self, idx: int, rect: pygame.Rect, color: tuple[int, int, int]) -> None:
        cx, cy = rect.center
        if idx == 0:
            pygame.draw.circle(self.screen, color, (cx, cy), 6, 1)
            pygame.draw.line(self.screen, color, (cx, cy - 9), (cx, cy - 4), 1)
            pygame.draw.line(self.screen, color, (cx, cy + 4), (cx, cy + 9), 1)
            pygame.draw.line(self.screen, color, (cx - 9, cy), (cx - 4, cy), 1)
            pygame.draw.line(self.screen, color, (cx + 4, cy), (cx + 9, cy), 1)
        elif idx == 1:
            for px, py in ((-5, -4), (4, -6), (5, 5)):
                pygame.draw.circle(self.screen, color, (cx + px, cy + py), 2, 1)
            pygame.draw.line(self.screen, color, (cx - 3, cy - 4), (cx + 2, cy - 6), 1)
            pygame.draw.line(self.screen, color, (cx + 4, cy - 4), (cx + 5, cy + 3), 1)
        elif idx == 2:
            pygame.draw.circle(self.screen, color, (cx - 2, cy - 2), 6, 1)
            pygame.draw.line(self.screen, color, (cx + 3, cy + 3), (cx + 8, cy + 8), 2)
            pygame.draw.line(self.screen, color, (cx - 2, cy - 8), (cx - 2, cy + 4), 1)
            pygame.draw.line(self.screen, color, (cx - 8, cy - 2), (cx + 4, cy - 2), 1)
        elif idx == 3:
            for ox, oy in ((-5, -5), (5, -5), (-5, 5), (5, 5)):
                pygame.draw.rect(self.screen, color, pygame.Rect(cx + ox - 3, cy + oy - 3, 6, 6), 1, border_radius=1)
            pygame.draw.line(self.screen, color, (cx - 2, cy), (cx + 2, cy), 1)
            pygame.draw.line(self.screen, color, (cx, cy - 2), (cx, cy + 2), 1)
        elif idx == 4:
            pygame.draw.circle(self.screen, color, (cx, cy), 7, 1)
            pygame.draw.line(self.screen, color, (cx, cy - 9), (cx, cy + 9), 1)
            pygame.draw.line(self.screen, color, (cx - 9, cy), (cx + 9, cy), 1)
            pygame.draw.rect(self.screen, color, pygame.Rect(cx - 3, cy - 3, 6, 6), 1)
        else:
            pygame.draw.arc(self.screen, color, pygame.Rect(cx - 8, cy - 8, 16, 16), 0.2, 4.6, 1)
            pygame.draw.polygon(self.screen, color, [(cx + 8, cy - 1), (cx + 4, cy - 4), (cx + 5, cy + 1)])
            pygame.draw.circle(self.screen, color, (cx, cy), 3, 1)

    def _draw_right_panel(self) -> None:
        rect = self.layout.right_panel
        draw_panel(self.screen, rect, "Thông tin node")
        if not self._map_data:
            return
        graph = self._map_data.graph
        node_id = self.state.selected_node or self.state.hovered_node or self._map_data.hacker_start
        node = graph.get_node(node_id)
        if not node:
            return
        x = rect.x + 18
        y = rect.y + 58
        legend_h = max(214, min(268, int(rect.height * 0.42)))
        legend_top = rect.bottom - legend_h
        info_bottom = legend_top - 10
        node_color = COLOR_NODE_HACKER if node.id == self._map_data.hacker_start else get_node_color(node.kind)
        if node.id in self._map_data.goal_nodes:
            node_color = COLOR_NODE_SERVER
        draw_network_node(
            self.screen,
            node.kind,
            (x + 28, y + 28),
            22,
            node_color,
            hacker=node.id == self._map_data.hacker_start,
            selected=True,
        )
        name = get_font(18, bold=True).render(node.id, True, COLOR_TEXT_PRIMARY)
        self.screen.blit(name, (x + 72, y + 18))
        y += 66
        rows = [
            ("Loại", NODE_KIND_LABELS.get(node.kind, node.kind)),
            ("Mức bảo mật", f"{node.security_level} / 10"),
            ("Trạng thái", "Bị hacker kiểm soát" if node.compromised else "An toàn"),
            ("Thuộc Zone", node.zone or "Không có"),
            ("IDS giám sát", "Có" if node.monitored else "Không"),
        ]
        for label, value in rows:
            color = COLOR_TEXT_ERROR if label == "Trạng thái" and node.compromised else COLOR_TEXT_PRIMARY
            if y + 20 > info_bottom:
                break
            draw_text_fit(self.screen, label + ":", pygame.Rect(x, y, 112, 20), COLOR_TEXT_SECONDARY, size=12)
            draw_text_fit(self.screen, value, pygame.Rect(x + 118, y, rect.width - 146, 20), color, size=12)
            y += 23

        if y + 40 <= info_bottom:
            conn_title = get_font(12, bold=True).render("Kết nối:", True, COLOR_TEXT_SECONDARY)
            self.screen.blit(conn_title, (x, y))
            y += 22
            max_conn = max(0, (info_bottom - y) // 18)
            for neighbor, cost, _ in graph.neighbors_with_cost(node.id, ignore_blocked=False)[:max_conn]:
                text = f"- {neighbor} (chi phí: {cost:.0f})"
                draw_text_fit(self.screen, text, pygame.Rect(x + 10, y, rect.width - 44, 18), (228, 242, 255), size=11)
                y += 18

        pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (rect.x, legend_top), (rect.right, legend_top), 1)
        self._draw_legend(rect, legend_top + 14)

    def _draw_legend(self, rect: pygame.Rect, y: int) -> None:
        title = get_font(13, bold=True).render("CHÚ THÍCH", True, (116, 195, 255))
        self.screen.blit(title, (rect.x + 18, y))
        items = [
            (COLOR_NODE_HACKER, "Điểm xâm nhập / bắt đầu"),
            ((80, 216, 106), "Nút an toàn"),
            (COLOR_NODE_FIREWALL, "Tường lửa"),
            (COLOR_NODE_IDS, "IDS"),
            (COLOR_NODE_SERVER, "Máy chủ / CSDL"),
            (COLOR_CURRENT, "Đang xét"),
            (COLOR_FRONTIER, "Trong biên"),
            (COLOR_BLOCKED, "Đã duyệt / bị khóa"),
            (COLOR_EDGE_DEFAULT, "Kết nối"),
        ]
        y += 30
        available_h = rect.bottom - y - 10
        step = max(16, min(24, available_h // max(1, len(items))))
        for color, label in items:
            mark = pygame.Rect(rect.x + 20, y + 2, 14, 14)
            pygame.draw.rect(self.screen, color, mark, border_radius=4)
            pygame.draw.rect(self.screen, (220, 235, 255), mark, 1, border_radius=4)
            draw_text_fit(self.screen, label, pygame.Rect(rect.x + 44, y, rect.width - 60, step), COLOR_TEXT_SECONDARY, size=12)
            y += step

    def _draw_toast(self) -> None:
        if not self._toast or time.time() > self._toast_until:
            return
        font = get_font(13)
        surf = font.render(self._toast, True, (240, 240, 240))
        width, height = surf.get_size()
        center_x = self.screen.get_width() // 2
        box_x = center_x - width // 2 - 12
        box_y = self.screen.get_height() - 50
        bg = pygame.Surface((width + 24, height + 12), pygame.SRCALPHA)
        bg.fill((8, 24, 44, 232))
        self.screen.blit(bg, (box_x, box_y))
        pygame.draw.rect(self.screen, COLOR_PANEL_BORDER, pygame.Rect(box_x, box_y, width + 24, height + 12), 1, border_radius=7)
        self.screen.blit(surf, (box_x + 12, box_y + 6))

    def _draw_map_title(self) -> None:
        assert self._map_data is not None
        font = get_font(11)
        surf = font.render(map_label(self.state.selected_map_name), True, COLOR_TEXT_SECONDARY)
        self.screen.blit(surf, (self.layout.graph_area.x + 142, self.layout.graph_area.y + 14))
