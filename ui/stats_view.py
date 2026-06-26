"""Bottom result, details and path panels."""
from __future__ import annotations

from typing import Optional

import pygame

from core.models import AlgorithmMetrics, AlgorithmResult, StepEvent
from core.utils import format_cost
from ui.node_art import draw_network_node, infer_node_kind
from ui.panels import algo_label
from ui.theme import (
    COLOR_EDGE_DEFAULT,
    COLOR_NODE_HACKER,
    COLOR_NODE_SERVER,
    COLOR_PANEL_BORDER,
    COLOR_TEXT_ERROR,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_SUCCESS,
    COLOR_TEXT_WARNING,
    draw_panel,
    draw_text_fit,
    get_font,
    get_node_color,
)


class StatsView:
    """Draws the bottom monitoring/result area."""

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
        draw_panel(surface, self.rect)
        if compare_results:
            self._draw_compare(surface, compare_results)
            return

        left_w = max(220, self.rect.width // 3)
        mid_w = max(220, self.rect.width // 3)
        left = pygame.Rect(self.rect.x, self.rect.y, left_w, self.rect.height)
        mid = pygame.Rect(left.right, self.rect.y, mid_w, self.rect.height)
        right = pygame.Rect(mid.right, self.rect.y, self.rect.right - mid.right, self.rect.height)
        pygame.draw.line(surface, COLOR_PANEL_BORDER, (left.right, self.rect.y), (left.right, self.rect.bottom), 1)
        pygame.draw.line(surface, COLOR_PANEL_BORDER, (mid.right, self.rect.y), (mid.right, self.rect.bottom), 1)
        self._draw_details_table(surface, left, step, show_details)
        self._draw_result(surface, mid, step, metrics, status)
        self._draw_path(surface, right, step, metrics)

    def _draw_details_table(self, surface: pygame.Surface, rect: pygame.Rect, step: Optional[StepEvent], show_details: bool) -> None:
        title = get_font(13, bold=True).render("GIÁM SÁT", True, (116, 195, 255))
        surface.blit(title, (rect.x + 12, rect.y + 12))
        rows = [
            ("Biên", ", ".join(step.frontier[:6]) if step else "-"),
            ("Đã duyệt", ", ".join(step.explored[-8:]) if step else "-"),
            ("Đang xét", step.current_node if step and step.current_node else "-"),
        ]
        if show_details and step and step.data:
            for key in ("g", "h", "f", "threshold", "evaluation", "expected_value", "belief", "plan"):
                if key in step.data:
                    value = step.data[key]
                    rows.append((key, str(len(value)) if isinstance(value, list) else str(value)))

        y = rect.y + 34
        visible_rows = rows[:4]
        row_h = max(34, min(44, (rect.height - 48) // max(1, len(visible_rows))))
        for label, value in visible_rows:
            row_rect = pygame.Rect(rect.x + 12, y, rect.width - 24, row_h)
            pygame.draw.rect(surface, (7, 17, 31), row_rect, border_radius=5)
            pygame.draw.rect(surface, (30, 55, 80), row_rect, 1, border_radius=5)
            draw_text_fit(surface, label, pygame.Rect(row_rect.x + 10, row_rect.y, 78, row_rect.height), COLOR_TEXT_PRIMARY, size=11, bold=True)
            self._draw_wrapped_text(
                surface,
                value or "-",
                pygame.Rect(row_rect.x + 92, row_rect.y + 3, row_rect.width - 100, row_rect.height - 6),
                COLOR_TEXT_PRIMARY,
                size=10,
            )
            y += row_h + 4

    def _draw_result(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        step: Optional[StepEvent],
        metrics: Optional[AlgorithmMetrics],
        status: str,
    ) -> None:
        title = get_font(13, bold=True).render("KẾT QUẢ", True, (116, 195, 255))
        surface.blit(title, (rect.x + 14, rect.y + 12))
        algorithm = algo_label(step.algorithm) if step else (algo_label(metrics.algorithm) if metrics else "-")
        path = step.path if step else (metrics.path if metrics else [])
        cost = step.total_cost if step else (metrics.total_cost if metrics else 0)
        expanded = step.nodes_expanded if step else (metrics.nodes_expanded if metrics else 0)
        generated = step.nodes_generated if step else (metrics.nodes_generated if metrics else 0)
        status_color = {
            "success": COLOR_TEXT_SUCCESS,
            "failure": COLOR_TEXT_ERROR,
            "running": COLOR_TEXT_WARNING,
            "paused": (100, 180, 255),
        }.get(status, COLOR_TEXT_SECONDARY)
        status_label = {
            "ready": "Sẵn sàng",
            "running": "Đang chạy",
            "paused": "Tạm dừng",
            "success": "Thành công",
            "failure": "Thất bại",
        }.get(status, status)
        rows = [
            ("Thuật toán", algorithm),
            ("Đường đi", " -> ".join(path) if path else "-"),
            ("Node mở rộng", str(expanded)),
            ("Node sinh ra", str(generated)),
            ("Chi phí / điểm", format_cost(cost)),
            ("Trạng thái", status_label),
        ]
        y = rect.y + 34
        full_w = rect.width - 28
        label_w = 102
        row_h = 18
        draw_text_fit(surface, rows[0][0] + ":", pygame.Rect(rect.x + 14, y, label_w, row_h), COLOR_TEXT_PRIMARY, size=8, bold=True)
        draw_text_fit(surface, rows[0][1], pygame.Rect(rect.x + 14 + label_w, y, rect.width - label_w - 28, row_h), COLOR_TEXT_PRIMARY, size=8)
        y += row_h + 4

        draw_text_fit(surface, rows[1][0] + ":", pygame.Rect(rect.x + 14, y, full_w, 16), COLOR_TEXT_PRIMARY, size=8, bold=True)
        self._draw_wrapped_text(
            surface,
            rows[1][1],
            pygame.Rect(rect.x + 14, y + 18, full_w, 22),
            COLOR_TEXT_PRIMARY,
            size=7,
        )
        y += 40

        for label, value in (rows[2], rows[3], rows[4], rows[5]):
            row_h = 16
            color = status_color if label == "Trạng thái" else COLOR_TEXT_PRIMARY
            draw_text_fit(surface, label + ":", pygame.Rect(rect.x + 14, y, label_w, row_h), COLOR_TEXT_PRIMARY, size=8, bold=True)
            draw_text_fit(
                surface,
                value,
                pygame.Rect(rect.x + 14 + label_w, y, rect.width - label_w - 28, row_h),
                color,
                size=8,
            )
            y += row_h
        return
        y = rect.y + 38
        label_w = 94
        for label, value in (rows[0], rows[2], rows[3], rows[4], rows[5]):
            row_h = 18
            color = status_color if label == "Trạng thái" else COLOR_TEXT_PRIMARY
            draw_text_fit(surface, label + ":", pygame.Rect(rect.x + 14, y, label_w, row_h), COLOR_TEXT_PRIMARY, size=10, bold=True)
            self._draw_wrapped_text(
                surface,
                value,
                pygame.Rect(rect.x + 14 + label_w, y, rect.width - label_w - 28, row_h),
                color,
                size=10,
            )
            y += row_h

        if y + 34 <= rect.bottom - 6:
            label, value = rows[1]
            draw_text_fit(surface, label + ":", pygame.Rect(rect.x + 14, y, rect.width - 28, 17), COLOR_TEXT_PRIMARY, size=10, bold=True)
            y += 17
            self._draw_wrapped_text(
                surface,
                value,
                pygame.Rect(rect.x + 14, y, rect.width - 28, rect.bottom - y - 6),
                COLOR_TEXT_PRIMARY,
                size=10,
            )

    def _draw_path(self, surface: pygame.Surface, rect: pygame.Rect, step: Optional[StepEvent], metrics: Optional[AlgorithmMetrics]) -> None:
        title = get_font(13, bold=True).render("ĐƯỜNG ĐI", True, (116, 195, 255))
        surface.blit(title, (rect.x + 14, rect.y + 12))
        path = step.path if step else (metrics.path if metrics else [])
        if not path:
            draw_text_fit(surface, "Chưa có đường đi hoặc kế hoạch.", pygame.Rect(rect.x + 14, rect.y + 48, rect.width - 28, 24), COLOR_TEXT_SECONDARY, size=12)
            return

        max_nodes = min(len(path), 6)
        gap = 0 if max_nodes <= 1 else (rect.width - 66) / (max_nodes - 1)
        radius = max(13, min(17, int(gap / 3.0) if gap else 16))
        y = min(rect.y + 74, rect.bottom - 68)
        x = rect.x + 32
        for i, node_id in enumerate(path[:max_nodes]):
            kind = infer_node_kind(node_id)
            color = get_node_color(kind)
            if i == 0:
                color = COLOR_NODE_HACKER
            elif i == len(path[:max_nodes]) - 1:
                color = COLOR_NODE_SERVER if kind in ("server", "database") else color
            center = (int(x + i * gap), y)
            draw_network_node(surface, kind, center, radius, color, hacker=i == 0)
            label = get_font(8, bold=True).render(node_id[:10], True, COLOR_TEXT_PRIMARY)
            label_y = center[1] + radius + (11 if i % 2 == 0 else 25)
            surface.blit(label, (center[0] - label.get_width() // 2, label_y))
            if i < max_nodes - 1:
                start = (center[0] + radius + 12, center[1])
                end = (int(x + (i + 1) * gap - radius - 12), y)
                pygame.draw.line(surface, (8, 15, 26), start, end, 4)
                pygame.draw.line(surface, COLOR_EDGE_DEFAULT, start, end, 2)
                pygame.draw.polygon(surface, COLOR_EDGE_DEFAULT, [(end[0], end[1]), (end[0] - 7, end[1] - 4), (end[0] - 7, end[1] + 4)])

    def _draw_compare(self, surface: pygame.Surface, compare_results: list[AlgorithmResult]) -> None:
        title = get_font(13, bold=True).render("SO SÁNH", True, (116, 195, 255))
        surface.blit(title, (self.rect.x + 14, self.rect.y + 12))
        headers = ["Thuật toán", "Đạt", "Chi phí", "Mở rộng", "Thời gian"]
        widths = [150, 52, 96, 88, 82]
        x = self.rect.x + 14
        y = self.rect.y + 42
        font_b = get_font(11, bold=True)
        font = get_font(11)
        for header, width in zip(headers, widths):
            surface.blit(font_b.render(header, True, COLOR_TEXT_SECONDARY), (x, y))
            x += width
        y += 24
        for result in compare_results[:6]:
            x = self.rect.x + 14
            metrics = result.metrics
            values = [
                algo_label(metrics.algorithm),
                "Có" if metrics.success else "Không",
                format_cost(metrics.total_cost),
                str(metrics.nodes_expanded),
                f"{metrics.time_ms:.2f}ms",
            ]
            color = COLOR_TEXT_SUCCESS if metrics.success else COLOR_TEXT_ERROR
            for value, width in zip(values, widths):
                surface.blit(font.render(value[:18], True, color if value in ("Có", "Không") else COLOR_TEXT_PRIMARY), (x, y))
                x += width
            y += 22

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        if " -> " in str(text):
            parts = [part.strip() for part in str(text).split("->") if part.strip()]
            lines: list[str] = []
            current = ""
            for part in parts:
                candidate = part if not current else f"{current} -> {part}"
                if font.size(candidate)[0] <= max_width:
                    current = candidate
                    continue
                if current:
                    lines.append(current)
                current = part
            if current:
                lines.append(current)
            return lines or [""]

        words = str(text).split(" ")
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if font.size(candidate)[0] <= max_width:
                current = candidate
                continue
            if current:
                lines.append(current)
            while font.size(word)[0] > max_width and len(word) > 1:
                cut = len(word)
                while cut > 1 and font.size(word[:cut])[0] > max_width:
                    cut -= 1
                lines.append(word[:cut])
                word = word[cut:]
            current = word
        if current:
            lines.append(current)
        return lines or [""]

    def _draw_wrapped_text(
        self,
        surface: pygame.Surface,
        text: str,
        rect: pygame.Rect,
        color: tuple[int, int, int],
        size: int = 10,
        bold: bool = False,
    ) -> int:
        if rect.width <= 0 or rect.height <= 0:
            return 0
        font = get_font(size, bold=bold)
        line_h = max(14, font.get_height())
        old_clip = surface.get_clip()
        surface.set_clip(rect)
        y = rect.y
        drawn = 0
        for line in self._wrap_text(text, font, rect.width):
            if y + line_h > rect.bottom:
                break
            surface.blit(font.render(line, True, color), (rect.x, y))
            y += line_h
            drawn += 1
        surface.set_clip(old_clip)
        return drawn
