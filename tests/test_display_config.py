from __future__ import annotations

from kidgame.ui.display_config import (
    preset_by_id,
    save_launcher_config,
    settings_from_saved_config,
)


def test_preset_by_id() -> None:
    s = preset_by_id("window_960")
    assert s is not None
    assert s.width == 960 and s.height == 720 and not s.fullscreen


def test_save_and_load_roundtrip(tmp_path, monkeypatch) -> None:
    import kidgame.ui.display_config as dc

    monkeypatch.setattr(dc, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(dc, "CONFIG_PATH", tmp_path / "display.json")
    save_launcher_config(ask_every_time=False, preset_id="window_1280")
    cfg = dc.load_launcher_config()
    assert cfg["ask_every_time"] is False
    loaded = settings_from_saved_config(cfg)
    assert loaded is not None
    assert loaded.width == 1280 and loaded.fullscreen is False
