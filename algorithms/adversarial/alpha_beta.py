"""Alpha-Beta pruning for the adversarial simulator."""
from __future__ import annotations

import time
from math import inf
from typing import Iterator

from algorithms.adversarial.common import (
    apply_action,
    defender_actions,
    hacker_actions,
    hacker_value,
    initial_state,
    is_terminal,
)
from core.graph import NetworkGraph
from core.models import Action, AlgorithmMetrics, AlgorithmResult, GameState, StepEvent


def _alpha_beta(
    graph: NetworkGraph,
    state: GameState,
    goals: list[str],
    depth: int,
    alpha: float,
    beta: float,
    counters: dict[str, int],
) -> tuple[float, Action | None]:
    counters["visited"] += 1
    if depth == 0 or is_terminal(graph, state, goals):
        return hacker_value(graph, state, goals), None

    actions = hacker_actions(graph, state, goals) if state.turn == "hacker" else defender_actions(graph, state, goals)
    if not actions:
        return hacker_value(graph, state, goals), None

    if state.turn == "hacker":
        best_value = -inf
        best_action: Action | None = None
        for action in actions:
            value, _ = _alpha_beta(graph, apply_action(graph, state, action), goals, depth - 1, alpha, beta, counters)
            if value > best_value:
                best_value = value
                best_action = action
            alpha = max(alpha, best_value)
            if alpha >= beta:
                counters["pruned"] += 1
                break
        return best_value, best_action

    best_value = inf
    best_action = None
    for action in actions:
        value, _ = _alpha_beta(graph, apply_action(graph, state, action), goals, depth - 1, alpha, beta, counters)
        if value < best_value:
            best_value = value
            best_action = action
        beta = min(beta, best_value)
        if alpha >= beta:
            counters["pruned"] += 1
            break
    return best_value, best_action


def solve_steps(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    depth: int = 3,
) -> Iterator[StepEvent]:
    """Yield root-level Alpha-Beta decisions."""
    state = initial_state(graph, start)
    counters = {"visited": 0, "pruned": 0}
    step_idx = 0
    hacker_choices = hacker_actions(graph, state, goals)
    defender_choices = defender_actions(graph, state, goals)
    yield StepEvent(
        step_index=step_idx,
        algorithm="Alpha-Beta",
        event_type="info",
        current_node=state.hacker_position,
        message=f"[Step {step_idx:03d}] Alpha-Beta adversarial sim start at {start}, depth={depth}.",
        data={"turn": state.turn, "depth": depth, "alpha": -inf, "beta": inf, "state": state},
    )
    step_idx += 1

    best_value = -inf
    best_action: Action | None = None
    alpha = -inf
    beta = inf
    for action in hacker_choices:
        before_visited = counters["visited"]
        before_pruned = counters["pruned"]
        child = apply_action(graph, state, action, next_turn="defender")
        value, _ = _alpha_beta(graph, child, goals, depth - 1, alpha, beta, counters)
        if value > best_value:
            best_value = value
            best_action = action
        alpha = max(alpha, best_value)
        defender_best = None
        defender_state = child
        if best_action is not None:
            defender_choices_local = defender_actions(graph, defender_state, goals)
            defender_best = defender_choices_local[0] if defender_choices_local else None
        yield StepEvent(
            step_index=step_idx,
            algorithm="Alpha-Beta",
            event_type="update",
            current_node=action.target,
            path=[state.hacker_position, action.target] if action.action_type == "move" else [state.hacker_position],
            message=(
                f"[Step {step_idx:03d}] Hacker {action.description}; score={value:.2f}; alpha={alpha:.2f}; beta={beta:.2f}; "
                f"pruned+={counters['pruned'] - before_pruned}."
            ),
            nodes_expanded=counters["visited"],
            nodes_generated=counters["visited"],
            total_cost=value,
            data={
                "turn": state.turn,
                "depth": depth,
                "action": action,
                "defender_action": defender_best,
                "evaluation": value,
                "alpha": alpha,
                "beta": beta,
                "pruned_branches": counters["pruned"],
                "state": child,
                "visited_delta": counters["visited"] - before_visited,
            },
        )
        step_idx += 1

    if best_action is None:
        best_value = hacker_value(graph, state, goals)
    yield StepEvent(
        step_index=step_idx,
        algorithm="Alpha-Beta",
        event_type="found",
        current_node=best_action.target if best_action else state.hacker_position,
        path=[state.hacker_position, best_action.target] if best_action and best_action.action_type == "move" else [state.hacker_position],
        message=(
            f"[Step {step_idx:03d}] Alpha-Beta chọn {best_action.description if best_action else 'no-op'}; "
            f"score={best_value:.2f}; pruned={counters['pruned']}."
        ),
        nodes_expanded=counters["visited"],
        nodes_generated=counters["visited"],
        total_cost=best_value,
        data={
            "turn": state.turn,
            "depth": depth,
            "action": best_action,
            "evaluation": best_value,
            "alpha": alpha,
            "beta": beta,
            "pruned_branches": counters["pruned"],
            "state": state,
        },
    )


def run(
    graph: NetworkGraph,
    start: str,
    goals: list[str],
    depth: int = 3,
) -> AlgorithmResult:
    """Run Alpha-Beta and return a full result."""
    start_time = time.perf_counter()
    steps = list(solve_steps(graph, start, goals, depth=depth))
    time_ms = (time.perf_counter() - start_time) * 1000.0
    last = steps[-1] if steps else None
    action = last.data.get("action") if last else None
    metrics = AlgorithmMetrics(
        algorithm="Alpha-Beta",
        success=last is not None and last.event_type == "found",
        path=last.path if last else [],
        total_cost=last.total_cost if last else 0.0,
        nodes_expanded=last.nodes_expanded if last else 0,
        nodes_generated=last.nodes_generated if last else 0,
        time_ms=time_ms,
        num_steps=len(steps),
        extra={
            "chosen_action": action.description if action else "no-op",
            "evaluation": last.total_cost if last else 0.0,
            "nodes_evaluated": last.nodes_expanded if last else 0,
            "pruned_branches": last.data.get("pruned_branches", 0) if last else 0,
        },
    )
    return AlgorithmResult(metrics=metrics, steps=steps, final_state=action)
