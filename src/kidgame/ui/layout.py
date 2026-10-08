from __future__ import annotations

from dataclasses import dataclass

from kidgame.ui.display_config import BASE_LAYOUT_H, BASE_LAYOUT_W


@dataclass(frozen=True, slots=True)
class ScreenLayout:
    """1024×600 基準の UI を任意解像度にスケール。"""

    width: int
    height: int

    @property
    def sx(self) -> float:
        return self.width / BASE_LAYOUT_W

    @property
    def sy(self) -> float:
        return self.height / BASE_LAYOUT_H

    @property
    def font_scale(self) -> float:
        return min(self.sx, self.sy)

    @property
    def status_w(self) -> int:
        return max(180, int(self.width * 0.28))

    @property
    def main_w(self) -> int:
        return self.width - self.status_w

    def x(self, value: int) -> int:
        return int(value * self.sx)

    def y(self, value: int) -> int:
        return int(value * self.sy)
