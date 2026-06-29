"""Shared helpers for the adversarial simulator."""
from __future__ import annotations

from collections import deque
from math import inf
from typing import Iterable

from core.constants import (
    EVAL_HACKER_DATABASE,
    EVAL_HACKER_DETECTED,
    EVAL_HACKER_LOW_SECURITY,
    EVAL_HACKER_NEAR_SERVER,
    EVAL_HACKER_NO_PATH,
    EVAL_HACKER_SERVER,
    IDS_DETECT_PROB,
    IDS_MISS_PROB,
)
from core.graph import NetworkGraph
from core.models import Action, GameState


ADVERSARIAL_HACKER_ACTIONS = ("move", "scan", "attack")
ADVERSARIAL_DEFENDER_ACTIONS = ("block_node", "block_edge", "upgrade", "deploy_ids")


def initial_state(graph: NetworkGraph, start: str, max_turns: int = 10) -> GameState:
    ids_positions = tuple(node.id for node in graph.get_all_nodes() if node.kind == "ids")
    firewall_positions = tuple(node.id for node in graph.get_all_nodes() if node.kind == "firewall")
    return GameState(
        hacker_position=start,
        ids_positions=ids_positions,
        firewall_positions=firewall_positions,
        turn="hacker",
        remaining_turns=max_turns,
    )


def edge_key(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))


def _is_blocked_edge(state: GameState, left: str, right: str) -> bool:
    return edge_key(left, right) in {edge_key(*item) for item in state.blocked_edges}


def active_neighbors(graph: NetworkGraph, state: GameState, node_id: str) -> list[str]:
    result: list[str] = []
    for neighbor in sorted(graph.neighbors(node_id, ignore_blocked=True)):
        if neighbor in state.blocked_nodes:
            continue
        if _is_blocked_edge(state, node_id, neighbor):
            continue
        result.append(neighbor)
    return result


def shortest_distance(graph: NetworkGraph, state: GameState, start: str, goals: list[str]) -> float:
    if start in goals:
        return 0
    queue: deque[tuple[str, int]] = deque([(start, 0)])
    seen = {start}
    while queue:
        current, dist = queue.popleft()
        for neighbor in active_neighbors(graph, state, current):
            if neighbor in seen:
                continue
            if neighbor in goals:
                return dist + 1
            seen.add(neighbor)
            queue.append((neighbor, dist + 1))
    return inf


def has_goal_path(graph: NetworkGraph, state: GameState, goals: list[str]) -> bool:
    return shortest_distance(graph, state, state.hacker_position, goals) < inf


def is_terminal(graph: NetworkGraph, state: GameState, goals: list[str]) -> bool:
    if state.hacker_position in goals:
        return True
    if not has_goal_path(graph, state, goals):
        return True
    return state.remaining_turns <= 0


def hacker_value(graph: NetworkGraph, state: GameState, goals: list[str]) -> float:
    node = graph.get_node(state.hacker_position)
    if node and node.kind == "database":
        return float(EVAL_HACKER_DATABASE)
    if node and node.kind == "server":
        return float(EVAL_HACKER_SERVER)
    if not has_goal_path(graph, state, goals):
        return float(EVAL_HACKER_NO_PATH)

    dist = shortest_distance(graph, state, state.hacker_position, goals)
    security_bonus = 0.0
    if node:
        security_bonus = EVAL_HACKER_LOW_SECURITY * max(0, 6 - node.security_level)
    detected_penalty = EVAL_HACKER_DETECTED if state.detected else 0
    return EVAL_HACKER_NEAR_SERVER / max(dist, 1) + security_bonus + detected_penalty


def defender_value(graph: NetworkGraph, state: GameState, goals: list[str]) -> float:
    value = -hacker_value(graph, state, goals)
    node = graph.get_node(state.hacker_position)
    if node and node.kind in ("server", "database"):
        value -= 100.0
    if not has_goal_path(graph, state, goals):
        value += 150.0
    return value


