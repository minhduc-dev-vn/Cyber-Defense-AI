"""Shared defense-optimization helpers for local search algorithms."""
from __future__ import annotations

import heapq
from dataclasses import replace
from typing import Iterable

from core.constants import (
    DEFENSE_VALUE_BLOCK_PATH,
    DEFENSE_VALUE_OPEN_PATH,
    DEFENSE_VALUE_PROTECTED,
    DEFENSE_VALUE_RESOURCE_COST,
    DEFENSE_VALUE_SLOW_DOWN,
    RISK_COST_DEFENSE_COST,
    RISK_COST_OPEN_PATH,
    RISK_COST_PATH_RISK,
    RISK_COST_PROTECTED,
)
from core.graph import NetworkGraph
from core.models import DefenseConfig


def edge_base_cost(graph: NetworkGraph, source: str, target: str) -> float:
    edge = graph.get_edge(source, target)
    if not edge or edge.blocked:
        return float("inf")
    return float(edge.base_cost)


def path_cost(graph: NetworkGraph, path: list[str]) -> float:
    total = 0.0
    for left, right in zip(path, path[1:]):
        total += edge_base_cost(graph, left, right)
    return total


def shortest_path_to_goal(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
) -> tuple[float, list[str]]:
    """Return lowest base-edge-cost path from start to any goal."""
    goal_set = set(goals)
    if start in goal_set:
        return 0.0, [start]
    queue: list[tuple[float, str, list[str]]] = [(0.0, start, [start])]
    best: dict[str, float] = {start: 0.0}
    while queue:
        cost, node_id, path = heapq.heappop(queue)
        if cost > best.get(node_id, float("inf")):
            continue
        for neighbor in graph.neighbors(node_id, ignore_blocked=True):
            edge_cost = edge_base_cost(graph, node_id, neighbor)
            if edge_cost == float("inf"):
                continue
            next_cost = cost + edge_cost
            if next_cost >= best.get(neighbor, float("inf")):
                continue
            next_path = path + [neighbor]
            if neighbor in goal_set:
                return next_cost, next_path
            best[neighbor] = next_cost
            heapq.heappush(queue, (next_cost, neighbor, next_path))
    return float("inf"), []


def heuristic_value(graph: NetworkGraph, node_id: str, goals: list[str]) -> float:
    """h(n): shortest weighted cost from node_id to the nearest goal."""
    cost, _ = shortest_path_to_goal(graph, node_id, goals)
    return cost


def heuristic_table(graph: NetworkGraph, goals: list[str]) -> dict[str, float]:
    return {node.id: heuristic_value(graph, node.id, goals) for node in graph.get_all_nodes()}


def path_edges(path: list[str]) -> list[tuple[str, str]]:
    return [(left, right) for left, right in zip(path, path[1:])]


