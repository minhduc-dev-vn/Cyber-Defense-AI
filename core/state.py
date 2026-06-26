"""
state.py — AlgorithmState và GameplayState.

AlgorithmState: trạng thái UI cho 1 thuật toán đang chạy (step, pause, ...).
GameplayState: trạng thái toàn bộ ứng dụng (map được chọn, chế độ, ...).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional

from core.models import AlgorithmResult, StepEvent, AlgorithmMetrics
from core.event_log import EventLog


@dataclass
class AlgorithmRunState:
    """
    Trạng thái chạy một thuật toán trong UI.

    Lưu: danh sách step đã sinh, bước hiện tại, trạng thái play/pause.
    """
    algorithm_name: str = ""
    status: str = "ready"        # "ready" | "running" | "paused" | "success" | "failure"
    steps: List[StepEvent] = field(default_factory=list)
    current_step_index: int = -1
    result: Optional[AlgorithmResult] = None
    log: EventLog = field(default_factory=EventLog)
    metrics: Optional[AlgorithmMetrics] = None

    # Animation timing
    last_step_time: float = 0.0
    step_delay: float = 0.6      # giây, tương ứng speed 1x

    def reset(self) -> None:
        """Reset về trạng thái ban đầu."""
        self.status = "ready"
        self.steps.clear()
        self.current_step_index = -1
        self.result = None
        self.log.clear()
        self.metrics = None
        self.last_step_time = 0.0

    @property
    def current_step(self) -> Optional[StepEvent]:
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance_step(self) -> bool:
        """Tiến một bước animation. Trả về True nếu còn bước tiếp theo."""
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            return True
        return False

    def is_done(self) -> bool:
        return self.status in ("success", "failure")

    def is_running(self) -> bool:
        return self.status == "running"


@dataclass
class AppState:
    """
    Trạng thái toàn bộ ứng dụng Pygame.

    Lưu: nhóm thuật toán đang chọn, map đang dùng,
    tốc độ, seed, chế độ hiển thị, ...
    """
    # Chọn thuật toán
    selected_group_index: int = 0     # 0..5 (6 nhóm)
    selected_algo_index: int = 0      # index trong nhóm
    selected_map_name: str = "pathfinding_basic"

    # Map và đồ thị
    map_data: Optional[Any] = None    # MapData

    # Trạng thái chạy
    run_state: AlgorithmRunState = field(default_factory=AlgorithmRunState)

    # Điều khiển
    speed_key: str = "1x"
    random_seed: int = 42
    show_details: bool = True

    # Simulated Annealing params
    sa_t0: float = 100.0
    sa_alpha: float = 0.95
    sa_tmin: float = 0.1
    sa_max_steps: int = 1000

    # Minimax/Alpha-Beta/Expectimax params
    game_depth: int = 3

    # UI state
    hovered_node: Optional[str] = None
    selected_node: Optional[str] = None  # Node đang click xem metadata

    # Compare mode
    compare_results: List[AlgorithmResult] = field(default_factory=list)
    compare_mode: bool = False

    # Thông báo tạm thời
    toast_message: str = ""
    toast_timer: float = 0.0
