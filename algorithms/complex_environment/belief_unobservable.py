"""Belief-state search in a fully unobservable environment."""
from __future__ import annotations

import time
from collections import deque
from typing import Any, Iterator

from algorithms.complex_environment.common import (
    action_for_block,
    belief_is_safe,
    choke_candidates,
    initial_belief,
    possible_after_one_hacker_move,
)
from core.graph import NetworkGraph
from core.models import Action, AlgorithmMetrics, AlgorithmResult, BeliefState, StepEvent


def _search_plan_generator(
    graph: NetworkGraph,
    belief0: frozenset[str],
    goals: list[str],
    state: dict[str, Any],
    max_depth: int = 3,
) -> Iterator[StepEvent]:
    # State includes (belief, blocked, plan)
    queue: deque[tuple[frozenset[str], frozenset[str], list[Action]]] = deque([(belief0, frozenset(), [])])
    seen = {(belief0, frozenset())}
    expanded = 0
    candidates = choke_candidates(graph, goals)
    
    hidden_nodes = state["hidden_nodes"]
    algorithm = state["algorithm"]

    while queue:
        belief, blocked, plan = queue.popleft()
        expanded += 1
        
        # Yield exploration step
        if plan:
            yield StepEvent(
                step_index=state["step_idx"],
                algorithm=algorithm,
                event_type="update",
                current_node=plan[-1].target if plan else None,
                frontier=list(blocked),
                message=f"[Step {state['step_idx']:03d}] {algorithm.split()[0]}: xét chặn {list(blocked)}, belief mở rộng thành {list(belief)}.",
                nodes_expanded=expanded,
                nodes_generated=len(plan),
                total_cost=float(len(blocked)),
                data={
                    "belief": sorted(belief),
                    "hidden_nodes": hidden_nodes,
                    "blocked_nodes": list(blocked),
                    "plan": [item.description for item in plan],
                    "teacher_view": False,
                    "observed_nodes": state.get("observed_nodes", [])
                },
            )
            state["step_idx"] += 1

        # Check failure
        if any(g in belief for g in goals):
            continue

        # Check success
        if not belief or belief_is_safe(graph, belief, goals, blocked):
            state["plan"] = plan
            state["expanded"] = expanded
            state["blocked"] = list(blocked)
            state["final_belief"] = list(belief)
            return

        if len(plan) >= max_depth:
            continue
            
        for node_id in candidates:
            if node_id in blocked:
                continue
            next_blocked = blocked | frozenset([node_id])
            next_belief = frozenset(p for p in possible_after_one_hacker_move(graph, belief) if p not in next_blocked)
            
            state_key = (next_belief, next_blocked)
            if state_key in seen:
                continue
            seen.add(state_key)
            queue.append((next_belief, next_blocked, plan + [action_for_block(node_id)]))
            
    state["plan"] = []
    state["expanded"] = expanded
    state["blocked"] = []
    state["final_belief"] = []
    return


def solve_steps(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    metadata: dict | None = None,
) -> Iterator[StepEvent]:
    """Yield belief-state planning steps for an unobservable map."""
    belief = initial_belief(graph, metadata)
    hidden_nodes = [node.id for node in graph.get_all_nodes() if not node.visible]
    
    state = {
        "step_idx": 0,
        "algorithm": "Belief Unobservable",
        "hidden_nodes": hidden_nodes,
        "plan": [],
        "expanded": 0,
        "blocked": []
    }

    yield StepEvent(
        step_index=state["step_idx"],
        algorithm="Belief Unobservable",
        event_type="info",
        current_node=None,
        message=f"[Step {state['step_idx']:03d}] Belief: initial possible Hacker positions = {sorted(belief)}.",
        data={"belief": sorted(belief), "hidden_nodes": hidden_nodes, "teacher_view": False, "blocked_nodes": []},
    )
    state["step_idx"] += 1

    yield from _search_plan_generator(graph, belief, goals, state)

    plan = state["plan"]
    expanded = state["expanded"]
    blocked = frozenset(state["blocked"])
    final_belief = state.get("final_belief", list(belief))
    success = bool(plan) and (not final_belief or belief_is_safe(graph, frozenset(final_belief), goals, blocked))
    
    yield StepEvent(
        step_index=state["step_idx"],
        algorithm="Belief Unobservable",
        event_type="found" if success else "failure",
        frontier=list(blocked),
        message=(
            f"[Step {state['step_idx']:03d}] Belief: "
            f"{'conditional-free plan found' if success else 'no plan found'}; "
            f"plan={[item.description for item in plan]}."
        ),
        nodes_expanded=expanded,
        nodes_generated=len(plan),
        total_cost=float(len(blocked)),
        data={
            "belief": sorted(final_belief) if success else sorted(belief),
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
