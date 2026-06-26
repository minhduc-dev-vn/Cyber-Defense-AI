"""Shared helpers for CSP network segmentation algorithms."""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from core.constants import VALID_ZONES
from core.graph import NetworkGraph

ZONES = ["User Zone", "DMZ", "Server Zone", "Quarantine Zone"]


def variables(graph: NetworkGraph) -> list[str]:
    """Return CSP variables in a stable order."""
    return [node.id for node in graph.get_all_nodes()]


def initial_domains(graph: NetworkGraph) -> dict[str, list[str]]:
    """Build domains with simple unary constraints already applied."""
    domains: dict[str, list[str]] = {}
    for node in graph.get_all_nodes():
        domain = list(ZONES)
        if node.kind in ("server", "database"):
            domain = ["Server Zone"]
        elif node.compromised:
            domain = ["Quarantine Zone"]
        elif node.kind == "pc":
            domain = ["User Zone", "DMZ", "Quarantine Zone"]
        domains[node.id] = domain
    return domains


def unary_violations(
    graph: NetworkGraph,
    var: str,
    value: str,
) -> list[str]:
    node = graph.get_node(var)
    if not node:
        return [f"{var} does not exist"]
    violations: list[str] = []
    if value not in VALID_ZONES:
        violations.append(f"{var} uses invalid zone {value}")
    if node.kind in ("server", "database") and value != "Server Zone":
        violations.append(f"{var} must be Server Zone")
    if node.compromised and value != "Quarantine Zone":
        violations.append(f"{var} is compromised and must be Quarantine Zone")
    if node.kind == "pc" and not node.compromised and value == "Server Zone":
        violations.append(f"{var} is a user PC and cannot be Server Zone")
    return violations


def pair_violations(
    graph: NetworkGraph,
    left: str,
    left_zone: str,
    right: str,
    right_zone: str,
) -> list[str]:
    """Return pairwise constraint violations for an assigned edge."""
    violations: list[str] = []
    left_node = graph.get_node(left)
    right_node = graph.get_node(right)
    if not left_node or not right_node:
        return violations

    if graph.has_edge(left, right) and left_zone == right_zone:
        violations.append(f"{left} and {right} are adjacent in the same zone")

    if left_node.kind == "pc" and right_node.kind in ("server", "database"):
        if left_zone == right_zone:
            violations.append(f"user node {left} cannot share zone with {right}")
    if right_node.kind == "pc" and left_node.kind in ("server", "database"):
        if left_zone == right_zone:
            violations.append(f"user node {right} cannot share zone with {left}")

    return violations


def final_violations(graph: NetworkGraph, assignment: dict[str, str]) -> list[str]:
    """Return every violated CSP constraint for a complete or partial assignment."""
    violations: list[str] = []
    for var, zone in assignment.items():
        violations.extend(unary_violations(graph, var, zone))

    seen_edges: set[frozenset[str]] = set()
    for edge in graph.get_all_edges():
        key = frozenset((edge.source, edge.target))
        if key in seen_edges:
            continue
        seen_edges.add(key)
        if edge.source in assignment and edge.target in assignment:
            violations.extend(
                pair_violations(
                    graph,
                    edge.source,
                    assignment[edge.source],
                    edge.target,
                    assignment[edge.target],
                )
            )

    if len(assignment) == graph.node_count():
        counts = Counter(assignment.values())
        for zone in ZONES:
            if counts[zone] == 0:
                violations.append(f"{zone} must contain at least one node")
    return violations


def is_consistent(
    graph: NetworkGraph,
    assignment: dict[str, str],
    var: str,
    value: str,
) -> tuple[bool, list[str]]:
    """Check whether assigning var=value is consistent with current assignment."""
    trial = dict(assignment)
    trial[var] = value
    violations = unary_violations(graph, var, value)
    for other, other_zone in assignment.items():
        if graph.has_edge(var, other):
            violations.extend(pair_violations(graph, var, value, other, other_zone))
    return not violations, violations


def count_conflicts(
    graph: NetworkGraph,
    assignment: dict[str, str],
    variables_subset: Iterable[str] | None = None,
) -> int:
    """Count how many constraints are violated."""
    if variables_subset is None:
        return len(final_violations(graph, assignment))

    interested = set(variables_subset)
    count = 0
    for var in interested:
        if var in assignment:
            count += len(unary_violations(graph, var, assignment[var]))
    for edge in graph.get_all_edges():
        if edge.source not in assignment or edge.target not in assignment:
            continue
        if edge.source in interested or edge.target in interested:
            count += len(
                pair_violations(
                    graph,
                    edge.source,
                    assignment[edge.source],
                    edge.target,
                    assignment[edge.target],
                )
            )
    if len(assignment) == graph.node_count():
        missing = set(ZONES) - set(assignment.values())
        count += len(missing)
    return count


def select_unassigned_variable(
    graph: NetworkGraph,
    assignment: dict[str, str],
    domains: dict[str, list[str]],
) -> str | None:
    """Use MRV, with stable node order as the tie-breaker."""
    remaining = [var for var in variables(graph) if var not in assignment]
    if not remaining:
        return None
    return min(remaining, key=lambda var: (len(domains[var]), variables(graph).index(var)))


def assignment_edges(graph: NetworkGraph, assignment: dict[str, str]) -> list[tuple[str, str]]:
    """Edges whose endpoints are already assigned."""
    result: list[tuple[str, str]] = []
    for edge in graph.get_all_edges():
        if edge.source in assignment and edge.target in assignment:
            result.append((edge.source, edge.target))
    return result
