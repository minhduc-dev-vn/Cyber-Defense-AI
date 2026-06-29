"""Simulated Annealing on a weighted network path."""
from __future__ import annotations

import math
import random
import time
from typing import Iterator

from algorithms.local_search.common import (
    format_cost_value,
    heuristic_value,
    local_step_data,
    neighbor_heuristics,
    path_cost,
    path_edges,
)
from core.constants import SA_DEFAULT_ALPHA, SA_DEFAULT_MAX_STEPS, SA_DEFAULT_T0, SA_DEFAULT_TMIN
from core.graph import NetworkGraph
from core.models import AlgorithmMetrics, AlgorithmResult, StepEvent


def solve_steps(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    seed: int = 42,
    t0: float = SA_DEFAULT_T0,
    alpha: float = SA_DEFAULT_ALPHA,
    tmin: float = SA_DEFAULT_TMIN,
    max_steps: int = SA_DEFAULT_MAX_STEPS,
) -> Iterator[StepEvent]:
    """Yield Simulated Annealing steps. h(n) is minimized, with probabilistic uphill moves."""
    rng = random.Random(seed)
    current = start
    path = [start]
    best = current
    best_h = heuristic_value(graph, current, goals)
    temperature = t0
    accepted_worse = 0
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
            extra={
                "seed": seed,
                "temperature": temperature,
                "best_node": best,
                "best_heuristic": best_h,
                "accepted_worse_moves": accepted_worse,
            },
        )
        if extra:
            details.update(extra)
        return StepEvent(
            step_index=step_idx,
            algorithm="Simulated Annealing",
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
        f"[Step {step_idx:03d}] SA: start at {current}; h={format_cost_value(current_h)}; T={temperature:.2f}.",
    )
    step_idx += 1

    while temperature > tmin and step_idx <= max_steps:
        if current in goals:
            yield make_step(
                "found",
                f"[Step {step_idx:03d}] SA: reached goal {current}; path cost={format_cost_value(path_cost(graph, path))}.",
                accepted=True,
                reason="goal",
            )
            return

        candidates = neighbor_heuristics(graph, current, goals)
        if not candidates:
            break
        candidate = rng.choice(candidates)
        candidate_node = str(candidate["node"])
        candidate_h = float(candidate["heuristic"])
        previous_h = heuristic_value(graph, current, goals)
        delta = candidate_h - previous_h
        probability = 1.0 if delta <= 0 else math.exp(-delta / max(temperature, 1e-9))
        roll = rng.random()
        accepted = delta <= 0 or roll < probability
        reason = "lower-heuristic" if delta <= 0 else "probabilistic-worse"

        if accepted:
            if delta > 0:
                accepted_worse += 1
            current = candidate_node
            path.append(current)
            if candidate_h < best_h:
                best = current
                best_h = candidate_h

        yield make_step(
            "move" if accepted else "update",
            (
                f"[Step {step_idx:03d}] SA: candidate {candidate_node}; "
                f"h_next={format_cost_value(candidate_h)}, h_current={format_cost_value(previous_h)}, "
                f"delta={format_cost_value(delta)}, p={probability:.3f}, r={roll:.3f}, "
                f"{'accept' if accepted else 'reject'} ({reason})."
            ),
            chosen_neighbor=candidate_node,
            accepted=accepted,
            reason=reason,
            extra={
                "delta": delta,
                "accept_probability": probability,
                "random_value": roll,
                "candidate_heuristic": candidate_h,
                "previous_heuristic": previous_h,
            },
        )
        step_idx += 1
        temperature *= alpha

    if current in goals:
        yield make_step(
            "found",
            f"[Step {step_idx:03d}] SA: reached goal {current}; path cost={format_cost_value(path_cost(graph, path))}.",
            accepted=True,
            reason="goal",
        )
        return

    yield make_step(
        "failure",
        f"[Step {step_idx:03d}] SA: stopped before goal; best node={best}, best h={format_cost_value(best_h)}.",
        accepted=False,
        reason="stopped-before-goal",
    )


def run(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    seed: int = 42,
    t0: float = SA_DEFAULT_T0,
    alpha: float = SA_DEFAULT_ALPHA,
    tmin: float = SA_DEFAULT_TMIN,
    max_steps: int = SA_DEFAULT_MAX_STEPS,
) -> AlgorithmResult:
    """Run SA and return a full result."""
    start_time = time.perf_counter()
    steps = list(
        solve_steps(
            graph,
            start,
            goals,
            seed=seed,
            t0=t0,
            alpha=alpha,
            tmin=tmin,
            max_steps=max_steps,
        )
    )
    time_ms = (time.perf_counter() - start_time) * 1000.0
    last = steps[-1] if steps else None
    path = last.path if last else []
    success = last is not None and last.event_type == "found"
    metrics = AlgorithmMetrics(
        algorithm="Simulated Annealing",
        success=success,
        path=path,
        total_cost=float(last.data.get("path_cost", 0)) if last else 0.0,
        nodes_expanded=last.nodes_expanded if last else 0,
        nodes_generated=last.nodes_generated if last else 0,
        time_ms=time_ms,
        num_steps=len(steps),
        extra=dict(last.data) if last else {},
    )
    return AlgorithmResult(metrics=metrics, steps=steps, final_state=path)
