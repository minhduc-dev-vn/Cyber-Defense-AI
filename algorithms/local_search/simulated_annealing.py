"""Simulated Annealing for defender optimization."""
from __future__ import annotations

import math
import random
import time
from typing import Iterator

from algorithms.local_search.common import (
    config_label,
    initial_config,
    neighbors,
    risk_cost,
    score_details,
)
from core.constants import SA_DEFAULT_ALPHA, SA_DEFAULT_MAX_STEPS, SA_DEFAULT_T0, SA_DEFAULT_TMIN
from core.graph import NetworkGraph
from core.models import AlgorithmMetrics, AlgorithmResult, DefenseConfig, StepEvent


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
    """Yield Simulated Annealing steps. RiskCost is minimized."""
    rng = random.Random(seed)
    current = initial_config(graph, start, goals)
    current_risk = risk_cost(graph, start, goals, current)
    best = current
    best_risk = current_risk
    temperature = t0
    accepted_worse = 0
    step_idx = 0

    def make_step(
        event_type: str,
        message: str,
        config: DefenseConfig,
        extra: dict | None = None,
    ) -> StepEvent:
        details = score_details(graph, start, goals, config)
        details.update(
            {
                "seed": seed,
                "temperature": temperature,
                "best_risk": best_risk,
                "accepted_worse_moves": accepted_worse,
            }
        )
        if extra:
            details.update(extra)
        return StepEvent(
            step_index=step_idx,
            algorithm="Simulated Annealing",
            event_type=event_type,
            current_node=(config.firewall_nodes[0] if config.firewall_nodes else None),
            frontier=config.firewall_nodes + config.ids_nodes + config.upgraded_nodes,
            explored=config.firewall_nodes,
            message=message,
            nodes_expanded=step_idx,
            nodes_generated=step_idx,
            total_cost=float(details["risk_cost"]),
            data=details,
        )

    yield make_step(
        "info",
        f"[Step {step_idx:03d}] SA: init {config_label(current)}; risk={current_risk}; T={temperature:.2f}.",
        current,
    )
    step_idx += 1

    while temperature > tmin and step_idx <= max_steps:
        candidates = neighbors(graph, start, goals, current)
        if not candidates:
            break
        candidate = rng.choice(candidates)
        candidate_risk = risk_cost(graph, start, goals, candidate)
        delta = candidate_risk - current_risk
        probability = 1.0 if delta <= 0 else math.exp(-delta / max(temperature, 1e-9))
        roll = rng.random()
        accepted = delta <= 0 or roll < probability
        reason = "better" if delta <= 0 else "worse-prob"

        if accepted:
            if delta > 0:
                accepted_worse += 1
            current = candidate
            current_risk = candidate_risk
            if current_risk < best_risk:
                best = current
                best_risk = current_risk

        yield make_step(
            "move" if accepted else "update",
            (
                f"[Step {step_idx:03d}] SA: next risk={candidate_risk}, current risk={current_risk}, "
                f"delta={delta}, p={probability:.3f}, r={roll:.3f}, "
                f"{'accept' if accepted else 'reject'} ({reason})."
            ),
            current if accepted else candidate,
            {
                "delta": delta,
                "accept_probability": probability,
                "random_value": roll,
                "accepted": accepted,
            },
        )
        step_idx += 1
        temperature *= alpha

    yield make_step(
        "found",
        f"[Step {step_idx:03d}] SA: best risk={best_risk}; final {config_label(best)}.",
        best,
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
    config = last.data.get("defense_config") if last else None
    risk = float(last.data.get("risk_cost", 0)) if last else 0.0
    metrics = AlgorithmMetrics(
        algorithm="Simulated Annealing",
        success=last is not None and last.event_type == "found",
        total_cost=risk,
        nodes_expanded=last.nodes_expanded if last else 0,
        nodes_generated=last.nodes_generated if last else 0,
        time_ms=time_ms,
        num_steps=len(steps),
        extra=dict(last.data) if last else {},
    )
    return AlgorithmResult(metrics=metrics, steps=steps, final_state=config)
