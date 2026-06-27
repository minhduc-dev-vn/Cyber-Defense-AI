"""Interactive turn loop for Human Hacker vs AI Defender."""
from __future__ import annotations

from dataclasses import dataclass
from math import inf

from algorithms.adversarial.common import (
    active_neighbors,
    apply_action,
    defender_actions,
    defender_value,
    has_goal_path,
    hacker_value,
    initial_state,
    is_terminal,
)
from core.graph import NetworkGraph
from core.models import Action, GameState, StepEvent


@dataclass(frozen=True)
class TurnResult:
    """Result of one human turn plus the AI reaction when applicable."""

    state: GameState
    steps: list[StepEvent]
    hacker_action: Action
    defender_action: Action | None
    terminal: bool
    winner: str | None = None


def new_game_state(graph: NetworkGraph, start: str, max_turns: int = 10) -> GameState:
    """Create the central state for an interactive adversarial match."""
    return initial_state(graph, start, max_turns=max_turns)


def legal_hacker_actions(graph: NetworkGraph, state: GameState, goals: list[str]) -> list[Action]:
    """Return only actions the human can legally take from the current state."""
    actions = [
        Action("hacker", "move", neighbor, f"Move to {neighbor}")
        for neighbor in active_neighbors(graph, state, state.hacker_position)
    ]
    actions.append(Action("hacker", "scan", state.hacker_position, f"Scan {state.hacker_position}"))
    if state.hacker_position in goals:
        actions.append(Action("hacker", "attack", state.hacker_position, f"Attack {state.hacker_position}"))
    return actions


def make_hacker_action(
    graph: NetworkGraph,
    state: GameState,
    goals: list[str],
    action_type: str,
    target: str | None = None,
) -> Action:
    """Build and validate a human action from UI input."""
    normalized = action_type.lower()
    if normalized == "scan":
        target = state.hacker_position
    elif normalized == "attack":
        target = state.hacker_position
    if not target:
        raise ValueError("Hacker action needs a target node.")

    for action in legal_hacker_actions(graph, state, goals):
        if action.action_type == normalized and action.target == target:
            return action
    if normalized == "move":
        raise ValueError(f"Cannot move from {state.hacker_position} to {target}.")
    if normalized == "attack":
        raise ValueError("Attack is only valid after the hacker reaches a goal node.")
    raise ValueError(f"Invalid hacker action: {normalized}.")


def choose_defender_action(
    graph: NetworkGraph,
    state: GameState,
    goals: list[str],
    algorithm: str,
    depth: int,
) -> tuple[Action | None, float, dict[str, int]]:
    """Choose the AI defender response using the selected adversarial algorithm."""
    counters = {"visited": 0, "pruned": 0}
    actions = defender_actions(graph, state, goals)
    if not actions:
        return None, hacker_value(graph, state, goals), counters

    name = algorithm.lower()
    if name == "alpha-beta":
        from algorithms.adversarial.alpha_beta import _alpha_beta

        value, action = _alpha_beta(graph, state, goals, depth, -inf, inf, counters)
    elif name == "expectimax":
        from algorithms.adversarial.expectimax import _expectimax

        value, action = _expectimax(graph, state, goals, depth, counters)
    else:
        from algorithms.adversarial.minimax import _minimax

        value, action = _minimax(graph, state, goals, depth, counters)

    return action or actions[0], value, counters


def play_hacker_turn(
    graph: NetworkGraph,
    state: GameState,
    goals: list[str],
    action_type: str,
    target: str | None,
    algorithm: str,
    depth: int,
    step_index: int = 0,
) -> TurnResult:
    """Apply a human action, let the AI respond, and emit UI-friendly steps."""
    if state.turn != "hacker":
        raise ValueError("It is not the hacker turn.")

    hacker_action = make_hacker_action(graph, state, goals, action_type, target)
    attack_edges = []
    if hacker_action.action_type == "move":
        attack_edges = [_edge_tuple(state.hacker_position, hacker_action.target)]
    after_hacker = apply_action(graph, state, hacker_action, next_turn="defender")
    steps: list[StepEvent] = [
        _step_event(
            step_index,
            algorithm,
            "move" if hacker_action.action_type == "move" else "update",
            graph,
            after_hacker,
            goals,
            action=hacker_action,
            defender_action=None,
            evaluation=hacker_value(graph, after_hacker, goals),
            nodes_evaluated=0,
            attack_edges=attack_edges,
            message=f"Hacker {hacker_action.description}.",
        )
    ]

    if hacker_action.action_type == "attack" and state.hacker_position in goals:
        steps[-1].event_type = "found"
        _mark_terminal(steps[-1], graph, after_hacker, goals, "hacker")
        return TurnResult(after_hacker, steps, hacker_action, None, True, "hacker")

    if is_terminal(graph, after_hacker, goals):
        winner = "hacker" if after_hacker.hacker_position in goals else "defender"
        steps[-1].event_type = "found" if winner == "hacker" else "failure"
        _mark_terminal(steps[-1], graph, after_hacker, goals, winner)
        return TurnResult(after_hacker, steps, hacker_action, None, True, winner)

    defender_action, value, counters = choose_defender_action(
        graph,
        after_hacker,
        goals,
        algorithm,
        max(1, depth),
    )
    if defender_action is None:
        after_defender = after_hacker
    else:
        after_defender = apply_action(graph, after_hacker, defender_action, next_turn="hacker")

    terminal = is_terminal(graph, after_defender, goals)
    winner = None
    event_type = "update"
    if terminal:
        winner = "hacker" if after_defender.hacker_position in goals else "defender"
        event_type = "found" if winner == "hacker" else "failure"

    steps.append(
        _step_event(
            step_index + 1,
            algorithm,
            event_type,
            graph,
            after_defender,
            goals,
            action=hacker_action,
            defender_action=defender_action,
            evaluation=value,
            nodes_evaluated=counters.get("visited", 0),
            attack_edges=attack_edges,
            pruned=counters.get("pruned", 0),
            message=(
                f"AI Defender {defender_action.description if defender_action else 'waits'}; "
                f"utility={value:.2f}."
            ),
        )
    )
    if terminal and winner:
        _mark_terminal(steps[-1], graph, after_defender, goals, winner)
    return TurnResult(after_defender, steps, hacker_action, defender_action, terminal, winner)


