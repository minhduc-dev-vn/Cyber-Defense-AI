"""
test_informed.py - Unit tests for Greedy, A*, and IDA*.

Run: python -m pytest tests/test_informed.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from algorithms.informed import astar, greedy_search, idastar
from core.graph import NetworkGraph
from core.models import Edge, Node


def make_weighted_choice_graph() -> NetworkGraph:
    """
    A --(10)-- D(server)
    |
    (1)
    B --(1)-- C --(1)-- D

    Greedy can choose D directly because h(D)=0. A*/IDA* should choose cost=3.
    """
    graph = NetworkGraph()
    for node_id, kind in [
        ("A", "pc"),
        ("B", "router"),
        ("C", "switch"),
        ("D", "server"),
    ]:
        graph.add_node(
            Node(node_id, kind, (0, 0), security_level=0, detection_risk=0.0)
        )
    graph.add_edge(Edge("A", "D", 10.0))
    graph.add_edge(Edge("A", "B", 1.0))
    graph.add_edge(Edge("B", "C", 1.0))
    graph.add_edge(Edge("C", "D", 1.0))
    return graph


def make_no_path_graph() -> NetworkGraph:
    graph = make_weighted_choice_graph()
    for edge in graph.get_all_edges():
        edge.blocked = True
    return graph


class TestGreedy:

    def test_finds_goal(self):
        graph = make_weighted_choice_graph()
        result = greedy_search.run(graph, "A", ["D"])
        assert result.success
        assert result.metrics.path[-1] == "D"

    def test_can_be_non_optimal_on_weighted_graph(self):
        graph = make_weighted_choice_graph()
        greedy_result = greedy_search.run(graph, "A", ["D"])
        astar_result = astar.run(graph, "A", ["D"])
        assert greedy_result.success and astar_result.success
        assert greedy_result.metrics.total_cost >= astar_result.metrics.total_cost

    def test_step_events_include_heuristic(self):
        graph = make_weighted_choice_graph()
        result = greedy_search.run(graph, "A", ["D"])
        assert any("h" in step.data for step in result.steps)


class TestAStar:

    def test_finds_optimal_cost_path(self):
        graph = make_weighted_choice_graph()
        result = astar.run(graph, "A", ["D"])
        assert result.success
        assert result.metrics.path == ["A", "B", "C", "D"]
        assert result.metrics.total_cost == 3.0

    def test_step_events_include_g_h_f(self):
        graph = make_weighted_choice_graph()
        result = astar.run(graph, "A", ["D"])
        assert any({"g", "h", "f"}.issubset(step.data) for step in result.steps)

    def test_no_path_returns_failure(self):
        graph = make_no_path_graph()
        result = astar.run(graph, "A", ["D"])
        assert not result.success


class TestIDAStar:

    def test_finds_same_optimal_path_as_astar(self):
        graph = make_weighted_choice_graph()
        ida_result = idastar.run(graph, "A", ["D"])
        astar_result = astar.run(graph, "A", ["D"])
        assert ida_result.success
        assert ida_result.metrics.path == astar_result.metrics.path
        assert ida_result.metrics.total_cost == astar_result.metrics.total_cost

    def test_threshold_updates_are_logged(self):
        graph = make_weighted_choice_graph()
        result = idastar.run(graph, "A", ["D"])
        updates = [step for step in result.steps if step.event_type == "update"]
        assert updates
        assert all("threshold" in step.data for step in updates)

    def test_start_is_goal(self):
        graph = make_weighted_choice_graph()
        result = idastar.run(graph, "A", ["A"])
        assert result.success
        assert result.metrics.path == ["A"]
        assert result.metrics.total_cost == 0.0
