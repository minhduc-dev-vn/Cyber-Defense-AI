"""
graph_view.py - Graph display panel.

Manages GraphRenderer, node click/hover detection, and the selected-node
metadata popup. Map JSON coordinates are treated as local to this panel.
"""
from __future__ import annotations

from typing import Optional

import pygame

from core.graph import NetworkGraph
from core.models import StepEvent
from core.state import AppState
from ui.renderer import GraphRenderer
from ui.theme import (
    get_font,
    COLOR_PANEL_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_WARNING,
)


class GraphView:
    """Graph display area and node metadata view."""

    def __init__(self, rect: pygame.Rect, app_state: AppState) -> None:
        self.rect = rect
        self.app_state = app_state
        self._renderer: Optional[GraphRenderer] = None

    def set_graph(self, graph: NetworkGraph) -> None:
        """Assign a graph after loading or switching maps."""
        surf = pygame.display.get_surface()
        self._renderer = GraphRenderer(surf, graph)

    def _graph_offset(self) -> tuple[int, int]:
        return (self.rect.x, self.rect.y)

    def handle_event(self, event: pygame.event.Event) -> None:
        offset = self._graph_offset()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self._renderer:
                self.app_state.selected_node = self._renderer.get_node_at(
                    event.pos[0],
                    event.pos[1],
                    offset=offset,
                )
        elif event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos) and self._renderer:
                self.app_state.hovered_node = self._renderer.get_node_at(
                    event.pos[0],
                    event.pos[1],
                    offset=offset,
                )
            elif not self.rect.collidepoint(event.pos):
                self.app_state.hovered_node = None

    def draw(
        self,
        surface: pygame.Surface,
        step: Optional[StepEvent],
        hacker_pos: str,
        goal_nodes: list[str],
        graph: Optional[NetworkGraph] = None,
    ) -> None:
        pygame.draw.rect(surface, (14, 18, 30), self.rect)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, self.rect, 1)

        if graph and not self._renderer:
            self._renderer = GraphRenderer(surface, graph)

        if self._renderer:
            self._renderer.surface = surface
            self._renderer.draw(
                step,
                hacker_pos,
                goal_nodes,
                selected_node=self.app_state.selected_node,
                hovered_node=self.app_state.hovered_node,
                offset=self._graph_offset(),
            )

        if self.app_state.selected_node and graph:
            node = graph.get_node(self.app_state.selected_node)
            if node:
                self._draw_node_info(surface, node)

    def _draw_node_info(self, surface: pygame.Surface, node) -> None:
        """Draw metadata for the selected node."""
        info_lines = [
            f"ID: {node.id}",
            f"Type: {node.kind}",
            f"Security: {node.security_level}/10",
            f"Zone: {node.zone or 'None'}",
            f"Blocked: {'Yes' if node.blocked else 'No'}",
            f"Compromised: {'Yes' if node.compromised else 'No'}",
            f"Monitored: {'Yes' if node.monitored else 'No'}",
            f"Importance: {node.importance}/10",
            f"Detect risk: {node.detection_risk:.2f}",
        ]
        width, height = 190, len(info_lines) * 14 + 16
        ox, oy = self._graph_offset()
        px = min(node.position[0] + ox + 30, self.rect.right - width - 4)
        py = min(node.position[1] + oy - 10, self.rect.bottom - height - 4)
        px = max(px, self.rect.x + 4)
        py = max(py, self.rect.y + 4)

        bg = pygame.Surface((width, height), pygame.SRCALPHA)
        bg.fill((20, 26, 46, 230))
        surface.blit(bg, (px, py))
        pygame.draw.rect(
            surface,
            COLOR_PANEL_BORDER,
            pygame.Rect(px, py, width, height),
            1,
            border_radius=5,
        )

        font = get_font(11)
        for i, line in enumerate(info_lines):
            is_warning = "Yes" in line and (
                "Blocked" in line or "Compromised" in line
            )
            color = COLOR_TEXT_WARNING if is_warning else COLOR_TEXT_PRIMARY
            surf = font.render(line, True, color)
            surface.blit(surf, (px + 6, py + 6 + i * 14))
