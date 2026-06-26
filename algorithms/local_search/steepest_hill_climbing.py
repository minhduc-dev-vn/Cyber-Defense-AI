"""Steepest Ascent Hill Climbing for defender optimization."""
from __future__ import annotations

import time
from typing import Iterator

from algorithms.local_search.common import (
    config_label,
    defense_value,
    initial_config,
    neighbors,
    score_details,
)
from core.graph import NetworkGraph
from core.models import AlgorithmMetrics, AlgorithmResult, DefenseConfig, StepEvent


def solve_steps(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    max_steps: int = 50,
) -> Iterator[StepEvent]:
    """Yield Steepest Ascent steps. DefenseValue is maximized."""
    current = initial_config(graph, start, goals)
    current_value = defense_value(graph, start, goals, current)
    step_idx = 0

    def make_step(event_type: str, message: str, config: DefenseConfig, extra: dict | None = None) -> StepEvent:
        details = score_details(graph, start, goals, config)
        if extra:
            details.update(extra)
        return StepEvent(
            step_index=step_idx,
            algorithm="Steepest HC",
            event_type=event_type,
            current_node=(config.firewall_nodes[0] if config.firewall_nodes else None),
            frontier=config.firewall_nodes + config.ids_nodes + config.upgraded_nodes,
            explored=config.firewall_nodes,
            message=message,
            nodes_expanded=step_idx,
            nodes_generated=step_idx,
            total_cost=float(details["defense_value"]),
            data=details,
        )

    yield make_step(
        "info",
        f"[Step {step_idx:03d}] Steepest HC: init {config_label(current)}; value={current_value}.",
        current,
    )
    step_idx += 1

    for _ in range(max_steps):
        best = current
        best_value = current_value
        checked = 0
        for candidate in neighbors(graph, start, goals, current):
            checked += 1
            candidate_value = defense_value(graph, start, goals, candidate)
            if candidate_value > best_value:
                best = candidate
                best_value = candidate_value

        yield make_step(
            "update",
            (
                f"[Step {step_idx:03d}] Steepest HC: checked {checked} neighbors; "
                f"best={best_value}, current={current_value}."
            ),
            best,
            {"neighbors_checked": checked},
        )
        step_idx += 1

        if best_value <= current_value:
            yield make_step(
                "found",
                f"[Step {step_idx:03d}] Steepest HC: local optimum; value={current_value}.",
                current,
            )
            return

        current = best
        current_value = best_value
        yield make_step(
            "move",
            f"[Step {step_idx:03d}] Steepest HC: move to best neighbor; value={current_value}.",
            current,
        )
        step_idx += 1

    yield make_step(
        "found",
        f"[Step {step_idx:03d}] Steepest HC: stop at max_steps; value={current_value}.",
        current,
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
    config = last.data.get("defense_config") if last else None
    value = float(last.data.get("defense_value", 0)) if last else 0.0
    metrics = AlgorithmMetrics(
        algorithm="Steepest HC",
        success=last is not None and last.event_type == "found",
        total_cost=value,
        nodes_expanded=last.nodes_expanded if last else 0,
        nodes_generated=last.nodes_generated if last else 0,
        time_ms=time_ms,
        num_steps=len(steps),
        extra=dict(last.data) if last else {},
    )
    return AlgorithmResult(metrics=metrics, steps=steps, final_state=config)
