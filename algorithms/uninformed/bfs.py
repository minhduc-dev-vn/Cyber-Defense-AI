"""
bfs.py — Breadth-First Search (Nhóm 1: Tìm kiếm không có thông tin).

Bài toán: Hacker tìm đường từ node xuất phát tới Server/Database.
Dùng FIFO queue. Tìm đường ít bước nhất khi mọi cạnh đều bằng nhau.
"""
from __future__ import annotations

import time
from collections import deque
from typing import Dict, Iterator, List, Optional

from core.graph import NetworkGraph
from core.models import StepEvent, AlgorithmResult, AlgorithmMetrics
from core.metrics import MetricsCollector
from core.utils import reconstruct_path


def solve_steps(
    graph: NetworkGraph,
    start: str,
    goals: List[str],
) -> Iterator[StepEvent]:
    """
    Generator BFS từng bước.

    Yields StepEvent cho mỗi thao tác mở rộng node.
    """
    mc = MetricsCollector("BFS")
    mc.start()

    goal_set = set(goals)
    frontier: deque[str] = deque([start])
    reached: Dict[str, Optional[str]] = {start: None}  # node -> parent

    step_idx = 0

    yield StepEvent(
        step_index=step_idx,
        algorithm="BFS",
        event_type="info",
        current_node=start,
        frontier=list(frontier),
        explored=[],
        message=f"[Bước {step_idx:03d}] BFS: Khởi tạo. Start = {start!r}, Goals = {goals}",
    )

    explored: List[str] = []

    while frontier:
        current = frontier.popleft()
        mc.expand_node()
        explored.append(current)

        step_idx += 1

        if current in goal_set:
            path = reconstruct_path(reached, current)
            mc.set_result(True, path, float(len(path) - 1))
            mc.stop()
            yield StepEvent(
                step_index=step_idx,
                algorithm="BFS",
                event_type="found",
                current_node=current,
                frontier=list(frontier),
                explored=list(explored),
                path=path,
                message=(
                    f"[Bước {step_idx:03d}] BFS: 🎯 Tìm thấy mục tiêu {current!r}! "
                    f"Đường đi: {' → '.join(path)} (độ dài {len(path)-1} bước)"
                ),
                nodes_expanded=mc.nodes_expanded,
                nodes_generated=mc.nodes_generated,
                max_frontier_size=mc.max_frontier_size,
                total_cost=float(len(path) - 1),
            )
            return

        neighbors = sorted(graph.neighbors(current, ignore_blocked=True))
        for neighbor in neighbors:
            if neighbor not in reached:
                reached[neighbor] = current
                frontier.append(neighbor)
                mc.nodes_generated += 1

        mc.update_frontier_size(len(frontier))

        yield StepEvent(
            step_index=step_idx,
            algorithm="BFS",
            event_type="expand",
            current_node=current,
            frontier=list(frontier),
            explored=list(explored),
            message=(
                f"[Bước {step_idx:03d}] BFS: Mở rộng {current!r}. "
                f"Frontier ({len(frontier)} node): {list(frontier)}"
            ),
            nodes_expanded=mc.nodes_expanded,
            nodes_generated=mc.nodes_generated,
            max_frontier_size=mc.max_frontier_size,
        )

    # Không tìm thấy
    mc.set_result(False, [])
    mc.stop()
    step_idx += 1
    yield StepEvent(
        step_index=step_idx,
        algorithm="BFS",
        event_type="info",
        frontier=[],
        explored=list(explored),
        message=f"[Bước {step_idx:03d}] BFS: ❌ Không tìm thấy đường đến mục tiêu.",
        nodes_expanded=mc.nodes_expanded,
        nodes_generated=mc.nodes_generated,
        max_frontier_size=mc.max_frontier_size,
    )


def run(
    graph: NetworkGraph,
    start: str,
    goals: List[str],
) -> AlgorithmResult:
    """Chạy BFS và trả về AlgorithmResult đầy đủ."""
    start_time = time.perf_counter()
    steps = list(solve_steps(graph, start, goals))
    time_ms = (time.perf_counter() - start_time) * 1000.0
    last = steps[-1] if steps else None

    success = last is not None and last.event_type == "found"
    path = last.path if (last and last.path) else []
    cost = last.total_cost if last else 0.0

    metrics = AlgorithmMetrics(
        algorithm="BFS",
        success=success,
        path=path,
        total_cost=cost,
        nodes_expanded=last.nodes_expanded if last else 0,
        nodes_generated=last.nodes_generated if last else 0,
        max_frontier_size=last.max_frontier_size if last else 0,
        time_ms=time_ms,
        num_steps=len(steps),
    )
    return AlgorithmResult(metrics=metrics, steps=steps)
