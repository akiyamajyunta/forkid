from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from kidgame.ui.display_config import (
    DISPLAY_PRESETS,
    DisplaySettings,
    load_launcher_config,
    preset_by_id,
    save_launcher_config,
    settings_from_saved_config,
)


def resolve_display_settings() -> DisplaySettings | None:
    """起動ダイアログで表示設定を決定。キャンセル時は None。"""
    config = load_launcher_config()
    if not config.get("ask_every_time", True):
        saved = settings_from_saved_config(config)
        if saved:
            return saved
    return _show_launcher_dialog(config)


def _show_launcher_dialog(config: dict) -> DisplaySettings | None:
    default_id = str(config.get("preset_id", "window_960"))
    ask_default = bool(config.get("ask_every_time", True))
    result: DisplaySettings | None = None

    root = tk.Tk()
    root.title("なぞなぞ大作戦")
    root.resizable(False, False)
    root.attributes("-topmost", True)

    frame = ttk.Frame(root, padding=16)
    frame.grid(row=0, column=0, sticky="nsew")

    ttk.Label(frame, text="ウィンドウモードを選択してください").grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
    )

    choice = tk.StringVar(value=default_id)
    for row, (pid, label, _w, _h, _fs) in enumerate(DISPLAY_PRESETS, start=1):
        ttk.Radiobutton(frame, text=label, variable=choice, value=pid).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=2
        )

    ask_var = tk.BooleanVar(value=ask_default)
    ttk.Checkbutton(frame, text="起動時に毎回聞く", variable=ask_var).grid(
        row=len(DISPLAY_PRESETS) + 1, column=0, columnspan=2, sticky="w", pady=(12, 8)
    )

    def on_start() -> None:
        nonlocal result
        preset = preset_by_id(choice.get())
        if preset is None:
            return
        save_launcher_config(
            ask_every_time=ask_var.get(),
            preset_id=preset.preset_id,
        )
        result = preset
        root.destroy()

    def on_close() -> None:
        root.destroy()

    btn = ttk.Button(frame, text="ゲーム起動", command=on_start, width=16)
    btn.grid(row=len(DISPLAY_PRESETS) + 2, column=0, columnspan=2, pady=(8, 0))

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"+{x}+{y}")
    root.mainloop()
    return result
