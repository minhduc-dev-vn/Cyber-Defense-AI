"""
stats_view.py - Compact algorithm statistics overlay.
"""
from __future__ import annotations

from typing import Optional

import pygame

from core.models import AlgorithmMetrics, AlgorithmResult, StepEvent
from core.utils import format_cost
from ui.theme import (
    get_font,
    COLOR_PANEL_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_SUCCESS,
    COLOR_TEXT_ERROR,
    COLOR_TEXT_WARNING,
)


class StatsView:
    """Draws the live stats overlay in the top-right graph area."""

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect

    def draw(
        self,
        surface: pygame.Surface,
        step: Optional[StepEvent] = None,
        metrics: Optional[AlgorithmMetrics] = None,
        status: str = "ready",
        show_details: bool = False,
        compare_results: Optional[list[AlgorithmResult]] = None,
    ) -> None:
        bg_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        bg_surf.fill((20, 24, 40, 215))
        surface.blit(bg_surf, (self.rect.x, self.rect.y))
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, self.rect, 1, border_radius=6)

        if compare_results:
            self._draw_compare(surface, compare_results)
            return

        font = get_font(11)
        font_b = get_font(11, bold=True)

        status_colors = {
            "ready": COLOR_TEXT_SECONDARY,
            "running": COLOR_TEXT_WARNING,
            "paused": (100, 180, 255),
            "success": COLOR_TEXT_SUCCESS,
            "failure": COLOR_TEXT_ERROR,
        }
        status_texts = {
            "ready": "Ready",
            "running": "Running",
            "paused": "Paused",
            "success": "Success",
            "failure": "Failure",
        }

        lines: list[tuple[str, str, tuple[int, int, int]]] = []

        if step:
            lines.append(("Algorithm:", step.algorithm, COLOR_TEXT_PRIMARY))
            lines.append(("Status:", status_texts.get(status, status), status_colors.get(status, COLOR_TEXT_PRIMARY)))
            lines.append(("Step:", str(step.step_index), COLOR_TEXT_PRIMARY))
            lines.append(("Expanded:", str(step.nodes_expanded), COLOR_TEXT_PRIMARY))
            lines.append(("Generated:", str(step.nodes_generated), COLOR_TEXT_PRIMARY))
            lines.append(("Frontier:", str(len(step.frontier)), COLOR_TEXT_PRIMARY))
            if step.total_cost > 0 or step.path:
                lines.append(("Cost:", format_cost(step.total_cost), COLOR_TEXT_PRIMARY))
            if step.path:
                path_text = " -> ".join(step.path[:4]) + ("..." if len(step.path) > 4 else "")
                lines.append(("Path:", path_text, COLOR_TEXT_SUCCESS))
            if show_details and step.data:
                for key in ("g", "h", "f", "threshold"):
                    if key in step.data:
                        value = step.data[key]
                        if isinstance(value, float):
                            text = format_cost(value)
                        else:
                            text = str(value)
                        lines.append((f"{key}:", text, COLOR_TEXT_WARNING))
                for key, label in (
                    ("defense_value", "Value"),
                    ("risk_cost", "Risk"),
                    ("open_paths", "Open"),
                    ("blocked_paths", "Blocked"),
                    ("conflicts", "Conflicts"),
                    ("backtracks", "Backtracks"),
                    ("temperature", "Temp"),
                    ("accepted_worse_moves", "Worse"),
                    ("evaluation", "Eval"),
                    ("expected_value", "Expected"),
                    ("alpha", "Alpha"),
                    ("beta", "Beta"),
                    ("pruned_branches", "Pruned"),
                    ("belief", "Belief"),
                    ("plan", "Plan"),
                    ("plan_lines", "Plan"),
                ):
                    if key in step.data:
                        value = step.data[key]
                        if isinstance(value, list):
                            text = str(len(value))
                        elif isinstance(value, float):
                            text = format_cost(value)
                        else:
                            text = str(value)
                        lines.append((f"{label}:", text, COLOR_TEXT_WARNING))
        elif metrics:
            lines.append(("Algorithm:", metrics.algorithm, COLOR_TEXT_PRIMARY))
            lines.append(("Result:", "OK" if metrics.success else "Fail", COLOR_TEXT_SUCCESS if metrics.success else COLOR_TEXT_ERROR))
            lines.append(("Expanded:", str(metrics.nodes_expanded), COLOR_TEXT_PRIMARY))
            lines.append(("Generated:", str(metrics.nodes_generated), COLOR_TEXT_PRIMARY))
            lines.append(("Cost:", format_cost(metrics.total_cost), COLOR_TEXT_PRIMARY))
            lines.append(("Time:", f"{metrics.time_ms:.2f}ms", COLOR_TEXT_PRIMARY))
        else:
            lines.append(("Status:", "Choose algorithm and map", COLOR_TEXT_SECONDARY))

        y = self.rect.y + 6
        for label, value, color in lines:
            if y > self.rect.bottom - 14:
                break
            label_surf = font.render(label, True, COLOR_TEXT_SECONDARY)
            value_surf = font_b.render(value, True, color)
            surface.blit(label_surf, (self.rect.x + 6, y))
            surface.blit(value_surf, (self.rect.x + 82, y))
            y += 14

    def _draw_compare(
        self,
        surface: pygame.Surface,
        compare_results: list[AlgorithmResult],
    ) -> None:
        font = get_font(10)
        font_b = get_font(10, bold=True)
        title = font_b.render("Compare", True, COLOR_TEXT_PRIMARY)
        surface.blit(title, (self.rect.x + 6, self.rect.y + 6))

        y = self.rect.y + 24
        headers = ["Alg", "OK", "Cost", "Exp"]
        x_positions = [self.rect.x + 6, self.rect.x + 72, self.rect.x + 104, self.rect.x + 154]
        for x, header in zip(x_positions, headers):
            surface.blit(font_b.render(header, True, COLOR_TEXT_SECONDARY), (x, y))
        y += 14

        for result in compare_results[:6]:
            metrics = result.metrics
            if y > self.rect.bottom - 12:
                break
            ok = "Y" if metrics.success else "N"
            color = COLOR_TEXT_SUCCESS if metrics.success else COLOR_TEXT_ERROR
            values = [
                metrics.algorithm[:9],
                ok,
                format_cost(metrics.total_cost),
                str(metrics.nodes_expanded),
            ]
            for x, value in zip(x_positions, values):
                surface.blit(font.render(value, True, color if value == ok else COLOR_TEXT_PRIMARY), (x, y))
            y += 13
