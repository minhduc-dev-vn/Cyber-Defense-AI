"""Tests for Phase 6 adversarial search."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from algorithms.adversarial import alpha_beta, expectimax, minimax
from algorithms.adversarial.common import is_terminal
from algorithms.adversarial.game_loop import (
    legal_hacker_actions,
    new_game_state,
    play_hacker_turn,
)
from core.map_loader import load_map


ROOT = Path(__file__).resolve().parents[1]


def _game_map():
    return load_map(ROOT / "maps" / "adversarial_game.json")


def test_minimax_returns_a_real_hacker_action() -> None:
    data = _game_map()
    result = minimax.run(data.graph, data.hacker_start, data.goal_nodes, depth=3)

    assert result.success
    assert result.final_state is not None
    assert result.final_state.actor == "hacker"
    assert result.final_state.action_type == "move"
    assert result.metrics.extra["nodes_evaluated"] > 0


def test_adversarial_map_has_multiple_routes() -> None:
    data = _game_map()

    assert data.graph.node_count() >= 14
    assert data.graph.edge_count() >= 24
    assert len(data.graph.all_simple_paths(data.hacker_start, "Server", max_paths=10)) >= 4
    assert len(data.graph.all_simple_paths(data.hacker_start, "Database", max_paths=10)) >= 4


def test_adversarial_terminal_uses_declared_goals_only() -> None:
    data = _game_map()
    state = new_game_state(data.graph, data.hacker_start, max_turns=10)

    app_server_state = replace(state, hacker_position="AppServer")
    server_state = replace(state, hacker_position="Server")

    assert not is_terminal(data.graph, app_server_state, data.goal_nodes)
    assert is_terminal(data.graph, server_state, data.goal_nodes)


def test_alpha_beta_matches_minimax_and_prunes() -> None:
    data = _game_map()
    mm = minimax.run(data.graph, data.hacker_start, data.goal_nodes, depth=4)
    ab = alpha_beta.run(data.graph, data.hacker_start, data.goal_nodes, depth=4)

    assert ab.success
    assert mm.final_state == ab.final_state
    assert ab.metrics.extra["nodes_evaluated"] <= mm.metrics.extra["nodes_evaluated"]
    assert ab.metrics.extra["pruned_branches"] > 0


def test_expectimax_uses_valid_chance_probabilities() -> None:
    data = _game_map()
    result = expectimax.run(data.graph, data.hacker_start, data.goal_nodes, depth=3)

    assert result.success
    outcomes = result.metrics.extra["chance_outcomes"]
    assert outcomes
    assert sum(probability for probability, _ in outcomes) == 1.0
    assert "expected_value" in result.metrics.extra


def test_adversarial_steps_expose_tree_values_for_ui() -> None:
    data = _game_map()
    result = alpha_beta.run(data.graph, data.hacker_start, data.goal_nodes, depth=3)

    assert any("alpha" in step.data and "beta" in step.data for step in result.steps)
    assert result.steps[-1].data["action"] is not None


def test_interactive_turn_moves_hacker_then_ai_responds() -> None:
    data = _game_map()
    state = new_game_state(data.graph, data.hacker_start, max_turns=10)

    actions = legal_hacker_actions(data.graph, state, data.goal_nodes)
    assert any(action.action_type == "move" and action.target == "Gateway" for action in actions)

    result = play_hacker_turn(
        data.graph,
        state,
        data.goal_nodes,
        "move",
        "Gateway",
        "Alpha-Beta",
        depth=3,
    )

    assert result.state.hacker_position == "Gateway"
    assert result.state.turn == "hacker"
    assert result.defender_action is not None
    assert result.steps[-1].data["defender_action"] == result.defender_action
    assert result.steps[0].data["attack_edges"]
    assert result.steps[-1].data["defender_edges"]
    assert result.steps[-1].data["ai_focus_node"]
    assert len(result.state.history) == 2


def test_interactive_turn_rejects_illegal_move() -> None:
    data = _game_map()
    state = new_game_state(data.graph, data.hacker_start, max_turns=10)

    try:
        play_hacker_turn(data.graph, state, data.goal_nodes, "move", "Server", "Minimax", depth=2)
    except ValueError as exc:
        assert "Cannot move" in str(exc)
    else:
        raise AssertionError("Expected an illegal move to be rejected.")


def test_interactive_terminal_step_explains_winner() -> None:
    data = _game_map()
    state = replace(new_game_state(data.graph, data.hacker_start, max_turns=10), hacker_position="FirewallA")

    result = play_hacker_turn(
        data.graph,
        state,
        data.goal_nodes,
        "move",
        "Server",
        "Alpha-Beta",
        depth=3,
    )

    assert result.terminal
    assert result.winner == "hacker"
    assert result.steps[-1].data["outcome_title"] == "Hacker thành công"
    assert "Server" in result.steps[-1].data["outcome_reason"]
