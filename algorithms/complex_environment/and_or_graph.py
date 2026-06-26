"""AND-OR graph search for conditional defender plans."""
from __future__ import annotations

import time
from typing import Any, Iterator

from algorithms.complex_environment.common import belief_is_safe, initial_belief
from core.graph import NetworkGraph
from core.models import Action, AlgorithmMetrics, AlgorithmResult, StepEvent


def _outcomes(action: Action, blocked: frozenset[str]) -> list[tuple[str, frozenset[str]]]:
    if action.target == "Firewall":
        return [
            ("lockdown succeeds", blocked | frozenset(["Firewall"])),
            ("manual fallback blocks Router and Switch", blocked | frozenset(["Router", "Switch"])),
        ]
    return [
        ("success", blocked | frozenset([action.target])),
        ("failure", blocked),
    ]


def _actions(blocked: frozenset[str], tried: frozenset[str]) -> list[Action]:
    candidates = ["Router", "Switch", "Firewall"]
    return [
        Action("defender", "uncertain_block", node_id, f"Try isolate {node_id}")
        for node_id in candidates
        if node_id not in tried and node_id not in blocked
    ]


def _and_or_search(
    graph: NetworkGraph,
    belief: frozenset[str],
    goals: list[str],
    blocked: frozenset[str],
    tried: frozenset[str],
    counters: dict[str, int],
) -> dict[str, Any] | None:
    counters["visited"] += 1
    if belief_is_safe(graph, belief, goals, blocked):
        return {"type": "goal", "blocked_nodes": sorted(blocked)}

    for action in _actions(blocked, tried):
        branches: dict[str, Any] = {}
        ok = True
        for outcome_name, next_blocked in _outcomes(action, blocked):
            subtree = _and_or_search(
                graph,
                belief,
                goals,
                next_blocked,
                tried | frozenset([action.target]),
                counters,
            )
            if subtree is None:
                ok = False
                break
            branches[outcome_name] = subtree
        if ok:
            return {
                "type": "action",
                "action": action.description,
                "target": action.target,
                "branches": branches,
                "blocked_nodes": sorted(blocked),
            }
    return None


def _plan_lines(plan: dict[str, Any], prefix: str = "") -> list[str]:
    if plan.get("type") == "goal":
        return [f"{prefix}Safe with blocked={plan.get('blocked_nodes', [])}"]
    lines = [f"{prefix}{plan['action']}"]
    for outcome, subtree in plan.get("branches", {}).items():
        lines.extend(_plan_lines(subtree, prefix=f"{prefix}  If {outcome} -> "))
    return lines


def solve_steps(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    metadata: dict | None = None,
) -> Iterator[StepEvent]:
    """Yield AND-OR conditional-plan steps."""
    belief = initial_belief(graph, metadata)
    counters = {"visited": 0}
    step_idx = 0
    yield StepEvent(
        step_index=step_idx,
        algorithm="AND-OR",
        event_type="info",
        message=f"[Step {step_idx:03d}] AND-OR: belief={sorted(belief)}.",
        data={"belief": sorted(belief), "plan_tree": None},
    )
    step_idx += 1

    plan = _and_or_search(graph, belief, goals, frozenset(), frozenset(), counters)
    if plan:
        for line in _plan_lines(plan)[:6]:
            yield StepEvent(
                step_index=step_idx,
                algorithm="AND-OR",
                event_type="update",
                current_node=plan.get("target"),
                message=f"[Step {step_idx:03d}] AND-OR: {line}",
                nodes_expanded=counters["visited"],
                nodes_generated=counters["visited"],
                data={"belief": sorted(belief), "plan_tree": plan, "plan_lines": _plan_lines(plan)},
            )
            step_idx += 1

    yield StepEvent(
        step_index=step_idx,
        algorithm="AND-OR",
        event_type="found" if plan else "failure",
        current_node=plan.get("target") if plan else None,
        message=(
            f"[Step {step_idx:03d}] AND-OR: "
            f"{'conditional plan found' if plan else 'no conditional plan'}."
        ),
        nodes_expanded=counters["visited"],
        nodes_generated=counters["visited"],
        total_cost=float(counters["visited"]),
        data={
            "belief": sorted(belief),
            "plan_tree": plan,
            "plan_lines": _plan_lines(plan) if plan else [],
        },
    )


def run(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    metadata: dict | None = None,
) -> AlgorithmResult:
    """Run AND-OR graph search."""
    start_time = time.perf_counter()
    steps = list(solve_steps(graph, start, goals, metadata=metadata))
    time_ms = (time.perf_counter() - start_time) * 1000.0
    last = steps[-1] if steps else None
    success = last is not None and last.event_type == "found"
    metrics = AlgorithmMetrics(
        algorithm="AND-OR",
        success=success,
        total_cost=last.total_cost if last else 0.0,
        nodes_expanded=last.nodes_expanded if last else 0,
        nodes_generated=last.nodes_generated if last else 0,
        time_ms=time_ms,
        num_steps=len(steps),
        extra=dict(last.data) if last else {},
    )
    return AlgorithmResult(metrics=metrics, steps=steps, final_state=last.data.get("plan_tree") if last else None)
