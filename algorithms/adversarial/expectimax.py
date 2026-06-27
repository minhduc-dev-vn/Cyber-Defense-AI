"""Expectimax search for the adversarial simulator."""
from __future__ import annotations

import time
from math import inf
from typing import Iterator

from algorithms.adversarial.common import (
    apply_action,
    chance_outcomes,
    defender_actions,
    hacker_actions,
    hacker_value,
    initial_state,
    is_terminal,
)
from core.graph import NetworkGraph
from core.models import Action, AlgorithmMetrics, AlgorithmResult, GameState, StepEvent


def _expectimax(
    graph: NetworkGraph,
    state: GameState,
    goals: list[str],
    depth: int,
    counters: dict[str, int],
) -> tuple[float, Action | None]:
    counters["visited"] += 1
    if depth == 0 or is_terminal(graph, state, goals):
        return hacker_value(graph, state, goals), None

    if state.turn == "chance":
        expected = 0.0
        for probability, action in chance_outcomes(state):
            child = apply_action(graph, state, action, next_turn="defender")
            value, _ = _expectimax(graph, child, goals, depth - 1, counters)
            expected += probability * value
        return expected, None

    actions = hacker_actions(graph, state, goals) if state.turn == "hacker" else defender_actions(graph, state, goals)
    if not actions:
        return hacker_value(graph, state, goals), None

    if state.turn == "hacker":
        best_value = -inf
        best_action: Action | None = None
        for action in actions:
            child_turn = "chance" if action.action_type == "move" else "defender"
            child = apply_action(graph, state, action, next_turn=child_turn)
            value, _ = _expectimax(graph, child, goals, depth - 1, counters)
            if value > best_value:
                best_value = value
                best_action = action
        return best_value, best_action

    best_value = inf
    best_action = None
    for action in actions:
        value, _ = _expectimax(graph, apply_action(graph, state, action), goals, depth - 1, counters)
        if value < best_value:
            best_value = value
            best_action = action
    return best_value, best_action


def solve_steps(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    depth: int = 3,
) -> Iterator[StepEvent]:
    """Yield root-level Expectimax decisions."""
    state = initial_state(graph, start)
    counters = {"visited": 0}
    step_idx = 0
    outcomes = [(prob, action.description) for prob, action in chance_outcomes(state)]
    hacker_choices = hacker_actions(graph, state, goals)
    defender_choices = defender_actions(graph, state, goals)
    yield StepEvent(
        step_index=step_idx,
        algorithm="Expectimax",
        event_type="info",
        current_node=state.hacker_position,
        message=f"[Step {step_idx:03d}] Expectimax adversarial sim start at {start}, depth={depth}, chance={outcomes}.",
        data={"turn": state.turn, "depth": depth, "chance_outcomes": outcomes, "state": state},
    )
    step_idx += 1

    best_value = -inf
    best_action: Action | None = None
    for action in hacker_choices:
        child_turn = "chance" if action.action_type == "move" else "defender"
        child = apply_action(graph, state, action, next_turn=child_turn)
        value, _ = _expectimax(graph, child, goals, depth - 1, counters)
        if value > best_value:
            best_value = value
            best_action = action
        defender_best = None
        if child_turn == "defender":
            defender_choices_local = defender_actions(graph, child, goals)
            defender_best = defender_choices_local[0] if defender_choices_local else None
        yield StepEvent(
            step_index=step_idx,
            algorithm="Expectimax",
            event_type="update",
            current_node=action.target,
            path=[state.hacker_position, action.target] if action.action_type == "move" else [state.hacker_position],
            message=(
                f"[Step {step_idx:03d}] Hacker {action.description}; expected={value:.2f}; chance={outcomes}."
            ),
            nodes_expanded=counters["visited"],
            nodes_generated=counters["visited"],
            total_cost=value,
            data={
                "turn": state.turn,
                "depth": depth,
                "action": action,
                "defender_action": defender_best,
                "expected_value": value,
                "evaluation": value,
                "chance_outcomes": outcomes,
                "state": child,
            },
        )
        step_idx += 1

    if best_action is None:
        best_value = hacker_value(graph, state, goals)
    yield StepEvent(
        step_index=step_idx,
        algorithm="Expectimax",
        event_type="found",
        current_node=best_action.target if best_action else state.hacker_position,
        path=[state.hacker_position, best_action.target] if best_action and best_action.action_type == "move" else [state.hacker_position],
        message=(
            f"[Step {step_idx:03d}] Expectimax chọn {best_action.description if best_action else 'no-op'}; expected={best_value:.2f}."
        ),
        nodes_expanded=counters["visited"],
        nodes_generated=counters["visited"],
        total_cost=best_value,
        data={
            "turn": state.turn,
            "depth": depth,
            "action": best_action,
            "expected_value": best_value,
            "evaluation": best_value,
            "chance_outcomes": outcomes,
            "state": state,
        },
    )


def run(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    depth: int = 3,
) -> AlgorithmResult:
    """Run Expectimax and return a full result."""
    start_time = time.perf_counter()
    steps = list(solve_steps(graph, start, goals, depth=depth))
    time_ms = (time.perf_counter() - start_time) * 1000.0
    last = steps[-1] if steps else None
    action = last.data.get("action") if last else None
    metrics = AlgorithmMetrics(
        algorithm="Expectimax",
        success=last is not None and last.event_type == "found",
        path=last.path if last else [],
        total_cost=last.total_cost if last else 0.0,
        nodes_expanded=last.nodes_expanded if last else 0,
        nodes_generated=last.nodes_generated if last else 0,
        time_ms=time_ms,
        num_steps=len(steps),
        extra={
            "chosen_action": action.description if action else "no-op",
            "expected_value": last.total_cost if last else 0.0,
            "nodes_evaluated": last.nodes_expanded if last else 0,
            "chance_outcomes": last.data.get("chance_outcomes", []) if last else [],
        },
    )
    return AlgorithmResult(metrics=metrics, steps=steps, final_state=action)
