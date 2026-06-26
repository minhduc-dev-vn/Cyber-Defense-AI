"""Belief-state search in a fully unobservable environment."""
from __future__ import annotations

import time
from collections import deque
from typing import Iterator

from algorithms.complex_environment.common import (
    action_for_block,
    belief_is_safe,
    choke_candidates,
    initial_belief,
)
from core.graph import NetworkGraph
from core.models import Action, AlgorithmMetrics, AlgorithmResult, BeliefState, StepEvent


def _search_plan(
    graph: NetworkGraph,
    belief: frozenset[str],
    goals: list[str],
    max_depth: int = 3,
) -> tuple[list[Action], int]:
    queue: deque[tuple[frozenset[str], list[Action]]] = deque([(frozenset(), [])])
    seen = {frozenset()}
    expanded = 0
    candidates = choke_candidates(graph, goals)
    while queue:
        blocked, plan = queue.popleft()
        expanded += 1
        if belief_is_safe(graph, belief, goals, blocked):
            return plan, expanded
        if len(plan) >= max_depth:
            continue
        for node_id in candidates:
            if node_id in blocked:
                continue
            next_blocked = blocked | frozenset([node_id])
            if next_blocked in seen:
                continue
            seen.add(next_blocked)
            queue.append((next_blocked, plan + [action_for_block(node_id)]))
    return [], expanded


def solve_steps(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    metadata: dict | None = None,
) -> Iterator[StepEvent]:
    """Yield belief-state planning steps for an unobservable map."""
    belief = initial_belief(graph, metadata)
    step_idx = 0
    hidden_nodes = [node.id for node in graph.get_all_nodes() if not node.visible]
    yield StepEvent(
        step_index=step_idx,
        algorithm="Belief Unobservable",
        event_type="info",
        current_node=None,
        message=f"[Step {step_idx:03d}] Belief: initial possible Hacker positions = {sorted(belief)}.",
        data={"belief": sorted(belief), "hidden_nodes": hidden_nodes, "teacher_view": False, "blocked_nodes": []},
    )
    step_idx += 1

    plan, expanded = _search_plan(graph, belief, goals)
    blocked: list[str] = []
    for action in plan:
        blocked.append(action.target)
        safe = belief_is_safe(graph, belief, goals, blocked)
        yield StepEvent(
            step_index=step_idx,
            algorithm="Belief Unobservable",
            event_type="update",
            current_node=action.target,
            frontier=blocked,
            message=(
                f"[Step {step_idx:03d}] Belief: apply {action.description}; "
                f"safe_for_all_belief={safe}."
            ),
            nodes_expanded=expanded,
            nodes_generated=len(plan),
            total_cost=float(len(blocked)),
            data={
                "belief": sorted(belief),
                "hidden_nodes": hidden_nodes,
                "blocked_nodes": list(blocked),
                "plan": [item.description for item in plan],
                "teacher_view": False,
            },
        )
        step_idx += 1

    success = bool(plan) and belief_is_safe(graph, belief, goals, blocked)
    yield StepEvent(
        step_index=step_idx,
        algorithm="Belief Unobservable",
        event_type="found" if success else "failure",
        frontier=blocked,
        message=(
            f"[Step {step_idx:03d}] Belief: "
            f"{'conditional-free plan found' if success else 'no plan found'}; "
            f"plan={[item.description for item in plan]}."
        ),
        nodes_expanded=expanded,
        nodes_generated=len(plan),
        total_cost=float(len(blocked)),
        data={
            "belief": sorted(belief),
            "hidden_nodes": hidden_nodes,
            "blocked_nodes": list(blocked),
            "plan": [item.description for item in plan],
            "teacher_view": False,
        },
    )


def run(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    metadata: dict | None = None,
) -> AlgorithmResult:
    """Run unobservable belief-state search."""
    start_time = time.perf_counter()
    steps = list(solve_steps(graph, start, goals, metadata=metadata))
    time_ms = (time.perf_counter() - start_time) * 1000.0
    last = steps[-1] if steps else None
    success = last is not None and last.event_type == "found"
    final_state = BeliefState(frozenset(last.data.get("belief", []))) if last else None
    metrics = AlgorithmMetrics(
        algorithm="Belief Unobservable",
        success=success,
        total_cost=last.total_cost if last else 0.0,
        nodes_expanded=last.nodes_expanded if last else 0,
        nodes_generated=last.nodes_generated if last else 0,
        time_ms=time_ms,
        num_steps=len(steps),
        extra=dict(last.data) if last else {},
    )
    return AlgorithmResult(metrics=metrics, steps=steps, final_state=final_state)
