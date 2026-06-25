"""
astar.py - A* Search (Group 2).

Chooses the node with the smallest f(n) = g(n) + h(n). With the admissible
heuristic provided by NetworkGraph, A* finds a lowest-cost path.
"""
from __future__ import annotations

import heapq
import time
from typing import Dict, Iterator, List, Optional, Tuple

from core.graph import NetworkGraph
from core.metrics import MetricsCollector
from core.models import AlgorithmMetrics, AlgorithmResult, StepEvent
from core.utils import reconstruct_path


def _best_goal_heuristic(
    graph: NetworkGraph,
    node_id: str,
    goals: List[str],
) -> Tuple[float, str]:
    """Return the smallest heuristic from node_id to any goal."""
    best_h = float("inf")
    best_goal = ""
    for goal in goals:
        h_value = graph.heuristic(node_id, goal)
        if h_value < best_h:
            best_h = h_value
            best_goal = goal
    return best_h, best_goal


def solve_steps(
    graph: NetworkGraph,
    start: str,
    goals: List[str],
) -> Iterator[StepEvent]:
    """Yield A* animation steps."""
    mc = MetricsCollector("A*")
    mc.start()

    goal_set = set(goals)
    start_h, start_goal = _best_goal_heuristic(graph, start, goals)
    g_cost: Dict[str, float] = {start: 0.0}
    parent: Dict[str, Optional[str]] = {start: None}
    frontier: List[Tuple[float, float, str]] = [(start_h, start_h, start)]
    explored: List[str] = []

    step_idx = 0
    mc.update_frontier_size(len(frontier))
    yield StepEvent(
        step_index=step_idx,
        algorithm="A*",
        event_type="info",
        current_node=start,
        frontier=[start],
        explored=[],
        message=(
            f"[Step {step_idx:03d}] A*: init. g(start)=0, "
            f"h(start)={start_h:.2f}, f={start_h:.2f} toward {start_goal!r}"
        ),
        max_frontier_size=mc.max_frontier_size,
        data={"g": 0.0, "h": start_h, "f": start_h, "goal_for_h": start_goal},
    )

    while frontier:
        f_value, h_value, current = heapq.heappop(frontier)
        current_g = g_cost.get(current, float("inf"))

        if current in explored:
            continue

        mc.expand_node()
        explored.append(current)
        step_idx += 1

        if current in goal_set:
            path = reconstruct_path(parent, current)
            mc.set_result(True, path, current_g)
            mc.stop()
            yield StepEvent(
                step_index=step_idx,
                algorithm="A*",
                event_type="found",
                current_node=current,
                frontier=[node for _, _, node in frontier],
                explored=list(explored),
                path=path,
                message=(
                    f"[Step {step_idx:03d}] A*: found goal {current!r}. "
                    f"g={current_g:.2f}, h={h_value:.2f}, f={f_value:.2f}. "
                    f"Path: {' -> '.join(path)}"
                ),
                nodes_expanded=mc.nodes_expanded,
                nodes_generated=mc.nodes_generated,
                max_frontier_size=mc.max_frontier_size,
                total_cost=current_g,
                data={"g": current_g, "h": h_value, "f": f_value},
            )
            return

        generated = 0
        for neighbor_id, edge_cost, _ in graph.neighbors_with_cost(current, ignore_blocked=True):
            new_g = current_g + edge_cost
            if new_g >= g_cost.get(neighbor_id, float("inf")):
                continue
            neighbor_h, _ = _best_goal_heuristic(graph, neighbor_id, goals)
            neighbor_f = new_g + neighbor_h
            g_cost[neighbor_id] = new_g
            parent[neighbor_id] = current
            heapq.heappush(frontier, (neighbor_f, neighbor_h, neighbor_id))
            generated += 1
            mc.nodes_generated += 1

        mc.update_frontier_size(len(frontier))

        yield StepEvent(
            step_index=step_idx,
            algorithm="A*",
            event_type="expand",
            current_node=current,
            frontier=[node for _, _, node in sorted(frontier)],
            explored=list(explored),
            message=(
                f"[Step {step_idx:03d}] A*: expand {current!r}. "
                f"g={current_g:.2f}, h={h_value:.2f}, f={f_value:.2f}; "
                f"generated {generated} node(s)."
            ),
            nodes_expanded=mc.nodes_expanded,
            nodes_generated=mc.nodes_generated,
            max_frontier_size=mc.max_frontier_size,
            data={"g": current_g, "h": h_value, "f": f_value},
        )

    mc.set_result(False, [])
    mc.stop()
    step_idx += 1
    yield StepEvent(
        step_index=step_idx,
        algorithm="A*",
        event_type="failure",
        frontier=[],
        explored=list(explored),
        message=f"[Step {step_idx:03d}] A*: no path to any goal.",
        nodes_expanded=mc.nodes_expanded,
        nodes_generated=mc.nodes_generated,
        max_frontier_size=mc.max_frontier_size,
    )


def run(
    graph: NetworkGraph,
    start: str,
    goals: List[str],
) -> AlgorithmResult:
    """Run A* and return a full result."""
    start_time = time.perf_counter()
    steps = list(solve_steps(graph, start, goals))
    time_ms = (time.perf_counter() - start_time) * 1000.0
    last = steps[-1] if steps else None
    success = last is not None and last.event_type == "found"
    path = last.path if (last and last.path) else []
    cost = last.total_cost if last else 0.0
    metrics = AlgorithmMetrics(
        algorithm="A*",
        success=success,
        path=path,
        total_cost=cost,
        nodes_expanded=last.nodes_expanded if last else 0,
        nodes_generated=last.nodes_generated if last else 0,
        max_frontier_size=last.max_frontier_size if last else 0,
        time_ms=time_ms,
        num_steps=len(steps),
    )
    return AlgorithmResult(metrics=metrics, steps=steps)
