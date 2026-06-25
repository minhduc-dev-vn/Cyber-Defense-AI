"""
idastar.py - IDA* Search (Group 2).

Runs depth-first search repeatedly with an f(n) = g(n) + h(n) threshold.
It uses less memory than A*, at the cost of revisiting nodes across rounds.
"""
from __future__ import annotations

import time
from typing import Generator, Iterator, List, Optional, Tuple

from core.graph import NetworkGraph
from core.metrics import MetricsCollector
from core.models import AlgorithmMetrics, AlgorithmResult, StepEvent


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
    """Yield IDA* animation steps."""
    mc = MetricsCollector("IDA*")
    mc.start()

    goal_set = set(goals)
    threshold, start_goal = _best_goal_heuristic(graph, start, goals)
    path: List[str] = [start]
    explored: List[str] = []
    step_idx = 0

    yield StepEvent(
        step_index=step_idx,
        algorithm="IDA*",
        event_type="info",
        current_node=start,
        frontier=list(path),
        explored=[],
        message=(
            f"[Step {step_idx:03d}] IDA*: init threshold=h(start)="
            f"{threshold:.2f} toward {start_goal!r}"
        ),
        data={"g": 0.0, "h": threshold, "f": threshold, "threshold": threshold},
    )

    if threshold == float("inf"):
        mc.set_result(False, [])
        mc.stop()
        step_idx += 1
        yield StepEvent(
            step_index=step_idx,
            algorithm="IDA*",
            event_type="failure",
            frontier=[],
            explored=[],
            message=f"[Step {step_idx:03d}] IDA*: no finite heuristic to any goal.",
        )
        return

    def search(
        g_value: float,
        current_threshold: float,
    ) -> Generator[StepEvent, None, Tuple[bool, float, Optional[List[str]], float]]:
        nonlocal step_idx

        current = path[-1]
        h_value, _ = _best_goal_heuristic(graph, current, goals)
        f_value = g_value + h_value

        mc.expand_node()
        explored.append(current)
        step_idx += 1

        yield StepEvent(
            step_index=step_idx,
            algorithm="IDA*",
            event_type="expand",
            current_node=current,
            frontier=list(path),
            explored=list(explored),
            path=list(path),
            message=(
                f"[Step {step_idx:03d}] IDA*: visit {current!r}. "
                f"g={g_value:.2f}, h={h_value:.2f}, f={f_value:.2f}, "
                f"threshold={current_threshold:.2f}."
            ),
            nodes_expanded=mc.nodes_expanded,
            nodes_generated=mc.nodes_generated,
            max_frontier_size=mc.max_frontier_size,
            total_cost=g_value,
            data={"g": g_value, "h": h_value, "f": f_value, "threshold": current_threshold},
        )

        if f_value > current_threshold:
            return False, f_value, None, g_value

        if current in goal_set:
            return True, g_value, list(path), g_value

        min_next_threshold = float("inf")
        neighbors = sorted(
            graph.neighbors_with_cost(current, ignore_blocked=True),
            key=lambda item: (_best_goal_heuristic(graph, item[0], goals)[0], item[0]),
        )

        for neighbor_id, edge_cost, _ in neighbors:
            if neighbor_id in path:
                continue
            path.append(neighbor_id)
            mc.nodes_generated += 1
            mc.update_frontier_size(len(path))
            found, value, found_path, found_cost = yield from search(
                g_value + edge_cost,
                current_threshold,
            )
            path.pop()
            if found:
                return True, value, found_path, found_cost
            if value < min_next_threshold:
                min_next_threshold = value

        return False, min_next_threshold, None, g_value

    while True:
        found, next_threshold, found_path, found_cost = yield from search(0.0, threshold)
        if found and found_path is not None:
            mc.set_result(True, found_path, found_cost)
            mc.stop()
            step_idx += 1
            yield StepEvent(
                step_index=step_idx,
                algorithm="IDA*",
                event_type="found",
                current_node=found_path[-1],
                frontier=[],
                explored=list(explored),
                path=found_path,
                message=(
                    f"[Step {step_idx:03d}] IDA*: found goal {found_path[-1]!r}. "
                    f"cost={found_cost:.2f}. Path: {' -> '.join(found_path)}"
                ),
                nodes_expanded=mc.nodes_expanded,
                nodes_generated=mc.nodes_generated,
                max_frontier_size=mc.max_frontier_size,
                total_cost=found_cost,
                data={"threshold": threshold, "g": found_cost, "h": 0.0, "f": found_cost},
            )
            return

        if next_threshold == float("inf"):
            mc.set_result(False, [])
            mc.stop()
            step_idx += 1
            yield StepEvent(
                step_index=step_idx,
                algorithm="IDA*",
                event_type="failure",
                frontier=[],
                explored=list(explored),
                message=f"[Step {step_idx:03d}] IDA*: no path to any goal.",
                nodes_expanded=mc.nodes_expanded,
                nodes_generated=mc.nodes_generated,
                max_frontier_size=mc.max_frontier_size,
            )
            return

        old_threshold = threshold
        threshold = next_threshold
        step_idx += 1
        yield StepEvent(
            step_index=step_idx,
            algorithm="IDA*",
            event_type="update",
            current_node=start,
            frontier=list(path),
            explored=list(explored),
            message=(
                f"[Step {step_idx:03d}] IDA*: raise threshold "
                f"{old_threshold:.2f} -> {threshold:.2f}."
            ),
            nodes_expanded=mc.nodes_expanded,
            nodes_generated=mc.nodes_generated,
            max_frontier_size=mc.max_frontier_size,
            data={"threshold": threshold, "previous_threshold": old_threshold},
        )


def run(
    graph: NetworkGraph,
    start: str,
    goals: List[str],
) -> AlgorithmResult:
    """Run IDA* and return a full result."""
    start_time = time.perf_counter()
    steps = list(solve_steps(graph, start, goals))
    time_ms = (time.perf_counter() - start_time) * 1000.0
    last = steps[-1] if steps else None
    success = last is not None and last.event_type == "found"
    path = last.path if (last and last.path) else []
    cost = last.total_cost if last else 0.0
    metrics = AlgorithmMetrics(
        algorithm="IDA*",
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
