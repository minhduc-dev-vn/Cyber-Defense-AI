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
    COLOR_NODE_SERVER,
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
        self._scale = max(0.58, min(scale, 1.12))
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
        domains = step.data.get("domains", {}) if step else {}
        current_domain = step.data.get("current_domain", []) if step else []
        attempted_value = step.data.get("attempted_value") if step else None
        removed_domains = step.data.get("removed", {}) if step else {}
        conflicted_variables = set(step.data.get("conflicted_variables", [])) if step else set()
        defense_config = step.data.get("defense_config") if step else None
        firewall_nodes = set(getattr(defense_config, "firewall_nodes", []))
        ids_nodes = set(getattr(defense_config, "ids_nodes", []))
        upgraded_nodes = set(getattr(defense_config, "upgraded_nodes", []))
        blocked_path_samples = step.data.get("blocked_path_samples", []) if step else []
        open_path_samples = step.data.get("open_path_samples", []) if step else []
        virtual_blocked_nodes = set(step.data.get("blocked_nodes", [])) if step else set()
        virtual_blocked_edges = {
            tuple(sorted(edge))
            for edge in (step.data.get("blocked_edges", []) if step else [])
            if isinstance(edge, (list, tuple)) and len(edge) == 2
        }
        attack_edges = {
            tuple(sorted(edge))
            for edge in (step.data.get("attack_edges", []) if step else [])
            if isinstance(edge, (list, tuple)) and len(edge) == 2
        }
        defender_edges = {
            tuple(sorted(edge))
            for edge in (step.data.get("defender_edges", []) if step else [])
            if isinstance(edge, (list, tuple)) and len(edge) == 2
        }
        hidden_nodes = set(step.data.get("hidden_nodes", [])) if step else set()
        teacher_view = bool(step.data.get("teacher_view", False)) if step else False
        local_mode = step.data.get("local_search_mode") == "heuristic_path" if step else False
        heuristic_table = step.data.get("heuristic_table", {}) if step else {}
        chosen_neighbor = step.data.get("chosen_neighbor") if step else None
        belief_nodes = set(step.data.get("belief", [])) if step else set()
        observed_nodes = set(step.data.get("observed_nodes", [])) if step else set()
        ai_focus_node = step.data.get("ai_focus_node") if step else None
        if step:
            ids_nodes.update(step.data.get("ids_positions", []))
            upgraded_nodes.update(step.data.get("upgraded_nodes", []))

        # Tập edge thuộc final path
        if final_path:
            for i in range(len(final_path) - 1):
                final_edges.add((final_path[i], final_path[i + 1]))
                final_edges.add((final_path[i + 1], final_path[i]))

        csp_trial_assignments = dict(assignments) if isinstance(assignments, dict) else {}
        if current and attempted_value and isinstance(domains, dict) and current in domains:
            csp_trial_assignments[current] = str(attempted_value)
        csp_conflict_edges: Set[tuple[str, str]] = set()
        if csp_trial_assignments:
            for edge in self.graph.get_all_edges():
                left_zone = csp_trial_assignments.get(edge.source)
                right_zone = csp_trial_assignments.get(edge.target)
                if left_zone and right_zone and left_zone == right_zone:
                    csp_conflict_edges.add((edge.source, edge.target))
                    csp_conflict_edges.add((edge.target, edge.source))

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
            edge_key = tuple(sorted((edge.source, edge.target)))
            blocked_by_state = edge_key in virtual_blocked_edges
            defended_by_state = edge_key in defender_edges
            attacked_by_state = edge_key in attack_edges
            if edge.blocked or blocked_by_state:
                color = COLOR_EDGE_BLOCKED
                width = EDGE_WIDTH
            elif defended_by_state:
                color = (255, 92, 80)
                width = EDGE_WIDTH + 2
            elif (edge.source, edge.target) in csp_conflict_edges:
                color = (255, 82, 82)
                width = EDGE_WIDTH + 2
            elif attacked_by_state:
                color = COLOR_NODE_HACKER
                width = EDGE_WIDTH + 2
            elif (edge.source, edge.target) in final_edges or (edge.target, edge.source) in final_edges:
                color = COLOR_EDGE_FINAL
                width = EDGE_WIDTH + 2
            else:
                color = COLOR_EDGE_DEFAULT
                width = EDGE_WIDTH

            mid_x, mid_y = (sx + dx) // 2, (sy + dy) // 2
            pygame.draw.line(self.surface, (2, 8, 15), (sx, sy), (dx, dy), width + 4)
            if (edge.source, edge.target) in csp_conflict_edges:
                self._draw_dashed_line(self.surface, (255, 82, 82), (sx, sy), (dx, dy), width + 1, dash_len=10, gap_len=7)
                self._draw_dashed_line(self.surface, (255, 195, 195), (sx, sy), (dx, dy), 1, dash_len=10, gap_len=7)
                err_font = get_font(8, bold=True)
                err = err_font.render("LOI", True, (255, 230, 230))
                err_rect = err.get_rect(center=(mid_x, mid_y + 12))
                bg = err_rect.inflate(10, 5)
                pygame.draw.rect(self.surface, (95, 14, 22), bg, border_radius=5)
                pygame.draw.rect(self.surface, (255, 92, 80), bg, 1, border_radius=5)
                self.surface.blit(err, err_rect)
            elif blocked_by_state:
                self._draw_dashed_line(self.surface, COLOR_EDGE_BLOCKED, (sx, sy), (dx, dy), width + 2, dash_len=10, gap_len=7)
                cross_font = get_font(8, bold=True)
                cross = cross_font.render("BLOCK", True, (255, 230, 230))
                cross_rect = cross.get_rect(center=(mid_x, mid_y + 12))
                pygame.draw.rect(self.surface, (95, 14, 22), cross_rect.inflate(10, 5), border_radius=5)
                self.surface.blit(cross, cross_rect)
            elif defended_by_state:
                self._draw_dashed_line(self.surface, (255, 92, 80), (sx, sy), (dx, dy), width + 1, dash_len=12, gap_len=7)
                self._draw_edge_tag("DEF", (mid_x, mid_y + 12), (95, 14, 22), (255, 230, 230))
            elif width > EDGE_WIDTH:
                pygame.draw.line(self.surface, color, (sx, sy), (dx, dy), width + 3)
                accent = (255, 236, 180) if attacked_by_state else (255, 206, 122)
                pygame.draw.line(self.surface, accent, (sx, sy), (dx, dy), 2)
                if attacked_by_state:
                    self._draw_edge_tag("ATK", (mid_x, mid_y + 12), (91, 50, 8), (255, 240, 190))
            else:
                pygame.draw.line(self.surface, (82, 101, 122), (sx, sy), (dx, dy), width + 2)
                pygame.draw.line(self.surface, color, (sx, sy), (dx, dy), width)

            # Label chi phí cạnh
            cost_label = f"{edge.base_cost:.0f}"
            font_small = get_font(12, bold=True)
            cost_surf = font_small.render(cost_label, True, COLOR_TEXT_PRIMARY)
            shadow_surf = font_small.render(cost_label, True, (3, 8, 14))
            center = (mid_x + 3, mid_y - 8)
            self.surface.blit(shadow_surf, shadow_surf.get_rect(center=(center[0] + 1, center[1] + 1)))
            self.surface.blit(cost_surf, cost_surf.get_rect(center=center))

        if defense_config:
            for path in open_path_samples[:1]:
                self._draw_path_overlay(path, (72, 214, 112), width=3, dashed=False)
            for path in blocked_path_samples[:2]:
                self._draw_path_overlay(path, (255, 92, 80), width=4, dashed=True)

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
            elif local_mode and node.id == chosen_neighbor:
                state = "frontier"
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
                base_color = COLOR_NODE_SERVER
            if node.id in assignments:
                base_color = CSP_ZONE_COLORS.get(assignments[node.id], base_color)
            elif node.id == current and attempted_value and isinstance(domains, dict) and node.id in domains:
                base_color = CSP_ZONE_COLORS.get(str(attempted_value), base_color)

            # Vẽ viền (highlight node đang chọn hoặc hover)
            if node.id == selected_node:
                pygame.draw.circle(self.surface, (255, 255, 255), (nx, ny), r + 5, 3)
            elif node.id == hovered_node:
                pygame.draw.circle(self.surface, (200, 200, 200), (nx, ny), r + 3, 2)
            elif node.id in conflicted_variables:
                pygame.draw.circle(self.surface, (255, 82, 82), (nx, ny), r + 11, 3)

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
                pygame.draw.line(self.surface, (255, 255, 100), (nx - r - 6, ny), (nx - r - 2, ny), 2)
                pygame.draw.line(self.surface, (255, 255, 100), (nx + r + 2, ny), (nx + r + 6, ny), 2)
                pygame.draw.line(self.surface, (255, 255, 100), (nx, ny - r - 6), (nx, ny - r - 2), 2)
                pygame.draw.line(self.surface, (255, 255, 100), (nx, ny + r + 2), (nx, ny + r + 6), 2)
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

            if node.id in observed_nodes:
                self._draw_observation_indicator(nx, ny, r)

            if node.id in belief_nodes:
                self._draw_belief_indicator(nx, ny, r)

            if node.id == ai_focus_node:
                pygame.draw.circle(self.surface, (255, 92, 80), (nx, ny), r + 18, 3)
                self._draw_defense_badge(nx, ny, r, "AI", (255, 92, 80), "bottom_left")

            if node.id in firewall_nodes:
                pygame.draw.circle(self.surface, (255, 145, 45), (nx, ny), r + 5, 3)
                self._draw_defense_badge(nx, ny, r, "FW", (255, 145, 45), "top_left")
            if node.id in ids_nodes:
                pygame.draw.circle(self.surface, (255, 220, 70), (nx, ny), r + 9, 2)
                self._draw_defense_badge(nx, ny, r, "IDS", (255, 220, 70), "top_right")
            if node.id in upgraded_nodes:
                pygame.draw.circle(self.surface, (80, 220, 220), (nx, ny), r - 6, 3)
                self._draw_defense_badge(nx, ny, r, "UP", (80, 220, 220), "bottom_right")

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
                zone = str(assignments[node.id]).replace(" Zone", "")
                self._draw_zone_badge(nx, ny, r, zone, base_color, below=ny <= label_mid_y)
            elif node.id == current and attempted_value and isinstance(domains, dict) and node.id in domains:
                zone = str(attempted_value).replace(" Zone", "")
                self._draw_zone_badge(nx, ny, r, zone, base_color, below=ny <= label_mid_y)

            if local_mode and isinstance(heuristic_table, dict) and node.id in heuristic_table:
                self._draw_heuristic_badge(nx, ny, r, heuristic_table.get(node.id), below=ny > label_mid_y)

            if node.id == current and current_domain:
                self._draw_csp_domain_chips(
                    nx,
                    ny,
                    r,
                    list(current_domain),
                    str(attempted_value) if attempted_value else None,
                    below=ny <= label_mid_y,
                )
            elif isinstance(removed_domains, dict) and node.id in removed_domains:
                self._draw_csp_domain_chips(
                    nx,
                    ny,
                    r,
                    list(removed_domains.get(node.id, [])),
                    None,
                    below=ny <= label_mid_y,
                    pruned=True,
                )

            if node.id in hidden_nodes and not teacher_view:
                fog = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
                fog.fill((8, 10, 18, 185))
                self.surface.blit(fog, (nx - r - 4, ny - r - 4))
                q_font = get_font(18, bold=True)
                q_surf = q_font.render("?", True, (230, 235, 250))
                qw, qh = q_surf.get_size()
                self.surface.blit(q_surf, (nx - qw // 2, ny - qh // 2))

    def _draw_edge_tag(
        self,
        text: str,
        center: tuple[int, int],
        bg_color: tuple[int, int, int],
        text_color: tuple[int, int, int],
    ) -> None:
        font = get_font(8, bold=True)
        label = font.render(text, True, text_color)
        rect = label.get_rect(center=center).inflate(10, 5)
        pygame.draw.rect(self.surface, bg_color, rect, border_radius=5)
        pygame.draw.rect(self.surface, text_color, rect, 1, border_radius=5)
        self.surface.blit(label, label.get_rect(center=rect.center))

    def _draw_path_overlay(
        self,
        path: list[str],
        color: tuple[int, int, int],
        *,
        width: int = 3,
        dashed: bool = False,
    ) -> None:
        if len(path) < 2:
            return
        points: list[tuple[int, int]] = []
        for node_id in path:
            node = self.graph.get_node(str(node_id))
            if not node:
                return
            points.append(self._node_pos(node))
        glow = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        for start, end in zip(points, points[1:]):
            if dashed:
                self._draw_dashed_line(glow, (*color, 120), start, end, width + 5)
                self._draw_dashed_line(self.surface, color, start, end, width)
            else:
                pygame.draw.line(glow, (*color, 86), start, end, width + 6)
                pygame.draw.line(self.surface, color, start, end, width)
        self.surface.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_dashed_line(
        self,
        surface: pygame.Surface,
        color: tuple[int, ...],
        start: tuple[int, int],
        end: tuple[int, int],
        width: int,
        dash_len: int = 14,
        gap_len: int = 8,
    ) -> None:
        sx, sy = start
        ex, ey = end
        dx, dy = ex - sx, ey - sy
        length = math.hypot(dx, dy)
        if length <= 0:
            return
        ux, uy = dx / length, dy / length
        pos = 0.0
        while pos < length:
            seg_end = min(length, pos + dash_len)
            p1 = (int(sx + ux * pos), int(sy + uy * pos))
            p2 = (int(sx + ux * seg_end), int(sy + uy * seg_end))
            pygame.draw.line(surface, color, p1, p2, width)
            pos += dash_len + gap_len

    def _draw_defense_badge(
        self,
        cx: int,
        cy: int,
        r: int,
        text: str,
        color: tuple[int, int, int],
        corner: str,
    ) -> None:
        font = get_font(8, bold=True)
        label = font.render(text, True, (5, 14, 25))
        badge_w = max(24, label.get_width() + 10)
        badge_h = 16
        dx = r - 7
        dy = r - 7
        if corner == "top_left":
            center = (cx - dx, cy - dy)
        elif corner == "top_right":
            center = (cx + dx, cy - dy)
        elif corner == "bottom_left":
            center = (cx - dx, cy + dy)
        else:
            center = (cx + dx, cy + dy)
        rect = pygame.Rect(0, 0, badge_w, badge_h)
        rect.center = center
        glow = pygame.Surface((badge_w + 10, badge_h + 10), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*color, 70), glow.get_rect(), border_radius=8)
        self.surface.blit(glow, (rect.x - 5, rect.y - 5))
        pygame.draw.rect(self.surface, color, rect, border_radius=6)
        pygame.draw.rect(self.surface, (245, 252, 255), rect, 1, border_radius=6)
        self.surface.blit(label, label.get_rect(center=rect.center))

    def _draw_zone_badge(
        self,
        cx: int,
        cy: int,
        r: int,
        zone: str,
        color: tuple[int, int, int],
        *,
        below: bool,
    ) -> None:
        label_text = {
            "User": "USER",
            "DMZ": "DMZ",
            "Server": "SERVER",
            "Quarantine": "QUAR",
        }.get(zone, zone[:6].upper())
        font = get_font(7, bold=True)
        label = font.render(label_text, True, (235, 248, 255))
        badge_w = max(32, label.get_width() + 10)
        badge_h = 15
        y = cy + r + 22 if below else cy - r - badge_h - 22
        rect = pygame.Rect(cx - badge_w // 2, y, badge_w, badge_h)
        pygame.draw.rect(self.surface, (4, 13, 24), rect, border_radius=5)
        pygame.draw.rect(self.surface, color, rect, 2, border_radius=5)
        self.surface.blit(label, label.get_rect(center=rect.center))

    def _draw_heuristic_badge(self, cx: int, cy: int, r: int, value: object, *, below: bool) -> None:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            text = "h=?"
        else:
            text_value = "inf" if numeric == float("inf") else (str(int(numeric)) if numeric.is_integer() else f"{numeric:.1f}")
            text = f"h={text_value}"
        font = get_font(8, bold=True)
        label = font.render(text, True, (235, 248, 255))
        badge_w = max(34, label.get_width() + 10)
        badge_h = 16
        y = cy + r + 24 if below else cy - r - badge_h - 24
        rect = pygame.Rect(cx - badge_w // 2, y, badge_w, badge_h)
        pygame.draw.rect(self.surface, (4, 13, 24), rect, border_radius=5)
        pygame.draw.rect(self.surface, (116, 195, 255), rect, 1, border_radius=5)
        self.surface.blit(label, label.get_rect(center=rect.center))

    def _draw_csp_domain_chips(
        self,
        cx: int,
        cy: int,
        r: int,
        domain: list[str],
        attempted: Optional[str],
        *,
        below: bool,
        pruned: bool = False,
    ) -> None:
        if not domain:
            return
        labels = {
            "User Zone": "U",
            "DMZ": "D",
            "Server Zone": "S",
            "Quarantine Zone": "Q",
        }
        chips = [(labels.get(zone, zone[:1].upper()), zone) for zone in domain[:4]]
        chip_w = 21
        chip_h = 18
        gap = 4
        total_w = len(chips) * chip_w + max(0, len(chips) - 1) * gap
        y = cy + r + 42 if below else cy - r - chip_h - 42
        panel = pygame.Rect(cx - total_w // 2 - 8, y - 5, total_w + 16, chip_h + 10)
        pygame.draw.rect(self.surface, (3, 11, 21), panel, border_radius=7)
        pygame.draw.rect(self.surface, (34, 82, 126), panel, 1, border_radius=7)
        font = get_font(8, bold=True)
        for idx, (label_text, zone) in enumerate(chips):
            x = cx - total_w // 2 + idx * (chip_w + gap)
            rect = pygame.Rect(x, y, chip_w, chip_h)
            zone_color = CSP_ZONE_COLORS.get(zone, (120, 140, 160))
            is_attempted = attempted == zone
            fill = zone_color if is_attempted and not pruned else (7, 17, 31)
            border = (255, 240, 135) if is_attempted else zone_color
            text_color = (5, 14, 25) if is_attempted and not pruned else (235, 248, 255)
            pygame.draw.rect(self.surface, fill, rect, border_radius=5)
            pygame.draw.rect(self.surface, border, rect, 2 if is_attempted else 1, border_radius=5)
            label = font.render(label_text, True, text_color)
            self.surface.blit(label, label.get_rect(center=rect.center))
            if pruned:
                pygame.draw.line(self.surface, (255, 92, 80), (rect.x + 4, rect.bottom - 4), (rect.right - 4, rect.y + 4), 2)

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

    def _draw_belief_indicator(self, cx: int, cy: int, r: int) -> None:
        """Vẽ vòng đứt nét màu tím biểu thị Hacker tiềm năng."""
        color = (220, 80, 255)
        self._draw_dashed_circle(cx, cy, r + 12, color, 2)
        self._draw_dashed_circle(cx, cy, r + 18, color, 1)

    def _draw_observation_indicator(self, cx: int, cy: int, r: int) -> None:
        """Vẽ vòng sáng màu lam nhạt biểu thị vùng được IDS quét."""
        color = (100, 200, 255)
        glow = pygame.Surface(((r + 20) * 2, (r + 20) * 2), pygame.SRCALPHA)
        center = (r + 20, r + 20)
        pygame.draw.circle(glow, (*color, 30), center, r + 14)
        pygame.draw.circle(glow, (*color, 60), center, r + 8)
        self.surface.blit(glow, (cx - (r + 20), cy - (r + 20)))
        self._draw_dashed_circle(cx, cy, r + 8, color, 1)

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
