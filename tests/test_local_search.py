"""Tests for weighted-graph local-search algorithms."""
from __future__ import annotations

from pathlib import Path

from algorithms.local_search import (
    simple_hill_climbing,
    simulated_annealing,
    steepest_hill_climbing,
)
from algorithms.local_search.common import (
    heuristic_value,
    neighbor_heuristics,
    path_cost,
    shortest_path_to_goal,
)
from core.map_loader import load_map


ROOT = Path(__file__).resolve().parents[1]


def _local_map():
    return load_map(ROOT / "maps" / "defense_optimization.json")


def _assert_goal_path(result) -> None:
    assert result.success
    assert result.metrics.path
    assert result.metrics.path[-1] == "Server"
    assert result.metrics.extra["local_search_mode"] == "heuristic_path"
    assert result.metrics.extra["final_heuristic"] == 0


def test_heuristic_is_shortest_weighted_cost_to_goal() -> None:
    data = _local_map()

    cost, path = shortest_path_to_goal(data.graph, "Hacker", data.goal_nodes)

    assert cost == heuristic_value(data.graph, "Hacker", data.goal_nodes)
    assert path[0] == "Hacker"
    assert path[-1] == "Server"
    assert path_cost(data.graph, path) == cost


def test_simple_hill_climbing_moves_to_lower_heuristic_until_goal() -> None:
    data = _local_map()
    result = simple_hill_climbing.run(data.graph, data.hacker_start, data.goal_nodes)

    _assert_goal_path(result)
    move_steps = [step for step in result.steps if step.event_type == "move"]
    assert move_steps
    assert all(step.data["current_heuristic"] >= 0 for step in move_steps)
    assert any(step.data.get("neighbor_scores") for step in result.steps)


def test_steepest_hill_climbing_checks_all_neighbors_before_move() -> None:
    data = _local_map()
    result = steepest_hill_climbing.run(data.graph, data.hacker_start, data.goal_nodes)

    _assert_goal_path(result)
    scan_steps = [step for step in result.steps if "neighbors_checked" in step.data]
    assert scan_steps
    assert scan_steps[0].data["neighbors_checked"] == len(
        neighbor_heuristics(data.graph, data.hacker_start, data.goal_nodes)
    )


def test_simulated_annealing_is_seed_reproducible() -> None:
    data = _local_map()
    first = simulated_annealing.run(
        data.graph,
        data.hacker_start,
        data.goal_nodes,
        seed=11,
        max_steps=30,
    )
    second = simulated_annealing.run(
        data.graph,
        data.hacker_start,
        data.goal_nodes,
        seed=11,
        max_steps=30,
    )

    assert first.success == second.success
    assert first.final_state == second.final_state
    assert first.metrics.total_cost == second.metrics.total_cost
    assert first.metrics.extra["local_search_mode"] == "heuristic_path"
