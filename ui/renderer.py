"""
renderer.py — Vẽ đồ thị mạng lên Pygame surface.

Không chứa logic thuật toán. Nhận StepEvent và trạng thái,
vẽ node/edge với màu đúng quy ước.
"""
from __future__ import annotations

import math
from typing import Optional, Set

import pygame

from core.constants import (
    NODE_RADIUS,
    EDGE_WIDTH,
    CSP_ZONE_COLORS,
)
from core.graph import NetworkGraph
from core.models import StepEvent
from ui.theme import (
    get_font,
    get_node_color,
    COLOR_EDGE_DEFAULT,
    COLOR_EDGE_FINAL,
    COLOR_EDGE_BLOCKED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_PANEL_BORDER,
    COLOR_NODE_HACKER,
    COLOR_FINAL_PATH,
    COLOR_FRONTIER,
    COLOR_CURRENT,
    COLOR_EXPLORED,
    COLOR_BLOCKED,
)


class GraphRenderer:
    """
    Vẽ đồ thị mạng lên surface.

    Cách dùng:
        renderer = GraphRenderer(surface, graph)
        renderer.draw(step_event, hacker_pos, goal_nodes)
    """

    def __init__(self, surface: pygame.Surface, graph: NetworkGraph) -> None:
        self.surface = surface
        self.graph = graph

    def draw(
        self,
        step: Optional[StepEvent],
        hacker_pos: str,
        goal_nodes: list[str],
        selected_node: Optional[str] = None,
        hovered_node: Optional[str] = None,
        offset: tuple[int, int] = (0, 0),
    ) -> None:
        """
        Vẽ toàn bộ đồ thị dựa trên bước thuật toán hiện tại.

        step=None: vẽ trạng thái ban đầu (không có animation).
        """
        frontier: Set[str] = set(step.frontier) if step else set()
        explored: Set[str] = set(step.explored) if step else set()
        final_path: list[str] = step.path if step else []
        current: Optional[str] = step.current_node if step else None
        final_edges: Set[tuple[str, str]] = set()
        assignments = step.data.get("assignments", {}) if step else {}
        defense_config = step.data.get("defense_config") if step else None
        firewall_nodes = set(getattr(defense_config, "firewall_nodes", []))
        ids_nodes = set(getattr(defense_config, "ids_nodes", []))
        upgraded_nodes = set(getattr(defense_config, "upgraded_nodes", []))
        virtual_blocked_nodes = set(step.data.get("blocked_nodes", [])) if step else set()
        hidden_nodes = set(step.data.get("hidden_nodes", [])) if step else set()
        teacher_view = bool(step.data.get("teacher_view", False)) if step else False

        # Tập edge thuộc final path
        if final_path:
            for i in range(len(final_path) - 1):
                final_edges.add((final_path[i], final_path[i + 1]))
                final_edges.add((final_path[i + 1], final_path[i]))

        ox, oy = offset

        # ── Vẽ edges trước (dưới nodes) ─────────────────────────────────────
        for edge in self.graph.get_all_edges():
            n_src = self.graph.get_node(edge.source)
            n_dst = self.graph.get_node(edge.target)
            if not n_src or not n_dst:
                continue

            sx, sy = n_src.position[0] + ox, n_src.position[1] + oy
            dx, dy = n_dst.position[0] + ox, n_dst.position[1] + oy

            # Màu cạnh
            if edge.blocked:
                color = COLOR_EDGE_BLOCKED
                width = EDGE_WIDTH
            elif (edge.source, edge.target) in final_edges or (edge.target, edge.source) in final_edges:
                color = COLOR_EDGE_FINAL
                width = EDGE_WIDTH + 2
            else:
                color = COLOR_EDGE_DEFAULT
                width = EDGE_WIDTH

            pygame.draw.line(self.surface, color, (sx, sy), (dx, dy), width)

            # Label chi phí cạnh
            mid_x, mid_y = (sx + dx) // 2, (sy + dy) // 2
            cost_label = f"{edge.base_cost:.0f}"
            font_small = get_font(10)
            cost_surf = font_small.render(cost_label, True, COLOR_TEXT_SECONDARY)
            self.surface.blit(cost_surf, (mid_x + 3, mid_y - 8))

        # ── Vẽ nodes ────────────────────────────────────────────────────────
        for node in self.graph.get_all_nodes():
            nx, ny = node.position[0] + ox, node.position[1] + oy
            r = NODE_RADIUS

            # Xác định trạng thái của node
            if node.blocked or node.id in virtual_blocked_nodes:
                state = "blocked"
            elif node.id == current:
                state = "current"
            elif node.id in final_path and final_path:
                state = "final"
            elif node.id in explored:
                state = "explored"
            elif node.id in frontier:
                state = "frontier"
            elif node.id == hacker_pos:
                state = "hacker"
            else:
                state = "default"

            if node.kind in ("server", "database"):
                base_color = get_node_color(node.kind, "default")
            else:
                base_color = get_node_color(node.kind, state)

            if node.id in goal_nodes:
                base_color = get_node_color(node.kind, "default")
            if node.id in assignments:
                base_color = CSP_ZONE_COLORS.get(assignments[node.id], base_color)

            # Vẽ viền (highlight node đang chọn hoặc hover)
            if node.id == selected_node:
                pygame.draw.circle(self.surface, (255, 255, 255), (nx, ny), r + 5, 3)
            elif node.id == hovered_node:
                pygame.draw.circle(self.surface, (200, 200, 200), (nx, ny), r + 3, 2)

            # Vẽ node chính
            pygame.draw.circle(self.surface, base_color, (nx, ny), r)

            # Viền trạng thái đặc biệt
            if state == "current":
                pygame.draw.circle(self.surface, (255, 255, 100), (nx, ny), r, 3)
            elif state == "frontier":
                pygame.draw.circle(self.surface, (255, 165, 0), (nx, ny), r, 2)
            elif state == "final":
                pygame.draw.circle(self.surface, COLOR_FINAL_PATH, (nx, ny), r, 3)
            elif node.id == hacker_pos:
                pygame.draw.circle(self.surface, COLOR_NODE_HACKER, (nx, ny), r, 3)
            else:
                pygame.draw.circle(self.surface, COLOR_PANEL_BORDER, (nx, ny), r, 1)

            if node.id in firewall_nodes:
                pygame.draw.circle(self.surface, (255, 145, 45), (nx, ny), r + 5, 3)
            if node.id in ids_nodes:
                pygame.draw.circle(self.surface, (255, 220, 70), (nx, ny), r + 9, 2)
            if node.id in upgraded_nodes:
                pygame.draw.circle(self.surface, (80, 220, 220), (nx, ny), r - 6, 3)

            # Icon đặc biệt cho từng loại node
            self._draw_node_icon(node.kind, nx, ny, r)

            # Label node
            font = get_font(11, bold=(node.kind in ("server", "database")))
            label = font.render(node.id, True, COLOR_TEXT_PRIMARY)
            lw, lh = label.get_size()
            self.surface.blit(label, (nx - lw // 2, ny + r + 3))

            # Node bị chặn: vẽ dấu X
            if node.blocked or node.id in virtual_blocked_nodes:
                pygame.draw.line(self.surface, (200, 50, 50), (nx - 10, ny - 10), (nx + 10, ny + 10), 2)
                pygame.draw.line(self.surface, (200, 50, 50), (nx + 10, ny - 10), (nx - 10, ny + 10), 2)

            if node.id in assignments:
                zone_font = get_font(9)
                zone = str(assignments[node.id]).replace(" Zone", "")
                zone_surf = zone_font.render(zone[:10], True, COLOR_TEXT_SECONDARY)
                zw, _ = zone_surf.get_size()
                self.surface.blit(zone_surf, (nx - zw // 2, ny + r + 16))

            if node.id in hidden_nodes and not teacher_view:
                fog = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
                fog.fill((8, 10, 18, 185))
                self.surface.blit(fog, (nx - r - 4, ny - r - 4))
                q_font = get_font(18, bold=True)
                q_surf = q_font.render("?", True, (230, 235, 250))
                qw, qh = q_surf.get_size()
                self.surface.blit(q_surf, (nx - qw // 2, ny - qh // 2))

    def _draw_node_icon(self, kind: str, cx: int, cy: int, r: int) -> None:
        """Vẽ icon nhỏ bên trong node theo loại."""
        font_icon = get_font(12, bold=True)
        icons = {
            "pc": "PC",
            "router": "RT",
            "switch": "SW",
            "firewall": "FW",
            "ids": "IDS",
            "server": "SRV",
            "database": "DB",
        }
        text = icons.get(kind, "?")
        surf = font_icon.render(text, True, (230, 240, 255))
        tw, th = surf.get_size()
        self.surface.blit(surf, (cx - tw // 2, cy - th // 2))

    def get_node_at(self, x: int, y: int, offset: tuple[int, int] = (0, 0)) -> Optional[str]:
        """Trả về id node dưới điểm (x, y), hoặc None."""
        ox, oy = offset
        for node in self.graph.get_all_nodes():
            nx, ny = node.position[0] + ox, node.position[1] + oy
            dist = math.hypot(x - nx, y - ny)
            if dist <= NODE_RADIUS + 4:
                return node.id
        return None
