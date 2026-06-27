"""Steepest Hill Climbing on a weighted network path."""
from __future__ import annotations

import time
from typing import Iterator

from algorithms.local_search.common import (
    best_lower_neighbor,
    format_cost_value,
    heuristic_value,
    local_step_data,
    neighbor_heuristics,
    path_cost,
    path_edges,
)
from core.graph import NetworkGraph
from core.models import AlgorithmMetrics, AlgorithmResult, StepEvent


def solve_steps(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    max_steps: int = 50,
) -> Iterator[StepEvent]:
    """Yield Steepest Hill Climbing steps. h(n) is minimized."""
    current = start
    path = [start]
    visited = {start}
    step_idx = 0

    def make_step(
        event_type: str,
        message: str,
        *,
        chosen_neighbor: str | None = None,
        accepted: bool | None = None,
        reason: str = "",
        extra: dict | None = None,
    ) -> StepEvent:
        details = local_step_data(
            graph,
            current,
            goals,
            path,
            chosen_neighbor=chosen_neighbor,
            accepted=accepted,
            reason=reason,
            extra=extra,
        )
        return StepEvent(
            step_index=step_idx,
            algorithm="Steepest HC",
            event_type=event_type,
            current_node=current,
            frontier=[str(row["node"]) for row in details["neighbor_scores"]],
            explored=list(path),
            path=list(path),
            highlighted_edges=path_edges(path),
            message=message,
            nodes_expanded=step_idx,
            nodes_generated=len(details["neighbor_scores"]),
            max_frontier_size=len(details["neighbor_scores"]),
            total_cost=float(details["current_heuristic"]),
            data=details,
        )

    current_h = heuristic_value(graph, current, goals)
    yield make_step(
        "info",
        f"[Step {step_idx:03d}] Steepest HC: start at {current}; h={format_cost_value(current_h)}.",
    )
    step_idx += 1

    for _ in range(max_steps):
        current_h = heuristic_value(graph, current, goals)
        if current in goals:
            yield make_step(
                "found",
                f"[Step {step_idx:03d}] Steepest HC: reached goal {current}; path cost={format_cost_value(path_cost(graph, path))}.",
                accepted=True,
                reason="goal",
            )
            return

        scores = neighbor_heuristics(graph, current, goals)
        best = best_lower_neighbor(graph, current, goals)
        best_node = str(best["node"]) if best else None
        best_h = float(best["heuristic"]) if best else current_h

        yield make_step(
            "update",
            (
                f"[Step {step_idx:03d}] Steepest HC: checked {len(scores)} neighbors; "
                f"best h={format_cost_value(best_h)}, current h={format_cost_value(current_h)}."
            ),
            chosen_neighbor=best_node,
            accepted=False,
            reason="scan-all-neighbors",
            extra={"neighbors_checked": len(scores), "best_neighbor": best_node, "best_heuristic": best_h},
        )
        step_idx += 1

        if not best or best_node in visited:
            yield make_step(
                "failure",
                (
                    f"[Step {step_idx:03d}] Steepest HC: local maximum/local optimum at {current}; "
                    f"no neighbor has h lower than {format_cost_value(current_h)}."
                ),
                accepted=False,
                reason="local-optimum",
            )
            return

        current = best_node
        path.append(current)
        visited.add(current)
        yield make_step(
            "move",
            f"[Step {step_idx:03d}] Steepest HC: move to {current}; h={format_cost_value(best_h)}.",
            chosen_neighbor=current,
            accepted=True,
            reason="lowest-neighbor-heuristic",
        )
        step_idx += 1

    yield make_step(
        "failure",
        f"[Step {step_idx:03d}] Steepest HC: stop at max_steps={max_steps}.",
        accepted=False,
        reason="max-steps",
    )


def run(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    max_steps: int = 50,
) -> AlgorithmResult:
    """Run Steepest HC and return a full result."""
    start_time = time.perf_counter()
    steps = list(solve_steps(graph, start, goals, max_steps=max_steps))
    time_ms = (time.perf_counter() - start_time) * 1000.0
    last = steps[-1] if steps else None
    path = last.path if last else []
    heuristic = float(last.data.get("current_heuristic", 0)) if last else 0.0
    success = last is not None and last.event_type == "found"
    metrics = AlgorithmMetrics(
        algorithm="Steepest HC",
        success=success,
        path=path,
        total_cost=float(last.data.get("path_cost", 0)) if last else 0.0,
        nodes_expanded=last.nodes_expanded if last else 0,
        nodes_generated=last.nodes_generated if last else 0,
        time_ms=time_ms,
        num_steps=len(steps),
        extra={**(dict(last.data) if last else {}), "final_heuristic": heuristic},
    )
    return AlgorithmResult(metrics=metrics, steps=steps, final_state=path)
