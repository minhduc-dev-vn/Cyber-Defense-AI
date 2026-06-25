"""
models.py — Dataclass cho toàn bộ domain model của Cyber Defense AI.

Bao gồm: Node, Edge, GameState, Action, StepEvent, AlgorithmResult,
DefenseConfig, BeliefState, CSPState.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ─── Node ─────────────────────────────────────────────────────────────────────

@dataclass
class Node:
    """Một node trong đồ thị mạng máy tính."""
    id: str
    kind: str                            # pc/router/switch/firewall/ids/server/database
    position: tuple[int, int]            # Tọa độ hiển thị trên UI (pixel)
    security_level: int = 5             # 1..10
    zone: Optional[str] = None          # User Zone / DMZ / Server Zone / Quarantine Zone
    blocked: bool = False
    visible: bool = True
    compromised: bool = False
    monitored: bool = False
    importance: int = 5                 # 1..10
    detection_risk: float = 0.0         # Xác suất bị IDS phát hiện khi đi qua

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Node):
            return self.id == other.id
        return NotImplemented

    def __repr__(self) -> str:
        return f"Node({self.id!r}, kind={self.kind!r})"


# ─── Edge ─────────────────────────────────────────────────────────────────────

@dataclass
class Edge:
    """Một cạnh kết nối giữa hai node."""
    source: str
    target: str
    base_cost: float = 1.0
    blocked: bool = False
    bidirectional: bool = True

    def __hash__(self) -> int:
        if self.bidirectional:
            return hash(frozenset([self.source, self.target]))
        return hash((self.source, self.target))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Edge):
            if self.bidirectional and other.bidirectional:
                return frozenset([self.source, self.target]) == frozenset([other.source, other.target])
            return (self.source, self.target) == (other.source, other.target)
        return NotImplemented

    def __repr__(self) -> str:
        arrow = "↔" if self.bidirectional else "→"
        return f"Edge({self.source!r} {arrow} {self.target!r}, cost={self.base_cost})"


# ─── Action ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Action:
    """Một hành động trong game (Hacker hoặc Defender thực hiện)."""
    actor: str                          # "hacker" | "defender"
    action_type: str                    # "move" | "block_node" | "block_edge" | "upgrade" | "deploy_firewall" | "deploy_ids"
    target: str                         # node id hoặc "src-dst" cho edge
    description: str = ""


# ─── GameState ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class GameState:
    """Trạng thái game đầy đủ cho mode đối kháng."""
    hacker_position: str
    blocked_nodes: frozenset[str] = field(default_factory=frozenset)
    blocked_edges: frozenset[tuple[str, str]] = field(default_factory=frozenset)
    firewall_positions: tuple[str, ...] = field(default_factory=tuple)
    ids_positions: tuple[str, ...] = field(default_factory=tuple)
    upgraded_nodes: frozenset[str] = field(default_factory=frozenset)
    detected: bool = False
    turn: str = "hacker"               # "hacker" | "defender"
    remaining_turns: int = 10
    history: tuple[Action, ...] = field(default_factory=tuple)


# ─── DefenseConfig ────────────────────────────────────────────────────────────

@dataclass
class DefenseConfig:
    """Cấu hình phòng thủ cho Local Search (Hill Climbing / SA)."""
    firewall_nodes: list[str] = field(default_factory=list)
    ids_nodes: list[str] = field(default_factory=list)
    upgraded_nodes: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"DefenseConfig(firewalls={self.firewall_nodes}, "
            f"ids={self.ids_nodes}, upgraded={self.upgraded_nodes})"
        )


# ─── BeliefState ──────────────────────────────────────────────────────────────

@dataclass
class BeliefState:
    """Tập hợp vị trí Hacker mà Defender tin là có thể xảy ra."""
    possible_positions: frozenset[str]
    observations: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"BeliefState({set(self.possible_positions)})"


# ─── CSPState ─────────────────────────────────────────────────────────────────

@dataclass
class CSPAssignment:
    """Kết quả gán zone cho các node trong bài toán CSP."""
    assignments: dict[str, str] = field(default_factory=dict)   # node_id -> zone
    domains: dict[str, list[str]] = field(default_factory=dict) # node_id -> danh sách zone còn lại
    num_backtracks: int = 0
    num_assignments: int = 0
    num_conflicts: int = 0


# ─── StepEvent ────────────────────────────────────────────────────────────────

@dataclass
class StepEvent:
    """
    Sự kiện một bước của thuật toán, dùng để UI animation.

    Thuật toán trả về generator của StepEvent thay vì vẽ Pygame trực tiếp.
    """
    step_index: int
    algorithm: str
    event_type: str                     # "expand" | "add_frontier" | "found" | "backtrack" | "assign" | "move" | "update" | "info"
    current_node: Optional[str] = None
    frontier: list[str] = field(default_factory=list)
    explored: list[str] = field(default_factory=list)
    path: list[str] = field(default_factory=list)
    highlighted_edges: list[tuple[str, str]] = field(default_factory=list)
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)  # Dữ liệu bổ sung tùy thuật toán

    # Thống kê tích lũy đến bước này
    nodes_expanded: int = 0
    nodes_generated: int = 0
    max_frontier_size: int = 0
    total_cost: float = 0.0


# ─── AlgorithmMetrics ─────────────────────────────────────────────────────────

@dataclass
class AlgorithmMetrics:
    """Thống kê kết quả sau khi thuật toán hoàn thành."""
    algorithm: str
    success: bool = False
    path: list[str] = field(default_factory=list)
    total_cost: float = 0.0
    nodes_expanded: int = 0
    nodes_generated: int = 0
    max_frontier_size: int = 0
    time_ms: float = 0.0
    num_steps: int = 0
    extra: dict[str, Any] = field(default_factory=dict)  # Dữ liệu đặc thù từng thuật toán


# ─── AlgorithmResult ──────────────────────────────────────────────────────────

@dataclass
class AlgorithmResult:
    """Kết quả đầy đủ trả về bởi thuật toán."""
    metrics: AlgorithmMetrics
    steps: list[StepEvent] = field(default_factory=list)
    final_state: Optional[Any] = None  # Trạng thái cuối (DefenseConfig, CSPAssignment, ...)

    @property
    def success(self) -> bool:
        return self.metrics.success