def _rank_nodes_near_hacker(graph: NetworkGraph, state: GameState, goals: list[str]) -> list[str]:
    excluded = set(goals) | {state.hacker_position} | set(state.blocked_nodes)
    candidates = [
        node.id
        for node in graph.get_all_nodes()
        if node.id not in excluded and node.kind not in ("server", "database")
    ]

    def rank(node_id: str) -> tuple[float, str]:
        probe = GameState(
            hacker_position=state.hacker_position,
            blocked_nodes=state.blocked_nodes | frozenset([node_id]),
            blocked_edges=state.blocked_edges,
            firewall_positions=state.firewall_positions,
            ids_positions=state.ids_positions,
            upgraded_nodes=state.upgraded_nodes,
            detected=state.detected,
            turn=state.turn,
            remaining_turns=state.remaining_turns,
            history=state.history,
        )
        if not has_goal_path(graph, probe, goals):
            return (-1, node_id)
        return (shortest_distance(graph, probe, state.hacker_position, goals), node_id)

    ranked = sorted((rank(node_id) for node_id in candidates), reverse=True)
    return [node_id for score, node_id in ranked if score >= 0]


def hacker_actions(graph: NetworkGraph, state: GameState, goals: list[str]) -> list[Action]:
    actions: list[Action] = []
    for neighbor in active_neighbors(graph, state, state.hacker_position):
        actions.append(Action("hacker", "move", neighbor, f"Move to {neighbor}"))
    if state.hacker_position not in goals:
        actions.append(Action("hacker", "scan", state.hacker_position, f"Scan {state.hacker_position}"))
    return actions[:4]


def defender_actions(graph: NetworkGraph, state: GameState, goals: list[str]) -> list[Action]:
    actions: list[Action] = []
    for node_id in _rank_nodes_near_hacker(graph, state, goals)[:3]:
        actions.append(Action("defender", "block_node", node_id, f"Block {node_id}"))

    if state.ids_positions:
        actions.append(Action("defender", "deploy_ids", state.ids_positions[0], f"Activate IDS at {state.ids_positions[0]}"))
    else:
        for node_id in _rank_nodes_near_hacker(graph, state, goals):
            actions.append(Action("defender", "upgrade", node_id, f"Upgrade {node_id}"))
            break
    return actions[:4]


def apply_action(
    graph: NetworkGraph,
    state: GameState,
    action: Action,
    next_turn: str | None = None,
) -> GameState:
    blocked_nodes = set(state.blocked_nodes)
    blocked_edges = set(state.blocked_edges)
    upgraded_nodes = set(state.upgraded_nodes)
    firewall_positions = set(state.firewall_positions)
    ids_positions = set(state.ids_positions)
    hacker_position = state.hacker_position
    detected = state.detected

    if action.actor == "hacker":
        if action.action_type == "move":
            hacker_position = action.target
            if action.target in state.ids_positions:
                detected = True
            for ids_node in state.ids_positions:
                if graph.has_edge(action.target, ids_node):
                    detected = True
        elif action.action_type == "scan":
            detected = True
        elif action.action_type == "attack":
            detected = True
    else:
        if action.action_type == "block_node":
            blocked_nodes.add(action.target)
        elif action.action_type == "block_edge":
            left, right = action.target.split("|", 1)
            blocked_edges.add(edge_key(left, right))
        elif action.action_type == "upgrade":
            upgraded_nodes.add(action.target)
        elif action.action_type == "deploy_ids":
            ids_positions.add(action.target)
            detected = True
        elif action.action_type == "detect":
            detected = action.target == "detected"

    if next_turn is None:
        next_turn = "defender" if state.turn == "hacker" else "hacker"
    return GameState(
        hacker_position=hacker_position,
        blocked_nodes=frozenset(blocked_nodes),
        blocked_edges=frozenset(blocked_edges),
        firewall_positions=tuple(sorted(firewall_positions)),
        ids_positions=tuple(sorted(ids_positions)),
        upgraded_nodes=frozenset(upgraded_nodes),
        detected=detected,
        turn=next_turn,
        remaining_turns=max(0, state.remaining_turns - 1),
        history=state.history + (action,),
    )


def chance_outcomes(state: GameState) -> list[tuple[float, Action]]:
    return [
        (IDS_DETECT_PROB, Action("chance", "detect", "detected", "IDS detects Hacker")),
        (IDS_MISS_PROB, Action("chance", "detect", "undetected", "IDS misses Hacker")),
    ]
