"""AND-OR graph search for conditional defender plans."""
from __future__ import annotations

import time
from typing import Any, Iterator

from algorithms.complex_environment.common import (
    belief_is_safe,
    initial_belief,
    possible_after_one_hacker_move,
)
from core.graph import NetworkGraph
from core.models import AlgorithmMetrics, AlgorithmResult, BeliefState, StepEvent


def _actions(blocked: frozenset[str], tried: frozenset[str]) -> list[Any]:
    from core.models import Action
    candidates = ["Router", "Switch", "Firewall"]
    return [
        Action("defender", "uncertain_block", node_id, f"Try isolate {node_id}")
        for node_id in candidates
        if node_id not in tried and node_id not in blocked
    ]


def _outcomes(action: Any, blocked: frozenset[str]) -> list[tuple[str, frozenset[str]]]:
    if action.target == "Firewall":
        return [
            ("success", blocked | frozenset(["Firewall"])),
            ("fallback", blocked | frozenset(["Router", "Switch"])),
        ]
    return [
        ("success", blocked | frozenset([action.target])),
        ("failure", blocked),
    ]


def _and_or_search_generator(
    graph: NetworkGraph,
    belief: frozenset[str],
    goals: list[str],
    blocked: frozenset[str],
    tried: frozenset[str],
    state: dict[str, Any],
) -> Iterator[StepEvent]:
    state["counters"]["visited"] += 1
    
    yield StepEvent(
        step_index=state["step_idx"],
        algorithm="AND-OR",
        event_type="update",
        current_node=None,
        message=f"[Step {state['step_idx']:03d}] AND-OR: thử nghiệm trạng thái chặn={list(blocked)}, belief={list(belief)}",
        nodes_expanded=state["counters"]["visited"],
        nodes_generated=state["counters"]["visited"],
        data={
            "belief": sorted(belief),
            "plan_tree": None,
            "plan_lines": [f"Thử nghiệm chặn={list(blocked)}"]
        },
    )
    state["step_idx"] += 1

    if not belief or belief_is_safe(graph, belief, goals, blocked):
        return {"type": "goal", "blocked_nodes": sorted(blocked), "final_belief": sorted(belief)}

    for action in _actions(blocked, tried):
        branches: dict[str, Any] = {}
        ok = True
        
        yield StepEvent(
            step_index=state["step_idx"],
            algorithm="AND-OR",
            event_type="update",
            current_node=action.target,
            message=f"[Step {state['step_idx']:03d}] AND-OR: xem xét nhánh {action.description}",
            nodes_expanded=state["counters"]["visited"],
            nodes_generated=state["counters"]["visited"],
            data={
                "belief": sorted(belief),
                "plan_tree": None,
                "plan_lines": [f"Xem xét {action.description}"]
            },
        )
        state["step_idx"] += 1

        for outcome_name, next_blocked in _outcomes(action, blocked):
            next_belief = frozenset(p for p in possible_after_one_hacker_move(graph, belief) if p not in next_blocked)
            subtree = yield from _and_or_search_generator(
                graph,
                next_belief,
                goals,
                next_blocked,
                tried | frozenset([action.target]),
                state,
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
                "final_belief": sorted(belief),
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
    state = {
        "step_idx": 0,
        "counters": {"visited": 0}
    }
    
    yield StepEvent(
        step_index=state["step_idx"],
        algorithm="AND-OR",
        event_type="info",
        message=f"[Step {state['step_idx']:03d}] AND-OR: belief={sorted(belief)}.",
        data={"belief": sorted(belief), "plan_tree": None},
    )
    state["step_idx"] += 1

    plan = yield from _and_or_search_generator(graph, belief, goals, frozenset(), frozenset(), state)

    yield StepEvent(
        step_index=state["step_idx"],
        algorithm="AND-OR",
        event_type="found" if plan else "failure",
        current_node=plan.get("target") if plan else None,
        message=(
            f"[Step {state['step_idx']:03d}] AND-OR: "
            f"{'conditional plan found' if plan else 'no conditional plan'}."
        ),
        nodes_expanded=state["counters"]["visited"],
        nodes_generated=state["counters"]["visited"],
        total_cost=float(state["counters"]["visited"]),
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
