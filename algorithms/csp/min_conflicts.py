"""Min-Conflicts CSP for network security-zone assignment."""
from __future__ import annotations

import random
import time
from typing import Iterator

from algorithms.csp.common import (
    assignment_edges,
    count_conflicts,
    final_violations,
    initial_domains,
)
from core.graph import NetworkGraph
from core.models import AlgorithmMetrics, AlgorithmResult, CSPAssignment, StepEvent


DEMO_SEED = 1169


def _conflicted_variables(graph: NetworkGraph, assignment: dict[str, str]) -> list[str]:
    return [
        node.id
        for node in graph.get_all_nodes()
        if count_conflicts(graph, assignment, [node.id]) > 0
    ]


def _initial_assignment(
    graph: NetworkGraph,
    rng: random.Random,
    domains: dict[str, list[str]],
) -> dict[str, str]:
    assignment: dict[str, str] = {}
    for node in graph.get_all_nodes():
        domain = domains[node.id]
        assignment[node.id] = rng.choice(domain)
    return assignment


def solve_steps(
    graph: NetworkGraph,
    start: str = "",
    goals: list[str] | None = None,
    seed: int = DEMO_SEED,
    max_steps: int = 200,
) -> Iterator[StepEvent]:
    """Yield Min-Conflicts CSP steps."""
    rng = random.Random(seed)
    domains = initial_domains(graph)
    assignment = _initial_assignment(graph, rng, domains)
    step_idx = 0

    def make_step(
        event_type: str,
        message: str,
        current: str | None = None,
        extra: dict | None = None,
    ) -> StepEvent:
        conflicts = final_violations(graph, assignment)
        data = {
            "assignments": dict(assignment),
            "domains": {k: list(v) for k, v in domains.items()},
            "current_domain": list(domains.get(current, [])) if current else [],
            "conflicts": conflicts,
            "seed": seed,
            "max_steps": max_steps,
            "assigned_count": len(assignment),
        }
        if extra:
            data.update(extra)
        return StepEvent(
            step_index=step_idx,
            algorithm="Min-Conflicts",
            event_type=event_type,
            current_node=current,
            explored=list(assignment),
            highlighted_edges=assignment_edges(graph, assignment),
            message=message,
            nodes_expanded=step_idx,
            nodes_generated=step_idx,
            max_frontier_size=len(_conflicted_variables(graph, assignment)),
            total_cost=float(len(conflicts)),
            data=data,
        )

    yield make_step(
        "info",
        f"[Step {step_idx:03d}] Min-Conflicts: random init with seed={seed}.",
    )
    step_idx += 1

    for _ in range(max_steps):
        conflicts = final_violations(graph, assignment)
        if not conflicts:
            yield make_step(
                "found",
                f"[Step {step_idx:03d}] Min-Conflicts: solution found with 0 conflicts.",
            )
            return

        conflicted = _conflicted_variables(graph, assignment)
        if not conflicted:
            yield make_step(
                "failure",
                f"[Step {step_idx:03d}] Min-Conflicts: no conflicted variable but constraints remain.",
            )
            return

        var = rng.choice(conflicted)
        best_values: list[str] = []
        best_conflicts = 10**9
        for value in domains[var]:
            old_value = assignment[var]
            assignment[var] = value
            value_conflicts = count_conflicts(graph, assignment)
            assignment[var] = old_value
            if value_conflicts < best_conflicts:
                best_conflicts = value_conflicts
                best_values = [value]
            elif value_conflicts == best_conflicts:
                best_values.append(value)

        new_value = rng.choice(best_values)
        old_value = assignment[var]
        assignment[var] = new_value
        yield make_step(
            "update",
            (
                f"[Step {step_idx:03d}] Min-Conflicts: choose {var}; "
                f"{old_value} -> {new_value}; conflicts={best_conflicts}."
            ),
            current=var,
            extra={
                "old_value": old_value,
                "new_value": new_value,
                "attempted_value": new_value,
                "best_conflicts": best_conflicts,
                "conflicted_variables": conflicted,
            },
        )
        step_idx += 1

    yield make_step(
        "failure",
        f"[Step {step_idx:03d}] Min-Conflicts: reached max_steps={max_steps}.",
    )


def run(
    graph: NetworkGraph,
    start: str = "",
    goals: list[str] | None = None,
    seed: int = DEMO_SEED,
    max_steps: int = 200,
) -> AlgorithmResult:
    """Run Min-Conflicts and return a full result."""
    start_time = time.perf_counter()
    steps = list(solve_steps(graph, start, goals or [], seed=seed, max_steps=max_steps))
    time_ms = (time.perf_counter() - start_time) * 1000.0
    last = steps[-1] if steps else None
    success = last is not None and last.event_type == "found"
    assignments = dict(last.data.get("assignments", {})) if last else {}
    domains = {k: list(v) for k, v in (last.data.get("domains", {}) if last else {}).items()}
    conflicts = final_violations(graph, assignments)
    final_state = CSPAssignment(
        assignments=assignments,
        domains=domains,
        num_assignments=last.nodes_expanded if last else 0,
        num_conflicts=len(conflicts),
    )
    metrics = AlgorithmMetrics(
        algorithm="Min-Conflicts",
        success=success,
        total_cost=float(len(conflicts)),
        nodes_expanded=last.nodes_expanded if last else 0,
        nodes_generated=last.nodes_generated if last else 0,
        max_frontier_size=last.max_frontier_size if last else 0,
        time_ms=time_ms,
        num_steps=len(steps),
        extra={"assignments": assignments, "conflicts": conflicts, "seed": seed},
    )
    return AlgorithmResult(metrics=metrics, steps=steps, final_state=final_state)
