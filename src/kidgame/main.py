from kidgame.ui.app import run_app
from kidgame.ui.launcher import resolve_display_settings


def main() -> None:
    display = resolve_display_settings()
    if display is None:
        return
    run_app(display)


if __name__ == "__main__":
    main()
