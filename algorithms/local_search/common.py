"""Shared defense-optimization helpers for local search algorithms."""
from __future__ import annotations

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
