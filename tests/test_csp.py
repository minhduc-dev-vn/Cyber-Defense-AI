"""Tests for Phase 4 CSP algorithms."""
from __future__ import annotations

from pathlib import Path

from algorithms.csp import backtracking, forward_checking, min_conflicts
from algorithms.csp.common import final_violations
from core.map_loader import load_map


ROOT = Path(__file__).resolve().parents[1]


def _csp_map():
    return load_map(ROOT / "maps" / "csp_segmentation.json")


def test_backtracking_finds_valid_zone_assignment() -> None:
    data = _csp_map()
    result = backtracking.run(data.graph, data.hacker_start, data.goal_nodes)

    assert result.success
    assert result.final_state is not None
    assert len(result.final_state.assignments) == data.graph.node_count()
    assert final_violations(data.graph, result.final_state.assignments) == []
    assert result.final_state.assignments["PC2"] == "Quarantine Zone"
    assert result.final_state.assignments["Server"] == "Server Zone"
    assert result.final_state.assignments["Database"] == "Server Zone"


def test_forward_checking_finds_valid_assignment_and_prunes_domains() -> None:
    data = _csp_map()
    result = forward_checking.run(data.graph, data.hacker_start, data.goal_nodes)

    assert result.success
    assert result.final_state is not None
    assert final_violations(data.graph, result.final_state.assignments) == []
    assert any(step.data.get("removed") for step in result.steps)
    assert any(step.event_type == "found" for step in result.steps)


def test_min_conflicts_is_seed_reproducible() -> None:
    data = _csp_map()
    first = min_conflicts.run(data.graph, data.hacker_start, data.goal_nodes, seed=7, max_steps=500)
    second = min_conflicts.run(data.graph, data.hacker_start, data.goal_nodes, seed=7, max_steps=500)

    assert first.success
    assert second.success
    assert first.final_state is not None
    assert second.final_state is not None
    assert first.final_state.assignments == second.final_state.assignments
    assert final_violations(data.graph, first.final_state.assignments) == []


def test_csp_steps_expose_assignments_for_ui_coloring() -> None:
    data = _csp_map()
    result = backtracking.run(data.graph, data.hacker_start, data.goal_nodes)

    assert result.steps[-1].data["assignments"]
    assert result.steps[-1].highlighted_edges
