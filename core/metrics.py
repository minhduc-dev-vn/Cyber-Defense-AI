"""
metrics.py - Collect and format algorithm metrics.
"""
from __future__ import annotations

import time
from typing import Dict, List

from core.models import AlgorithmMetrics


class MetricsCollector:
    """Collects metrics while an algorithm is running."""

    def __init__(self, algorithm_name: str) -> None:
        self.algorithm_name = algorithm_name
        self._start_time: float = 0.0
        self._end_time: float = 0.0

        self.nodes_expanded: int = 0
        self.nodes_generated: int = 0
        self.max_frontier_size: int = 0
        self.num_steps: int = 0
        self.success: bool = False
        self.path: List[str] = []
        self.total_cost: float = 0.0
        self.extra: Dict = {}

    def __enter__(self) -> "MetricsCollector":
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, *args) -> None:
        self._end_time = time.perf_counter()

    def start(self) -> None:
        self._start_time = time.perf_counter()

    def stop(self) -> None:
        self._end_time = time.perf_counter()

    def expand_node(self) -> None:
        self.nodes_expanded += 1
        self.num_steps += 1

    def generate_nodes(self, count: int) -> None:
        self.nodes_generated += count

    def update_frontier_size(self, size: int) -> None:
        if size > self.max_frontier_size:
            self.max_frontier_size = size

    def set_result(self, success: bool, path: List[str], cost: float = 0.0) -> None:
        self.success = success
        self.path = path
        self.total_cost = cost

    @property
    def time_ms(self) -> float:
        end = self._end_time if self._end_time else time.perf_counter()
        return (end - self._start_time) * 1000.0

    def to_metrics(self) -> AlgorithmMetrics:
        return AlgorithmMetrics(
            algorithm=self.algorithm_name,
            success=self.success,
            path=list(self.path),
            total_cost=self.total_cost,
            nodes_expanded=self.nodes_expanded,
            nodes_generated=self.nodes_generated,
            max_frontier_size=self.max_frontier_size,
            time_ms=self.time_ms,
            num_steps=self.num_steps,
            extra=dict(self.extra),
        )


def format_compare_table(metrics_list: List[AlgorithmMetrics]) -> str:
    """Return an ASCII comparison table for log output."""
    header = (
        f"{'Algorithm':<18} | {'OK':>5} | {'Path':>5} | {'Cost':>10} | "
        f"{'Expanded':>9} | {'MaxFront':>9} | {'Time(ms)':>9}"
    )
    sep = "-" * len(header)
    rows = [header, sep]
    for metrics in metrics_list:
        path_len = max(0, len(metrics.path) - 1)
        rows.append(
            f"{metrics.algorithm:<18} | "
            f"{'Yes' if metrics.success else 'No':>5} | "
            f"{path_len:>5} | "
            f"{metrics.total_cost:>10.2f} | "
            f"{metrics.nodes_expanded:>9} | "
            f"{metrics.max_frontier_size:>9} | "
            f"{metrics.time_ms:>9.2f}"
        )
    return "\n".join(rows)
