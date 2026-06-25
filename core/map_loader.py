"""
map_loader.py — Đọc file JSON map và tạo NetworkGraph.

Định dạng JSON map:
{
  "name": "...",
  "description": "...",
  "hacker_start": "PC1",
  "goal_nodes": ["Server"],
  "nodes": [
    {
      "id": "PC1", "kind": "pc",
      "position": [100, 200],
      "security_level": 2,
      "zone": "User Zone",
      "blocked": false, "visible": true,
      "compromised": false, "monitored": false,
      "importance": 3, "detection_risk": 0.1
    }, ...
  ],
  "edges": [
    {"source": "PC1", "target": "Router", "base_cost": 1.0, "blocked": false, "bidirectional": true},
    ...
  ],
  "metadata": { ... }
}
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from core.models import Node, Edge
from core.graph import NetworkGraph


class MapLoadError(Exception):
    """Ngoại lệ khi đọc file map JSON thất bại."""


class MapData:
    """Dữ liệu đã tải từ file JSON map."""

    def __init__(
        self,
        graph: NetworkGraph,
        hacker_start: str,
        goal_nodes: list[str],
        name: str = "",
        description: str = "",
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        self.graph = graph
        self.hacker_start = hacker_start
        self.goal_nodes = goal_nodes
        self.name = name
        self.description = description
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return (
            f"MapData({self.name!r}, "
            f"start={self.hacker_start!r}, "
            f"goals={self.goal_nodes}, "
            f"{self.graph})"
        )


def load_map(path: str | Path) -> MapData:
    """
    Đọc file JSON map và trả về MapData.

    Raises MapLoadError nếu file không hợp lệ.
    """
    path = Path(path)
    if not path.exists():
        raise MapLoadError(f"Không tìm thấy file map: {path}")

    with path.open(encoding="utf-8") as f:
        try:
            raw: Dict[str, Any] = json.load(f)
        except json.JSONDecodeError as e:
            raise MapLoadError(f"JSON không hợp lệ: {e}") from e

    graph = NetworkGraph()

    # ── Đọc nodes ────────────────────────────────────────────────────────────
    nodes_raw = raw.get("nodes", [])
    if not nodes_raw:
        raise MapLoadError("Map không có nodes.")

    for node_data in nodes_raw:
        try:
            pos = node_data["position"]
            node = Node(
                id=node_data["id"],
                kind=node_data.get("kind", "pc"),
                position=(int(pos[0]), int(pos[1])),
                security_level=int(node_data.get("security_level", 5)),
                zone=node_data.get("zone"),
                blocked=bool(node_data.get("blocked", False)),
                visible=bool(node_data.get("visible", True)),
                compromised=bool(node_data.get("compromised", False)),
                monitored=bool(node_data.get("monitored", False)),
                importance=int(node_data.get("importance", 5)),
                detection_risk=float(node_data.get("detection_risk", 0.0)),
            )
            graph.add_node(node)
        except (KeyError, TypeError, ValueError) as e:
            raise MapLoadError(f"Node không hợp lệ {node_data}: {e}") from e

    # ── Đọc edges ────────────────────────────────────────────────────────────
    for edge_data in raw.get("edges", []):
        try:
            edge = Edge(
                source=edge_data["source"],
                target=edge_data["target"],
                base_cost=float(edge_data.get("base_cost", 1.0)),
                blocked=bool(edge_data.get("blocked", False)),
                bidirectional=bool(edge_data.get("bidirectional", True)),
            )
            graph.add_edge(edge)
        except (KeyError, TypeError, ValueError) as e:
            raise MapLoadError(f"Edge không hợp lệ {edge_data}: {e}") from e

    hacker_start = raw.get("hacker_start", "")
    if not hacker_start or not graph.has_node(hacker_start):
        raise MapLoadError(f"hacker_start={hacker_start!r} không hợp lệ.")

    goal_nodes: list[str] = raw.get("goal_nodes", [])
    if not goal_nodes:
        # Tự suy ra từ node kind
        goal_nodes = [
            n.id for n in graph.get_all_nodes() if n.kind in ("server", "database")
        ]
    if not goal_nodes:
        raise MapLoadError("Map không có goal_nodes và không có node server/database.")

    return MapData(
        graph=graph,
        hacker_start=hacker_start,
        goal_nodes=goal_nodes,
        name=raw.get("name", path.stem),
        description=raw.get("description", ""),
        metadata=raw.get("metadata", {}),
    )


def get_maps_dir() -> Path:
    """Trả về đường dẫn thư mục maps/ của project."""
    return Path(__file__).parent.parent / "maps"


def list_available_maps() -> list[Tuple[str, Path]]:
    """Trả về danh sách (tên, path) của tất cả map JSON."""
    maps_dir = get_maps_dir()
    result = []
    for p in sorted(maps_dir.glob("*.json")):
        result.append((p.stem, p))
    return result
