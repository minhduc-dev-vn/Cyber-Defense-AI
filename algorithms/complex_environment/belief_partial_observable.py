"""Belief-state search with partial IDS observations."""
from __future__ import annotations

import time
from typing import Iterator

from algorithms.complex_environment.belief_unobservable import _search_plan
from algorithms.complex_environment.common import (
    belief_is_safe,
    initial_belief,
    observation_region,
    possible_after_one_hacker_move,
)
from core.graph import NetworkGraph
from core.models import AlgorithmMetrics, AlgorithmResult, BeliefState, StepEvent


def solve_steps(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    metadata: dict | None = None,
) -> Iterator[StepEvent]:
    """Yield partial-observable belief update and planning steps."""
    metadata = metadata or {}
    ids_node = metadata.get("ids_node", "IDS")
    radius = int(metadata.get("ids_observation_radius", 1))
    observed = observation_region(graph, ids_node, radius)
    hidden_nodes = [node.id for node in graph.get_all_nodes() if node.id not in observed]
    belief0 = initial_belief(graph, metadata)
    step_idx = 0

    yield StepEvent(
        step_index=step_idx,
        algorithm="Belief Partial",
        event_type="info",
        message=f"[Step {step_idx:03d}] Partial: initial belief={sorted(belief0)}, observed={sorted(observed)}.",
        data={"belief": sorted(belief0), "observed_nodes": sorted(observed), "hidden_nodes": hidden_nodes},
    )
    step_idx += 1

    possible = possible_after_one_hacker_move(graph, belief0)
    belief1 = frozenset(pos for pos in possible if pos in observed or any(n in observed for n in graph.neighbors(pos, ignore_blocked=True)))
    if not belief1:
        belief1 = belief0
    yield StepEvent(
        step_index=step_idx,
        algorithm="Belief Partial",
        event_type="update",
        current_node=ids_node,
        message=(
            f"[Step {step_idx:03d}] Partial: observation near {ids_node}; "
            f"belief {sorted(belief0)} -> {sorted(belief1)}."
        ),
        data={
            "belief": sorted(belief1),
            "previous_belief": sorted(belief0),
            "observed_nodes": sorted(observed),
            "hidden_nodes": hidden_nodes,
            "observation": f"suspicious activity near {ids_node}",
        },
    )
    step_idx += 1

    plan, expanded = _search_plan(graph, belief1, goals, max_depth=3)
    blocked: list[str] = []
    for action in plan:
        blocked.append(action.target)
        yield StepEvent(
            step_index=step_idx,
            algorithm="Belief Partial",
            event_type="update",
            current_node=action.target,
            frontier=blocked,
            message=f"[Step {step_idx:03d}] Partial: apply {action.description}.",
            nodes_expanded=expanded,
            nodes_generated=len(plan),
            total_cost=float(len(blocked)),
            data={
                "belief": sorted(belief1),
                "observed_nodes": sorted(observed),
                "hidden_nodes": hidden_nodes,
                "blocked_nodes": list(blocked),
                "plan": [item.description for item in plan],
            },
        )
        step_idx += 1

    success = bool(plan) and belief_is_safe(graph, belief1, goals, blocked)
    yield StepEvent(
        step_index=step_idx,
        algorithm="Belief Partial",
        event_type="found" if success else "failure",
        frontier=blocked,
        message=(
            f"[Step {step_idx:03d}] Partial: "
            f"{'plan found' if success else 'no plan found'} after observation."
        ),
        nodes_expanded=expanded,
        nodes_generated=len(plan),
        total_cost=float(len(blocked)),
        data={
            "belief": sorted(belief1),
            "observed_nodes": sorted(observed),
            "hidden_nodes": hidden_nodes,
            "blocked_nodes": list(blocked),
            "plan": [item.description for item in plan],
        },
    )


def run(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    metadata: dict | None = None,
) -> AlgorithmResult:
    """Run partial-observable belief-state search."""
    start_time = time.perf_counter()
    steps = list(solve_steps(graph, start, goals, metadata=metadata))
    time_ms = (time.perf_counter() - start_time) * 1000.0
    last = steps[-1] if steps else None
    success = last is not None and last.event_type == "found"
    final_state = BeliefState(frozenset(last.data.get("belief", []))) if last else None
    metrics = AlgorithmMetrics(
        algorithm="Belief Partial",
        success=success,
        total_cost=last.total_cost if last else 0.0,
        nodes_expanded=last.nodes_expanded if last else 0,
        nodes_generated=last.nodes_generated if last else 0,
        time_ms=time_ms,
        num_steps=len(steps),
        extra=dict(last.data) if last else {},
    )
    return AlgorithmResult(metrics=metrics, steps=steps, final_state=final_state)
