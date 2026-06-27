"""Tests for Phase 7 complex-environment search."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from algorithms.complex_environment import (
    and_or_graph,
    belief_partial_observable,
    belief_unobservable,
)
from algorithms.complex_environment.common import (
    belief_is_safe,
    initial_belief,
    possible_after_one_hacker_move,
)
from core.map_loader import load_map


ROOT = Path(__file__).resolve().parents[1]


def _hidden_map():
    return load_map(ROOT / "maps" / "belief_hidden.json")


def _partial_map():
    return load_map(ROOT / "maps" / "belief_partial.json")


def _leaf_block_sets(plan: dict[str, Any]) -> list[list[str]]:
    if plan.get("type") == "goal":
        return [plan.get("blocked_nodes", [])]
    leaves: list[list[str]] = []
    for subtree in plan.get("branches", {}).values():
        leaves.extend(_leaf_block_sets(subtree))
    return leaves


def test_unobservable_belief_plan_blocks_all_possible_hacker_positions() -> None:
    data = _hidden_map()
    result = belief_unobservable.run(data.graph, data.hacker_start, data.goal_nodes, metadata=data.metadata)

    assert result.success
    belief = result.metrics.extra["belief"]
    blocked_nodes = result.metrics.extra["blocked_nodes"]
    for g in data.goal_nodes:
        assert g not in belief
    assert bool(blocked_nodes)
    assert result.metrics.extra["teacher_view"] is False


def test_partial_observation_updates_belief_to_observation_compatible_states() -> None:
    data = _partial_map()
    result = belief_partial_observable.run(data.graph, data.hacker_start, data.goal_nodes, metadata=data.metadata)

    assert result.success
    updated = set(result.metrics.extra["belief"])
    assert updated
    for g in data.goal_nodes:
        assert g not in updated
    assert belief_is_safe(data.graph, updated, data.goal_nodes, result.metrics.extra["blocked_nodes"])


def test_and_or_graph_returns_conditional_plan_with_safe_leaves() -> None:
    data = _hidden_map()
    result = and_or_graph.run(data.graph, data.hacker_start, data.goal_nodes, metadata=data.metadata)

    assert result.success
    assert result.final_state is not None
    assert result.final_state["type"] == "action"
    leaves = _leaf_block_sets(result.final_state)
    assert leaves
    for blocked_nodes in leaves:
        assert belief_is_safe(data.graph, data.metadata["belief_initial"], data.goal_nodes, blocked_nodes)


def test_complex_steps_expose_belief_and_plan_for_ui() -> None:
    data = _hidden_map()
    result = and_or_graph.run(data.graph, data.hacker_start, data.goal_nodes, metadata=data.metadata)

    assert any("belief" in step.data for step in result.steps)
    assert result.steps[-1].data["plan_lines"]
