"""Shared helpers for belief-state and AND-OR search."""
from __future__ import annotations

from collections import deque
from typing import Iterable

from core.graph import NetworkGraph
from core.models import Action


def initial_belief(graph: NetworkGraph, metadata: dict | None = None) -> frozenset[str]:
    metadata = metadata or {}
    if metadata.get("belief_initial"):
        return frozenset(metadata["belief_initial"])
    return frozenset(node.id for node in graph.get_all_nodes() if node.kind == "pc")


def has_path_with_blocks(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    blocked_nodes: Iterable[str],
) -> bool:
    blocked = set(blocked_nodes)
    if start in blocked:
        return False
    queue: deque[str] = deque([start])
    seen = {start}
    while queue:
        current = queue.popleft()
        if current in goals:
            return True
        for neighbor in graph.neighbors(current, ignore_blocked=True):
            if neighbor in seen or neighbor in blocked:
                continue
            seen.add(neighbor)
            queue.append(neighbor)
    return False


def belief_is_safe(
    graph: NetworkGraph,
    belief: Iterable[str],
    goals: list[str],
    blocked_nodes: Iterable[str],
) -> bool:
    return all(not has_path_with_blocks(graph, pos, goals, blocked_nodes) for pos in belief)


def choke_candidates(graph: NetworkGraph, goals: list[str]) -> list[str]:
    excluded = set(goals)
    candidates = [
        node.id
        for node in graph.get_all_nodes()
        if node.id not in excluded and node.kind not in ("server", "database", "pc")
    ]
    candidates.sort(key=lambda node_id: (-len(graph.neighbors(node_id, ignore_blocked=True)), node_id))
    return candidates


def observation_region(graph: NetworkGraph, ids_node: str, radius: int = 1) -> set[str]:
    seen = {ids_node}
    frontier = {ids_node}
    for _ in range(radius):
        next_frontier: set[str] = set()
        for node_id in frontier:
            for neighbor in graph.neighbors(node_id, ignore_blocked=True):
                if neighbor not in seen:
                    seen.add(neighbor)
                    next_frontier.add(neighbor)
        frontier = next_frontier
    return seen


def possible_after_one_hacker_move(graph: NetworkGraph, belief: Iterable[str]) -> frozenset[str]:
    possible = set(belief)
    for pos in belief:
        possible.update(graph.neighbors(pos, ignore_blocked=True))
    return frozenset(possible)


def action_for_block(node_id: str) -> Action:
    return Action("defender", "block_node", node_id, f"Block {node_id}")
