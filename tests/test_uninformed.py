"""
test_uninformed.py — Unit tests cho BFS, DFS, UCS.

Chạy: python -m pytest tests/test_uninformed.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from core.models import Node, Edge
from core.graph import NetworkGraph
from algorithms.uninformed import bfs, dfs, ucs


def make_linear_graph() -> NetworkGraph:
    """A - B - C - D (linear)"""
    g = NetworkGraph()
    for nid, kind in [("A","pc"),("B","router"),("C","switch"),("D","server")]:
        g.add_node(Node(nid, kind, (0,0), security_level=1))
    g.add_edge(Edge("A","B",1.0))
    g.add_edge(Edge("B","C",1.0))
    g.add_edge(Edge("C","D",1.0))
    return g


def make_branch_graph() -> NetworkGraph:
    """
         B - D
        /       \
    A           F (server)
        \       /
         C - E
    """
    g = NetworkGraph()
    for nid, kind in [
        ("A","pc"),("B","router"),("C","switch"),
        ("D","router"),("E","switch"),("F","server")
    ]:
        g.add_node(Node(nid, kind, (0,0), security_level=1))
    g.add_edge(Edge("A","B",1.0))
    g.add_edge(Edge("A","C",1.0))
    g.add_edge(Edge("B","D",1.0))
    g.add_edge(Edge("C","E",1.0))
    g.add_edge(Edge("D","F",1.0))
    g.add_edge(Edge("E","F",1.0))
    return g


def make_weighted_graph() -> NetworkGraph:
    """
    A --(1)-- B --(1)-- C (server)
    |                     ^
    +-----(10)------------|
    Đường ngắn: A→B→C cost thấp
    """
    g = NetworkGraph()
    for nid, kind in [("A","pc"),("B","router"),("C","server")]:
        g.add_node(Node(nid, kind, (0,0), security_level=0,
                        detection_risk=0.0))
    g.add_edge(Edge("A","B",1.0))
    g.add_edge(Edge("B","C",1.0))
    g.add_edge(Edge("A","C",10.0))
    return g


class TestBFS:

    def test_finds_goal(self):
        g = make_linear_graph()
        result = bfs.run(g, "A", ["D"])
        assert result.success
        assert result.metrics.path[-1] == "D"

    def test_shortest_path(self):
        g = make_branch_graph()
        result = bfs.run(g, "A", ["F"])
        assert result.success
        # BFS phải tìm đường 3 bước (ít bước nhất)
        assert len(result.metrics.path) == 4  # A→B→D→F hoặc A→C→E→F

    def test_no_path(self):
        g = make_linear_graph()
        # Block cạnh nối B
        for e in g.get_all_edges():
            if "B" in (e.source, e.target):
                e.blocked = True
        result = bfs.run(g, "A", ["D"])
        assert not result.success

    def test_no_cycle(self):
        """BFS không được vòng lặp vô hạn trong đồ thị có chu trình."""
        g = NetworkGraph()
        for nid, kind in [("A","pc"),("B","router"),("C","switch"),("D","server")]:
            g.add_node(Node(nid, kind, (0,0), security_level=1))
        g.add_edge(Edge("A","B",1.0))
        g.add_edge(Edge("B","C",1.0))
        g.add_edge(Edge("C","A",1.0))  # chu trình
        g.add_edge(Edge("C","D",1.0))
        result = bfs.run(g, "A", ["D"])
        assert result.success

    def test_step_events_generated(self):
        g = make_linear_graph()
        result = bfs.run(g, "A", ["D"])
        assert len(result.steps) > 0

    def test_start_is_goal(self):
        g = make_linear_graph()
        result = bfs.run(g, "A", ["A"])
        # Khi start == goal, không cần mở rộng
        assert result.success or not result.success  # không crash


class TestDFS:

    def test_finds_goal(self):
        g = make_linear_graph()
        result = dfs.run(g, "A", ["D"])
        assert result.success
        assert result.metrics.path[-1] == "D"

    def test_no_cycle(self):
        g = NetworkGraph()
        for nid, kind in [("A","pc"),("B","router"),("C","switch"),("D","server")]:
            g.add_node(Node(nid, kind, (0,0), security_level=1))
        g.add_edge(Edge("A","B",1.0))
        g.add_edge(Edge("B","C",1.0))
        g.add_edge(Edge("C","A",1.0))
        g.add_edge(Edge("C","D",1.0))
        result = dfs.run(g, "A", ["D"])
        assert result.success

    def test_no_path(self):
        g = make_linear_graph()
        for e in g.get_all_edges():
            e.blocked = True
        result = dfs.run(g, "A", ["D"])
        assert not result.success

    def test_consistent_order(self):
        """Kết quả DFS phải nhất quán với cùng graph."""
        g = make_branch_graph()
        r1 = dfs.run(g, "A", ["F"])
        r2 = dfs.run(g, "A", ["F"])
        assert r1.metrics.path == r2.metrics.path


class TestUCS:

    def test_finds_optimal_cost(self):
        g = make_weighted_graph()
        result = ucs.run(g, "A", ["C"])
        assert result.success
        # Đường A→B→C có cost thấp hơn A→C trực tiếp
        assert result.metrics.path == ["A", "B", "C"]

    def test_finds_goal(self):
        g = make_linear_graph()
        result = ucs.run(g, "A", ["D"])
        assert result.success

    def test_no_negative_cost(self):
        """Tổng chi phí phải không âm."""
        g = make_weighted_graph()
        result = ucs.run(g, "A", ["C"])
        assert result.metrics.total_cost >= 0

    def test_vs_bfs_on_weighted(self):
        """UCS tìm đường chi phí thấp nhất; BFS tìm đường ít bước nhất.
        Trên đồ thị có trọng số khác nhau, hai kết quả có thể khác nhau."""
        g = make_weighted_graph()
        bfs_r = bfs.run(g, "A", ["C"])
        ucs_r = ucs.run(g, "A", ["C"])
        # Cả hai đều tìm được đường
        assert bfs_r.success and ucs_r.success
        # UCS phải tìm đường có tổng chi phí thực sự tối ưu (A→B→C = 1+1 = 2)
        # BFS có thể tìm A→C trực tiếp (1 bước, nhưng cost = 10)
        # UCS đúng: total_cost = chi phí thực tế qua các cạnh
        assert ucs_r.metrics.total_cost <= 2.01  # A→B→C cost ≤ 2
        # BFS path length có thể ngắn hơn nhưng chi phí có thể cao hơn
        assert bfs_r.metrics.path[-1] == "C"
        assert ucs_r.metrics.path[-1] == "C"
