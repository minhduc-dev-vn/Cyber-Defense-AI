"""
stats_view.py - Hiển thị thông tin chi tiết: Right Panel (Node Info, Legend) và Bottom Panel (Kết quả, Đường đi, Frontier).
"""
from __future__ import annotations

from typing import Optional

import pygame

from core.models import AlgorithmMetrics, AlgorithmResult, StepEvent
from core.utils import format_cost
from core.state import AppState
from ui.theme import (
    get_font,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_SUCCESS,
    COLOR_TEXT_ERROR,
    COLOR_TEXT_WARNING,
    COLOR_NODE_HACKER,
    COLOR_NODE_SERVER,
    COLOR_FRONTIER,
    COLOR_EXPLORED,
    COLOR_CURRENT,
    COLOR_FINAL_PATH,
    COLOR_BG,
)


class RightPanelView:
    """Panel cột phải: THÔNG TIN NODE và CHÚ THÍCH."""

    def __init__(self, rect: pygame.Rect, app_state: AppState) -> None:
        self.rect = rect
        self.app_state = app_state

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, COLOR_PANEL_BG, self.rect)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, self.rect, 1)

        font_title = get_font(13, bold=True)
        font_b = get_font(12, bold=True)
        font = get_font(12)

        # THÔNG TIN NODE
        y = self.rect.y + 16
        x = self.rect.x + 16
        
        t1 = font_title.render("THÔNG TIN NODE", True, (140, 180, 240))
        surface.blit(t1, (x, y))
        y += 30

        node_id = self.app_state.selected_node
        if not node_id:
            txt = font.render("Chọn một node trên bản đồ", True, COLOR_TEXT_SECONDARY)
            txt2 = font.render("để xem thông tin chi tiết.", True, COLOR_TEXT_SECONDARY)
            surface.blit(txt, (x, y))
            surface.blit(txt2, (x, y + 20))
            y += 100
        else:
            # Lấy info node từ map_data
            node = None
            if self.app_state.map_data:
                node = self.app_state.map_data.graph.get_node(node_id)
            
            if node:
                from ui.theme import get_node_color
                color = get_node_color(node.kind, "default")
                pygame.draw.circle(surface, color, (x + 15, y + 15), 15)
                n_surf = get_font(16, bold=True).render(node.id, True, COLOR_TEXT_PRIMARY)
                surface.blit(n_surf, (x + 40, y + 5))
                y += 45
                
                lines = [
                    ("Loại:", f"{node.kind.upper()}"),
                    ("Mức bảo mật:", f"{node.security_level} / 10"),
                    ("Trạng thái:", "Bị hacker kiểm soát" if node.id == self.app_state.map_data.hacker_start else "An toàn"),
                    ("Thuộc Zone:", str(node.zone)),
                    ("Đang được IDS giám sát:", "Có" if node.monitored else "Không"),
                ]
                for lbl, val in lines:
                    surface.blit(font.render(lbl, True, COLOR_TEXT_SECONDARY), (x, y))
                    val_color = COLOR_TEXT_ERROR if "Bị hacker" in val else COLOR_TEXT_PRIMARY
                    surface.blit(font_b.render(val, True, val_color), (x + int(self.rect.width * 0.55), y))
                    y += 24
                
                y += 10
                surface.blit(font.render("Kết nối:", True, COLOR_TEXT_SECONDARY), (x, y))
                y += 20
                for edge in self.app_state.map_data.graph.get_all_edges():
                    if edge.source == node.id or edge.target == node.id:
                        other = edge.target if edge.source == node.id else edge.source
                        surface.blit(font.render(f"• {other} (chi phí: {edge.base_cost:.0f})", True, COLOR_TEXT_PRIMARY), (x + 10, y))
                        y += 20
            else:
                surface.blit(font.render(f"Node: {node_id}", True, COLOR_TEXT_PRIMARY), (x, y))
                y += 100

        # Separator
        y += 30
        pygame.draw.line(surface, COLOR_PANEL_BORDER, (x, y), (self.rect.right - 16, y), 1)
        y += 20

        # CHÚ THÍCH
        t2 = font_title.render("CHÚ THÍCH", True, (140, 180, 240))
        surface.blit(t2, (x, y))
        y += 30

        items = [
            (COLOR_NODE_HACKER, "Hacker (Vị trí bắt đầu)"),
            ((40, 100, 180), "Node an toàn"),
            ((240, 120, 30), "Firewall"),
            ((230, 180, 40), "IDS"),
            (COLOR_NODE_SERVER, "Server / Database"),
            (COLOR_CURRENT, "Đang xét"),
            (COLOR_FRONTIER, "Trong Frontier"),
            (COLOR_EXPLORED, "Đã duyệt / Bị khóa"),
        ]
        for color, label in items:
            pygame.draw.circle(surface, color, (x + 8, y + 8), 8)
            lbl_surf = font.render(label, True, COLOR_TEXT_SECONDARY)
            surface.blit(lbl_surf, (x + 25, y))
            y += 22


