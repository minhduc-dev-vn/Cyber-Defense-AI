"""
ucs.py — Uniform Cost Search (Nhóm 1: Tìm kiếm không có thông tin).

Bài toán: Hacker tìm đường có tổng chi phí thấp nhất tới Server/Database.
Dùng priority queue theo g(n). Đảm bảo tối ưu với cost không âm.
"""
from __future__ import annotations

import heapq
import time
from typing import Dict, Iterator, List, Optional, Tuple

from core.graph import NetworkGraph
from core.models import StepEvent, AlgorithmResult, AlgorithmMetrics
from core.metrics import MetricsCollector
from core.utils import reconstruct_path


def solve_steps(
    graph: NetworkGraph,
    start: str,
    goals: List[str],
) -> Iterator[StepEvent]:
    """Generator UCS từng bước (priority queue theo g(n))."""
    mc = MetricsCollector("UCS")
    mc.start()

    goal_set = set(goals)
    # heap: (cost, node_id)
    frontier: List[Tuple[float, str]] = [(0.0, start)]
    reached: Dict[str, Optional[str]] = {start: None}   # node -> parent
    g_cost: Dict[str, float] = {start: 0.0}

    step_idx = 0
    explored: List[str] = []

    yield StepEvent(
        step_index=step_idx,
        algorithm="UCS",
        event_type="info",
        current_node=start,
        frontier=[start],
        explored=[],
        message=f"[Bước {step_idx:03d}] UCS: Khởi tạo. Start = {start!r}, g(start) = 0",
    )

    while frontier:
        cost, current = heapq.heappop(frontier)

        # Bỏ qua nếu đã tìm được đường rẻ hơn tới current
        if current in explored:
            continue

        mc.expand_node()
        explored.append(current)

        step_idx += 1

        if current in goal_set:
            path = reconstruct_path(reached, current)
            mc.set_result(True, path, cost)
            mc.stop()
            yield StepEvent(
                step_index=step_idx,
                algorithm="UCS",
                event_type="found",
                current_node=current,
                frontier=[n for _, n in frontier],
                explored=list(explored),
                path=path,
                message=(
                    f"[Bước {step_idx:03d}] UCS: 🎯 Mục tiêu {current!r}! "
                    f"g = {cost:.2f}. Đường: {' → '.join(path)}"
                ),
                nodes_expanded=mc.nodes_expanded,
                nodes_generated=mc.nodes_generated,
                max_frontier_size=mc.max_frontier_size,
                total_cost=cost,
                data={"g": cost},
            )
            return

        for neighbor_id, edge_cost, _ in graph.neighbors_with_cost(current, ignore_blocked=True):
            new_cost = cost + edge_cost
            if neighbor_id not in g_cost or new_cost < g_cost[neighbor_id]:
                g_cost[neighbor_id] = new_cost
                reached[neighbor_id] = current
                heapq.heappush(frontier, (new_cost, neighbor_id))
                mc.nodes_generated += 1

        mc.update_frontier_size(len(frontier))

        yield StepEvent(
            step_index=step_idx,
            algorithm="UCS",
            event_type="expand",
            current_node=current,
            frontier=[n for _, n in frontier],
            explored=list(explored),
            message=(
                f"[Bước {step_idx:03d}] UCS: Mở rộng {current!r} với g = {cost:.2f}."
            ),
            nodes_expanded=mc.nodes_expanded,
            nodes_generated=mc.nodes_generated,
            max_frontier_size=mc.max_frontier_size,
            data={"g": cost},
        )

    mc.set_result(False, [])
    mc.stop()
    step_idx += 1
    yield StepEvent(
        step_index=step_idx,
        algorithm="UCS",
        event_type="info",
        frontier=[],
        explored=list(explored),
        message=f"[Bước {step_idx:03d}] UCS: ❌ Không tìm thấy đường đến mục tiêu.",
        nodes_expanded=mc.nodes_expanded,
        nodes_generated=mc.nodes_generated,
        max_frontier_size=mc.max_frontier_size,
    )


def run(
    graph: NetworkGraph,
    start: str,
    goals: List[str],
) -> AlgorithmResult:
    """Chạy UCS và trả về AlgorithmResult đầy đủ."""
    start_time = time.perf_counter()
    steps = list(solve_steps(graph, start, goals))
    time_ms = (time.perf_counter() - start_time) * 1000.0
    last = steps[-1] if steps else None
    success = last is not None and last.event_type == "found"
    path = last.path if (last and last.path) else []
    cost = last.total_cost if last else 0.0
    metrics = AlgorithmMetrics(
        algorithm="UCS",
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
