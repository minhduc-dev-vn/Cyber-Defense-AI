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
        self._scale = 1.0
        self._tx = 0.0
        self._ty = 0.0

    def configure_viewport(self, rect: pygame.Rect, padding: int = 72) -> None:
        nodes = self.graph.get_all_nodes()
        if not nodes:
            self._scale = 1.0
            self._tx = rect.x
            self._ty = rect.y
            return
        min_x = min(node.position[0] for node in nodes)
        max_x = max(node.position[0] for node in nodes)
        min_y = min(node.position[1] for node in nodes)
        max_y = max(node.position[1] for node in nodes)
        span_x = max(1, max_x - min_x)
        span_y = max(1, max_y - min_y)
        scale = min((rect.width - padding * 2) / span_x, (rect.height - padding * 2) / span_y)
        self._scale = max(0.72, min(scale, 1.12))
        graph_w = span_x * self._scale
        graph_h = span_y * self._scale
        self._tx = rect.x + (rect.width - graph_w) / 2 - min_x * self._scale
        self._ty = rect.y + (rect.height - graph_h) / 2 - min_y * self._scale + 10

    def _node_pos(self, node) -> tuple[int, int]:
        return int(node.position[0] * self._scale + self._tx), int(node.position[1] * self._scale + self._ty)

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

            sx, sy = self._node_pos(n_src)
            dx, dy = self._node_pos(n_dst)

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

            pygame.draw.line(self.surface, (2, 8, 15), (sx, sy), (dx, dy), width + 4)
            if width > EDGE_WIDTH:
                pygame.draw.line(self.surface, color, (sx, sy), (dx, dy), width + 3)
                pygame.draw.line(self.surface, (255, 206, 122), (sx, sy), (dx, dy), 2)
            else:
                pygame.draw.line(self.surface, (82, 101, 122), (sx, sy), (dx, dy), width + 2)
                pygame.draw.line(self.surface, color, (sx, sy), (dx, dy), width)

            # Label chi phí cạnh
            mid_x, mid_y = (sx + dx) // 2, (sy + dy) // 2
            cost_label = f"{edge.base_cost:.0f}"
            font_small = get_font(12, bold=True)
            cost_surf = font_small.render(cost_label, True, COLOR_TEXT_PRIMARY)
            shadow_surf = font_small.render(cost_label, True, (3, 8, 14))
            center = (mid_x + 3, mid_y - 8)
            self.surface.blit(shadow_surf, shadow_surf.get_rect(center=(center[0] + 1, center[1] + 1)))
            self.surface.blit(cost_surf, cost_surf.get_rect(center=center))

        # ── Vẽ nodes ────────────────────────────────────────────────────────
        nodes = self.graph.get_all_nodes()
        node_positions = {node.id: self._node_pos(node) for node in nodes}
        label_mid_y = sum(pos[1] for pos in node_positions.values()) / max(1, len(node_positions))
        for node in nodes:
            nx, ny = node_positions[node.id]
            r = NODE_RADIUS + 3

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
            shadow = pygame.Surface((r * 3, r * 3), pygame.SRCALPHA)
            pygame.draw.circle(shadow, (*base_color, 55), (r + r // 2, r + r // 2), r + 10)
            self.surface.blit(shadow, (nx - r - r // 2, ny - r - r // 2))
            pygame.draw.circle(self.surface, (4, 13, 24), (nx, ny), r + 4)
            pygame.draw.circle(self.surface, base_color, (nx, ny), r)
            pygame.draw.circle(self.surface, (255, 255, 255), (nx, ny), r + 1, 1)

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

            ring_color = base_color
            if state == "current":
                ring_color = COLOR_CURRENT
            elif state == "frontier":
                ring_color = COLOR_FRONTIER
            elif state == "final":
                ring_color = COLOR_FINAL_PATH
            elif state == "blocked":
                ring_color = COLOR_BLOCKED
            elif state == "explored":
                ring_color = COLOR_EXPLORED

            self._draw_node_shell(
                nx,
                ny,
                r,
                ring_color,
                hacker=node.id == hacker_pos,
                selected=node.id == selected_node,
                hovered=node.id == hovered_node,
            )

            if node.id in firewall_nodes:
                pygame.draw.circle(self.surface, (255, 145, 45), (nx, ny), r + 5, 3)
            if node.id in ids_nodes:
                pygame.draw.circle(self.surface, (255, 220, 70), (nx, ny), r + 9, 2)
            if node.id in upgraded_nodes:
                pygame.draw.circle(self.surface, (80, 220, 220), (nx, ny), r - 6, 3)

            # Icon đặc biệt cho từng loại node
            self._draw_node_icon(node.kind, nx, ny, r, ring_color)

            # Label node
            font = get_font(12, bold=True)
            label = font.render(node.id, True, COLOR_TEXT_PRIMARY)
            lw, lh = label.get_size()
            label_y = ny - r - lh - 6 if ny <= label_mid_y else ny + r + 5
            self.surface.blit(label, (nx - lw // 2, label_y))

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

    def _draw_node_shell(
        self,
        cx: int,
        cy: int,
        r: int,
        color: tuple[int, int, int],
        *,
        hacker: bool = False,
        selected: bool = False,
        hovered: bool = False,
    ) -> None:
        """Draw the cyber-map node shell: glow, dark core and bright ring."""
        glow_size = (r + 18) * 2
        glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        center = (glow_size // 2, glow_size // 2)
        for radius, alpha in ((r + 15, 28), (r + 10, 42), (r + 5, 58)):
            pygame.draw.circle(glow, (*color, alpha), center, radius)
        self.surface.blit(glow, (cx - glow_size // 2, cy - glow_size // 2))

        if hacker:
            self._draw_dashed_circle(cx, cy, r + 12, color, 2)
            self._draw_dashed_circle(cx, cy, r + 18, color, 1)

        if selected:
            pygame.draw.circle(self.surface, (250, 255, 255), (cx, cy), r + 9, 3)
        elif hovered:
            pygame.draw.circle(self.surface, (210, 232, 255), (cx, cy), r + 7, 2)

        pygame.draw.circle(self.surface, (5, 14, 25), (cx, cy), r + 5)
        pygame.draw.circle(self.surface, (13, 29, 43), (cx, cy), r)
        pygame.draw.circle(self.surface, color, (cx, cy), r + 1, 3)
        pygame.draw.circle(self.surface, (230, 244, 255), (cx, cy), r - 5, 1)

    def _draw_dashed_circle(self, cx: int, cy: int, radius: int, color: tuple[int, int, int], width: int) -> None:
        rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
        for i in range(0, 360, 28):
            pygame.draw.arc(self.surface, color, rect, math.radians(i), math.radians(i + 16), width)

    def _draw_node_icon(self, kind: str, cx: int, cy: int, r: int, color: tuple[int, int, int]) -> None:
        """Vẽ icon nhỏ bên trong node theo loại."""
        icon_color = (235, 248, 255)
        accent = color
        if kind == "pc":
            screen = pygame.Rect(cx - 12, cy - 10, 24, 16)
            pygame.draw.rect(self.surface, icon_color, screen, 3, border_radius=2)
            pygame.draw.line(self.surface, icon_color, (cx, cy + 6), (cx, cy + 13), 3)
            pygame.draw.line(self.surface, icon_color, (cx - 10, cy + 14), (cx + 10, cy + 14), 3)
        elif kind == "switch":
            body = pygame.Rect(cx - 15, cy - 8, 30, 16)
            pygame.draw.rect(self.surface, icon_color, body, 3, border_radius=3)
            for px in (-8, 0, 8):
                pygame.draw.circle(self.surface, accent, (cx + px, cy), 3)
            pygame.draw.line(self.surface, icon_color, (cx - 18, cy), (cx - 15, cy), 2)
            pygame.draw.line(self.surface, icon_color, (cx + 15, cy), (cx + 18, cy), 2)
        elif kind == "router":
            for ox, oy in ((-9, -9), (9, -9), (-9, 9), (9, 9)):
                pygame.draw.rect(self.surface, icon_color, pygame.Rect(cx + ox - 5, cy + oy - 5, 10, 10), 2, border_radius=2)
            pygame.draw.circle(self.surface, accent, (cx, cy), 4)
            pygame.draw.line(self.surface, icon_color, (cx - 4, cy), (cx - 14, cy - 9), 2)
            pygame.draw.line(self.surface, icon_color, (cx + 4, cy), (cx + 14, cy - 9), 2)
            pygame.draw.line(self.surface, icon_color, (cx - 4, cy), (cx - 14, cy + 9), 2)
            pygame.draw.line(self.surface, icon_color, (cx + 4, cy), (cx + 14, cy + 9), 2)
        elif kind == "firewall":
            shield = [
                (cx, cy - 16),
                (cx + 13, cy - 10),
                (cx + 10, cy + 9),
                (cx, cy + 17),
                (cx - 10, cy + 9),
                (cx - 13, cy - 10),
            ]
            pygame.draw.polygon(self.surface, icon_color, shield)
            pygame.draw.polygon(self.surface, accent, shield, 2)
            pygame.draw.line(self.surface, accent, (cx, cy - 8), (cx, cy + 8), 3)
        elif kind == "ids":
            pygame.draw.circle(self.surface, icon_color, (cx, cy), 14, 2)
            pygame.draw.circle(self.surface, accent, (cx, cy), 5, 2)
            pygame.draw.line(self.surface, icon_color, (cx - 10, cy + 10), (cx + 10, cy - 10), 2)
            pygame.draw.polygon(self.surface, icon_color, [(cx + 12, cy - 12), (cx + 5, cy - 10), (cx + 10, cy - 5)])
        elif kind == "server":
            for i in range(3):
                rack = pygame.Rect(cx - 14, cy - 14 + i * 10, 28, 7)
                pygame.draw.rect(self.surface, icon_color, rack, 2, border_radius=2)
                pygame.draw.circle(self.surface, accent, (cx + 8, rack.centery), 2)
        elif kind == "database":
            top = pygame.Rect(cx - 13, cy - 15, 26, 10)
            pygame.draw.ellipse(self.surface, icon_color, top, 2)
            pygame.draw.line(self.surface, icon_color, (cx - 13, cy - 10), (cx - 13, cy + 12), 2)
            pygame.draw.line(self.surface, icon_color, (cx + 13, cy - 10), (cx + 13, cy + 12), 2)
            for y in (-1, 10):
                pygame.draw.arc(self.surface, icon_color, pygame.Rect(cx - 13, cy + y - 5, 26, 10), 0, math.pi, 2)
            pygame.draw.arc(self.surface, icon_color, pygame.Rect(cx - 13, cy + 7, 26, 10), math.pi, math.tau, 2)
        else:
            q = get_font(15, bold=True).render("?", True, icon_color)
            self.surface.blit(q, q.get_rect(center=(cx, cy)))
        return

    def get_node_at(self, x: int, y: int, offset: tuple[int, int] = (0, 0)) -> Optional[str]:
        """Trả về id node dưới điểm (x, y), hoặc None."""
        ox, oy = offset
        for node in self.graph.get_all_nodes():
            nx, ny = self._node_pos(node)
            dist = math.hypot(x - nx, y - ny)
            if dist <= NODE_RADIUS + 10:
                return node.id
        if offset != (0, 0):
            for node in self.graph.get_all_nodes():
                nx, ny = node.position[0] + ox, node.position[1] + oy
                dist = math.hypot(x - nx, y - ny)
                if dist <= NODE_RADIUS + 10:
                    return node.id
        return None
