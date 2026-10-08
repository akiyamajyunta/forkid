"""ゲーム画面用画像素材の読み込み。"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pygame


def _ui_assets_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "assets" / "ui"


def _load_image(path: Path, *, alpha: bool = True) -> pygame.Surface | None:
    if not path.is_file():
        return None
    try:
        img = pygame.image.load(str(path))
        if pygame.display.get_surface():
            return img.convert_alpha() if alpha else img.convert()
        return img
    except pygame.error:
        return None


def _is_overlay_brown(r: int, g: int, b: int) -> bool:
    return 70 <= r <= 120 and 55 <= g <= 105 and 55 <= b <= 105


def _prepare_overlay(img: pygame.Surface) -> pygame.Surface:
    """黒と茶色の横帯を透過（赤帯はコード側で描画）。"""
    s = img.convert_alpha()
    w, h = s.get_size()
    y_band_lo, y_band_hi = int(h * 0.48), int(h * 0.88)
    for y in range(h):
        for x in range(w):
            r, g, b, a = s.get_at((x, y))
            if r + g + b < 28:
                s.set_at((x, y), (0, 0, 0, 0))
            elif y_band_lo <= y <= y_band_hi and _is_overlay_brown(r, g, b):
                s.set_at((x, y), (0, 0, 0, 0))
    return s


def _load_overlay(path: Path) -> pygame.Surface | None:
    if not path.is_file():
        return None
    try:
        return _prepare_overlay(pygame.image.load(str(path)))
    except pygame.error:
        return None


@dataclass(frozen=True, slots=True)
class GameUiAssets:
    bg_pattern: pygame.Surface | None
    bg_overlay: pygame.Surface | None
    main_frame: pygame.Surface | None
    question_panel: pygame.Surface | None
    option_bar: pygame.Surface | None
    option_bar_selected: pygame.Surface | None
    status_panel: pygame.Surface | None

    def blit_stretched(
        self,
        surface: pygame.Surface,
        target: pygame.Surface,
        rect: pygame.Rect,
    ) -> None:
        if surface is None:
            return
        img = pygame.transform.smoothscale(
            surface, (max(1, rect.width), max(1, rect.height))
        )
        target.blit(img, rect.topleft)


@lru_cache(maxsize=1)
def load_game_ui_assets() -> GameUiAssets:
    base = _ui_assets_dir()
    return GameUiAssets(
        bg_pattern=_load_image(base / "bg_pattern.jpg", alpha=False),
        bg_overlay=_load_overlay(base / "bg_overlay.png"),
        main_frame=_load_image(base / "main_frame.png"),
        question_panel=_load_image(base / "question_panel.png"),
        option_bar=_load_image(base / "option_bar.png"),
        option_bar_selected=_load_image(base / "option_bar_selected.png"),
        status_panel=_load_image(base / "status_panel.png"),
    )
