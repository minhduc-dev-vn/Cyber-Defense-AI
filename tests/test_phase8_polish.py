"""Phase 8 stability and delivery checks."""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).parent.parent))

import pygame
import pytest

from algorithms.local_search import simulated_annealing
from core.map_loader import load_map
from ui import theme
from ui.app import App


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def app():
    theme._font_cache.clear()
    instance = App()
    yield instance
    theme._font_cache.clear()
    pygame.quit()


def _drive_until_terminal(app: App, max_steps: int = 100) -> None:
    for _ in range(max_steps):
        if app.state.run_state.status != "running":
            return
        app._do_one_step()
    raise AssertionError("run did not reach a terminal state")


def test_no_path_failure_does_not_crash_app_or_renderer(app: App) -> None:
    assert app._map_data is not None
    for edge in app._map_data.graph.get_all_edges():
        edge.blocked = True

    app._on_start()
    _drive_until_terminal(app)
    app.render_frame()

    assert app.state.run_state.status == "failure"
    assert app.state.run_state.current_step is not None
    assert app.state.run_state.metrics is not None
    assert app.state.run_state.metrics.success is False


def test_reset_restores_initial_run_state(app: App) -> None:
    app._on_start()
    app._do_one_step()
    app.state.selected_node = "PC1"
    app.state.compare_mode = True

    app._on_reset()

    run = app.state.run_state
    assert run.status == "ready"
    assert run.steps == []
    assert run.current_step_index == -1
    assert run.metrics is None
    assert app.state.selected_node is None
    assert app.state.compare_mode is False


def test_pause_then_step_advances_without_corrupting_state(app: App) -> None:
    app._on_start()
    app._do_one_step()
    app._on_pause()
    before_count = len(app.state.run_state.steps)

    app._on_step()

    run = app.state.run_state
    assert len(run.steps) == before_count + 1
    assert run.current_step_index == len(run.steps) - 1
    assert run.status in {"paused", "success", "failure"}


def test_seed_reproducibility_for_random_algorithm() -> None:
    data = load_map(ROOT / "maps" / "defense_optimization.json")

    first = simulated_annealing.run(data.graph, data.hacker_start, data.goal_nodes, seed=2026, max_steps=45)
    second = simulated_annealing.run(data.graph, data.hacker_start, data.goal_nodes, seed=2026, max_steps=45)

    assert first.success and second.success
    assert first.final_state == second.final_state
    assert first.metrics.total_cost == second.metrics.total_cost
    assert first.metrics.extra["seed"] == second.metrics.extra["seed"] == 2026


@pytest.mark.parametrize("size", [(1366, 768), (1920, 1080)])
def test_ui_renders_at_demo_resolutions(app: App, size: tuple[int, int]) -> None:
    app.screen = pygame.display.set_mode(size)
    app.layout.update(*size)
    app._rebuild_views()

    app.render_frame()

    assert app.screen.get_size() == size
    assert app.layout.control_panel.width > 0
    assert app.layout.graph_area.width > 0
    assert app.layout.right_panel.width > 0
    assert app.layout.log_panel.bottom <= size[1]
    assert app.layout.stats_overlay.bottom <= size[1]
    assert not app.layout.graph_area.colliderect(app.layout.right_panel)
