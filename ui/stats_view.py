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
        rows = self._monitor_rows(step, show_details)

        y = rect.y + 34
        is_csp = bool(step and "assignments" in (step.data or {}) and "domains" in (step.data or {}))
        if is_csp:
            visible_rows = rows[:5]
        elif step and step.algorithm == "IDA*":
            visible_rows = rows[:5]
        else:
            visible_rows = rows[:4]
        row_gap = 4
        min_row_h = 20 if len(visible_rows) > 4 else 28
        row_h = max(
            min_row_h,
            min(44, (rect.height - 52 - row_gap * max(0, len(visible_rows) - 1)) // max(1, len(visible_rows))),
        )
        for label, value in visible_rows:
            row_rect = pygame.Rect(rect.x + 12, y, rect.width - 24, row_h)
            pygame.draw.rect(surface, (7, 17, 31), row_rect, border_radius=5)
            pygame.draw.rect(surface, (30, 55, 80), row_rect, 1, border_radius=5)
            draw_text_fit(surface, label, pygame.Rect(row_rect.x + 10, row_rect.y, 78, row_rect.height), COLOR_TEXT_PRIMARY, size=11, bold=True)
            draw_text_fit(
                surface,
                value or "-",
                pygame.Rect(row_rect.x + 92, row_rect.y, row_rect.width - 100, row_rect.height),
                COLOR_TEXT_PRIMARY,
                size=10,
            )
            y += row_h + row_gap

    def _monitor_rows(self, step: Optional[StepEvent], show_details: bool) -> list[tuple[str, str]]:
        if not step:
            return [
                ("Biên", "-"),
                ("Đã duyệt", "-"),
                ("Đang xét", "-"),
            ]

        data = step.data or {}
        if data.get("local_search_mode") == "heuristic_path":
            chosen = data.get("chosen_neighbor") or "-"
            neighbors = data.get("neighbor_scores", [])
            best = self._best_neighbor_text(neighbors)
            rows = [
                ("Node", step.current_node or "-"),
                ("h hiện tại", self._cost_text(data.get("current_heuristic"))),
                ("Láng giềng", self._neighbor_summary(neighbors)),
                ("Đang xét", str(chosen)),
                ("Tốt nhất", best),
            ]
            return rows

        if "assignments" in data and "domains" in data:
            assignments = data.get("assignments", {})
            conflicts = data.get("conflicts", [])
            removed = data.get("removed", {})
            current_domain = data.get("current_domain") or (
                data.get("domains", {}).get(step.current_node, []) if isinstance(data.get("domains"), dict) else []
            )
            attempted = data.get("attempted_value") or (
                assignments.get(step.current_node) if isinstance(assignments, dict) and step.current_node else None
            )
            candidate = self._candidate_text(data)
            check_text = "OK" if not conflicts else f"Vi phạm {len(conflicts)}"
            rows = [
                ("Biến", step.current_node or "-"),
                ("Miền còn lại", self._zone_short_list(current_domain)),
                ("Đang thử", f"{candidate}{attempted or '-'}"),
                ("Ràng buộc", check_text),
                ("Đã gán", f"{len(assignments) if isinstance(assignments, dict) else 0} node"),
            ]
            if removed:
                rows[-1] = ("Cắt miền", self._domain_removal_text(removed))
            elif data.get("backtracks"):
                rows.append(("Quay lui", str(data.get("backtracks"))))
            return rows

        if any(key in data for key in ("g", "h", "f", "threshold")):
            rows = [("Đang xét", step.current_node or "-")]
            if "g" in data:
                rows.append(("g(n)", format_cost(float(data["g"]))))
            if "h" in data:
                rows.append(("h(n)", format_cost(float(data["h"]))))
            if "f" in data:
                rows.append(("f(n)=g+h", format_cost(float(data["f"]))))
            if "threshold" in data:
                rows.append(("Ngưỡng f", format_cost(float(data["threshold"]))))
            if len(rows) < 4:
                rows.append(("Biên", ", ".join(step.frontier[:6]) if step.frontier else "-"))
            return rows

        if "belief" in data:
            belief = data.get("belief", [])
            blocked = data.get("blocked_nodes", [])
            observed = data.get("observed_nodes", [])
            rows = [
                ("Belief", ", ".join(str(n) for n in belief) if belief else "∅ (trống)"),
                ("Đang xét", step.current_node if step.current_node else "-"),
                ("Đã chặn", ", ".join(str(n) for n in blocked) if blocked else "(chưa có)"),
            ]
            if observed:
                rows.append(("IDS quét", ", ".join(str(n) for n in observed[:4])))
            return rows

        rows = [
            ("Biên", ", ".join(step.frontier[:6]) if step.frontier else "-"),
            ("Đã duyệt", ", ".join(step.explored[-8:]) if step.explored else "-"),
            ("Đang xét", step.current_node if step.current_node else "-"),
        ]
        if "game_state" in data:
            blocked = data.get("blocked_nodes", [])
            blocked_edges = data.get("blocked_edges", [])
            rows = [
                ("Turn", str(data.get("turn", "-"))),
                ("Hacker", str(data.get("hacker_position", step.current_node or "-"))),
                ("Detected", "Yes" if data.get("detected") else "No"),
                ("Turns left", str(data.get("remaining_turns", "-"))),
            ]
            if blocked:
                rows.append(("Blocked", ", ".join(str(n) for n in blocked[:3])))
            elif blocked_edges:
                rows.append(("Blocked", ", ".join("-".join(edge) for edge in blocked_edges[:2])))
            return rows
        if show_details and data:
            for key in ("evaluation", "expected_value", "defense_value", "risk_cost", "blocked_paths", "open_paths", "belief", "plan"):
                if key in data:
                    value = data[key]
                    rows.append((key, str(len(value)) if isinstance(value, list) else str(value)))
        return rows

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
        adversarial_data = self._adversarial_data(step, metrics)
        if adversarial_data:
            self._draw_adversarial_result(surface, rect, adversarial_data, status_color, status_label)
            return
        defense_data = self._defense_data(step, metrics)
        if defense_data:
            self._draw_defense_result(surface, rect, defense_data, status_color, status_label)
            return
        local_data = self._local_search_data(step, metrics)
        if local_data:
            self._draw_local_search_result(surface, rect, local_data, status_color, status_label)
            return
        csp_data = self._csp_data(step, metrics)
        if csp_data:
            self._draw_csp_result(surface, rect, csp_data, status_color, status_label)
            return
        complex_data = self._complex_env_data(step, metrics)
        if complex_data:
            self._draw_complex_env_result(surface, rect, complex_data, status_color, status_label)
            return
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
        adversarial_data = self._adversarial_data(step, metrics)
        defense_data = self._defense_data(step, metrics)
        csp_data = self._csp_data(step, metrics)
        local_data = self._local_search_data(step, metrics)
        complex_data = self._complex_env_data(step, metrics)
        title_text = (
            "VÁN ĐỐI KHÁNG" if adversarial_data
            else "PHÒNG THỦ" if defense_data
            else "PHÂN VÙNG" if csp_data
            else "HEURISTIC" if local_data
            else "KẾ HOẠCH" if complex_data
            else "ĐƯỜNG ĐI"
        )
        title = get_font(13, bold=True).render(title_text, True, (116, 195, 255))
        surface.blit(title, (rect.x + 14, rect.y + 12))
        if adversarial_data:
            self._draw_adversarial_summary(surface, rect, adversarial_data)
            return
        if defense_data:
            self._draw_defense_summary(surface, rect, defense_data)
            return
        if csp_data:
            self._draw_csp_summary(surface, rect, csp_data)
            return
        if local_data:
            self._draw_local_search_summary(surface, rect, local_data)
            return
        if complex_data:
            self._draw_complex_env_summary(surface, rect, complex_data)
            return
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

    def _adversarial_data(self, step: Optional[StepEvent], metrics: Optional[AlgorithmMetrics]) -> Optional[dict]:
        if step and "game_state" in (step.data or {}):
            return step.data
        if metrics and "game_state" in (metrics.extra or {}):
            return metrics.extra
        return None

    def _draw_adversarial_result(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        data: dict,
        status_color: tuple[int, int, int],
        status_label: str,
    ) -> None:
        terminal = bool(data.get("terminal"))
        winner = data.get("winner")
        if terminal and winner == "hacker":
            conclusion = str(data.get("outcome_title") or "Hacker thành công")
            conclusion_color = COLOR_TEXT_SUCCESS
            result_text = "Hacker thắng"
        elif terminal and winner == "defender":
            conclusion = str(data.get("outcome_title") or "AI phòng thủ thành công")
            conclusion_color = COLOR_TEXT_ERROR
            result_text = "AI thắng"
        else:
            conclusion = "Ván đang diễn ra"
            conclusion_color = status_color
            result_text = status_label

        rows = [
            ("Kết luận", conclusion),
            ("Lý do", str(data.get("outcome_reason") or "chưa kết thúc")),
            ("Hacker", str(data.get("hacker_position", "-"))),
            ("Lượt còn", str(data.get("remaining_turns", "-"))),
            ("Phát hiện", "Có" if data.get("detected") else "Không"),
            ("Trạng thái", result_text),
        ]
        y = rect.y + 34
        label_w = 78
        value_w = rect.width - label_w - 32
        for label, value in rows:
            row_h = 32 if label == "Lý do" else 18
            color = conclusion_color if label in {"Kết luận", "Trạng thái"} else COLOR_TEXT_PRIMARY
            draw_text_fit(surface, label + ":", pygame.Rect(rect.x + 14, y, label_w, row_h), COLOR_TEXT_PRIMARY, size=8, bold=True)
            if label == "Lý do":
                self._draw_wrapped_text(
                    surface,
                    value,
                    pygame.Rect(rect.x + 14 + label_w, y, value_w, row_h),
                    color,
                    size=7,
                )
            else:
                draw_text_fit(
                    surface,
                    value,
                    pygame.Rect(rect.x + 14 + label_w, y, value_w, row_h),
                    color,
                    size=8,
                    bold=label == "Kết luận",
                )
            y += row_h

    def _draw_adversarial_summary(self, surface: pygame.Surface, rect: pygame.Rect, data: dict) -> None:
        path = data.get("hacker_path") or []
        if not path and data.get("hacker_position"):
            path = [data.get("hacker_position")]
        blocked_nodes = data.get("blocked_nodes", [])
        blocked_edges = data.get("blocked_edges", [])
        defender_action = data.get("defender_action")
        action_text = getattr(defender_action, "description", "") if defender_action else "chưa phản ứng"
        rows = [
            ("Đường hacker", " -> ".join(str(node) for node in path) if path else "-"),
            ("AI vừa làm", action_text),
            ("Node bị chặn", ", ".join(str(n) for n in blocked_nodes[:4]) if blocked_nodes else "-"),
            ("Cạnh bị chặn", ", ".join("-".join(edge) for edge in blocked_edges[:3]) if blocked_edges else "-"),
        ]
        y = rect.y + 38
        for label, value in rows:
            if y > rect.bottom - 22:
                break
            draw_text_fit(surface, label + ":", pygame.Rect(rect.x + 14, y, rect.width - 28, 16), COLOR_TEXT_PRIMARY, size=8, bold=True)
            self._draw_wrapped_text(
                surface,
                str(value),
                pygame.Rect(rect.x + 14, y + 16, rect.width - 28, 28),
                COLOR_TEXT_SECONDARY if value == "-" else COLOR_TEXT_PRIMARY,
                size=7,
            )
            y += 42

    def _defense_data(self, step: Optional[StepEvent], metrics: Optional[AlgorithmMetrics]) -> Optional[dict]:
        if step and step.data.get("defense_config"):
            return step.data
        if metrics and metrics.extra.get("defense_config"):
            return metrics.extra
        return None

    def _csp_data(self, step: Optional[StepEvent], metrics: Optional[AlgorithmMetrics]) -> Optional[dict]:
        if step and step.data.get("assignments") is not None and step.data.get("domains") is not None:
            return step.data
        if metrics and metrics.extra.get("assignments") is not None:
            return metrics.extra
        return None

    def _local_search_data(self, step: Optional[StepEvent], metrics: Optional[AlgorithmMetrics]) -> Optional[dict]:
        if step and step.data.get("local_search_mode") == "heuristic_path":
            return step.data
        if metrics and metrics.extra.get("local_search_mode") == "heuristic_path":
            return metrics.extra
        return None

    def _complex_env_data(self, step: Optional[StepEvent], metrics: Optional[AlgorithmMetrics]) -> Optional[dict]:
        """Detect data from Complex Environment algorithms (Belief/AND-OR)."""
        if step and "belief" in (step.data or {}):
            return step.data
        if metrics and "belief" in (metrics.extra or {}):
            return metrics.extra
        return None

    def _draw_complex_env_result(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        data: dict,
        status_color: tuple[int, int, int],
        status_label: str,
    ) -> None:
        belief = data.get("belief", [])
        blocked = data.get("blocked_nodes", [])
        observed = data.get("observed_nodes", [])
        plan = data.get("plan", data.get("plan_lines", []))
        plan_tree = data.get("plan_tree")
        algo_type = "AND-OR" if plan_tree is not None else ("Partial" if observed else "Sensorless")
        rows = [
            ("Mô phỏng", f"Belief-State ({algo_type})"),
            ("Belief hiện tại", f"{len(belief)} vị trí: " + ("∅" if not belief else ", ".join(str(n) for n in belief))),
            ("Đã chặn", ", ".join(str(n) for n in blocked) if blocked else "(chưa có)"),
            ("IDS quét", ", ".join(str(n) for n in observed) if observed else "-"),
            ("Kế hoạch", f"{len(plan)} bước" if isinstance(plan, list) and plan else "Đang tính..."),
            ("Trạng thái", status_label),
        ]
        y = rect.y + 36
        label_w = min(116, max(88, rect.width // 3))
        value_w = max(40, rect.width - label_w - 32)
        value_font = get_font(8)
        line_h = value_font.get_linesize()
        max_y = rect.bottom - 6
        for label, value in rows:
            color = (
                status_color if label == "Trạng thái"
                else (220, 80, 255) if label == "Belief hiện tại"
                else (100, 200, 255) if label == "IDS quét"
                else COLOR_TEXT_PRIMARY
            )
            wrapped = self._wrap_text(str(value), value_font, value_w)
            row_h = max(16, len(wrapped) * line_h)
            if y + row_h > max_y:
                row_h = max(14, max_y - y)
            draw_text_fit(surface, label + ":", pygame.Rect(rect.x + 14, y, label_w, min(row_h, 18)), COLOR_TEXT_PRIMARY, size=8, bold=True)
            old_clip = surface.get_clip()
            surface.set_clip(pygame.Rect(rect.x + 14 + label_w, y, value_w, row_h))
            for i, line in enumerate(wrapped):
                line_y = y + i * line_h
                if line_y + line_h > y + row_h:
                    break
                surface.blit(value_font.render(line, True, color), (rect.x + 14 + label_w, line_y))
            surface.set_clip(old_clip)
            y += row_h
            if y >= max_y:
                break

    def _draw_complex_env_summary(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        data: dict,
    ) -> None:
        """Right panel: display plan steps / AND-OR tree."""
        belief = data.get("belief", [])
        blocked = data.get("blocked_nodes", [])
        plan = data.get("plan", [])
        plan_tree = data.get("plan_tree")
        plan_lines = data.get("plan_lines", [])
        observed = data.get("observed_nodes", [])

        y = rect.y + 34
        w = rect.width - 28

        # Belief state bar
        belief_label = get_font(9, bold=True).render("Belief (vùng nghi ngờ):", True, (220, 80, 255))
        surface.blit(belief_label, (rect.x + 14, y))
        y += 16
        if belief:
            chip_w, chip_h, gap = 52, 18, 5
            x_chip = rect.x + 14
            max_chip_y = rect.bottom - 22
            for node_id in belief:
                if x_chip + chip_w > rect.right - 14:
                    x_chip = rect.x + 14
                    y += chip_h + gap
                if y + chip_h > max_chip_y:
                    break
                chip_rect = pygame.Rect(x_chip, y, chip_w, chip_h)
                pygame.draw.rect(surface, (55, 12, 70), chip_rect, border_radius=5)
                pygame.draw.rect(surface, (220, 80, 255), chip_rect, 1, border_radius=5)
                draw_text_fit(surface, str(node_id), chip_rect, (230, 190, 255), size=8, bold=True)
                x_chip += chip_w + gap
        else:
            draw_text_fit(surface, "∅  Hacker không còn đường xâm nhập", pygame.Rect(rect.x + 14, y, w, 18), COLOR_TEXT_SUCCESS, size=8, bold=True)
        y += 24

        # Blocked nodes
        if blocked:
            block_label = get_font(9, bold=True).render("Đã chặn:", True, COLOR_TEXT_ERROR)
            surface.blit(block_label, (rect.x + 14, y))
            draw_text_fit(
                surface,
                ", ".join(str(n) for n in blocked),
                pygame.Rect(rect.x + 80, y, w - 66, 16),
                COLOR_TEXT_ERROR,
                size=8,
            )
            y += 18

        # IDS observed
        if observed:
            ids_label = get_font(9, bold=True).render("IDS quét:", True, (100, 200, 255))
            surface.blit(ids_label, (rect.x + 14, y))
            draw_text_fit(
                surface,
                ", ".join(str(n) for n in observed[:5]),
                pygame.Rect(rect.x + 80, y, w - 66, 16),
                (100, 200, 255),
                size=8,
            )
            y += 18

        # Plan / tree
        pygame.draw.line(surface, (30, 55, 80), (rect.x + 14, y), (rect.right - 14, y), 1)
        y += 6
        plan_title_text = "Cây kế hoạch AND-OR:" if plan_tree is not None else ("Các bước phòng thủ:" if plan else "Đang tìm kế hoạch...")
        plan_title = get_font(9, bold=True).render(plan_title_text, True, (116, 195, 255))
        surface.blit(plan_title, (rect.x + 14, y))
        y += 16
        lines_to_show = plan_lines if plan_lines else ([item for item in plan] if isinstance(plan, list) else [])
        for line in lines_to_show[:6]:
            if y + 14 > rect.bottom - 6:
                break
            indent = 0
            text = str(line)
            while text.startswith(" "):
                indent += 8
                text = text[1:]
            is_leaf = "Safe" in text or "∅" in text or "an toàn" in text.lower()
            color = COLOR_TEXT_SUCCESS if is_leaf else COLOR_TEXT_PRIMARY
            draw_text_fit(surface, text, pygame.Rect(rect.x + 14 + indent, y, w - indent, 14), color, size=8)
            y += 14
        if not lines_to_show and y + 18 < rect.bottom:
            draw_text_fit(surface, "BFS đang xét các kết hợp chặn...", pygame.Rect(rect.x + 14, y, w, 16), COLOR_TEXT_SECONDARY, size=8)

    def _draw_local_search_result(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        data: dict,
        status_color: tuple[int, int, int],
        status_label: str,
    ) -> None:
        rows = [
            ("Mô phỏng", "Hill Climbing theo h(n)"),
            ("h hiện tại", self._cost_text(data.get("current_heuristic"))),
            ("Chi phí đi", self._cost_text(data.get("path_cost"))),
            ("Node chọn", str(data.get("chosen_neighbor") or "-")),
            ("Mục tiêu", str(data.get("goal") or "-")),
            ("Trạng thái", status_label),
        ]
        y = rect.y + 36
        label_w = 104
        for label, value in rows:
            row_h = 18
            color = status_color if label == "Trạng thái" else COLOR_TEXT_PRIMARY
            draw_text_fit(surface, label + ":", pygame.Rect(rect.x + 14, y, label_w, row_h), COLOR_TEXT_PRIMARY, size=9, bold=True)
            draw_text_fit(surface, value, pygame.Rect(rect.x + 14 + label_w, y, rect.width - label_w - 28, row_h), color, size=9)
            y += row_h

    def _draw_local_search_summary(self, surface: pygame.Surface, rect: pygame.Rect, data: dict) -> None:
        y = rect.y + 34
        path = data.get("path_so_far") or []
        path_text = " -> ".join(str(node) for node in path) if isinstance(path, list) and path else "-"
        current = path[-1] if isinstance(path, list) and path else "-"
        chosen = str(data.get("chosen_neighbor") or "-")

        rows = [
            ("Hiện tại", f"{current}   h={self._cost_text(data.get('current_heuristic'))}   cost={self._cost_text(data.get('path_cost'))}"),
            ("Đường", path_text),
            ("Ứng viên", f"{chosen}   {self._decision_text(data)}"),
        ]
        for label, value in rows:
            row_h = 18 if label != "Đường" else 24
            row_rect = pygame.Rect(rect.x + 14, y, rect.width - 28, row_h)
            pygame.draw.rect(surface, (7, 17, 31), row_rect, border_radius=5)
            pygame.draw.rect(surface, (30, 55, 80), row_rect, 1, border_radius=5)
            draw_text_fit(surface, label + ":", pygame.Rect(row_rect.x + 8, row_rect.y, 76, row_rect.height), COLOR_TEXT_PRIMARY, size=7, bold=True)
            if label == "Đường":
                self._draw_wrapped_text(
                    surface,
                    value,
                    pygame.Rect(row_rect.x + 86, row_rect.y + 2, row_rect.width - 94, row_rect.height - 4),
                    COLOR_TEXT_PRIMARY,
                    size=7,
                )
            else:
                color = COLOR_TEXT_SUCCESS if label == "Ứng viên" and data.get("accepted") else COLOR_TEXT_PRIMARY
                draw_text_fit(surface, value, pygame.Rect(row_rect.x + 86, row_rect.y, row_rect.width - 94, row_rect.height), color, size=7, bold=label == "Ứng viên")
            y += row_h + 4

        draw_text_fit(surface, "h(láng giềng):", pygame.Rect(rect.x + 14, y, rect.width - 28, 16), COLOR_TEXT_PRIMARY, size=8, bold=True)
        y += 16
        for row in (data.get("neighbor_scores") or [])[:3]:
            if not isinstance(row, dict):
                continue
            node = str(row.get("node", "-"))
            h_value = self._cost_text(row.get("heuristic"))
            edge_cost = self._cost_text(row.get("edge_cost"))
            color = COLOR_TEXT_SUCCESS if node == data.get("chosen_neighbor") else COLOR_TEXT_PRIMARY
            marker = ">" if node == data.get("chosen_neighbor") else " "
            draw_text_fit(
                surface,
                f"{marker} {node}: h={h_value}, cạnh={edge_cost}",
                pygame.Rect(rect.x + 18, y, rect.width - 36, 17),
                color,
                size=7,
                bold=node == data.get("chosen_neighbor"),
            )
            y += 15
        reason = str(data.get("reason") or "")
        if reason and y + 18 < rect.bottom:
            color = COLOR_TEXT_ERROR if "local" in reason or "stopped" in reason else COLOR_TEXT_SECONDARY
            draw_text_fit(surface, f"Kết luận: {self._reason_text(reason)}", pygame.Rect(rect.x + 14, rect.bottom - 24, rect.width - 28, 18), color, size=8, bold=True)

    def _draw_csp_result(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        data: dict,
        status_color: tuple[int, int, int],
        status_label: str,
    ) -> None:
        assignments = data.get("assignments", {})
        domains = data.get("domains", {})
        conflicts = data.get("conflicts", [])
        attempted = data.get("attempted_value") or data.get("new_value") or "-"
        current_domain = self._zone_short_list(data.get("current_domain", []))
        rows = [
            ("Mô phỏng", "CSP phân vùng mạng"),
            ("Biến", f"{len(assignments)}/{len(domains) or '-'} node đã gán"),
            ("Miền hiện tại", current_domain),
            ("Ràng buộc lỗi", str(len(conflicts) if isinstance(conflicts, list) else 0)),
            ("Zone đang thử", str(attempted)),
            ("Trạng thái", status_label),
        ]
        y = rect.y + 36
        label_w = 116
        for label, value in rows:
            row_h = 18
            color = status_color if label == "Trạng thái" else COLOR_TEXT_PRIMARY
            draw_text_fit(surface, label + ":", pygame.Rect(rect.x + 14, y, label_w, row_h), COLOR_TEXT_PRIMARY, size=9, bold=True)
            draw_text_fit(surface, value, pygame.Rect(rect.x + 14 + label_w, y, rect.width - label_w - 28, row_h), color, size=9)
            y += row_h

    def _draw_csp_summary(self, surface: pygame.Surface, rect: pygame.Rect, data: dict) -> None:
        assignments = data.get("assignments", {})
        conflicts = data.get("conflicts", [])
        zone_rows = self._zone_rows(assignments if isinstance(assignments, dict) else {})
        y = rect.y + 38
        colors = {
            "User Zone": (92, 215, 115),
            "DMZ": (255, 169, 42),
            "Server Zone": (170, 88, 255),
            "Quarantine Zone": (255, 76, 76),
        }
        for zone, nodes in zone_rows:
            color = colors.get(zone, COLOR_TEXT_SECONDARY)
            zone_label = zone.replace(" Zone", "")
            draw_text_fit(surface, zone_label + ":", pygame.Rect(rect.x + 14, y, 96, 18), color, size=9, bold=True)
            self._draw_wrapped_text(
                surface,
                ", ".join(nodes[:4]) if nodes else "-",
                pygame.Rect(rect.x + 112, y, rect.width - 126, 24),
                COLOR_TEXT_PRIMARY,
                size=8,
            )
            y += 23
        if y + 18 < rect.bottom:
            draw_text_fit(surface, f"Xung đột ràng buộc: {len(conflicts) if isinstance(conflicts, list) else 0}", pygame.Rect(rect.x + 14, y, rect.width - 28, 18), COLOR_TEXT_ERROR if conflicts else COLOR_TEXT_SUCCESS, size=9, bold=True)
            y += 20
        if conflicts and y + 22 < rect.bottom:
            self._draw_wrapped_text(
                surface,
                str(conflicts[0]),
                pygame.Rect(rect.x + 14, y, rect.width - 28, rect.bottom - y - 6),
                COLOR_TEXT_ERROR,
                size=8,
            )

    def _zone_rows(self, assignments: dict) -> list[tuple[str, list[str]]]:
        zones = ["User Zone", "DMZ", "Server Zone", "Quarantine Zone"]
        return [(zone, [node for node, value in assignments.items() if value == zone]) for zone in zones]

    def _domain_removal_text(self, removed: object) -> str:
        if not isinstance(removed, dict) or not removed:
            return "-"
        parts = []
        for node, values in list(removed.items())[:2]:
            if isinstance(values, list):
                parts.append(f"{node}: {', '.join(values[:2])}")
            else:
                parts.append(f"{node}: {values}")
        if len(removed) > 2:
            parts.append(f"+{len(removed) - 2}")
        return "; ".join(parts)

    def _cost_text(self, value: object) -> str:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return "-"
        if numeric == float("inf"):
            return "inf"
        if numeric.is_integer():
            return str(int(numeric))
        return f"{numeric:.2f}"

    def _neighbor_summary(self, rows: object) -> str:
        if not isinstance(rows, list) or not rows:
            return "-"
        parts: list[str] = []
        for row in rows[:3]:
            if isinstance(row, dict):
                parts.append(f"{row.get('node')}:{self._cost_text(row.get('heuristic'))}")
        if len(rows) > 3:
            parts.append(f"+{len(rows) - 3}")
        return ", ".join(parts) if parts else "-"

    def _best_neighbor_text(self, rows: object) -> str:
        if not isinstance(rows, list) or not rows:
            return "-"
        dict_rows = [row for row in rows if isinstance(row, dict)]
        if not dict_rows:
            return "-"
        best = min(dict_rows, key=lambda row: float(row.get("heuristic", float("inf"))))
        return f"{best.get('node')} h={self._cost_text(best.get('heuristic'))}"

    def _decision_text(self, data: dict) -> str:
        accepted = data.get("accepted")
        reason = str(data.get("reason") or "")
        if accepted is True:
            return "-> chọn"
        if accepted is False and data.get("chosen_neighbor"):
            return "-> đang xét"
        if reason == "goal":
            return "đã tới đích"
        return ""

    def _reason_text(self, reason: str) -> str:
        labels = {
            "goal": "Đã tới node mục tiêu.",
            "better": "Ứng viên có h thấp hơn node hiện tại.",
            "not-better": "Ứng viên không cải thiện h.",
            "first-lower-heuristic": "Chọn láng giềng đầu tiên có h thấp hơn.",
            "lowest-neighbor-heuristic": "Chọn láng giềng có h thấp nhất.",
            "scan-all-neighbors": "Đã quét toàn bộ láng giềng để tìm h tốt nhất.",
            "local-optimum": "Không còn láng giềng nào có h thấp hơn.",
            "max-steps": "Dừng vì đạt giới hạn bước.",
            "lower-heuristic": "Chấp nhận vì h giảm.",
            "probabilistic-worse": "Chấp nhận bước xấu theo xác suất nhiệt độ.",
            "stopped-before-goal": "Dừng trước khi tới goal.",
        }
        return labels.get(reason, reason or "-")

    def _zone_short_list(self, values: object) -> str:
        if not isinstance(values, list) or not values:
            return "-"
        labels = {
            "User Zone": "User",
            "DMZ": "DMZ",
            "Server Zone": "Server",
            "Quarantine Zone": "Quarantine",
        }
        return ", ".join(labels.get(str(value), str(value)) for value in values[:4])

    def _candidate_text(self, data: dict) -> str:
        idx = data.get("candidate_index")
        total = data.get("candidate_total")
        if idx and total:
            return f"{idx}/{total}: "
        return ""

    def _draw_defense_result(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        data: dict,
        status_color: tuple[int, int, int],
        status_label: str,
    ) -> None:
        protected = data.get("protected_nodes", [])
        protected_text = ", ".join(protected[:3]) if isinstance(protected, list) else str(protected)
        config = data.get("defense_config")
        upgraded = getattr(config, "upgraded_nodes", []) if config else []
        upgraded_text = ", ".join(upgraded[:3]) if upgraded else "-"
        rows = [
            ("Mô phỏng", "Tối ưu phòng thủ"),
            ("DefenseValue", f"{data.get('defense_value', '-')} (cao tốt)"),
            ("RiskCost", f"{data.get('risk_cost', '-')} (thấp tốt)"),
            ("Chặn/Mở", f"{data.get('blocked_paths', '-')}/{data.get('open_paths', '-')}"),
            ("Nâng cấp", upgraded_text),
            ("Bảo vệ", protected_text or "-"),
            ("Trạng thái", status_label),
        ]
        y = rect.y + 36
        label_w = 112
        for label, value in rows[:6]:
            row_h = 16
            color = status_color if label == "Trạng thái" else COLOR_TEXT_PRIMARY
            draw_text_fit(surface, label + ":", pygame.Rect(rect.x + 14, y, label_w, row_h), COLOR_TEXT_PRIMARY, size=8, bold=True)
            draw_text_fit(surface, value, pygame.Rect(rect.x + 14 + label_w, y, rect.width - label_w - 28, row_h), color, size=8)
            y += row_h

    def _draw_defense_summary(self, surface: pygame.Surface, rect: pygame.Rect, data: dict) -> None:
        config = data.get("defense_config")
        rows = [
            ("FW chặn tại", getattr(config, "firewall_nodes", []), COLOR_TEXT_WARNING),
            ("IDS giám sát", getattr(config, "ids_nodes", []), (90, 170, 255)),
            ("UP tăng bảo mật", getattr(config, "upgraded_nodes", []), COLOR_TEXT_SUCCESS),
        ]
        y = rect.y + 36
        for label, nodes, color in rows:
            node_text = ", ".join(nodes) if nodes else "-"
            draw_text_fit(surface, label + ":", pygame.Rect(rect.x + 14, y, 112, 18), color, size=7, bold=True)
            self._draw_wrapped_text(
                surface,
                node_text,
                pygame.Rect(rect.x + 128, y, rect.width - 142, 22),
                COLOR_TEXT_PRIMARY,
                size=7,
            )
            y += 23

        draw_text_fit(surface, "Đỏ đứt: bị FW chặn", pygame.Rect(rect.x + 14, y + 2, rect.width - 28, 16), COLOR_TEXT_ERROR, size=7, bold=True)
        draw_text_fit(surface, "Xanh: đường còn mở", pygame.Rect(rect.x + 14, y + 18, rect.width - 28, 16), COLOR_TEXT_SUCCESS, size=7, bold=True)
        y += 36
        blocked_sample = self._sample_path_text(data.get("blocked_path_samples"))
        open_sample = self._sample_path_text(data.get("open_path_samples"))
        blocked_reason = self._blocked_reason(data)
        if blocked_sample and y + 20 < rect.bottom:
            draw_text_fit(surface, "Mẫu chặn:", pygame.Rect(rect.x + 14, y, 78, 16), COLOR_TEXT_ERROR, size=7, bold=True)
            self._draw_wrapped_text(
                surface,
                f"{blocked_sample} ({blocked_reason})",
                pygame.Rect(rect.x + 92, y, rect.width - 106, 28),
                COLOR_TEXT_PRIMARY,
                size=7,
            )
        if open_sample and y + 48 < rect.bottom:
            draw_text_fit(surface, "Mẫu mở:", pygame.Rect(rect.x + 14, y + 28, 78, 16), COLOR_TEXT_SUCCESS, size=7, bold=True)
            self._draw_wrapped_text(
                surface,
                open_sample,
                pygame.Rect(rect.x + 92, y + 28, rect.width - 106, 28),
                COLOR_TEXT_PRIMARY,
                size=7,
            )

    def _sample_path_text(self, paths: object) -> str:
        if not isinstance(paths, list) or not paths:
            return ""
        first = paths[0]
        if not isinstance(first, list) or not first:
            return ""
        return " -> ".join(str(node_id) for node_id in first[:6])

    def _blocked_reason(self, data: dict) -> str:
        config = data.get("defense_config")
        firewalls = set(getattr(config, "firewall_nodes", [])) if config else set()
        paths = data.get("blocked_path_samples")
        if isinstance(paths, list) and paths and isinstance(paths[0], list):
            for node_id in paths[0][1:-1]:
                if node_id in firewalls:
                    return f"qua FW {node_id}"
        return "qua Firewall"

    def _draw_compare(self, surface: pygame.Surface, compare_results: list[AlgorithmResult]) -> None:
        if any(result.metrics.extra.get("local_search_mode") == "heuristic_path" for result in compare_results):
            self._draw_heuristic_local_compare(surface, compare_results)
            return
        if any(result.metrics.extra.get("defense_config") for result in compare_results):
            self._draw_local_search_compare(surface, compare_results)
            return
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

    def _draw_heuristic_local_compare(self, surface: pygame.Surface, compare_results: list[AlgorithmResult]) -> None:
        title = get_font(13, bold=True).render("SO SÁNH LOCAL SEARCH", True, (116, 195, 255))
        surface.blit(title, (self.rect.x + 14, self.rect.y + 12))
        headers = ["Thuật toán", "Đạt", "PathCost", "h cuối", "Bước", "Đường đi"]
        widths = [142, 44, 76, 70, 52, 230]
        x = self.rect.x + 14
        y = self.rect.y + 42
        font_b = get_font(9, bold=True)
        font = get_font(9)
        for header, width in zip(headers, widths):
            surface.blit(font_b.render(header, True, COLOR_TEXT_SECONDARY), (x, y))
            x += width
        y += 24
        for result in compare_results[:6]:
            x = self.rect.x + 14
            metrics = result.metrics
            extra = metrics.extra
            path = " -> ".join(metrics.path) if metrics.path else "-"
            values = [
                algo_label(metrics.algorithm),
                "Có" if metrics.success else "Không",
                self._cost_text(metrics.total_cost),
                self._cost_text(extra.get("final_heuristic", extra.get("current_heuristic"))),
                str(metrics.num_steps),
                path,
            ]
            status_color = COLOR_TEXT_SUCCESS if metrics.success else COLOR_TEXT_ERROR
            for value, width in zip(values, widths):
                color = status_color if value in ("Có", "Không") else COLOR_TEXT_PRIMARY
                surface.blit(font.render(str(value)[:24], True, color), (x, y))
                x += width
            y += 22

    def _draw_local_search_compare(self, surface: pygame.Surface, compare_results: list[AlgorithmResult]) -> None:
        title = get_font(13, bold=True).render("SO SÁNH LOCAL SEARCH", True, (116, 195, 255))
        surface.blit(title, (self.rect.x + 14, self.rect.y + 12))
        headers = ["Thuật toán", "Đạt", "Defense", "Risk", "Chặn/Mở", "Lặp", "Worse", "ms"]
        widths = [142, 44, 78, 62, 74, 48, 58, 64]
        x = self.rect.x + 14
        y = self.rect.y + 42
        font_b = get_font(9, bold=True)
        font = get_font(9)
        for header, width in zip(headers, widths):
            surface.blit(font_b.render(header, True, COLOR_TEXT_SECONDARY), (x, y))
            x += width
        y += 24
        for result in compare_results[:6]:
            x = self.rect.x + 14
            metrics = result.metrics
            extra = metrics.extra
            blocked = extra.get("blocked_paths", "-")
            open_paths = extra.get("open_paths", "-")
            values = [
                algo_label(metrics.algorithm),
                "Có" if metrics.success else "Không",
                str(extra.get("defense_value", "-")),
                str(extra.get("risk_cost", "-")),
                f"{blocked}/{open_paths}",
                str(metrics.num_steps),
                str(extra.get("accepted_worse_moves", "-")),
                f"{metrics.time_ms:.1f}",
            ]
            status_color = COLOR_TEXT_SUCCESS if metrics.success else COLOR_TEXT_ERROR
            for value, width in zip(values, widths):
                color = status_color if value in ("Có", "Không") else COLOR_TEXT_PRIMARY
                surface.blit(font.render(value[:16], True, color), (x, y))
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
