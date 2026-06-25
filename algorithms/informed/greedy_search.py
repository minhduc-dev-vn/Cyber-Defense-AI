"""
greedy_search.py - Greedy Best-First Search (Group 2).

Chooses the node with the smallest h(n). This is useful for demonstrating
heuristic guidance, but it does not guarantee the lowest total path cost.
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


def _path_cost(graph: NetworkGraph, path: List[str]) -> float:
    """Compute the real weighted cost of a path."""
    total = 0.0
    for source, target in zip(path, path[1:]):
        edge = graph.get_edge(source, target)
        target_node = graph.get_node(target)
        if edge is None:
            return float("inf")
        total += graph.edge_cost(edge, target_node)
    return total


def solve_steps(
    graph: NetworkGraph,
    start: str,
    goals: List[str],
) -> Iterator[StepEvent]:
    """Yield Greedy Best-First Search animation steps."""
    mc = MetricsCollector("Greedy")
    mc.start()

    goal_set = set(goals)
    start_h, start_goal = _best_goal_heuristic(graph, start, goals)
    frontier: List[Tuple[float, str]] = [(start_h, start)]
    reached: Dict[str, Optional[str]] = {start: None}
    explored: List[str] = []

    step_idx = 0
    mc.update_frontier_size(len(frontier))
    yield StepEvent(
        step_index=step_idx,
        algorithm="Greedy",
        event_type="info",
        current_node=start,
        frontier=[start],
        explored=[],
        message=(
            f"[Step {step_idx:03d}] Greedy: init. Start={start!r}, "
            f"h(start)={start_h:.2f} toward {start_goal!r}"
        ),
        max_frontier_size=mc.max_frontier_size,
        data={"h": start_h, "goal_for_h": start_goal},
    )

    while frontier:
        h_value, current = heapq.heappop(frontier)
        if current in explored:
            continue

        mc.expand_node()
        explored.append(current)
        step_idx += 1

        if current in goal_set:
            path = reconstruct_path(reached, current)
            cost = _path_cost(graph, path)
            mc.set_result(True, path, cost)
            mc.stop()
            yield StepEvent(
                step_index=step_idx,
                algorithm="Greedy",
                event_type="found",
                current_node=current,
                frontier=[node for _, node in frontier],
                explored=list(explored),
                path=path,
                message=(
                    f"[Step {step_idx:03d}] Greedy: found goal {current!r}. "
                    f"h={h_value:.2f}, real cost={cost:.2f}. Path: {' -> '.join(path)}"
                ),
                nodes_expanded=mc.nodes_expanded,
                nodes_generated=mc.nodes_generated,
                max_frontier_size=mc.max_frontier_size,
                total_cost=cost,
                data={"h": h_value},
            )
            return

        generated = 0
        for neighbor_id in sorted(graph.neighbors(current, ignore_blocked=True)):
            if neighbor_id in reached:
                continue
            neighbor_h, _ = _best_goal_heuristic(graph, neighbor_id, goals)
            reached[neighbor_id] = current
            heapq.heappush(frontier, (neighbor_h, neighbor_id))
            generated += 1
            mc.nodes_generated += 1

        mc.update_frontier_size(len(frontier))

        yield StepEvent(
            step_index=step_idx,
            algorithm="Greedy",
            event_type="expand",
            current_node=current,
            frontier=[node for _, node in sorted(frontier)],
            explored=list(explored),
            message=(
                f"[Step {step_idx:03d}] Greedy: expand {current!r} "
                f"with h={h_value:.2f}; generated {generated} node(s)."
            ),
            nodes_expanded=mc.nodes_expanded,
            nodes_generated=mc.nodes_generated,
            max_frontier_size=mc.max_frontier_size,
            data={"h": h_value},
        )

    mc.set_result(False, [])
    mc.stop()
    step_idx += 1
    yield StepEvent(
        step_index=step_idx,
        algorithm="Greedy",
        event_type="failure",
        frontier=[],
        explored=list(explored),
        message=f"[Step {step_idx:03d}] Greedy: no path to any goal.",
        nodes_expanded=mc.nodes_expanded,
        nodes_generated=mc.nodes_generated,
        max_frontier_size=mc.max_frontier_size,
    )


def run(
    graph: NetworkGraph,
    start: str,
    goals: List[str],
) -> AlgorithmResult:
    """Run Greedy Best-First Search and return a full result."""
    start_time = time.perf_counter()
    steps = list(solve_steps(graph, start, goals))
    time_ms = (time.perf_counter() - start_time) * 1000.0
    last = steps[-1] if steps else None
    success = last is not None and last.event_type == "found"
    path = last.path if (last and last.path) else []
    cost = last.total_cost if last else 0.0
    metrics = AlgorithmMetrics(
        algorithm="Greedy",
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