def neighbor_heuristics(
    graph: NetworkGraph,
    node_id: str,
    goals: list[str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for neighbor in graph.neighbors(node_id, ignore_blocked=True):
        edge_cost = edge_base_cost(graph, node_id, neighbor)
        h_value = heuristic_value(graph, neighbor, goals)
        best_cost, best_path = shortest_path_to_goal(graph, neighbor, goals)
        rows.append(
            {
                "node": neighbor,
                "edge_cost": edge_cost,
                "heuristic": h_value,
                "best_path": best_path,
                "total_estimate": edge_cost + h_value,
                "reachable": best_cost < float("inf"),
            }
        )
    return rows


def format_cost_value(value: float) -> str:
    if value == float("inf"):
        return "inf"
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}"


def local_step_data(
    graph: NetworkGraph,
    current: str,
    goals: list[str],
    path: list[str],
    *,
    chosen_neighbor: str | None = None,
    accepted: bool | None = None,
    reason: str = "",
    extra: dict | None = None,
) -> dict[str, object]:
    h_current = heuristic_value(graph, current, goals)
    best_cost, best_suffix = shortest_path_to_goal(graph, current, goals)
    data: dict[str, object] = {
        "local_search_mode": "heuristic_path",
        "goal": goals[0] if goals else "",
        "goals": list(goals),
        "current_heuristic": h_current,
        "heuristic": h_current,
        "path_cost": path_cost(graph, path),
        "path_so_far": list(path),
        "best_remaining_cost": best_cost,
        "best_remaining_path": best_suffix,
        "heuristic_table": heuristic_table(graph, goals),
        "neighbor_scores": neighbor_heuristics(graph, current, goals),
        "chosen_neighbor": chosen_neighbor,
        "accepted": accepted,
        "reason": reason,
    }
    if extra:
        data.update(extra)
    return data


def best_lower_neighbor(graph: NetworkGraph, current: str, goals: list[str]) -> dict[str, object] | None:
    current_h = heuristic_value(graph, current, goals)
    lower = [row for row in neighbor_heuristics(graph, current, goals) if float(row["heuristic"]) < current_h]
    if not lower:
        return None
    return min(lower, key=lambda row: (float(row["heuristic"]), str(row["node"])))


def defense_candidates(graph: NetworkGraph, start: str, goals: list[str]) -> list[str]:
    """Return stable nodes where defense resources may be placed."""
    excluded = {start, *goals}
    return [
        node.id
        for node in graph.get_all_nodes()
        if node.id not in excluded and node.kind not in ("server", "database")
    ]


def canonical_config(config: DefenseConfig) -> DefenseConfig:
    return DefenseConfig(
        firewall_nodes=sorted(dict.fromkeys(config.firewall_nodes)),
        ids_nodes=sorted(dict.fromkeys(config.ids_nodes)),
        upgraded_nodes=sorted(dict.fromkeys(config.upgraded_nodes)),
    )


def initial_config(graph: NetworkGraph, start: str, goals: list[str]) -> DefenseConfig:
    """Choose a deterministic initial configuration."""
    candidates = defense_candidates(graph, start, goals)
    firewall_nodes = candidates[:2]
    ids_nodes = candidates[2:3] if len(candidates) >= 3 else candidates[:1]
    upgraded_nodes = candidates[3:4] if len(candidates) >= 4 else candidates[-1:]
    return canonical_config(DefenseConfig(firewall_nodes, ids_nodes, upgraded_nodes))


def all_attack_paths(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    max_paths_per_goal: int = 40,
) -> list[list[str]]:
    paths: list[list[str]] = []
    for goal in goals:
        paths.extend(graph.all_simple_paths(start, goal, max_paths=max_paths_per_goal))
    return paths


def _is_path_blocked(path: list[str], config: DefenseConfig) -> bool:
    protected = set(config.firewall_nodes)
    return any(node in protected for node in path[1:-1])


def _ids_slows_path(graph: NetworkGraph, path: list[str], config: DefenseConfig) -> bool:
    ids_nodes = set(config.ids_nodes)
    if ids_nodes.intersection(path):
        return True
    for ids_node in ids_nodes:
        for path_node in path:
            if graph.has_edge(ids_node, path_node):
                return True
    return False


def _protected_important_nodes(graph: NetworkGraph, config: DefenseConfig) -> set[str]:
    protected = set(config.firewall_nodes) | set(config.ids_nodes) | set(config.upgraded_nodes)
    result: set[str] = set()
    for node_id in protected:
        node = graph.get_node(node_id)
        if node and node.importance >= 6:
            result.add(node_id)
        for neighbor_id in graph.neighbors(node_id, ignore_blocked=True):
            neighbor = graph.get_node(neighbor_id)
            if neighbor and neighbor.importance >= 8:
                result.add(neighbor_id)
    return result


def resource_cost(config: DefenseConfig) -> int:
    return len(config.firewall_nodes) + len(config.ids_nodes) + len(config.upgraded_nodes)


def occupied_nodes(config: DefenseConfig) -> set[str]:
    return set(config.firewall_nodes) | set(config.ids_nodes) | set(config.upgraded_nodes)


def defense_value(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    config: DefenseConfig,
) -> int:
    """DefenseValue from the checklist: larger is better."""
    paths = all_attack_paths(graph, start, goals)
    blocked_paths = [path for path in paths if _is_path_blocked(path, config)]
    open_paths = [path for path in paths if not _is_path_blocked(path, config)]
    protected = _protected_important_nodes(graph, config)
    slow_downs = sum(1 for path in open_paths if _ids_slows_path(graph, path, config))
    return (
        DEFENSE_VALUE_BLOCK_PATH * len(blocked_paths)
        + DEFENSE_VALUE_PROTECTED * len(protected)
        + DEFENSE_VALUE_SLOW_DOWN * slow_downs
        - DEFENSE_VALUE_RESOURCE_COST * resource_cost(config)
        - DEFENSE_VALUE_OPEN_PATH * len(open_paths)
    )


def risk_cost(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    config: DefenseConfig,
) -> int:
    """RiskCost from the checklist: smaller is better."""
    paths = all_attack_paths(graph, start, goals)
    open_paths = [path for path in paths if not _is_path_blocked(path, config)]
    path_risk = 0
    for path in open_paths:
        for node_id in path[1:]:
            node = graph.get_node(node_id)
            if node:
                path_risk += max(1, 11 - node.security_level)
    protected = _protected_important_nodes(graph, config)
    return (
        RISK_COST_OPEN_PATH * len(open_paths)
        + RISK_COST_PATH_RISK * path_risk
        + RISK_COST_DEFENSE_COST * resource_cost(config)
        - RISK_COST_PROTECTED * len(protected)
    )


def score_details(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    config: DefenseConfig,
) -> dict[str, object]:
    paths = all_attack_paths(graph, start, goals)
    blocked_paths = [path for path in paths if _is_path_blocked(path, config)]
    open_paths = [path for path in paths if not _is_path_blocked(path, config)]
    return {
        "defense_config": canonical_config(config),
        "defense_value": defense_value(graph, start, goals, config),
        "risk_cost": risk_cost(graph, start, goals, config),
        "blocked_paths": len(blocked_paths),
        "open_paths": len(open_paths),
        "blocked_path_samples": blocked_paths[:3],
        "open_path_samples": open_paths[:3],
        "protected_nodes": sorted(_protected_important_nodes(graph, config)),
        "resource_cost": resource_cost(config),
    }


def neighbors(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    config: DefenseConfig,
) -> list[DefenseConfig]:
    """Generate valid one-move neighbor configurations."""
    candidates = defense_candidates(graph, start, goals)
    result: list[DefenseConfig] = []
    seen: set[tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = set()

    def add_config(candidate: DefenseConfig) -> None:
        candidate = canonical_config(candidate)
        if resource_cost(candidate) != len(occupied_nodes(candidate)):
            return
        key = (
            tuple(candidate.firewall_nodes),
            tuple(candidate.ids_nodes),
            tuple(candidate.upgraded_nodes),
        )
        if key not in seen:
            seen.add(key)
            result.append(candidate)

    for idx, old in enumerate(config.firewall_nodes):
        for node in candidates:
            unavailable = occupied_nodes(config) - {old}
            if node == old or node in unavailable:
                continue
            next_firewalls = list(config.firewall_nodes)
            next_firewalls[idx] = node
            add_config(DefenseConfig(next_firewalls, list(config.ids_nodes), list(config.upgraded_nodes)))

    for idx, old in enumerate(config.ids_nodes):
        for node in candidates:
            unavailable = occupied_nodes(config) - {old}
            if node == old or node in unavailable:
                continue
            next_ids = list(config.ids_nodes)
            next_ids[idx] = node
            add_config(DefenseConfig(list(config.firewall_nodes), next_ids, list(config.upgraded_nodes)))

    for idx, old in enumerate(config.upgraded_nodes):
        for node in candidates:
            unavailable = occupied_nodes(config) - {old}
            if node == old or node in unavailable:
                continue
            next_upgrades = list(config.upgraded_nodes)
            next_upgrades[idx] = node
            add_config(DefenseConfig(list(config.firewall_nodes), list(config.ids_nodes), next_upgrades))

    return result


def config_label(config: DefenseConfig) -> str:
    return (
        f"FW={config.firewall_nodes}, "
        f"IDS={config.ids_nodes}, UP={config.upgraded_nodes}"
    )