def _state_payload(state: GameState, goals: list[str]) -> dict[str, object]:
    return {
        "game_state": state,
        "hacker_position": state.hacker_position,
        "blocked_nodes": sorted(state.blocked_nodes),
        "blocked_edges": sorted(state.blocked_edges),
        "ids_positions": list(state.ids_positions),
        "upgraded_nodes": sorted(state.upgraded_nodes),
        "detected": state.detected,
        "turn": state.turn,
        "remaining_turns": state.remaining_turns,
        "goals": list(goals),
    }


def _edge_tuple(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))


def _hacker_path_edges(state: GameState) -> list[tuple[str, str]]:
    path = list(_hacker_path(state))
    return [_edge_tuple(left, right) for left, right in zip(path, path[1:])]


def _defender_action_edges(graph: NetworkGraph, state: GameState, action: Action | None) -> list[tuple[str, str]]:
    if action is None:
        return []
    if action.action_type == "block_edge":
        left, right = action.target.split("|", 1)
        return [_edge_tuple(left, right)]
    if action.action_type == "block_node":
        return [_edge_tuple(action.target, neighbor) for neighbor in graph.neighbors(action.target, ignore_blocked=True)]
    if action.action_type in {"deploy_ids", "upgrade"}:
        return [_edge_tuple(action.target, neighbor) for neighbor in graph.neighbors(action.target, ignore_blocked=True)]
    return []


def _defender_focus_node(action: Action | None, fallback: str) -> str:
    if action is None:
        return fallback
    if action.action_type == "block_edge":
        return action.target.split("|", 1)[0]
    return action.target


def _step_event(
    index: int,
    algorithm: str,
    event_type: str,
    graph: NetworkGraph,
    state: GameState,
    goals: list[str],
    *,
    action: Action,
    defender_action: Action | None,
    evaluation: float,
    nodes_evaluated: int,
    message: str,
    attack_edges: list[tuple[str, str]] | None = None,
    pruned: int = 0,
) -> StepEvent:
    current_node = _defender_focus_node(defender_action, state.hacker_position)
    defender_edges = _defender_action_edges(graph, state, defender_action)
    data = _state_payload(state, goals)
    data.update(
        {
            "action": action,
            "defender_action": defender_action,
            "evaluation": evaluation,
            "defender_score": defender_value(graph, state, goals),
            "hacker_path": list(_hacker_path(state)),
            "attack_edges": attack_edges if attack_edges is not None else _hacker_path_edges(state),
            "defender_edges": defender_edges,
            "ai_focus_node": current_node if defender_action else None,
            "pruned_branches": pruned,
        }
    )
    return StepEvent(
        step_index=index,
        algorithm=algorithm,
        event_type=event_type,
        current_node=current_node,
        path=list(_hacker_path(state)),
        highlighted_edges=defender_edges or list(state.blocked_edges),
        message=message,
        nodes_expanded=nodes_evaluated,
        nodes_generated=nodes_evaluated,
        total_cost=evaluation,
        data=data,
    )


def _mark_terminal(
    step: StepEvent,
    graph: NetworkGraph,
    state: GameState,
    goals: list[str],
    winner: str,
) -> None:
    title, reason = _terminal_outcome(graph, state, goals, winner)
    step.data.update(
        {
            "terminal": True,
            "winner": winner,
            "outcome_title": title,
            "outcome_reason": reason,
        }
    )
    step.message = f"{title}: {reason}"


def _terminal_outcome(
    graph: NetworkGraph,
    state: GameState,
    goals: list[str],
    winner: str,
) -> tuple[str, str]:
    if winner == "hacker":
        return "Hacker thành công", f"đã xâm nhập mục tiêu {state.hacker_position}."
    if state.remaining_turns <= 0:
        return "AI phòng thủ thành công", "hacker đã hết lượt trước khi vào được mục tiêu."
    if not has_goal_path(graph, state, goals):
        return "AI phòng thủ thành công", "mọi đường còn lại tới mục tiêu đã bị chặn."
    return "AI phòng thủ thành công", "hacker chưa vào được mục tiêu."


def _hacker_path(state: GameState) -> tuple[str, ...]:
    path = [state.history[0].target] if state.history and state.history[0].action_type == "move" else []
    if not path:
        path = [state.hacker_position]
    for action in state.history[1:]:
        if action.actor == "hacker" and action.action_type == "move":
            path.append(action.target)
    if path[-1] != state.hacker_position:
        path.append(state.hacker_position)
    return tuple(path)
