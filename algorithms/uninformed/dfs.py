"""
dfs.py — Depth-First Search (Nhóm 1: Tìm kiếm không có thông tin).

Bài toán: Hacker tìm đường từ node xuất phát tới Server/Database.
Dùng LIFO stack. Thứ tự node kề cố định theo id để kết quả ổn định.
"""
from __future__ import annotations

import time
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
    """Generator DFS từng bước (LIFO stack, tránh lặp qua reached)."""
    mc = MetricsCollector("DFS")
    mc.start()

    goal_set = set(goals)
    stack: List[str] = [start]
    reached: Dict[str, Optional[str]] = {start: None}  # node -> parent

    step_idx = 0
    explored: List[str] = []

    yield StepEvent(
        step_index=step_idx,
        algorithm="DFS",
        event_type="info",
        current_node=start,
        frontier=list(stack),
        explored=[],
        message=f"[Bước {step_idx:03d}] DFS: Khởi tạo stack. Start = {start!r}, Goals = {goals}",
    )

    while stack:
        current = stack.pop()

        if current in explored:
            continue

        mc.expand_node()
        explored.append(current)

        step_idx += 1

        if current in goal_set:
            path = reconstruct_path(reached, current)
            mc.set_result(True, path, float(len(path) - 1))
            mc.stop()
            yield StepEvent(
                step_index=step_idx,
                algorithm="DFS",
                event_type="found",
                current_node=current,
                frontier=list(stack),
                explored=list(explored),
                path=path,
                message=(
                    f"[Bước {step_idx:03d}] DFS: 🎯 Tìm thấy mục tiêu {current!r}! "
                    f"Đường đi: {' → '.join(path)} (độ dài {len(path)-1} bước)"
                ),
                nodes_expanded=mc.nodes_expanded,
                nodes_generated=mc.nodes_generated,
                max_frontier_size=mc.max_frontier_size,
                total_cost=float(len(path) - 1),
            )
            return

        # Sắp xếp ngược để node có id nhỏ hơn được duyệt trước (ổn định)
        neighbors = sorted(graph.neighbors(current, ignore_blocked=True), reverse=True)
        for neighbor in neighbors:
            if neighbor not in reached:
                reached[neighbor] = current
                stack.append(neighbor)
                mc.nodes_generated += 1

        mc.update_frontier_size(len(stack))

        yield StepEvent(
            step_index=step_idx,
            algorithm="DFS",
            event_type="expand",
            current_node=current,
            frontier=list(stack),
            explored=list(explored),
            message=(
                f"[Bước {step_idx:03d}] DFS: Mở rộng {current!r} (đi sâu). "
                f"Stack ({len(stack)} node): {list(reversed(stack[:5]))!r}..."
            ),
            nodes_expanded=mc.nodes_expanded,
            nodes_generated=mc.nodes_generated,
            max_frontier_size=mc.max_frontier_size,
        )

    mc.set_result(False, [])
    mc.stop()
    step_idx += 1
    yield StepEvent(
        step_index=step_idx,
        algorithm="DFS",
        event_type="info",
        frontier=[],
        explored=list(explored),
        message=f"[Bước {step_idx:03d}] DFS: ❌ Không tìm thấy đường đến mục tiêu.",
        nodes_expanded=mc.nodes_expanded,
        nodes_generated=mc.nodes_generated,
        max_frontier_size=mc.max_frontier_size,
    )


def run(
    graph: NetworkGraph,
    start: str,
    goals: List[str],
) -> AlgorithmResult:
    """Chạy DFS và trả về AlgorithmResult đầy đủ."""
    start_time = time.perf_counter()
    steps = list(solve_steps(graph, start, goals))
    time_ms = (time.perf_counter() - start_time) * 1000.0
    last = steps[-1] if steps else None
    success = last is not None and last.event_type == "found"
    path = last.path if (last and last.path) else []
    cost = last.total_cost if last else 0.0
    metrics = AlgorithmMetrics(
        algorithm="DFS",
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
