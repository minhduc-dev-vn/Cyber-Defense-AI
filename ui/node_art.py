"""Reusable node artwork for dashboard panels."""
from __future__ import annotations

import math

import pygame

from ui.theme import get_font


def infer_node_kind(node_id: str) -> str:
    name = node_id.lower()
    if "firewall" in name:
        return "firewall"
    if "ids" in name:
        return "ids"
    if "server" in name:
        return "server"
    if "database" in name or "db" == name:
        return "database"
    if "router" in name:
        return "router"
    if "switch" in name:
        return "switch"
    if name.startswith("pc"):
        return "pc"
    return "pc"


def draw_network_node(
    surface: pygame.Surface,
    kind: str,
    center: tuple[int, int],
    radius: int,
    color: tuple[int, int, int],
    *,
    hacker: bool = False,
    selected: bool = False,
    hovered: bool = False,
) -> None:
    cx, cy = center
    _draw_shell(surface, cx, cy, radius, color, hacker=hacker, selected=selected, hovered=hovered)
    _draw_icon(surface, kind, cx, cy, radius, color)


def _draw_shell(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    r: int,
    color: tuple[int, int, int],
    *,
    hacker: bool,
    selected: bool,
    hovered: bool,
) -> None:
    glow_size = (r + 18) * 2
    glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
    glow_center = (glow_size // 2, glow_size // 2)
    for radius, alpha in ((r + 15, 28), (r + 10, 42), (r + 5, 58)):
        pygame.draw.circle(glow, (*color, alpha), glow_center, radius)
    surface.blit(glow, (cx - glow_size // 2, cy - glow_size // 2))

    if hacker:
        _draw_dashed_circle(surface, cx, cy, r + 10, color, 2)
        _draw_dashed_circle(surface, cx, cy, r + 16, color, 1)

    if selected:
        pygame.draw.circle(surface, (250, 255, 255), (cx, cy), r + 8, 3)
    elif hovered:
        pygame.draw.circle(surface, (210, 232, 255), (cx, cy), r + 6, 2)

    pygame.draw.circle(surface, (5, 14, 25), (cx, cy), r + 5)
    pygame.draw.circle(surface, (13, 29, 43), (cx, cy), r)
    pygame.draw.circle(surface, color, (cx, cy), r + 1, 3)
    pygame.draw.circle(surface, (230, 244, 255), (cx, cy), max(4, r - 5), 1)


def _draw_dashed_circle(
    surface: pygame.Surface,
    cx: int,
    cy: int,
    radius: int,
    color: tuple[int, int, int],
    width: int,
) -> None:
    rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
    for i in range(0, 360, 28):
        pygame.draw.arc(surface, color, rect, math.radians(i), math.radians(i + 16), width)


def _scale(radius: int) -> float:
    return max(0.52, radius / 29)


def _rect(cx: int, cy: int, x: float, y: float, w: float, h: float, s: float) -> pygame.Rect:
    return pygame.Rect(int(cx + x * s), int(cy + y * s), max(1, int(w * s)), max(1, int(h * s)))


def _point(cx: int, cy: int, x: float, y: float, s: float) -> tuple[int, int]:
    return int(cx + x * s), int(cy + y * s)


def _draw_icon(surface: pygame.Surface, kind: str, cx: int, cy: int, r: int, color: tuple[int, int, int]) -> None:
    icon_color = (235, 248, 255)
    accent = color
    s = _scale(r)
    lw = max(1, int(3 * s))
    thin = max(1, int(2 * s))

    if kind == "pc":
        pygame.draw.rect(surface, icon_color, _rect(cx, cy, -12, -10, 24, 16, s), lw, border_radius=max(1, int(2 * s)))
        pygame.draw.line(surface, icon_color, _point(cx, cy, 0, 6, s), _point(cx, cy, 0, 13, s), lw)
        pygame.draw.line(surface, icon_color, _point(cx, cy, -10, 14, s), _point(cx, cy, 10, 14, s), lw)
    elif kind == "switch":
        pygame.draw.rect(surface, icon_color, _rect(cx, cy, -15, -8, 30, 16, s), lw, border_radius=max(1, int(3 * s)))
        for px in (-8, 0, 8):
            pygame.draw.circle(surface, accent, _point(cx, cy, px, 0, s), max(2, int(3 * s)))
        pygame.draw.line(surface, icon_color, _point(cx, cy, -18, 0, s), _point(cx, cy, -15, 0, s), thin)
        pygame.draw.line(surface, icon_color, _point(cx, cy, 15, 0, s), _point(cx, cy, 18, 0, s), thin)
    elif kind == "router":
        for ox, oy in ((-9, -9), (9, -9), (-9, 9), (9, 9)):
            pygame.draw.rect(surface, icon_color, _rect(cx, cy, ox - 5, oy - 5, 10, 10, s), thin, border_radius=max(1, int(2 * s)))
        pygame.draw.circle(surface, accent, (cx, cy), max(2, int(4 * s)))
        for x1, y1, x2, y2 in ((-4, 0, -14, -9), (4, 0, 14, -9), (-4, 0, -14, 9), (4, 0, 14, 9)):
            pygame.draw.line(surface, icon_color, _point(cx, cy, x1, y1, s), _point(cx, cy, x2, y2, s), thin)
    elif kind == "firewall":
        shield = [_point(cx, cy, x, y, s) for x, y in ((0, -16), (13, -10), (10, 9), (0, 17), (-10, 9), (-13, -10))]
        pygame.draw.polygon(surface, icon_color, shield)
        pygame.draw.polygon(surface, accent, shield, thin)
        pygame.draw.line(surface, accent, _point(cx, cy, 0, -8, s), _point(cx, cy, 0, 8, s), lw)
    elif kind == "ids":
        pygame.draw.circle(surface, icon_color, (cx, cy), max(5, int(14 * s)), thin)
        pygame.draw.circle(surface, accent, (cx, cy), max(2, int(5 * s)), thin)
        pygame.draw.line(surface, icon_color, _point(cx, cy, -10, 10, s), _point(cx, cy, 10, -10, s), thin)
        pygame.draw.polygon(surface, icon_color, [_point(cx, cy, 12, -12, s), _point(cx, cy, 5, -10, s), _point(cx, cy, 10, -5, s)])
    elif kind == "server":
        for i in range(3):
            rack = _rect(cx, cy, -14, -14 + i * 10, 28, 7, s)
            pygame.draw.rect(surface, icon_color, rack, thin, border_radius=max(1, int(2 * s)))
            pygame.draw.circle(surface, accent, (int(cx + 8 * s), rack.centery), max(1, int(2 * s)))
    elif kind == "database":
        pygame.draw.ellipse(surface, icon_color, _rect(cx, cy, -13, -15, 26, 10, s), thin)
        pygame.draw.line(surface, icon_color, _point(cx, cy, -13, -10, s), _point(cx, cy, -13, 12, s), thin)
        pygame.draw.line(surface, icon_color, _point(cx, cy, 13, -10, s), _point(cx, cy, 13, 12, s), thin)
        for y in (-1, 10):
            pygame.draw.arc(surface, icon_color, _rect(cx, cy, -13, y - 5, 26, 10, s), 0, math.pi, thin)
        pygame.draw.arc(surface, icon_color, _rect(cx, cy, -13, 7, 26, 10, s), math.pi, math.tau, thin)
    else:
        q = get_font(max(10, int(15 * s)), bold=True).render("?", True, icon_color)
        surface.blit(q, q.get_rect(center=(cx, cy)))
