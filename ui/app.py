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
from core.metrics import format_compare_table
from core.models import AlgorithmMetrics, AlgorithmResult, StepEvent
from core.state import AlgorithmRunState, AppState
from ui.graph_view import GraphView
from ui.layout import Layout
from ui.log_view import LogView
from ui.panels import ControlPanel
from ui.stats_view import StatsView
from ui.theme import COLOR_BG, get_font


class App:
    """Pygame application shell for the Cyber Defense AI simulator."""

    TITLE = "Cyber Defense AI - AI network defense simulator"

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
            self._show_toast(f"Loaded map: {self._map_data.name}")
            return True
        except MapLoadError as exc:
            self._show_toast(f"Map load failed: {exc}", duration=4.0)
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
            self._show_toast("No map loaded")
            return

        group = self.state.selected_group_index
        if group not in (0, 1, 2, 3, 4, 5):
            self._show_toast("Compare is ready for groups 1-6")
            return

        self._step_gen = None
        run = self.state.run_state
        run.reset()

        results = self._run_compare_algorithms(group)
        self.state.compare_results = results
        self.state.compare_mode = True
        run.algorithm_name = "Compare"
        run.status = "success" if results and all(r.success for r in results) else "failure"
        run.metrics = results[0].metrics if results else None

        table = format_compare_table([result.metrics for result in results])
        for line in table.splitlines():
            run.log.log(line, "info")
        self.log_view.update(run.log)
        self._show_toast("Compare completed")

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

    def _build_step_gen(self) -> None:
        run = self.state.run_state
        run.reset()
        self.state.compare_mode = False
        self.state.compare_results.clear()

        if not self._map_data:
            self._show_toast("No map loaded")
            return

        group = self.state.selected_group_index
        algo_idx = self.state.selected_algo_index
        try:
            name, solve_steps = self._algorithm_step_runner(group, algo_idx)
        except ValueError:
            self._show_toast(f"Group {group + 1} will be implemented later")
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
        try:
            value = int(self.control_panel.seed_input.value)
        except (AttributeError, TypeError, ValueError):
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
            self._show_toast(f"{step.algorithm} completed")
            return False

        if self._is_failure_step(step):
            run.status = "failure"
            run.metrics = self._metrics_from_step(step, success=False)
            self._step_gen = None
            self._show_toast(f"{step.algorithm} failed")
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

            self.screen.fill(COLOR_BG)

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
            self._draw_toast()
            if self._map_data:
                self._draw_map_title()

            pygame.display.flip()

        pygame.quit()

    def _rebuild_views(self) -> None:
        self.graph_view.rect = self.layout.graph_area
        self.log_view.rect = self.layout.log_panel
        self.stats_view.rect = self.layout.stats_overlay
        self.control_panel.rect = self.layout.control_panel
        self.control_panel._build_widgets()

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
        bg.fill((30, 40, 70, 220))
        self.screen.blit(bg, (box_x, box_y))
        self.screen.blit(surf, (box_x + 12, box_y + 6))

    def _draw_map_title(self) -> None:
        assert self._map_data is not None
        font = get_font(11)
        surf = font.render(self._map_data.name, True, (100, 130, 180))
        self.screen.blit(surf, (self.layout.graph_area.x + 8, self.layout.graph_area.y + 6))