class BottomPanelView:
    """Panel dưới: Frontier, Kết quả và Đường đi."""

    def __init__(self, frontier_rect: pygame.Rect, result_rect: pygame.Rect) -> None:
        self.f_rect = frontier_rect
        self.r_rect = result_rect

    def draw(
        self,
        surface: pygame.Surface,
        step: Optional[StepEvent],
        metrics: Optional[AlgorithmMetrics],
        status: str,
        compare_results: Optional[list[AlgorithmResult]] = None,
    ) -> None:
        # Nền frontier panel
        pygame.draw.rect(surface, COLOR_PANEL_BG, self.f_rect)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, self.f_rect, 1)

        # Nền result panel
        pygame.draw.rect(surface, COLOR_PANEL_BG, self.r_rect)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, self.r_rect, 1)

        font = get_font(12)
        font_b = get_font(12, bold=True)
        font_title = get_font(13, bold=True)

        # ─── FRONTIER PANEL ───
        fy = self.f_rect.y + 16
        fx = self.f_rect.x + 16
        
        surface.blit(font_b.render("Frontier", True, (120, 150, 200)), (fx, fy))
        frontier_str = f"[{', '.join(step.frontier)}]" if step and step.frontier else "[]"
        if len(frontier_str) > 35: frontier_str = frontier_str[:32] + "...]"
        surface.blit(font.render(frontier_str, True, COLOR_TEXT_WARNING), (fx + 80, fy))
        
        fy += 40
        surface.blit(font_b.render("Explored", True, (120, 150, 200)), (fx, fy))
        explored_str = f"[{', '.join(step.explored)}]" if step and step.explored else "[]"
        if len(explored_str) > 35: explored_str = explored_str[:32] + "...]"
        surface.blit(font.render(explored_str, True, COLOR_TEXT_SECONDARY), (fx + 80, fy))
        
        fy += 40
        surface.blit(font_b.render("Current", True, (120, 150, 200)), (fx, fy))
        curr_str = str(step.current_node) if step and step.current_node else "None"
        surface.blit(font.render(curr_str, True, COLOR_TEXT_ERROR if status == 'failure' else COLOR_TEXT_SUCCESS if status == 'success' else COLOR_TEXT_PRIMARY), (fx + 80, fy))

        # ─── RESULT PANEL ───
        rx = self.r_rect.x + 16
        ry = self.r_rect.y + 16
        
        surface.blit(font_title.render("KẾT QUẢ", True, (140, 180, 240)), (rx, ry))
        
        # So sánh nhóm
        if compare_results:
            cy = ry + 30
            surface.blit(font_b.render("Alg", True, COLOR_TEXT_SECONDARY), (rx, cy))
            surface.blit(font_b.render("OK", True, COLOR_TEXT_SECONDARY), (rx + max(60, int(self.r_rect.width * 0.15)), cy))
            surface.blit(font_b.render("Cost", True, COLOR_TEXT_SECONDARY), (rx + max(100, int(self.r_rect.width * 0.28)), cy))
            surface.blit(font_b.render("Expanded", True, COLOR_TEXT_SECONDARY), (rx + max(160, int(self.r_rect.width * 0.45)), cy))
            cy += 20
            for res in compare_results[:4]:
                m = res.metrics
                surface.blit(font.render(m.algorithm, True, COLOR_TEXT_PRIMARY), (rx, cy))
                surface.blit(font.render("Y" if m.success else "N", True, COLOR_TEXT_SUCCESS if m.success else COLOR_TEXT_ERROR), (rx + max(60, int(self.r_rect.width * 0.15)), cy))
                surface.blit(font.render(format_cost(m.total_cost), True, COLOR_TEXT_PRIMARY), (rx + max(100, int(self.r_rect.width * 0.28)), cy))
                surface.blit(font.render(str(m.nodes_expanded), True, COLOR_TEXT_PRIMARY), (rx + max(160, int(self.r_rect.width * 0.45)), cy))
                cy += 20
            return

        status_colors = {
            "ready": COLOR_TEXT_SECONDARY,
            "running": COLOR_TEXT_WARNING,
            "paused": (100, 180, 255),
            "success": COLOR_TEXT_SUCCESS,
            "failure": COLOR_TEXT_ERROR,
        }
        status_texts = {
            "ready": "Sẵn sàng",
            "running": "Đang chạy",
            "paused": "Tạm dừng",
            "success": "Thành công",
            "failure": "Thất bại",
        }

        algo_name = step.algorithm if step else (metrics.algorithm if metrics else "-")
        exp = str(step.nodes_expanded if step else (metrics.nodes_expanded if metrics else 0))
        max_f = str(step.max_frontier_size if step else (metrics.max_frontier_size if metrics else 0))
        cost = format_cost(step.total_cost if step else (metrics.total_cost if metrics else 0))
        time_s = f"{(metrics.time_ms / 1000):.3f}s" if metrics else "-"
        st_text = status_texts.get(status, status)
        st_color = status_colors.get(status, COLOR_TEXT_PRIMARY)

        lines = [
            ("Thuật toán:", algo_name),
            ("Số node mở rộng:", exp),
            ("Max frontier:", max_f),
            ("Chi phí đường đi:", cost),
            ("Thời gian chạy:", time_s),
            ("Trạng thái:", (st_text, st_color)),
        ]
        
        ly = ry + 30
        for lbl, val in lines:
            surface.blit(font.render(lbl, True, COLOR_TEXT_SECONDARY), (rx, ly))
            if isinstance(val, tuple):
                v_txt, v_col = val
                surface.blit(font_b.render(v_txt, True, v_col), (rx + max(120, int(self.r_rect.width * 0.25)), ly))
            else:
                surface.blit(font_b.render(val, True, COLOR_TEXT_PRIMARY), (rx + max(120, int(self.r_rect.width * 0.25)), ly))
            ly += 22

        # ĐƯỜNG ĐI
        px = rx + max(220, int(self.r_rect.width * 0.48))
        py = ry
        surface.blit(font_title.render("ĐƯỜNG ĐI", True, (140, 180, 240)), (px, py))
        
        path = step.path if step else (metrics.path if metrics else [])
        if path:
            path_str = " → ".join(path)
            if len(path_str) > 60: path_str = path_str[:57] + "..."
            surface.blit(font_b.render(path_str, True, COLOR_TEXT_SUCCESS), (px, py + 30))
        else:
            surface.blit(font.render("Chưa có đường đi.", True, COLOR_TEXT_SECONDARY), (px, py + 30))

