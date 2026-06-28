"""
app.py - Main Pygame application for Cyber Defense AI.

The UI stays separate from algorithm logic: algorithms only yield StepEvent
objects, while this module handles playback, logging, stats, and controls.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Iterator, Optional

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
            on_start_node_change=self._on_start_node_change,
            on_goal_node_change=self._on_goal_node_change,
            on_adversarial_action_change=self._on_adversarial_action_change,
        )

        self._step_gen: Optional[Iterator[StepEvent]] = None
        self._last_auto_step: float = 0.0
        self._toast: str = ""
        self._toast_until: float = 0.0
        self._right_panel_scroll: int = 0
        self._right_panel_follow_tail: bool = True
        self._right_panel_node_id: Optional[str] = None
        self._right_panel_scroll: int = 0
        self._right_panel_scroll: int = 0

    def _load_map(self, map_name: str) -> bool:
        maps_dir = Path(__file__).parent.parent / "maps"
        path = maps_dir / f"{map_name}.json"
        try:
            self._map_data = load_map(path)
            self.state.map_data = self._map_data
            self.state.selected_map_name = map_name
            self.state.selected_start_node = self._map_data.hacker_start
            self.state.selected_goal_node = self._map_data.goal_nodes[0] if self._map_data.goal_nodes else None
            self.state.adversarial_game_state = None
            self.state.adversarial_turn_index = 0
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
        self.state.adversarial_game_state = None
        self.state.adversarial_turn_index = 0
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

    def _on_start_node_change(self, idx: int, node_id: str) -> None:
        if not self._map_data or not self._map_data.graph.has_node(node_id):
            return
        self.state.selected_start_node = node_id
        self._on_reset()
        self.state.selected_node = node_id
        self._show_toast(f"Start node: {node_id}")

    def _on_goal_node_change(self, idx: int, node_id: str) -> None:
        if not self._map_data or not self._map_data.graph.has_node(node_id):
            return
        self.state.selected_goal_node = node_id
        self._on_reset()
        self.state.selected_node = node_id
        self._show_toast(f"Goal node: {node_id}")

    def _on_adversarial_action_change(self, action: str) -> None:
        self.state.adversarial_hacker_action = action
        if self.state.selected_group_index != 5:
            return
        if action == "move":
            self._ensure_adversarial_game_state()
            self._show_toast("Chá»n node ká» trÃªn báº£n Ä‘á»“ Ä‘á»ƒ Move")
            return
        self._execute_adversarial_turn(action)

    def _execute_adversarial_turn(self, action: str, target: Optional[str] = None) -> None:
        if not self._map_data or self.state.selected_group_index != 5:
            return
        from algorithms.adversarial.game_loop import play_hacker_turn

        game_state = self._ensure_adversarial_game_state()
        if game_state is None:
            return
        name = self._current_adversarial_algorithm_name()
        try:
            result = play_hacker_turn(
                self._map_data.graph,
                game_state,
                self._current_goals(),
                action,
                target,
                name,
                self.state.game_depth,
                step_index=len(self.state.run_state.steps),
            )
        except ValueError as exc:
            self._show_toast(str(exc), duration=3.0)
            return

        run = self.state.run_state
        self._step_gen = None
        run.algorithm_name = name
        run.status = "paused"
        self.state.adversarial_game_state = result.state
        self.state.adversarial_turn = result.state.turn
        self.state.adversarial_target_node = target
        for step in result.steps:
            self._append_step_event(step)
        self.control_panel._build_widgets()
        if result.terminal:
            outcome = result.steps[-1].data.get("outcome_title") if result.steps else None
            reason = result.steps[-1].data.get("outcome_reason") if result.steps else None
            if outcome and reason:
                self._show_toast(f"{outcome}: {reason}", duration=4.0)
            else:
                winner = "Hacker" if result.winner == "hacker" else "AI Defender"
                self._show_toast(f"{winner} kết thúc ván đối kháng", duration=4.0)
        elif result.defender_action:
            self._show_toast(f"AI: {result.defender_action.description}")

    def _ensure_adversarial_game_state(self):
        if not self._map_data:
            return None
        if self.state.adversarial_game_state is None:
            from algorithms.adversarial.game_loop import new_game_state

            max_turns = int(self._map_data.metadata.get("max_turns", 10)) if self._map_data.metadata else 10
            self.state.adversarial_game_state = new_game_state(
                self._map_data.graph,
                self._current_start(),
                max_turns=max_turns,
            )
            self.state.adversarial_turn = "hacker"
        return self.state.adversarial_game_state

    def _current_adversarial_algorithm_name(self) -> str:
        return ("Minimax", "Alpha-Beta", "Expectimax")[min(self.state.selected_algo_index, 2)]

    def _append_step_event(self, step: StepEvent) -> None:
        run = self.state.run_state
        run.steps.append(step)
        run.current_step_index = len(run.steps) - 1
        run.metrics = self._metrics_from_step(step, success=(step.event_type == "found"))
        run.log.log(self._format_step_log(step), self._log_level_for_step(step))
        self.log_view.update(run.log)
        if step.event_type == "found":
            run.status = "success"
        elif self._is_failure_step(step):
            run.status = "failure"
        elif run.status == "ready":
            run.status = "paused"

    def _current_start(self) -> str:
        if not self._map_data:
            return ""
        selected = self.state.selected_start_node
        if selected and self._map_data.graph.has_node(selected):
            return selected
        return self._map_data.hacker_start

    def _current_hacker_position(self) -> str:
        game_state = self.state.adversarial_game_state
        if self.state.selected_group_index == 5 and game_state is not None:
            return game_state.hacker_position
        return self._current_start()

    def _current_goals(self) -> list[str]:
        if not self._map_data:
            return []
        if self.state.selected_group_index == 5:
            return list(self._map_data.goal_nodes)
        selected = self.state.selected_goal_node
        if selected and self._map_data.graph.has_node(selected):
            return [selected]
        return list(self._map_data.goal_nodes)

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
        start = self._current_start()
        goals = self._current_goals()
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
                from algorithms.csp.min_conflicts import DEMO_SEED

                result = run_func(graph, start, goals, seed=DEMO_SEED, max_steps=300)
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
        if any(result.metrics.extra.get("local_search_mode") == "heuristic_path" for result in results):
            return self._format_heuristic_local_compare_log(results)
        if any(result.metrics.extra.get("defense_config") for result in results):
            return self._format_local_search_compare_log(results)
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

    def _format_heuristic_local_compare_log(self, results: list[AlgorithmResult]) -> str:
        header = (
            f"{'Thuật toán':<28} | {'Đạt':>5} | {'PathCost':>8} | {'h cuối':>8} | "
            f"{'Bước':>5} | {'Đường đi':<36} | {'Thời gian':>10}"
        )
        rows = [header, "-" * len(header)]
        for result in results:
            metrics = result.metrics
            extra = metrics.extra
            path = " -> ".join(metrics.path) if metrics.path else "-"
            rows.append(
                f"{algo_label(metrics.algorithm):<28} | "
                f"{'Có' if metrics.success else 'Không':>5} | "
                f"{self._format_number(metrics.total_cost):>8} | "
                f"{self._format_number(extra.get('final_heuristic', extra.get('current_heuristic'))):>8} | "
                f"{metrics.num_steps:>5} | "
                f"{path[:36]:<36} | "
                f"{metrics.time_ms:>8.2f}ms"
            )
        return "\n".join(rows)

    def _format_local_search_compare_log(self, results: list[AlgorithmResult]) -> str:
        header = (
            f"{'Thuật toán':<28} | {'Đạt':>5} | {'DefenseValue':>12} | {'RiskCost':>8} | "
            f"{'Chặn/Mở':>8} | {'Lặp':>5} | {'Worse':>5} | {'Thời gian':>10}"
        )
        rows = [header, "-" * len(header)]
        for result in results:
            metrics = result.metrics
            extra = metrics.extra
            blocked = extra.get("blocked_paths", "-")
            open_paths = extra.get("open_paths", "-")
            worse = extra.get("accepted_worse_moves", "-")
            rows.append(
                f"{algo_label(metrics.algorithm):<28} | "
                f"{'Có' if metrics.success else 'Không':>5} | "
                f"{str(extra.get('defense_value', '-')):>12} | "
                f"{str(extra.get('risk_cost', '-')):>8} | "
                f"{f'{blocked}/{open_paths}':>8} | "
                f"{metrics.num_steps:>5} | "
                f"{str(worse):>5} | "
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
        start = self._current_start()
        goals = self._current_goals()
        if group == 2 and algo_idx == 2:
            self._step_gen = solve_steps(
                self._map_data.graph,
                start,
                goals,
                seed=seed,
                t0=self.state.sa_t0,
                alpha=self.state.sa_alpha,
                tmin=self.state.sa_tmin,
                max_steps=self.state.sa_max_steps,
            )
        elif group == 3 and algo_idx == 2:
            from algorithms.csp.min_conflicts import DEMO_SEED

            self._step_gen = solve_steps(
                self._map_data.graph,
                start,
                goals,
                seed=DEMO_SEED,
                max_steps=300,
            )
        elif group == 4:
            self._step_gen = solve_steps(
                self._map_data.graph,
                start,
                goals,
                metadata=self._map_data.metadata,
            )
        elif group == 5:
            self._step_gen = solve_steps(
                self._map_data.graph,
                start,
                goals,
                depth=self.state.game_depth,
            )
        else:
            self._step_gen = solve_steps(
                self._map_data.graph,
                start,
                goals,
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
        run.log.log(self._format_step_log(step), self._log_level_for_step(step))
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

    def _log_level_for_step(self, step: StepEvent) -> str:
        if step.event_type == "found":
            return "success"
        if step.event_type in {"failure"} or self._looks_like_no_path_step(step):
            return "error"
        if step.event_type in {"backtrack"}:
            return "warn"
        if step.data.get("accepted") is False:
            return "warn"
        return "info"

    def _looks_like_no_path_step(self, step: StepEvent) -> bool:
        text = step.message.lower()
        no_path_words = ("no path", "không tìm thấy", "khong tim thay", "không tìm được")
        return any(word in text for word in no_path_words) or (
            step.event_type == "info"
            and not step.current_node
            and not step.frontier
            and bool(step.explored)
        )

    def _format_step_log(self, step: StepEvent) -> str:
        group = self.state.selected_group_index
        if group == 0:
            return self._format_pathfinding_log(step, informed=False)
        if group == 1:
            return self._format_pathfinding_log(step, informed=True)
        if group == 2:
            return self._format_local_search_log(step)
        if group == 3:
            return self._format_csp_log(step)
        if group == 4:
            return self._format_complex_env_log(step)
        if group == 5:
            return self._format_adversarial_log(step)
        return step.message

    def _step_prefix(self, step: StepEvent) -> str:
        return f"[Bước {step.step_index:03d}] {step.algorithm}:"

    def _format_list(self, values: Any, limit: int = 5) -> str:
        if values is None:
            return "-"
        if isinstance(values, (str, int, float)):
            return str(values)
        items = list(values)
        if not items:
            return "-"
        shown = [str(item) for item in items[:limit]]
        suffix = f", +{len(items) - limit}" if len(items) > limit else ""
        return ", ".join(shown) + suffix

    def _format_path(self, path: list[str]) -> str:
        return " -> ".join(path) if path else "-"

    def _format_number(self, value: Any) -> str:
        if value is None:
            return "-"
        if isinstance(value, float):
            if value == float("inf"):
                return "inf"
            return f"{value:.2f}"
        return str(value)

    def _format_pathfinding_log(self, step: StepEvent, *, informed: bool) -> str:
        prefix = self._step_prefix(step)
        current = step.current_node or "-"
        frontier = self._format_list(step.frontier)
        explored_count = len(step.explored)
        data = step.data

        if step.event_type == "found":
            cost = step.total_cost if step.total_cost else max(0, len(step.path) - 1)
            return (
                f"{prefix} đạt Goal {current}; "
                f"đường đi tối ưu/theo chiến lược: {self._format_path(step.path)}; "
                f"chi phí={self._format_number(cost)}."
            )
        if step.event_type == "failure" or self._looks_like_no_path_step(step):
            return f"{prefix} frontier rỗng; không còn trạng thái ứng viên để đi tới Goal."
        if step.event_type == "info":
            if informed:
                score = self._score_text(data)
                strategy = {
                    "Greedy": "chọn node có h(n) nhỏ nhất",
                    "A*": "chọn node có f(n)=g(n)+h(n) nhỏ nhất",
                    "IDA*": "DFS giới hạn bởi ngưỡng f(n)",
                }.get(step.algorithm, "tìm kiếm có heuristic")
                return (
                    f"{prefix} khởi tạo tìm kiếm heuristic: {strategy}; Start={current}; "
                    f"Goal={self._format_list(self._current_goals())}; {score}; frontier={frontier}."
                )
            queue_name = {
                "BFS": "queue FIFO, duyệt theo chiều rộng",
                "DFS": "stack LIFO, duyệt theo chiều sâu",
                "UCS": "priority queue, ưu tiên chi phí g(n) nhỏ nhất",
            }.get(step.algorithm, "frontier")
            return (
                f"{prefix} khởi tạo {queue_name}; Start={current}; "
                f"Goal={self._format_list(self._current_goals())}; không dùng heuristic."
            )
        if informed:
            score = self._score_text(data)
            if "previous_threshold" in data:
                return (
                    f"{prefix} IDA* chưa tìm thấy trong ngưỡng cũ; "
                    f"tăng threshold từ {self._format_number(data.get('previous_threshold'))} "
                    f"lên {self._format_number(data.get('threshold'))}; đã duyệt={explored_count}."
                )
            return (
                f"{prefix} mở rộng {current} theo hàm đánh giá; "
                f"{score}; frontier={frontier}; closed={explored_count}; "
                f"đã sinh={step.nodes_generated}."
            )
        return (
            f"{prefix} lấy {current} khỏi cấu trúc frontier và mở rộng láng giềng; "
            f"frontier={frontier}; visited={explored_count}; đã sinh={step.nodes_generated}."
        )

    def _score_text(self, data: dict[str, Any]) -> str:
        parts: list[str] = []
        for key in ("g", "h", "f", "threshold"):
            if key in data:
                parts.append(f"{key}={self._format_number(data.get(key))}")
        return ", ".join(parts) if parts else "điểm đánh giá=-"

    def _format_local_search_log(self, step: StepEvent) -> str:
        prefix = self._step_prefix(step)
        data = step.data
        if data.get("local_search_mode") == "heuristic_path":
            current = step.current_node or "-"
            h_value = self._format_number(data.get("current_heuristic"))
            chosen = data.get("chosen_neighbor") or "-"
            path = self._format_path(data.get("path_so_far", step.path))
            if step.event_type == "info":
                return (
                    f"{prefix} khởi tạo Local Search trên đồ thị trọng số; bắt đầu tại {current}; "
                    f"h({current})={h_value}; goal={data.get('goal', '-')}."
                )
            if step.event_type == "found":
                return (
                    f"{prefix} đã tới goal {current}; đường đi={path}; "
                    f"chi phí đường đi={self._format_number(data.get('path_cost'))}."
                )
            if step.event_type == "failure":
                return (
                    f"{prefix} dừng tại {current}: rơi vào local maximum/local optimum; "
                    f"không có láng giềng nào có h thấp hơn {h_value}; đường đi={path}."
                )
            if step.algorithm == "Simulated Annealing":
                accepted = data.get("accepted")
                decision = "chấp nhận" if accepted else "từ chối"
                return (
                    f"{prefix} SA xét láng giềng {chosen}; h hiện tại={h_value}; "
                    f"h ứng viên={self._format_number(data.get('candidate_heuristic'))}; "
                    f"delta={self._format_number(data.get('delta'))}; "
                    f"T={self._format_number(data.get('temperature'))}; "
                    f"p={self._format_number(data.get('accept_probability'))}; {decision}."
                )
            if step.event_type == "move":
                return (
                    f"{prefix} chọn láng giềng {current} vì h thấp hơn; "
                    f"h({current})={h_value}; đường đi={path}."
                )
            checked = data.get("neighbors_checked")
            checked_text = f" đã xét {checked} láng giềng;" if checked is not None else ""
            neighbor_text = self._format_neighbor_scores(data.get("neighbor_scores", []))
            return (
                f"{prefix}{checked_text} node hiện tại={current}, h={h_value}; "
                f"đang xét/chọn={chosen}; láng giềng: {neighbor_text}."
            )

        value = data.get("defense_value")
        risk = data.get("risk_cost")
        blocked = data.get("blocked_paths")
        open_paths = data.get("open_paths")
        config = data.get("defense_config")
        config_text = self._format_defense_config(config)

        if step.event_type == "info":
            objective = "tối đa DefenseValue" if step.algorithm != "Simulated Annealing" else "tối thiểu RiskCost"
            return (
                f"{prefix} khởi tạo bài toán tối ưu cục bộ ({objective}); {config_text}; "
                f"DefenseValue={self._format_number(value)}, RiskCost={self._format_number(risk)}."
            )
        if step.event_type == "found":
            if step.algorithm == "Simulated Annealing":
                return (
                    f"{prefix} kết thúc Simulated Annealing; cấu hình tốt nhất {config_text}; "
                    f"RiskCost={self._format_number(risk)}, DefenseValue={self._format_number(value)}, "
                    f"đường bị chặn={self._format_number(blocked)}, đường còn mở={self._format_number(open_paths)}."
                )
            optimum = "cực đại cục bộ" if step.algorithm in {"Simple HC", "Steepest HC"} else "nghiệm tốt nhất"
            return (
                f"{prefix} đạt {optimum} cho cấu hình phòng thủ; {config_text}; "
                f"DefenseValue={self._format_number(value)}, RiskCost={self._format_number(risk)}, "
                f"đường bị chặn={self._format_number(blocked)}, đường còn mở={self._format_number(open_paths)}."
            )
        if step.algorithm == "Simulated Annealing":
            accepted = data.get("accepted")
            decision = "chấp nhận trạng thái mới" if accepted else "từ chối trạng thái mới"
            if accepted is None:
                decision = "kết thúc"
            return (
                f"{prefix} SA lấy mẫu một láng giềng và đánh giá theo RiskCost; "
                f"RiskCost={self._format_number(risk)}, "
                f"delta={self._format_number(data.get('delta'))}, "
                f"T={self._format_number(data.get('temperature'))}, "
                f"xác suất chấp nhận={self._format_number(data.get('accept_probability'))}; "
                f"{decision}; best RiskCost={self._format_number(data.get('best_risk'))}."
            )
        if step.event_type == "move":
            move_text = "chọn láng giềng tốt nhất" if step.algorithm == "Steepest HC" else "chấp nhận láng giềng cải thiện đầu tiên"
            return (
                f"{prefix} {move_text}; {config_text}; "
                f"DefenseValue={self._format_number(value)}, RiskCost={self._format_number(risk)}."
            )
        checked = data.get("neighbors_checked")
        checked_text = f"; đã xét toàn bộ {checked} láng giềng" if checked is not None else ""
        return (
            f"{prefix} đánh giá trạng thái láng giềng trong không gian cấu hình{checked_text}; {config_text}; "
            f"DefenseValue={self._format_number(value)}, RiskCost={self._format_number(risk)}."
        )

    def _format_neighbor_scores(self, rows: Any) -> str:
        if not isinstance(rows, list) or not rows:
            return "-"
        parts: list[str] = []
        for row in rows[:4]:
            if not isinstance(row, dict):
                continue
            parts.append(f"{row.get('node')} h={self._format_number(row.get('heuristic'))}")
        if len(rows) > 4:
            parts.append(f"+{len(rows) - 4}")
        return "; ".join(parts) if parts else "-"

    def _format_defense_config(self, config: Any) -> str:
        if not config:
            return "FW chặn=-; IDS giám sát=-; UP tăng bảo mật=-"
        return (
            f"FW chặn tại={self._format_list(getattr(config, 'firewall_nodes', []), 3)}; "
            f"IDS giám sát={self._format_list(getattr(config, 'ids_nodes', []), 3)}; "
            f"UP tăng bảo mật={self._format_list(getattr(config, 'upgraded_nodes', []), 3)}"
        )

    def _format_csp_log(self, step: StepEvent) -> str:
        prefix = self._step_prefix(step)
        data = step.data
        assignments = data.get("assignments", {})
        current = step.current_node or "-"
        current_value = assignments.get(current, "-") if isinstance(assignments, dict) else "-"
        conflicts = data.get("conflicts", [])
        removed = data.get("removed", {})
        assigned_count = len(assignments) if isinstance(assignments, dict) else 0

        if step.event_type == "info":
            domains = data.get("domains", {})
            return (
                f"{prefix} khởi tạo CSP phân vùng mạng; "
                f"biến={len(domains)}, miền giá trị là các Security Zone; ràng buộc dựa trên liên kết mạng."
            )
        if step.event_type == "assign":
            attempt = self._assignment_attempt(step, current)
            verdict = "nhất quán tạm thời" if not conflicts else f"vi phạm {len(conflicts)} ràng buộc: {conflicts[0]}"
            return (
                f"{prefix} kiểm tra phép gán {current}={attempt}; "
                f"kết quả {verdict}; số biến đã gán={assigned_count}."
            )
        if step.event_type == "update":
            if step.algorithm == "Min-Conflicts":
                old_value = data.get("old_value", "-")
                new_value = data.get("new_value", current_value)
                best = data.get("best_conflicts", len(conflicts))
                return (
                    f"{prefix} chọn biến đang xung đột {current}; đổi zone {old_value} -> {new_value}; "
                    f"số xung đột tốt nhất sau đổi={best}."
                )
            prune_text = f"; loại miền {self._format_domain_removal(removed)}" if removed else ""
            return (
                f"{prefix} chấp nhận gán {current}={current_value}{prune_text}; "
                f"tiếp tục lan truyền ràng buộc; đã gán={assigned_count}."
            )
        if step.event_type == "backtrack":
            return (
                f"{prefix} backtrack tại biến {current}; khôi phục miền/lựa chọn trước; "
                f"số lần quay lui={data.get('backtracks', 0)}."
            )
        if step.event_type == "found":
            return f"{prefix} tìm thấy nghiệm CSP; mọi biến đã được gán và thỏa toàn bộ ràng buộc; biến={assigned_count}."
        return f"{prefix} không tìm được nghiệm CSP hợp lệ; xung đột còn lại={len(conflicts)}."

    def _assignment_attempt(self, step: StepEvent, current: str) -> str:
        attempted = step.data.get("attempted_value")
        if attempted:
            return str(attempted)
        marker = f"{current} = "
        if marker not in step.message:
            return "-"
        value = step.message.split(marker, 1)[1].split(".", 1)[0].strip()
        return value or "-"

    def _format_domain_removal(self, removed: Any) -> str:
        if not isinstance(removed, dict) or not removed:
            return "-"
        parts = [f"{node}:{self._format_list(values, 3)}" for node, values in list(removed.items())[:3]]
        if len(removed) > 3:
            parts.append(f"+{len(removed) - 3}")
        return "; ".join(parts)

    def _format_complex_env_log(self, step: StepEvent) -> str:
        prefix = self._step_prefix(step)
        data = step.data
        belief = data.get("belief", [])
        blocked = data.get("blocked_nodes", [])
        plan = data.get("plan") or data.get("plan_lines") or []
        observed = data.get("observed_nodes", [])

        if step.algorithm == "AND-OR":
            if step.event_type == "found":
                return (
                    f"{prefix} tìm được kế hoạch điều kiện AND-OR bảo đảm an toàn; "
                    f"đỉnh đã xét={step.nodes_expanded}; kế hoạch={self._format_list(plan, 2)}."
                )
            if step.event_type == "failure":
                return f"{prefix} không có kế hoạch điều kiện an toàn cho mọi nhánh kết quả."
            return (
                f"{prefix} mở rộng cây AND-OR trên belief={self._format_list(belief)}; "
                f"xét nhánh hành động/kết quả: {self._format_list(plan, 1)}."
            )

        if step.event_type == "info":
            extra = f"; vùng quan sát={self._format_list(observed)}" if observed else ""
            mode = "quan sát một phần" if observed else "không quan sát trực tiếp"
            return (
                f"{prefix} khởi tạo trạng thái niềm tin trong môi trường {mode}; "
                f"vị trí Hacker có thể={self._format_list(belief)}{extra}."
            )
        if "previous_belief" in data:
            return (
                f"{prefix} cập nhật belief bằng quan sát IDS/Bayes-style filtering; "
                f"{self._format_list(data.get('previous_belief'))} -> {self._format_list(belief)}."
            )
        if step.event_type == "found":
            return f"{prefix} tìm được kế hoạch phòng thủ an toàn cho mọi trạng thái trong belief; chặn={self._format_list(blocked)}."
        if step.event_type == "failure":
            return f"{prefix} chưa tìm được kế hoạch bảo đảm an toàn với belief hiện tại."
        return (
            f"{prefix} áp dụng hành động phòng thủ theo belief-state search; "
            f"chặn={self._format_list(blocked)}; belief={self._format_list(belief)}."
        )

    def _format_adversarial_log(self, step: StepEvent) -> str:
        prefix = self._step_prefix(step)
        data = step.data
        action = self._format_action(data.get("defender_action") or data.get("action"))
        value = data.get("expected_value", data.get("evaluation", step.total_cost))
        turn = data.get("turn", "hacker")
        depth = data.get("depth", "-")

        if data.get("terminal"):
            title = data.get("outcome_title", "Ván đối kháng kết thúc")
            reason = data.get("outcome_reason", "-")
            path = self._format_path(step.path)
            return f"{prefix} {title}: {reason} Đường hacker: {path}."

        if step.event_type == "info":
            if step.algorithm == "Expectimax":
                return (
                    f"{prefix} khởi tạo Expectimax với nút xác suất IDS/chance node; "
                    f"lượt={turn}, độ sâu={depth}, outcomes={self._format_list(data.get('chance_outcomes'), 2)}."
                )
            if step.algorithm == "Alpha-Beta":
                return (
                    f"{prefix} khởi tạo Minimax có Alpha-Beta Pruning; "
                    f"Hacker(MAX), Defender(MIN), độ sâu={depth}, alpha=-inf, beta=inf."
                )
            return f"{prefix} khởi tạo cây trò chơi Minimax: Hacker(MAX) - Defender(MIN); lượt={turn}, độ sâu={depth}."
        if step.event_type == "found":
            return f"{prefix} chọn hành động tối ưu theo utility: {action}; giá trị đánh giá={self._format_number(value)}."
        if step.algorithm == "Alpha-Beta":
            return (
                f"{prefix} xét nhánh {action}; utility={self._format_number(value)}, "
                f"alpha={self._format_number(data.get('alpha'))}, beta={self._format_number(data.get('beta'))}, "
                f"số nhánh đã cắt={data.get('pruned_branches', 0)}."
            )
        if step.algorithm == "Expectimax":
            return (
                f"{prefix} xét hành động {action}; expected utility={self._format_number(value)} "
                f"sau khi tổng hợp các nhánh xác suất IDS."
            )
        return (
            f"{prefix} xét hành động {action}; utility Minimax={self._format_number(value)}; "
            f"đã đánh giá={step.nodes_expanded} trạng thái."
        )

    def _format_action(self, action: Any) -> str:
        if not action:
            return "không hành động"
        action_type = getattr(action, "action_type", "")
        target = getattr(action, "target", "")
        if action_type == "move":
            return f"Hacker di chuyển tới {target}"
        if action_type == "block_node":
            return f"Defender chặn node {target}"
        if action_type == "block_edge":
            return f"Defender chặn cạnh {target.replace('|', '-')}"
        if action_type == "upgrade":
            return f"Defender nâng cấp {target}"
        if action_type == "deploy_ids":
            return f"Defender deploy IDS at {target}"
        if action_type == "detect":
            return "IDS phát hiện Hacker" if target == "detected" else "IDS bỏ sót Hacker"
        return getattr(action, "description", str(action))

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
                self._handle_right_panel_event(event)
                if self.state.selected_group_index == 5:
                    self._handle_adversarial_graph_event(event)
                else:
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
        hacker_pos = self._current_hacker_position()
        goals = self._current_goals()
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
        self._right_panel_scroll = 0
        self._right_panel_follow_tail = True

    def _handle_adversarial_graph_event(self, event: pygame.event.Event) -> bool:
        self.graph_view.handle_event(event)
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        if not self.layout.graph_area.collidepoint(event.pos):
            return False
        target = self.state.selected_node
        if not target:
            return False
        self._execute_adversarial_turn("move", target)
        return True

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
                self._right_panel_scroll = 0
                self._right_panel_follow_tail = True
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
        start_node = self._current_start()
        hacker_position = self._current_hacker_position()
        goal_nodes = self._current_goals()
        node_id = self.state.selected_node or self.state.hovered_node or hacker_position
        node = graph.get_node(node_id)
        if not node:
            return
        if node_id != self._right_panel_node_id:
            self._right_panel_node_id = node_id
            self._right_panel_scroll = 0

        legend_h = 214
        legend_top = rect.bottom - legend_h
        info_bottom = legend_top - 10
        scroll_area = pygame.Rect(rect.x + 10, rect.y + 42, rect.width - 20, max(60, info_bottom - rect.y - 42))
        old_clip = self.screen.get_clip()
        self.screen.set_clip(scroll_area)

        x = rect.x + 18
        y = rect.y + 58 - self._right_panel_scroll
        is_start = node.id == start_node
        is_hacker_position = node.id == hacker_position
        is_goal = node.id in goal_nodes
        node_color = COLOR_NODE_HACKER if (is_hacker_position or is_start) else get_node_color(node.kind)
        if is_goal:
            node_color = COLOR_NODE_SERVER
        draw_network_node(
            self.screen,
            node.kind,
            (x + 28, y + 28),
            22,
            node_color,
            hacker=is_hacker_position,
            selected=True,
        )
        name = get_font(18, bold=True).render(node.id, True, COLOR_TEXT_PRIMARY)
        self.screen.blit(name, (x + 72, y + 18))
        y += 58
        if is_hacker_position and is_goal:
            role = "Hacker tại mục tiêu"
            status_text = "Đã tới mục tiêu"
            status_color = COLOR_ACCENT
        elif is_hacker_position and not is_start:
            role = "Hacker hiện tại"
            status_text = "Đang xâm nhập"
            status_color = COLOR_TEXT_ERROR
        elif is_start and is_goal:
            role = "Start + Goal"
            status_text = "Start trùng Goal"
            status_color = COLOR_ACCENT
        elif is_start:
            role = "Start Node"
            status_text = "Điểm bắt đầu"
            status_color = COLOR_TEXT_ERROR
        elif is_goal:
            role = "Goal Node"
            status_text = "Mục tiêu"
            status_color = COLOR_NODE_SERVER
        else:
            role = "Node trung gian"
            status_text = "An toàn"
            status_color = COLOR_TEXT_PRIMARY

        info_lines = [
            ("Vai trò", role),
            ("Loại", NODE_KIND_LABELS.get(node.kind, node.kind)),
            ("Mức bảo mật", f"{node.security_level} / 10"),
            ("Trạng thái", status_text),
            ("Thuộc Zone", node.zone or "Không có"),
            ("IDS giám sát", "Có" if node.monitored else "Không"),
        ]

        line_font = get_font(12)
        value_font = get_font(12, bold=True)
        max_width = rect.width - 156
        for label, value in info_lines:
            color = status_color if label == "Trạng thái" else COLOR_TEXT_PRIMARY
            draw_text_fit(self.screen, label + ":", pygame.Rect(x, y, 112, 22), COLOR_TEXT_SECONDARY, size=12)
            wrapped = self._wrap_panel_text(str(value), value_font, max_width)
            line_h = max(18, value_font.get_linesize() + 2)
            for i, part in enumerate(wrapped):
                self.screen.blit(value_font.render(part, True, color), (x + 118, y + i * line_h))
            y += max(22, len(wrapped) * line_h)

        y += 8
        conn_title = get_font(12, bold=True).render("Kết nối:", True, COLOR_TEXT_SECONDARY)
        self.screen.blit(conn_title, (x, y))
        y += 22
        for neighbor, cost, _ in graph.neighbors_with_cost(node.id, ignore_blocked=False):
            text = f"- {neighbor} (chi phí: {cost:.0f})"
            wrapped = self._wrap_panel_text(text, line_font, rect.width - 44)
            line_h = line_font.get_linesize() + 1
            for part in wrapped:
                self.screen.blit(line_font.render(part, True, (228, 242, 255)), (x + 10, y))
                y += line_h
            y += 2

        max_scroll = max(0, y + self._right_panel_scroll - scroll_area.bottom + 12)
        if self._right_panel_scroll > max_scroll:
            self._right_panel_scroll = max_scroll

        self.screen.set_clip(old_clip)
        pygame.draw.rect(self.screen, (4, 13, 24), pygame.Rect(rect.x + 1, legend_top, rect.width - 2, legend_h - 1))
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
        for color, label in items:
            mark = pygame.Rect(rect.x + 20, y + 2, 14, 14)
            pygame.draw.rect(self.screen, color, mark, border_radius=4)
            pygame.draw.rect(self.screen, (220, 235, 255), mark, 1, border_radius=4)
            draw_text_fit(self.screen, label, pygame.Rect(rect.x + 44, y, rect.width - 60, 18), COLOR_TEXT_SECONDARY, size=12)
            y += 20

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

    def _handle_right_panel_event(self, event: pygame.event.Event) -> bool:
        rect = self.layout.right_panel
        if not rect.collidepoint(pygame.mouse.get_pos()):
            return False
        if event.type == pygame.MOUSEWHEEL:
            self._right_panel_scroll = max(0, self._right_panel_scroll - event.y * 3)
            self._right_panel_follow_tail = False
            return True
        return False

    def _wrap_panel_text(self, text: str, font: pygame.font.Font, max_width: int) -> list[str]:
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

    def _draw_map_title(self) -> None:
        assert self._map_data is not None
        font = get_font(11)
        surf = font.render(map_label(self.state.selected_map_name), True, COLOR_TEXT_SECONDARY)
        self.screen.blit(surf, (self.layout.graph_area.x + 142, self.layout.graph_area.y + 14))

    def _handle_right_panel_event(self, event: pygame.event.Event) -> bool:
        rect = self.layout.right_panel
        if event.type != pygame.MOUSEWHEEL:
            return False
        if not rect.collidepoint(pygame.mouse.get_pos()):
            return False
        self._right_panel_scroll = max(0, self._right_panel_scroll - event.y * 24)
        self._right_panel_follow_tail = False
        return True

    def _wrap_panel_text(self, text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        words = str(text).split()
        if not words:
            return [""]
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if font.size(candidate)[0] <= max_width:
                current = candidate
                continue
            if current:
                lines.append(current)
            current = word
            while font.size(current)[0] > max_width and len(current) > 1:
                cut = len(current)
                while cut > 1 and font.size(current[:cut])[0] > max_width:
                    cut -= 1
                lines.append(current[:cut])
                current = current[cut:]
        if current:
            lines.append(current)
        return lines or [""]
