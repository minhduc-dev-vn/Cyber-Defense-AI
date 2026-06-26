"""
renderer.py — Vẽ đồ thị mạng lên Pygame surface.

Không chứa logic thuật toán. Nhận StepEvent và trạng thái,
vẽ node/edge với màu đúng quy ước. Hỗ trợ auto scale và centering.
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
    """

    def __init__(self, surface: pygame.Surface, graph: NetworkGraph) -> None:
        self.surface = surface
        self.graph = graph
        self._last_transform = (0.0, 0.0, 1.0) # ox, oy, scale

    def draw(
        self,
        step: Optional[StepEvent],
        hacker_pos: str,
        goal_nodes: list[str],
        selected_node: Optional[str] = None,
        hovered_node: Optional[str] = None,
        rect: Optional[pygame.Rect] = None,
    ) -> None:
        """
        Vẽ toàn bộ đồ thị. Tự động scale và canh giữa dựa vào rect.
        """
        frontier: Set[str] = set(step.frontier) if step else set()
        explored: Set[str] = set(step.explored) if step else set()
        final_path: list[str] = step.path if step else []
        current: Optional[str] = step.current_node if step else None
        final_edges: Set[tuple[str, str]] = set()

        if final_path:
            for i in range(len(final_path) - 1):
                final_edges.add((final_path[i], final_path[i + 1]))
                final_edges.add((final_path[i + 1], final_path[i]))

        # Calculate bounding box and scale
        ox, oy, scale = 0.0, 0.0, 1.0
        if rect:
            nodes = self.graph.get_all_nodes()
            if nodes:
                min_x = min(n.position[0] for n in nodes)
                max_x = max(n.position[0] for n in nodes)
                min_y = min(n.position[1] for n in nodes)
                max_y = max(n.position[1] for n in nodes)
                
                gw = max_x - min_x
                gh = max_y - min_y
                if gw == 0: gw = 1
                if gh == 0: gh = 1
                
                pad_x, pad_y = 50, 50
                scale_x = (rect.width - 2 * pad_x) / gw
                scale_y = (rect.height - 2 * pad_y) / gh
                scale = min(scale_x, scale_y)
                # Giới hạn scale không quá to
                scale = min(scale, 2.5)
                
                scaled_gw = gw * scale
                scaled_gh = gh * scale
                
                ox = rect.x + (rect.width - scaled_gw) / 2 - min_x * scale
                oy = rect.y + (rect.height - scaled_gh) / 2 - min_y * scale
        
        self._last_transform = (ox, oy, scale)
        r = max(10, int(NODE_RADIUS * min(scale, 1.2)))
        e_w = max(2, int(EDGE_WIDTH * min(scale, 1.2)))

        # ── Vẽ edges trước (dưới nodes) ─────────────────────────────────────
        for edge in self.graph.get_all_edges():
            n_src = self.graph.get_node(edge.source)
            n_dst = self.graph.get_node(edge.target)
            if not n_src or not n_dst:
                continue

            sx, sy = n_src.position[0] * scale + ox, n_src.position[1] * scale + oy
            dx, dy = n_dst.position[0] * scale + ox, n_dst.position[1] * scale + oy

            # Màu cạnh
            if edge.blocked:
                color = COLOR_EDGE_BLOCKED
                width = e_w
            elif (edge.source, edge.target) in final_edges or (edge.target, edge.source) in final_edges:
                color = COLOR_EDGE_FINAL
                width = e_w + 2
            else:
                color = COLOR_EDGE_DEFAULT
                width = e_w

            pygame.draw.line(self.surface, color, (sx, sy), (dx, dy), width)

            # Label chi phí cạnh
            mid_x, mid_y = (sx + dx) / 2, (sy + dy) / 2
            cost_label = f"{edge.base_cost:.0f}"
            font_small = get_font(10)
            cost_surf = font_small.render(cost_label, True, COLOR_TEXT_SECONDARY)
            self.surface.blit(cost_surf, (mid_x + 3, mid_y - 8))

        # ── Vẽ nodes ────────────────────────────────────────────────────────
        for node in self.graph.get_all_nodes():
            nx, ny = node.position[0] * scale + ox, node.position[1] * scale + oy

            # Xác định trạng thái của node
            if node.blocked:
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

            # Override màu cho goal nodes
            if node.kind in ("server", "database"):
                base_color = get_node_color(node.kind, "default")
            else:
                base_color = get_node_color(node.kind, state)

            if node.id in goal_nodes:
                base_color = get_node_color(node.kind, "default")

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

            # Icon đặc biệt cho từng loại node
            self._draw_node_icon(node.kind, nx, ny, r)

            # Label node
            font = get_font(11, bold=(node.kind in ("server", "database")))
            label = font.render(node.id, True, COLOR_TEXT_PRIMARY)
            lw, lh = label.get_size()
            self.surface.blit(label, (nx - lw / 2, ny + r + 3))

            # Node bị chặn: vẽ dấu X
            if node.blocked:
                pygame.draw.line(self.surface, (200, 50, 50), (nx - r + 4, ny - r + 4), (nx + r - 4, ny + r - 4), 2)
                pygame.draw.line(self.surface, (200, 50, 50), (nx + r - 4, ny - r + 4), (nx - r + 4, ny + r - 4), 2)

    def _draw_node_icon(self, kind: str, cx: float, cy: float, r: int) -> None:
        """Vẽ icon nhỏ bên trong node theo loại."""
        f_size = max(8, int(r * 0.5))
        font_icon = get_font(f_size, bold=True)
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
        self.surface.blit(surf, (cx - tw / 2, cy - th / 2))

    def get_node_at(self, x: int, y: int, rect: Optional[pygame.Rect] = None) -> Optional[str]:
        """Trả về id node dưới điểm (x, y), hoặc None."""
        ox, oy, scale = self._last_transform
        # Tính node_radius đã scale
        r = max(10, int(NODE_RADIUS * min(scale, 1.2)))
        for node in self.graph.get_all_nodes():
            nx, ny = node.position[0] * scale + ox, node.position[1] * scale + oy
            dist = math.hypot(x - nx, y - ny)
            if dist <= r + 4:
                return node.id
        return None

