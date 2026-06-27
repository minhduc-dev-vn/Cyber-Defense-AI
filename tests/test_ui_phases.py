"""
test_ui_phases.py - Headless checks for Phase 1-3 UI wiring.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).parent.parent))

import pygame
import pytest

from ui.app import App


@pytest.fixture
def app():
    instance = App()
    yield instance
    pygame.quit()


def test_graph_click_uses_graph_panel_offset(app):
    graph = app._map_data.graph
    node = graph.get_node(app._map_data.hacker_start)
    assert node is not None

    x = app.layout.graph_area.x + node.position[0]
    y = app.layout.graph_area.y + node.position[1]
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (x, y)})
    app.graph_view.handle_event(event)

    assert app.state.selected_node == node.id


def test_compare_group_1_runs_bfs_dfs_ucs(app):
    app.state.selected_group_index = 0
    app._on_compare()

    names = [result.metrics.algorithm for result in app.state.compare_results]
    assert app.state.compare_mode
    assert names == ["BFS", "DFS", "UCS"]
    assert all(result.steps for result in app.state.compare_results)


def test_compare_group_2_runs_informed_algorithms(app):
    app.state.selected_group_index = 1
    app._load_map("weighted_network")
    app._on_compare()

    names = [result.metrics.algorithm for result in app.state.compare_results]
    assert app.state.compare_mode
    assert names == ["Greedy", "A*", "IDA*"]
    assert all(result.success for result in app.state.compare_results)


def test_compare_group_3_reports_local_search_metrics(app):
    app.state.selected_group_index = 2
    app._load_map("defense_optimization")
    app._on_compare()

    names = [result.metrics.algorithm for result in app.state.compare_results]
    log_text = "\n".join(entry.message for entry in app.state.run_state.log.get_all())

    assert app.state.compare_mode
    assert names == ["Simple HC", "Steepest HC", "Sim. Annealing"]
    assert all(result.metrics.extra.get("local_search_mode") == "heuristic_path" for result in app.state.compare_results)
    assert all("current_heuristic" in result.metrics.extra for result in app.state.compare_results)
    assert "PathCost" in log_text
    assert "h cuối" in log_text


def test_group_2_step_builds_selected_algorithm(app):
    app.state.selected_group_index = 1
    app.state.selected_algo_index = 1
    app._load_map("weighted_network")
    app._on_step()

    step = app.state.run_state.current_step
    assert step is not None
    assert step.algorithm == "A*"
    assert {"g", "h", "f"}.issubset(step.data)


def test_adversarial_click_move_runs_ai_response(app):
    app.state.selected_group_index = 5
    app.state.selected_algo_index = 1
    app._load_map("adversarial_game")
    app.graph_view.set_graph(app._map_data.graph)
    app.control_panel._build_widgets()
    app.state.adversarial_hacker_action = "move"

    target = app._map_data.graph.get_node("Gateway")
    assert target is not None
    assert app.graph_view._renderer is not None
    pos = app.graph_view._renderer._node_pos(target)
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": pos})
    app._handle_adversarial_graph_event(event)

    game_state = app.state.adversarial_game_state
    assert game_state is not None
    assert game_state.hacker_position == "Gateway"
    assert len(game_state.history) == 2
    assert app.state.run_state.current_step is not None
    assert app.state.run_state.current_step.data["defender_action"] is not None

    assert app.control_panel.btn_adversarial_reset is not None
    assert app.control_panel.adversarial_action_buttons == []
    app.control_panel.btn_adversarial_reset.on_click()

    assert app.state.adversarial_game_state is None
    assert app.state.run_state.current_step is None


def test_adversarial_start_point_can_switch_to_pc2(app):
    app.state.selected_group_index = 5
    app._load_map("adversarial_game")
    app.graph_view.set_graph(app._map_data.graph)
    app.control_panel._build_widgets()

    labels = [button.label for button in app.control_panel.adversarial_start_buttons]
    assert labels == ["PC1", "PC2"]

    app.control_panel.adversarial_start_buttons[1].on_click()
    assert app.state.selected_start_node == "PC2"
    assert app.state.adversarial_game_state is None
    assert app._current_hacker_position() == "PC2"

    app._execute_adversarial_turn("move", "VPN")
    game_state = app.state.adversarial_game_state
    assert game_state is not None
    assert game_state.hacker_position == "VPN"
