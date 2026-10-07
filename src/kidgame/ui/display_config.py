from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

CONFIG_DIR = Path.home() / ".kidgame"
CONFIG_PATH = CONFIG_DIR / "display.json"

BASE_LAYOUT_W = 1024
BASE_LAYOUT_H = 600


@dataclass(frozen=True, slots=True)
class DisplaySettings:
    width: int
    height: int
    fullscreen: bool
    preset_id: str

    @classmethod
    def from_dict(cls, data: dict) -> DisplaySettings:
        return cls(
            width=int(data["width"]),
            height=int(data["height"]),
            fullscreen=bool(data["fullscreen"]),
            preset_id=str(data["preset_id"]),
        )


DISPLAY_PRESETS: tuple[tuple[str, str, int, int, bool], ...] = (
    ("fullscreen_640", "フルスクリーン(640×480)", 640, 480, True),
    ("window_640", "ウィンドウ(640×480)", 640, 480, False),
    ("window_960", "ウィンドウ(960×720)", 960, 720, False),
    ("window_1280", "ウィンドウ(1280×960)", 1280, 960, False),
)


def preset_by_id(preset_id: str) -> DisplaySettings | None:
    for pid, _label, w, h, fs in DISPLAY_PRESETS:
        if pid == preset_id:
            return DisplaySettings(w, h, fs, pid)
    return None


def load_launcher_config() -> dict:
    if not CONFIG_PATH.is_file():
        return {"ask_every_time": True, "preset_id": "window_960"}
    try:
        with CONFIG_PATH.open(encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {"ask_every_time": True, "preset_id": "window_960"}


def save_launcher_config(*, ask_every_time: bool, preset_id: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    preset = preset_by_id(preset_id)
    payload = {
        "ask_every_time": ask_every_time,
        "preset_id": preset_id,
    }
    if preset:
        payload["display"] = asdict(preset)
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def settings_from_saved_config(config: dict) -> DisplaySettings | None:
    if "display" in config and isinstance(config["display"], dict):
        return DisplaySettings.from_dict(config["display"])
    pid = config.get("preset_id", "window_960")
    return preset_by_id(str(pid))
