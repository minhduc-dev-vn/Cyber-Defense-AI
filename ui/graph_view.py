"""Graph display panel for the modern dashboard."""
from __future__ import annotations

from typing import Optional

import pygame

from core.graph import NetworkGraph
from core.models import StepEvent
from core.state import AppState
from ui.renderer import GraphRenderer
from ui.theme import draw_panel


class GraphView:
    """Graph canvas with grid background and node hit detection."""

    def __init__(self, rect: pygame.Rect, app_state: AppState) -> None:
        self.rect = rect
        self.app_state = app_state
        self._renderer: Optional[GraphRenderer] = None

    def set_graph(self, graph: NetworkGraph) -> None:
        surf = pygame.display.get_surface()
        self._renderer = GraphRenderer(surf, graph)
        self._renderer.configure_viewport(self.rect)

    def _graph_offset(self) -> tuple[int, int]:
        return (self.rect.x, self.rect.y)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._renderer:
            self._renderer.configure_viewport(self.rect)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self._renderer:
                self.app_state.selected_node = self._renderer.get_node_at(
                    event.pos[0],
                    event.pos[1],
                    offset=self._graph_offset(),
                )
        elif event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos) and self._renderer:
                self.app_state.hovered_node = self._renderer.get_node_at(
                    event.pos[0],
                    event.pos[1],
                    offset=self._graph_offset(),
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
        draw_panel(surface, self.rect, "Bản đồ mạng")
        self._draw_grid(surface)

        if graph and not self._renderer:
            self._renderer = GraphRenderer(surface, graph)

        if self._renderer:
            self._renderer.surface = surface
            self._renderer.configure_viewport(self.rect)
            clip = self.rect.inflate(-2, -2)
            old_clip = surface.get_clip()
            surface.set_clip(clip)
            self._renderer.draw(
                step,
                hacker_pos,
                goal_nodes,
                selected_node=self.app_state.selected_node,
                hovered_node=self.app_state.hovered_node,
                offset=(0, 0),
            )
            surface.set_clip(old_clip)

    def _draw_grid(self, surface: pygame.Surface) -> None:
        clip = self.rect.inflate(-2, -2)
        old_clip = surface.get_clip()
        surface.set_clip(clip)
        for x in range(self.rect.x + 16, self.rect.right, 22):
            for y in range(self.rect.y + 20, self.rect.bottom, 22):
                surface.set_at((x, y), (20, 64, 96))
        for x in range(self.rect.x + 2, self.rect.right, 88):
            pygame.draw.line(surface, (9, 31, 49), (x, self.rect.y + 2), (x, self.rect.bottom - 2), 1)
        for y in range(self.rect.y + 2, self.rect.bottom, 88):
            pygame.draw.line(surface, (9, 31, 49), (self.rect.x + 2, y), (self.rect.right - 2, y), 1)
        surface.set_clip(old_clip)
