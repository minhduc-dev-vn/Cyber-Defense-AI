"""Render demo screenshots for Phase 8 delivery."""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pygame

from ui import theme
from ui.app import App


def drive_to_terminal(app: App, max_steps: int = 200) -> None:
    app._on_start()
    for _ in range(max_steps):
        if app.state.run_state.status != "running":
            return
        app._do_one_step()
    raise RuntimeError("Demo run did not finish within max_steps")


def render(size: tuple[int, int], output: Path) -> None:
    theme._font_cache.clear()
    app = App()
    app.screen = pygame.display.set_mode(size)
    app.layout.update(*size)
    app._rebuild_views()
    drive_to_terminal(app)
    app._toast = ""
    app._toast_until = 0.0
    app.render_frame()
    pygame.image.save(app.screen, output)
    theme._font_cache.clear()
    pygame.quit()


def main() -> None:
    out_dir = ROOT / "screenshots"
    out_dir.mkdir(exist_ok=True)
    for size in ((1366, 768), (1920, 1080)):
        render(size, out_dir / f"demo_{size[0]}x{size[1]}.png")
    print("Saved demo screenshots to screenshots/")


if __name__ == "__main__":
    main()
