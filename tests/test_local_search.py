"""Tests for Phase 5 local-search algorithms."""
from __future__ import annotations

from pathlib import Path

from algorithms.local_search import (
    simple_hill_climbing,
    simulated_annealing,
    steepest_hill_climbing,
)
from algorithms.local_search.common import (
    defense_value,
    initial_config,
    occupied_nodes,
    resource_cost,
    risk_cost,
)
from core.map_loader import load_map


ROOT = Path(__file__).resolve().parents[1]


def _local_map():
    return load_map(ROOT / "maps" / "defense_optimization.json")


def _assert_valid_config(result) -> None:
    config = result.final_state
    assert config is not None
    assert resource_cost(config) == 4
    assert len(occupied_nodes(config)) == 4


def test_simple_hill_climbing_improves_or_keeps_initial_value() -> None:
    data = _local_map()
    initial = initial_config(data.graph, data.hacker_start, data.goal_nodes)
    initial_value = defense_value(data.graph, data.hacker_start, data.goal_nodes, initial)

    result = simple_hill_climbing.run(data.graph, data.hacker_start, data.goal_nodes)

    assert result.success
    _assert_valid_config(result)
    assert result.metrics.total_cost >= initial_value
    assert "defense_value" in result.metrics.extra


def test_steepest_hill_climbing_checks_neighbor_batches() -> None:
    data = _local_map()
    result = steepest_hill_climbing.run(data.graph, data.hacker_start, data.goal_nodes)

    assert result.success
    _assert_valid_config(result)
    assert any("neighbors_checked" in step.data for step in result.steps)
    assert result.metrics.extra["defense_value"] == result.metrics.total_cost


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

    assert first.success
    assert second.success
    _assert_valid_config(first)
    _assert_valid_config(second)
    assert first.final_state == second.final_state
    assert first.metrics.total_cost == second.metrics.total_cost


def test_risk_cost_and_defense_value_are_real_scores() -> None:
    data = _local_map()
    config = initial_config(data.graph, data.hacker_start, data.goal_nodes)

    value = defense_value(data.graph, data.hacker_start, data.goal_nodes, config)
    risk = risk_cost(data.graph, data.hacker_start, data.goal_nodes, config)

    assert isinstance(value, int)
    assert isinstance(risk, int)
    assert value != risk
