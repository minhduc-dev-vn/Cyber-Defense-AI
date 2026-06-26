"""Forward Checking CSP for network security-zone assignment."""
from __future__ import annotations

import time
from copy import deepcopy
from typing import Iterator

from algorithms.csp.common import (
    assignment_edges,
    final_violations,
    initial_domains,
    is_consistent,
    select_unassigned_variable,
)
from core.graph import NetworkGraph
from core.models import AlgorithmMetrics, AlgorithmResult, CSPAssignment, StepEvent


def solve_steps(
    graph: NetworkGraph,
    start: str = "",
    goals: list[str] | None = None,
) -> Iterator[StepEvent]:
    """Yield Forward Checking CSP steps."""
    domains = initial_domains(graph)
    assignment: dict[str, str] = {}
    counters = {"step": 0, "assignments": 0, "backtracks": 0}

    def make_step(
        event_type: str,
        message: str,
        current: str | None = None,
        removed: dict[str, list[str]] | None = None,
        violations: list[str] | None = None,
    ) -> StepEvent:
        step = StepEvent(
            step_index=counters["step"],
            algorithm="Forward Checking",
            event_type=event_type,
            current_node=current,
            explored=list(assignment),
            highlighted_edges=assignment_edges(graph, assignment),
            message=message,
            nodes_expanded=counters["assignments"],
            nodes_generated=counters["assignments"],
            max_frontier_size=max((len(v) for v in domains.values()), default=0),
            total_cost=float(len(final_violations(graph, assignment))),
            data={
                "assignments": dict(assignment),
                "domains": {k: list(v) for k, v in domains.items()},
                "removed": removed or {},
                "conflicts": violations or [],
                "backtracks": counters["backtracks"],
            },
        )
        counters["step"] += 1
        return step

    def prune_domains(var: str, value: str) -> tuple[bool, dict[str, list[str]], list[str]]:
        removed: dict[str, list[str]] = {}
        violations: list[str] = []
        for other in list(domains):
            if other in assignment or other == var or not graph.has_edge(var, other):
                continue
            for candidate in list(domains[other]):
                ok, _ = is_consistent(graph, {var: value}, other, candidate)
                if not ok:
                    domains[other].remove(candidate)
                    removed.setdefault(other, []).append(candidate)
            if not domains[other]:
                violations.append(f"domain({other}) is empty")
        return not violations, removed, violations

    yield make_step("info", "[Step 000] Forward Checking: init domains.")

    def backtrack() -> Iterator[StepEvent]:
        if len(assignment) == graph.node_count():
            violations = final_violations(graph, assignment)
            if not violations:
                yield make_step(
                    "found",
                    f"[Step {counters['step']:03d}] Forward Checking: solution found.",
                )
            else:
                yield make_step(
                    "failure",
                    f"[Step {counters['step']:03d}] Forward Checking: final constraints failed.",
                    violations=violations,
                )
            return

        var = select_unassigned_variable(graph, assignment, domains)
        if var is None:
            return

        for value in list(domains[var]):
            ok, violations = is_consistent(graph, assignment, var, value)
            yield make_step(
                "assign",
                f"[Step {counters['step']:03d}] Forward Checking: try {var} = {value}.",
                current=var,
                violations=violations,
            )
            if not ok:
                continue

            saved_domains = deepcopy(domains)
            assignment[var] = value
            counters["assignments"] += 1
            domains[var] = [value]
            pruned_ok, removed, prune_violations = prune_domains(var, value)
            yield make_step(
                "update",
                f"[Step {counters['step']:03d}] Forward Checking: assign {var} = {value}; prune {removed}.",
                current=var,
                removed=removed,
                violations=prune_violations,
            )

            if pruned_ok:
                found = False
                for child_step in backtrack():
                    if child_step.event_type == "found":
                        found = True
                    yield child_step
                    if found:
                        return

            assignment.pop(var, None)
            domains.clear()
            domains.update(saved_domains)
            counters["backtracks"] += 1
            yield make_step(
                "backtrack",
                f"[Step {counters['step']:03d}] Forward Checking: restore domains after {var}.",
                current=var,
            )

    yield from backtrack()

    if len(assignment) != graph.node_count():
        yield make_step(
            "failure",
            f"[Step {counters['step']:03d}] Forward Checking: no valid assignment.",
            violations=final_violations(graph, assignment),
        )


def run(
    graph: NetworkGraph,
    start: str = "",
    goals: list[str] | None = None,
) -> AlgorithmResult:
    """Run Forward Checking and return a full result."""
    start_time = time.perf_counter()
    steps = list(solve_steps(graph, start, goals or []))
    time_ms = (time.perf_counter() - start_time) * 1000.0
    last = steps[-1] if steps else None
    success = last is not None and last.event_type == "found"
    assignments = dict(last.data.get("assignments", {})) if last else {}
    domains = {k: list(v) for k, v in (last.data.get("domains", {}) if last else {}).items()}
    conflicts = final_violations(graph, assignments)
    final_state = CSPAssignment(
        assignments=assignments,
        domains=domains,
        num_backtracks=int(last.data.get("backtracks", 0)) if last else 0,
        num_assignments=last.nodes_expanded if last else 0,
        num_conflicts=len(conflicts),
    )
    metrics = AlgorithmMetrics(
        algorithm="Forward Checking",
        success=success,
        total_cost=float(len(conflicts)),
        nodes_expanded=last.nodes_expanded if last else 0,
        nodes_generated=last.nodes_generated if last else 0,
        max_frontier_size=last.max_frontier_size if last else 0,
        time_ms=time_ms,
        num_steps=len(steps),
        extra={"assignments": assignments, "domains": domains, "conflicts": conflicts},
    )
    return AlgorithmResult(metrics=metrics, steps=steps, final_state=final_state)
