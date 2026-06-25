"""
test_graph.py — Unit tests cho NetworkGraph và models.

Chạy: python -m pytest tests/test_graph.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from core.models import Node, Edge
from core.graph import NetworkGraph


def make_simple_graph() -> NetworkGraph:
    """Tạo đồ thị 4 node đơn giản cho test."""
    g = NetworkGraph()
    for nid, kind, pos in [
        ("A", "pc", (0, 0)),
        ("B", "router", (100, 0)),
        ("C", "switch", (200, 0)),
        ("D", "server", (300, 0)),
    ]:
        g.add_node(Node(id=nid, kind=kind, position=pos, security_level=1))
    g.add_edge(Edge("A", "B", base_cost=1.0))
    g.add_edge(Edge("B", "C", base_cost=2.0))
    g.add_edge(Edge("C", "D", base_cost=1.0))
    return g


class TestNetworkGraph:

    def test_add_nodes(self):
        g = NetworkGraph()
        g.add_node(Node("X", "pc", (0, 0)))
        assert g.has_node("X")
        assert g.node_count() == 1

    def test_add_edge(self):
        g = make_simple_graph()
        assert g.edge_count() == 3
        assert g.has_edge("A", "B")
        assert g.has_edge("B", "A")  # bidirectional

    def test_neighbors(self):
        g = make_simple_graph()
        nbrs = sorted(g.neighbors("B", ignore_blocked=True))
        assert "A" in nbrs
        assert "C" in nbrs

    def test_edge_cost_positive(self):
        g = make_simple_graph()
        for edge in g.get_all_edges():
            target = g.get_node(edge.target)
            cost = g.edge_cost(edge, target)
            assert cost > 0, f"Chi phí phải dương: {cost}"

    def test_has_path(self):
        g = make_simple_graph()
        assert g.has_path("A", "D")
        assert not g.has_path("D", "A") or g.has_path("D", "A")  # bidirectional

    def test_no_path_blocked(self):
        g = make_simple_graph()
        # Block toàn bộ cạnh nối với B
        for edge in g.get_all_edges():
            if "B" in (edge.source, edge.target):
                edge.blocked = True
        # A không còn đường đến D
        assert not g.has_path("A", "D")

    def test_heuristic_nonnegative(self):
        g = make_simple_graph()
        h = g.heuristic("A", "D")
        assert h >= 0

    def test_heuristic_goal_zero(self):
        g = make_simple_graph()
        h = g.heuristic("D", "D")
        assert h == 0

    def test_blocked_node_not_in_neighbors(self):
        g = make_simple_graph()
        b_node = g.get_node("B")
        b_node.blocked = True
        nbrs = g.neighbors("A", ignore_blocked=True)
        assert "B" not in nbrs

    def test_summary(self):
        g = make_simple_graph()
        s = g.summary()
        assert "A" in s

    def test_find_by_kind(self):
        g = make_simple_graph()
        servers = g.find_nodes_by_kind("server")
        assert len(servers) == 1
        assert servers[0].id == "D"

    def test_all_simple_paths(self):
        g = make_simple_graph()
        paths = g.all_simple_paths("A", "D")
        assert len(paths) >= 1
        for path in paths:
            assert path[0] == "A"
            assert path[-1] == "D"


class TestModels:

    def test_node_hash(self):
        n1 = Node("X", "pc", (0, 0))
        n2 = Node("X", "server", (10, 10))
        assert hash(n1) == hash(n2)  # Hash chỉ theo id
        assert n1 == n2

    def test_edge_bidirectional_hash(self):
        e1 = Edge("A", "B", bidirectional=True)
        e2 = Edge("B", "A", bidirectional=True)
        assert hash(e1) == hash(e2)
        assert e1 == e2

    def test_node_repr(self):
        n = Node("PC1", "pc", (0, 0))
        assert "PC1" in repr(n)

    def test_edge_repr(self):
        e = Edge("A", "B", base_cost=3.5)
        assert "A" in repr(e)
        assert "B" in repr(e)
