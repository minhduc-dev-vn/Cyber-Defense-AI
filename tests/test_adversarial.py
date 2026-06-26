"""Tests for Phase 6 adversarial search."""
from __future__ import annotations

from pathlib import Path

from algorithms.adversarial import alpha_beta, expectimax, minimax
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
