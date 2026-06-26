"""Simple Hill Climbing for defender configuration optimization."""
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
    max_steps: int = 80,
) -> Iterator[StepEvent]:
    """Yield Simple Hill Climbing steps. DefenseValue is maximized."""
    current = initial_config(graph, start, goals)
    current_value = defense_value(graph, start, goals, current)
    step_idx = 0

    def make_step(event_type: str, message: str, config: DefenseConfig) -> StepEvent:
        details = score_details(graph, start, goals, config)
        return StepEvent(
            step_index=step_idx,
            algorithm="Simple HC",
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
        f"[Step {step_idx:03d}] Simple HC: init {config_label(current)}; value={current_value}.",
        current,
    )
    step_idx += 1

    for _ in range(max_steps):
        accepted = False
        for candidate in neighbors(graph, start, goals, current):
            candidate_value = defense_value(graph, start, goals, candidate)
            yield make_step(
                "update",
                (
                    f"[Step {step_idx:03d}] Simple HC: check neighbor "
                    f"value={candidate_value} vs current={current_value}."
                ),
                candidate,
            )
            step_idx += 1
            if candidate_value > current_value:
                current = candidate
                current_value = candidate_value
                accepted = True
                yield make_step(
                    "move",
                    f"[Step {step_idx:03d}] Simple HC: accept first better state; value={current_value}.",
                    current,
                )
                step_idx += 1
                break
        if not accepted:
            yield make_step(
                "found",
                f"[Step {step_idx:03d}] Simple HC: local optimum; value={current_value}.",
                current,
            )
            return

    yield make_step(
        "found",
        f"[Step {step_idx:03d}] Simple HC: stop at max_steps; value={current_value}.",
        current,
    )


def run(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    max_steps: int = 80,
) -> AlgorithmResult:
    """Run Simple HC and return a full result."""
    start_time = time.perf_counter()
    steps = list(solve_steps(graph, start, goals, max_steps=max_steps))
    time_ms = (time.perf_counter() - start_time) * 1000.0
    last = steps[-1] if steps else None
    config = last.data.get("defense_config") if last else None
    value = float(last.data.get("defense_value", 0)) if last else 0.0
    metrics = AlgorithmMetrics(
        algorithm="Simple HC",
        success=last is not None and last.event_type == "found",
        total_cost=value,
        nodes_expanded=last.nodes_expanded if last else 0,
        nodes_generated=last.nodes_generated if last else 0,
        time_ms=time_ms,
        num_steps=len(steps),
        extra=dict(last.data) if last else {},
    )
    return AlgorithmResult(metrics=metrics, steps=steps, final_state=config)
