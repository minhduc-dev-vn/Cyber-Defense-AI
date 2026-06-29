"""
graph.py — Lớp NetworkGraph quản lý đồ thị mạng máy tính.

Cung cấp: thêm/xóa node/edge, tính chi phí cạnh, tìm hàng xóm,
kiểm tra kết nối, tính heuristic.
"""
from __future__ import annotations

import math
from collections import deque
from typing import Dict, Iterator, List, Optional, Set, Tuple

from core.models import Edge, Node
from core.constants import (
    SECURITY_WEIGHT,
    DETECTION_WEIGHT,
    FIREWALL_PENALTY,
    IDS_DETECTION_PENALTY,
    MIN_EDGE_COST,
)


class NetworkGraph:
    """
    Đồ thị mạng máy tính.

    Nodes lưu trong dict theo id.
    Edges lưu trong list; adjacency list xây dựng lazy.
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, Node] = {}
        self._edges: List[Edge] = []
        # Adjacency list: node_id -> list of (neighbor_id, edge)
        self._adj: Dict[str, List[Tuple[str, Edge]]] = {}

    # ── Thêm / cập nhật ───────────────────────────────────────────────────────

    def add_node(self, node: Node) -> None:
        """Thêm hoặc cập nhật node vào đồ thị."""
        self._nodes[node.id] = node
        if node.id not in self._adj:
            self._adj[node.id] = []

    def add_edge(self, edge: Edge) -> None:
        """Thêm cạnh vào đồ thị và cập nhật adjacency list."""
        if edge.source not in self._nodes or edge.target not in self._nodes:
            raise ValueError(
                f"Edge {edge.source!r}→{edge.target!r}: một trong hai node chưa tồn tại."
            )
        self._edges.append(edge)
        self._adj.setdefault(edge.source, []).append((edge.target, edge))
        if edge.bidirectional:
            self._adj.setdefault(edge.target, []).append((edge.source, edge))

    # ── Truy vấn node/edge ────────────────────────────────────────────────────

    def get_node(self, node_id: str) -> Optional[Node]:
        """Trả về Node theo id, hoặc None nếu không tồn tại."""
        return self._nodes.get(node_id)

    def get_all_nodes(self) -> List[Node]:
        """Trả về toàn bộ node."""
        return list(self._nodes.values())

    def get_all_edges(self) -> List[Edge]:
        """Trả về toàn bộ cạnh."""
        return list(self._edges)

    def has_node(self, node_id: str) -> bool:
        return node_id in self._nodes

    def has_edge(self, source: str, target: str) -> bool:
        for src, edge in self._adj.get(source, []):
            if src == target:
                return True
        return False

    def find_nodes_by_kind(self, kind: str) -> List[Node]:
        """Tìm tất cả node theo loại (pc/server/...)."""
        return [n for n in self._nodes.values() if n.kind == kind]

    def find_first_by_kind(self, kind: str) -> Optional[Node]:
        """Tìm node đầu tiên theo loại."""
        for n in self._nodes.values():
            if n.kind == kind:
                return n
        return None

    # ── Hàng xóm và chi phí ──────────────────────────────────────────────────

    def neighbors(self, node_id: str, ignore_blocked: bool = False) -> List[str]:
        """
        Trả về danh sách id node hàng xóm từ node_id.

        ignore_blocked=True: bỏ qua cạnh/node bị blocked.
        """
        result: List[str] = []
        current_node = self._nodes.get(node_id)
        for neighbor_id, edge in self._adj.get(node_id, []):
            if ignore_blocked:
                neighbor_node = self._nodes.get(neighbor_id)
                if edge.blocked:
                    continue
                if neighbor_node and neighbor_node.blocked:
                    continue
            result.append(neighbor_id)
        return result

    def neighbors_with_cost(
        self,
        node_id: str,
        ignore_blocked: bool = True,
    ) -> List[Tuple[str, float, Edge]]:
        """
        Trả về (neighbor_id, total_edge_cost, edge) cho từng hàng xóm.

        Chi phí = base_cost + security_level × SECURITY_WEIGHT
                + detection_risk × DETECTION_WEIGHT
                + firewall_penalty nếu neighbor là Firewall
                + ids_penalty nếu neighbor là IDS
        """
        result: List[Tuple[str, float, Edge]] = []
        for neighbor_id, edge in self._adj.get(node_id, []):
            if ignore_blocked and edge.blocked:
                continue
            neighbor = self._nodes.get(neighbor_id)
            if ignore_blocked and neighbor and neighbor.blocked:
                continue
            cost = self.edge_cost(edge, neighbor)
            result.append((neighbor_id, cost, edge))
        return result

    def edge_cost(self, edge: Edge, target_node: Optional[Node]) -> float:
        """
        Tính chi phí đi qua một cạnh đến target_node.

        Công thức theo checklist:
            edge_cost = base_cost
                      + node.security_level × SECURITY_WEIGHT
                      + detection_risk × DETECTION_WEIGHT
                      + firewall_penalty (nếu đi qua Firewall)
        """
        cost = edge.base_cost
        if target_node:
            cost += target_node.security_level * SECURITY_WEIGHT
            cost += target_node.detection_risk * DETECTION_WEIGHT
            if target_node.kind == "firewall":
                cost += FIREWALL_PENALTY
            elif target_node.kind == "ids":
                cost += IDS_DETECTION_PENALTY
        return max(cost, MIN_EDGE_COST)

    def get_edge(self, source: str, target: str) -> Optional[Edge]:
        """Tìm edge giữa source và target (theo cả hai hướng nếu bidirectional)."""
        for neighbor_id, edge in self._adj.get(source, []):
            if neighbor_id == target:
                return edge
        return None

    # ── Heuristic ──────────────────────────────────────────────────────────────

    def heuristic(self, node_id: str, goal_id: str) -> float:
        """
        h(n) = shortest_hop_distance(n, goal) × minimum_edge_cost.

        Dùng BFS để tính hop count; không đi qua node/cạnh blocked.
        Đây là heuristic admissible (không bao giờ vượt quá chi phí thật).
        """
        # Tìm hop count bằng BFS (bỏ qua blocked)
        hop_count = self._bfs_hop_count(node_id, goal_id, ignore_blocked=True)
        if hop_count == float("inf"):
            return float("inf")

        # Tìm chi phí cạnh nhỏ nhất trong đồ thị
        min_edge = self._min_edge_cost()
        return hop_count * min_edge

    def _bfs_hop_count(self, start: str, goal: str, ignore_blocked: bool = True) -> float:
        """BFS tính số bước tối thiểu từ start đến goal."""
        if start == goal:
            return 0
        visited: Set[str] = {start}
        queue: deque[Tuple[str, int]] = deque([(start, 0)])
        while queue:
            current, dist = queue.popleft()
            for neighbor_id, edge in self._adj.get(current, []):
                if neighbor_id in visited:
                    continue
                neighbor = self._nodes.get(neighbor_id)
                if ignore_blocked and (edge.blocked or (neighbor and neighbor.blocked)):
                    continue
                if neighbor_id == goal:
                    return dist + 1
                visited.add(neighbor_id)
                queue.append((neighbor_id, dist + 1))
        return float("inf")

    def _min_edge_cost(self) -> float:
        """Chi phí cạnh tối thiểu trong đồ thị (dùng cho heuristic)."""
        if not self._edges:
            return MIN_EDGE_COST
        unblocked_costs = [e.base_cost for e in self._edges if not e.blocked]
        if not unblocked_costs:
            return MIN_EDGE_COST
        return min(unblocked_costs) or MIN_EDGE_COST

    # ── Kiểm tra kết nối ──────────────────────────────────────────────────────

    def has_path(self, start: str, goal: str, ignore_blocked: bool = True) -> bool:
        """Kiểm tra có đường đi từ start đến goal hay không."""
        return self._bfs_hop_count(start, goal, ignore_blocked=ignore_blocked) < float("inf")

    def all_simple_paths(
        self,
        start: str,
        goal: str,
        max_paths: int = 20,
    ) -> List[List[str]]:
        """
        Tìm tất cả đường đơn giản từ start đến goal (không qua cùng node 2 lần).
        Giới hạn max_paths để tránh bùng nổ tổ hợp.
        """
        paths: List[List[str]] = []
        stack: List[Tuple[str, List[str]]] = [(start, [start])]
        while stack and len(paths) < max_paths:
            node, path = stack.pop()
            if node == goal:
                paths.append(list(path))
                continue
            for neighbor_id, edge in self._adj.get(node, []):
                if neighbor_id not in path and not edge.blocked:
                    neighbor = self._nodes.get(neighbor_id)
                    if neighbor and not neighbor.blocked:
                        stack.append((neighbor_id, path + [neighbor_id]))
        return paths

    def count_paths_to_server(self, hacker_id: str) -> int:
        """Đếm số đường từ Hacker đến Server/Database (dùng cho đánh giá defense)."""
        goals = [n.id for n in self._nodes.values() if n.kind in ("server", "database")]
        total = 0
        for g in goals:
            total += len(self.all_simple_paths(hacker_id, g))
        return total

    # ── Thông tin đồ thị ─────────────────────────────────────────────────────

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return len(self._edges)

    def __repr__(self) -> str:
        return f"NetworkGraph(nodes={self.node_count()}, edges={self.edge_count()})"

    def summary(self) -> str:
        """Trả về chuỗi tóm tắt đồ thị."""
        lines = [f"Đồ thị: {self.node_count()} node, {self.edge_count()} cạnh"]
        for node in self._nodes.values():
            neighbors = self.neighbors(node.id)
            lines.append(f"  {node.id} ({node.kind}) → {neighbors}")
        return "\n".join(lines)
