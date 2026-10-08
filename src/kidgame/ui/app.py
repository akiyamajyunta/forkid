from __future__ import annotations

import random
import time
from enum import StrEnum, auto

import pygame

from kidgame.data.loader import QuestionRepository
from kidgame.data.models import Difficulty
from kidgame.data.question_runtime import resolve_for_play
from kidgame.system.config import CORRECT_TO_CLEAR, RULES_BY_DIFFICULTY
from kidgame.system.game_session import GameSession, LossReason, SessionPhase
from kidgame.system.score_store import ScoreStore
from kidgame.ui.display_config import DisplaySettings
from kidgame.ui.game_assets import load_game_ui_assets
from kidgame.ui.game_sfx import (
    SCORE_BURST_COUNT,
    SCORE_BURST_INTERVAL_SEC,
    load_game_sfx,
    score_burst_duration_sec,
)
from kidgame.data.furigana import RubySegment, segments_or_reading_line
from kidgame.ui.draw_helpers import (
    blit_centered,
    draw_background_red_band,
    draw_game_container,
    draw_game_section,
    draw_option_bar,
    draw_panel,
    layout_option_row,
    scale_cover,
)
from kidgame.ui.status_sidebar import draw_status_sidebar
from kidgame.ui.fonts import FontSet
from kidgame.ui.input import GameAction, InputState
from kidgame.ui.layout import ScreenLayout
from kidgame.ui.option_labels import option_display_letter
from kidgame.ui.ruby_draw import (
    RUBY_MAIN_GAP,
    draw_text_with_furigana,
    measure_text_with_furigana,
)
from kidgame.ui.theme import (
    COLOR_BG,
    COLOR_CURSOR,
    COLOR_FURIGANA,
    COLOR_RIGHT,
    COLOR_RUBY,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_WRONG,
)


class AppScreen(StrEnum):
    TITLE = auto()
    HELP = auto()
    MODE = auto()
    GAME = auto()
    PAUSE = auto()
    RESULT = auto()


class KidgameApp:
    def __init__(self, display: DisplaySettings) -> None:
        pygame.init()
        flags = pygame.FULLSCREEN if display.fullscreen else 0
        self.layout = ScreenLayout(display.width, display.height)
        self.screen = pygame.display.set_mode(
            (display.width, display.height),
            flags,
        )
        pygame.display.set_caption("なぞなぞ大作戦")
        self.clock = pygame.time.Clock()
        load_game_ui_assets.cache_clear()
        self.fonts = FontSet(self.layout.font_scale)
        self.input_state = InputState()
        self.input_state.attach_joystick()
        self.repo = QuestionRepository.from_file()

        self.current = AppScreen.TITLE
        self.title_menu = 0  # 0=start, 1=help
        self.mode_cursor = 0
        self.modes = [Difficulty.EASY, Difficulty.NORMAL, Difficulty.HARD]
        self.session: GameSession | None = None
        self.running = True
        self.quit_modal_open = False
        self.quit_menu = 0
        self.ui_assets = load_game_ui_assets()
        self.sfx = load_game_sfx()
        self.score_store = ScoreStore.load()
        self._result_score_saved = False
        self._score_burst_start = 0.0
        self._score_burst_hit = 0
        self._score_countup_start = 0.0
        self._score_countup_from = 0
        self._score_countup_to = 0
        self._score_shown = 0

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self._open_quit_modal()

            actions = self.input_state.poll(events, dt)
            self._update(dt, actions)
            self._draw()
            pygame.display.flip()

        pygame.quit()

    def _quit_menu_choices(self) -> list[str]:
        if self.current in (AppScreen.GAME, AppScreen.PAUSE):
            return ["タイトルに戻る", "終了する", "キャンセル"]
        return ["終了する", "キャンセル"]

    def _open_quit_modal(self) -> None:
        self.quit_modal_open = True
        self.quit_menu = len(self._quit_menu_choices()) - 1

    def _close_quit_modal(self) -> None:
        self.quit_modal_open = False

    def _return_to_title_from_modal(self) -> None:
        self.session = None
        self._result_score_saved = False
        self.current = AppScreen.TITLE
        self.title_menu = 0
        self._close_quit_modal()

    def _split_cancel_actions(
        self, actions: list[GameAction]
    ) -> tuple[list[GameAction], bool]:
        cancelled = any(a is GameAction.CANCEL for a in actions)
        rest = [a for a in actions if a is not GameAction.CANCEL]
        return rest, cancelled

    def _update_quit_modal(self, actions: list[GameAction]) -> None:
        _, cancelled = self._split_cancel_actions(actions)
        if cancelled:
            self._close_quit_modal()
            return

        choices = self._quit_menu_choices()
        self.quit_menu = self._nav_vertical(actions, self.quit_menu, len(choices))
        for a in actions:
            if a is GameAction.CONFIRM:
                picked = choices[self.quit_menu]
                if picked == "タイトルに戻る":
                    self._return_to_title_from_modal()
                elif picked == "終了する":
                    self.running = False
                else:
                    self._close_quit_modal()

    def _update(self, dt: float, actions: list[GameAction]) -> None:
        if self.quit_modal_open:
            self._update_quit_modal(actions)
            self._tick_score_burst()
            self._tick_score_countup()
            return

        actions, cancelled = self._split_cancel_actions(actions)
        if cancelled:
            self._open_quit_modal()
            self._tick_score_burst()
            self._tick_score_countup()
            return

        if self.current is AppScreen.TITLE:
            self._update_title(actions)
        elif self.current is AppScreen.HELP:
            self._update_help(actions)
        elif self.current is AppScreen.MODE:
            self._update_mode(actions)
        elif self.current is AppScreen.GAME:
            self._update_game(dt, actions)
        elif self.current is AppScreen.PAUSE:
            self._update_pause(actions)
        elif self.current is AppScreen.RESULT:
            self._update_result(actions)

        self._tick_score_burst()
        self._tick_score_countup()

    def _nav_vertical(self, actions: list[GameAction], cursor: int, count: int) -> int:
        if count <= 1:
            return cursor
        prev = cursor
        for a in actions:
            if a is GameAction.UP:
                cursor = (cursor - 1) % count
            elif a is GameAction.DOWN:
                cursor = (cursor + 1) % count
        if cursor != prev:
            self.sfx.play_cursor_move()
        return cursor

    def _move_game_cursor(self, session: GameSession, delta: int) -> None:
        before = session.cursor
        session.move_cursor(delta)
        if session.cursor != before:
            self.sfx.play_cursor_move()

    def _start_score_burst(self, session: GameSession) -> None:
        gained = session.last_points_gained
        self._score_burst_start = time.monotonic()
        self._score_burst_hit = 0
        if gained <= 0:
            return
        self._score_countup_from = session.score - gained
        self._score_countup_to = session.score
        self._score_shown = self._score_countup_from
        self._score_countup_start = self._score_burst_start

    def _tick_score_countup(self) -> None:
        if self._score_countup_start <= 0.0:
            return
        elapsed = time.monotonic() - self._score_countup_start
        duration = score_burst_duration_sec()
        gained = self._score_countup_to - self._score_countup_from
        if elapsed >= duration:
            self._score_shown = self._score_countup_to
            self._score_countup_start = 0.0
            return
        cap = self._score_countup_from + int(gained * elapsed / duration)
        cap = min(self._score_countup_to, cap)
        while self._score_shown < cap:
            self._score_shown += 1

    def _display_session_score(self, session: GameSession) -> int:
        if self._score_countup_start > 0.0:
            return self._score_shown
        return session.score

    def _tick_score_burst(self) -> None:
        if self._score_burst_start <= 0.0:
            return
        elapsed = time.monotonic() - self._score_burst_start
        while self._score_burst_hit < SCORE_BURST_COUNT:
            due = self._score_burst_hit * SCORE_BURST_INTERVAL_SEC
            if elapsed < due:
                break
            self.sfx.play_score_tick()
            self._score_burst_hit += 1
        if self._score_burst_hit >= SCORE_BURST_COUNT:
            self._score_burst_start = 0.0

    def _update_title(self, actions: list[GameAction]) -> None:
        self.title_menu = self._nav_vertical(actions, self.title_menu, 2)
        for a in actions:
            if a is GameAction.CONFIRM:
                if self.title_menu == 0:
                    self.current = AppScreen.MODE
                    self.mode_cursor = 0
                else:
                    self.current = AppScreen.HELP

    def _update_help(self, actions: list[GameAction]) -> None:
        for a in actions:
            if a in (GameAction.CONFIRM, GameAction.MENU):
                self.current = AppScreen.TITLE

    def _update_mode(self, actions: list[GameAction]) -> None:
        self.mode_cursor = self._nav_vertical(actions, self.mode_cursor, len(self.modes))
        for a in actions:
            if a is GameAction.CONFIRM:
                self._start_game(self.modes[self.mode_cursor])
            elif a is GameAction.MENU:
                self.current = AppScreen.TITLE

    def _start_game(self, difficulty: Difficulty) -> None:
        self.repo.reset_pool(difficulty)
        try:
            questions = self.repo.draw(difficulty, CORRECT_TO_CLEAR, shuffle=True)
        except ValueError:
            questions = self.repo.draw(
                difficulty,
                self.repo.available_count(difficulty),
                shuffle=True,
            )
        rng = random.Random()
        play_questions = [
            resolve_for_play(q, difficulty, rng=rng) for q in questions
        ]
        self.session = GameSession.start(difficulty, play_questions)
        self._result_score_saved = False
        self.current = AppScreen.GAME

    def _update_game(self, dt: float, actions: list[GameAction]) -> None:
        session = self.session
        if session is None:
            self.current = AppScreen.TITLE
            return

        session.tick(dt)

        if session.phase in (SessionPhase.WON, SessionPhase.LOST):
            if not self._result_score_saved:
                self.score_store.record_session(session.difficulty, session.score)
                self._result_score_saved = True
            self.current = AppScreen.RESULT
            return

        for a in actions:
            if a is GameAction.MENU:
                self.current = AppScreen.PAUSE
                return

        if session.phase is not SessionPhase.PLAYING:
            return

        for a in actions:
            if a in (GameAction.UP, GameAction.LEFT):
                self._move_game_cursor(session, -1)
            elif a in (GameAction.DOWN, GameAction.RIGHT):
                self._move_game_cursor(session, 1)
            elif a is GameAction.BOMB:
                session.use_bomb()
            elif a is GameAction.CONFIRM:
                feedback = session.confirm_answer()
                if feedback is not None and feedback.was_correct:
                    self._start_score_burst(session)

    def _update_pause(self, actions: list[GameAction]) -> None:
        for a in actions:
            if a in (GameAction.MENU, GameAction.CONFIRM):
                self.current = AppScreen.GAME

    def _update_result(self, actions: list[GameAction]) -> None:
        for a in actions:
            if a is GameAction.CONFIRM:
                self.session = None
                self.current = AppScreen.TITLE
                self.title_menu = 0

    def _draw(self) -> None:
        self.screen.fill(COLOR_BG)
        if self.current is AppScreen.TITLE:
            self._draw_title()
        elif self.current is AppScreen.HELP:
            self._draw_help()
        elif self.current is AppScreen.MODE:
            self._draw_mode()
        elif self.current is AppScreen.GAME:
            self._draw_screen_background()
            self._draw_game()
        elif self.current is AppScreen.PAUSE:
            self._draw_screen_background()
            self._draw_game()
            self._draw_pause_overlay()
        elif self.current is AppScreen.RESULT:
            self._draw_result()
        if self.quit_modal_open:
            self._draw_quit_modal()

    def _draw_quit_modal(self) -> None:
        L = self.layout
        overlay = pygame.Surface((L.width, L.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        box_w = min(L.x(420), L.width - L.x(40))
        choices = self._quit_menu_choices()
        box_h = L.y(110 + len(choices) * 40 + 48)
        box = pygame.Rect(0, 0, box_w, box_h)
        box.center = (L.width // 2, L.height // 2)
        draw_panel(self.screen, box, status=True)

        cx = box.centerx
        blit_centered(
            self.screen,
            self.fonts.heading.render("メニュー", True, COLOR_TEXT),
            cx,
            box.y + L.y(28),
        )
        subtitle = (
            "どうしますか？"
            if len(choices) > 2
            else "ゲームを終了しますか？"
        )
        blit_centered(
            self.screen,
            self.fonts.body.render(subtitle, True, COLOR_TEXT_DIM),
            cx,
            box.y + L.y(72),
        )
        for i, label in enumerate(choices):
            color = COLOR_CURSOR if i == self.quit_menu else COLOR_TEXT
            prefix = "▶ " if i == self.quit_menu else "  "
            blit_centered(
                self.screen,
                self.fonts.body.render(prefix + label, True, color),
                cx,
                box.y + L.y(110 + i * 40),
            )
        blit_centered(
            self.screen,
            self.fonts.small.render(
                "↑↓ で選ぶ　X / Enter で決定　Esc で戻る",
                True,
                COLOR_TEXT_DIM,
            ),
            cx,
            box.bottom - L.y(24),
        )

    def _draw_title(self) -> None:
        L = self.layout
        cx = L.width // 2
        blit_centered(
            self.screen,
            self.fonts.title.render("なぞなぞ大作戦", True, COLOR_TEXT),
            cx,
            L.y(120),
        )
        blit_centered(
            self.screen,
            self.fonts.body.render("オフライン で 遊べる なぞなぞゲーム", True, COLOR_TEXT_DIM),
            cx,
            L.y(190),
        )
        items = ["はじめる", "操作説明"]
        for i, label in enumerate(items):
            color = COLOR_CURSOR if i == self.title_menu else COLOR_TEXT
            prefix = "▶ " if i == self.title_menu else "  "
            blit_centered(
                self.screen,
                self.fonts.heading.render(prefix + label, True, color),
                cx,
                L.y(300 + i * 56),
            )
        blit_centered(
            self.screen,
            self.fonts.small.render(
                "↑↓ で選ぶ　X / Enter で決定　Esc で終了確認", True, COLOR_TEXT_DIM
            ),
            cx,
            L.height - L.y(48),
        )

    def _draw_help(self) -> None:
        L = self.layout
        cx = L.width // 2
        blit_centered(
            self.screen,
            self.fonts.heading.render("操作説明", True, COLOR_TEXT),
            cx,
            L.y(48),
        )
        lines = [
            "十字キー … 選択移動",
            "X / Enter キー … 決定",
            "Z キー … ボム（間違い選択肢を半分消す）",
            "Shift … 一時停止",
            "Esc … メニュー（タイトルへ／終了）",
            "",
            "ゲームパッドも同じ操作に対応",
            "十字キー / 左スティック … 移動",
            "A ボタン … 決定　Y ボタン … ボム",
            "",
            "10問正解でクリア！",
            "ミスでライフ減少 / 1問あたり ノーマル3分・ハード1分",
            "ノーマル・ハードはその問題の残り時間が半分でヒント表示",
        ]
        y = L.y(120)
        for line in lines:
            blit_centered(self.screen, self.fonts.body.render(line, True, COLOR_TEXT_DIM), cx, y)
            y += L.y(36)
        blit_centered(
            self.screen,
            self.fonts.small.render(
                "X / Enter / Shift で タイトルへ", True, COLOR_CURSOR
            ),
            cx,
            L.height - L.y(40),
        )

    def _draw_mode(self) -> None:
        L = self.layout
        cx = L.width // 2
        blit_centered(
            self.screen,
            self.fonts.heading.render("モード選択", True, COLOR_TEXT),
            cx,
            L.y(60),
        )
        for i, diff in enumerate(self.modes):
            rules = RULES_BY_DIFFICULTY[diff]
            if not rules.has_timer:
                timer = "時間無制限"
            else:
                timer = f"1問 {int(rules.time_limit_seconds)}秒"
            label = f"{rules.label}（{timer}）"
            color = COLOR_CURSOR if i == self.mode_cursor else COLOR_TEXT
            prefix = "▶ " if i == self.mode_cursor else "  "
            blit_centered(
                self.screen,
                self.fonts.heading.render(prefix + label, True, color),
                cx,
                L.y(180 + i * 72),
            )
        blit_centered(
            self.screen,
            self.fonts.small.render(
                "X / Enter で開始　Shift でタイトル　Esc で終了確認",
                True,
                COLOR_TEXT_DIM,
            ),
            cx,
            L.height - L.y(40),
        )

    def _draw_screen_background(self) -> None:
        L = self.layout
        assets = self.ui_assets
        if assets.bg_pattern:
            bg = scale_cover(assets.bg_pattern, L.width, L.height)
            self.screen.blit(bg, (0, 0))
        else:
            self.screen.fill(COLOR_BG)
        if assets.bg_overlay:
            overlay = scale_cover(assets.bg_overlay, L.width, L.height)
            self.screen.blit(overlay, (0, 0))
        draw_background_red_band(self.screen, L.width, L.height)

    def _furigana_block_height(
        self,
        text: str,
        ruby: tuple[RubySegment, ...] | None,
        main_font: pygame.font.Font,
        ruby_font: pygame.font.Font,
    ) -> int:
        segments, _ = segments_or_reading_line(text, ruby)
        if segments and any(s.reading for s in segments):
            return ruby_font.get_height() + RUBY_MAIN_GAP + main_font.get_height()
        return main_font.get_height()

    def _draw_game(self) -> None:
        session = self.session
        if session is None:
            return

        L = self.layout
        pad = L.x(16)
        main_rect = pygame.Rect(pad, pad, L.main_w - L.x(32), L.height - L.y(32))
        status_rect = pygame.Rect(
            L.main_w + L.x(8),
            pad,
            L.status_w - L.x(24),
            L.height - L.y(32),
        )
        assets = self.ui_assets
        if assets.main_frame:
            assets.blit_stretched(assets.main_frame, self.screen, main_rect)
        if assets.status_panel:
            assets.blit_stretched(assets.status_panel, self.screen, status_rect)
        else:
            draw_panel(self.screen, status_rect, status=True)

        q = session.current_question

        inner_pad = L.x(10)
        container_rect = pygame.Rect(
            main_rect.x + inner_pad,
            main_rect.y + inner_pad,
            main_rect.width - inner_pad * 2,
            main_rect.height - inner_pad * 2,
        )
        draw_game_container(self.screen, container_rect)

        section_pad = L.x(12)
        section_gap = L.y(10)
        inner = container_rect.inflate(-section_pad, -section_pad)

        hint_zone_h = 0
        row_gap = L.y(6)
        row_h = L.y(32)
        opt_pad = L.x(10)
        entries: list = []

        if q and session.options_view:
            entries = session.options_view.visible_entries()
            n = max(1, len(entries))
            hint_visible_pre = session.show_playing_hint and bool(session.current_hint)
            text_pad = L.x(20)
            inner_w = inner.width - text_pad * 2
            opt_ruby = q.options_ruby or (None,) * len(q.options)

            label_reserve = L.x(18) + L.x(40) + L.x(22)
            opt_text_w = max(60, inner.width - opt_pad * 2 - label_reserve)
            min_row_h = L.y(28)
            for orig_idx, text in entries:
                ruby_seg = opt_ruby[orig_idx] if orig_idx < len(opt_ruby) else None
                mh = measure_text_with_furigana(
                    text,
                    ruby_seg,
                    opt_text_w,
                    self.fonts.option,
                    self.fonts.ruby,
                    self.fonts.furigana,
                )
                min_row_h = max(min_row_h, mh + L.y(8))

            row_gap = L.y(3) if n >= 6 else L.y(5)
            opt_vert_pad = L.y(10)
            options_need_h = n * min_row_h + (n - 1) * row_gap + opt_vert_pad
            abs_min_options_h = (
                n * L.y(24) + (n - 1) * row_gap + opt_vert_pad
            )

            if hint_visible_pre:
                hint_prefix_w = self.fonts.small.size("ヒント: ")[0] + L.x(4)
                hint_w = max(40, inner_w - hint_prefix_w)
                hh = measure_text_with_furigana(
                    q.hint,
                    q.hint_ruby,
                    hint_w,
                    self.fonts.small,
                    self.fonts.ruby,
                    self.fonts.furigana,
                )
                hint_zone_h = max(L.y(36), min(hh + L.y(14), int(inner.height * 0.36)))

            min_question_h = L.y(64)
            max_options_h = inner.height - section_gap - min_question_h
            options_h = min(max(options_need_h, abs_min_options_h), max_options_h)
            options_h = max(options_h, int(inner.height * min(0.62, 0.36 + n * 0.04)))
            options_h = min(options_h, inner.height - section_gap - min_question_h)
            question_h = inner.height - section_gap - options_h
            row_h = max(
                L.y(22),
                (options_h - opt_vert_pad - row_gap * (n - 1)) // n,
            )
            if row_h < min_row_h and options_need_h <= max_options_h:
                options_h = min(options_need_h, max_options_h)
                question_h = inner.height - section_gap - options_h
                row_h = max(
                    L.y(22),
                    (options_h - opt_vert_pad - row_gap * (n - 1)) // n,
                )
        else:
            question_h = int(inner.height * 0.40)

        question_rect = pygame.Rect(
            inner.x,
            inner.y,
            inner.width,
            question_h,
        )
        options_rect = pygame.Rect(
            inner.x,
            question_rect.bottom + section_gap,
            inner.width,
            inner.bottom - question_rect.bottom - section_gap,
        )
        draw_game_section(self.screen, question_rect)
        draw_game_section(self.screen, options_rect)

        if q and session.options_view:
            text_pad = L.x(20)
            inner_w = question_rect.width - text_pad * 2
            opt_ruby = q.options_ruby or (None,) * len(q.options)

            header = self.fonts.status.render(
                f"第 {session.question_index + 1} 問",
                True,
                COLOR_TEXT_DIM,
            )
            self.screen.blit(
                header,
                (question_rect.x + text_pad, question_rect.y + L.y(14)),
            )

            hint_visible = session.show_playing_hint and bool(session.current_hint)
            if hint_visible and hint_zone_h <= 0:
                hint_prefix_w = self.fonts.small.size("ヒント: ")[0] + L.x(4)
                hint_w = max(40, inner_w - hint_prefix_w)
                hh = measure_text_with_furigana(
                    q.hint,
                    q.hint_ruby,
                    hint_w,
                    self.fonts.small,
                    self.fonts.ruby,
                    self.fonts.furigana,
                )
                hint_zone_h = max(L.y(36), min(hh + L.y(14), int(inner.height * 0.36)))
            if not hint_visible:
                hint_zone_h = 0
            hint_top = question_rect.bottom - hint_zone_h - L.y(6)

            q_text_y = question_rect.y + L.y(48)
            clip_prev = self.screen.get_clip()
            clip_rect = pygame.Rect(
                question_rect.x + text_pad,
                q_text_y,
                inner_w,
                max(0, (hint_top if hint_visible else question_rect.bottom - L.y(8)) - q_text_y),
            )
            self.screen.set_clip(clip_rect)
            draw_text_with_furigana(
                self.screen,
                q.question,
                q.ruby,
                clip_rect.x,
                q_text_y,
                inner_w,
                self.fonts.body,
                self.fonts.ruby,
                self.fonts.furigana,
                COLOR_TEXT,
                COLOR_RUBY,
                COLOR_FURIGANA,
            )
            self.screen.set_clip(clip_prev)

            if hint_visible:
                hint_clip = pygame.Rect(
                    question_rect.x + text_pad,
                    hint_top,
                    inner_w,
                    max(0, question_rect.bottom - L.y(8) - hint_top),
                )
                self.screen.set_clip(hint_clip)
                hint_label = "ヒント: "
                hint_label_surf = self.fonts.small.render(hint_label, True, COLOR_CURSOR)
                hint_prefix_w = hint_label_surf.get_width()
                hint_segments, _ = segments_or_reading_line(q.hint, q.hint_ruby)
                hint_has_ruby = bool(
                    hint_segments and any(s.reading for s in hint_segments)
                )
                hint_text_y, hint_label_x, hint_label_y = layout_option_row(
                    hint_clip,
                    hint_label_surf,
                    self.fonts.small,
                    self.fonts.ruby,
                    has_ruby=hint_has_ruby,
                    pad_x=0,
                )
                self.screen.blit(hint_label_surf, (hint_label_x, hint_label_y))
                draw_text_with_furigana(
                    self.screen,
                    q.hint,
                    q.hint_ruby,
                    hint_clip.x + hint_prefix_w + L.x(4),
                    hint_text_y,
                    max(0, hint_clip.width - hint_prefix_w - L.x(4)),
                    self.fonts.small,
                    self.fonts.ruby,
                    self.fonts.furigana,
                    COLOR_TEXT_DIM,
                    COLOR_RUBY,
                    COLOR_FURIGANA,
                )
                self.screen.set_clip(clip_prev)

            if session.phase is SessionPhase.FEEDBACK and session.last_feedback:
                fb = session.last_feedback
                msg = "正解！" if fb.was_correct else "ざんねん…"
                col = COLOR_RIGHT if fb.was_correct else COLOR_WRONG
                blit_centered(
                    self.screen,
                    self.fonts.heading.render(msg, True, col),
                    question_rect.centerx,
                    question_rect.centery,
                )

            n = max(1, len(entries))
            opt_inner = options_rect.inflate(-opt_pad, -L.y(8))
            opt_clip = pygame.Rect(
                opt_inner.x,
                opt_inner.y,
                opt_inner.width,
                min(opt_inner.height, n * row_h + (n - 1) * row_gap),
            )
            clip_prev_opts = self.screen.get_clip()
            self.screen.set_clip(opt_clip)
            for i, (orig_idx, text) in enumerate(entries):
                bar = pygame.Rect(
                    opt_inner.x,
                    opt_inner.y + i * (row_h + row_gap),
                    opt_inner.width,
                    row_h,
                )
                is_cursor = i == session.cursor
                bar_tile = None
                if is_cursor and assets.option_bar_selected:
                    bar_tile = assets.option_bar_selected
                elif assets.option_bar:
                    bar_tile = assets.option_bar
                draw_option_bar(
                    self.screen, bar, selected=is_cursor, tile=bar_tile
                )
                color = COLOR_CURSOR if is_cursor else COLOR_TEXT
                label = f"{option_display_letter(i)}."
                label_surf = self.fonts.option.render(label, True, color)
                label_w = label_surf.get_width()
                text_x = bar.x + L.x(18) + label_w + L.x(8)
                text_w = bar.width - (text_x - bar.x) - L.x(14)
                ruby_seg = opt_ruby[orig_idx] if orig_idx < len(opt_ruby) else None
                segments, _ = segments_or_reading_line(text, ruby_seg)
                has_ruby = bool(segments and any(s.reading for s in segments))
                text_y, label_x, label_y = layout_option_row(
                    bar,
                    label_surf,
                    self.fonts.option,
                    self.fonts.ruby,
                    has_ruby=has_ruby,
                    pad_x=L.x(18),
                )
                self.screen.blit(label_surf, (label_x, label_y))
                bar_clip = bar.clip(opt_clip)
                if bar_clip.width > 0 and bar_clip.height > 0:
                    prev = self.screen.get_clip()
                    self.screen.set_clip(bar_clip)
                    draw_text_with_furigana(
                        self.screen,
                        text,
                        ruby_seg,
                        text_x,
                        text_y,
                        text_w,
                        self.fonts.option,
                        self.fonts.ruby,
                        self.fonts.furigana,
                        color,
                        COLOR_RUBY,
                        COLOR_FURIGANA,
                    )
                    self.screen.set_clip(prev)

            self.screen.set_clip(clip_prev_opts)

        draw_status_sidebar(
            self.screen,
            status_rect,
            session,
            self.score_store.high_score(session.difficulty),
            self._display_session_score(session),
            L,
            self.fonts.score_label,
            self.fonts.score_value,
            self.fonts.small,
            self.fonts.difficulty_mode,
        )

    def _draw_pause_overlay(self) -> None:
        L = self.layout
        overlay = pygame.Surface((L.width, L.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        blit_centered(
            self.screen,
            self.fonts.heading.render("一時停止", True, COLOR_TEXT),
            L.width // 2,
            L.height // 2 - L.y(24),
        )
        blit_centered(
            self.screen,
            self.fonts.body.render(
                "Shift / X / Enter で 再開　Esc でメニュー", True, COLOR_TEXT_DIM
            ),
            L.width // 2,
            L.height // 2 + L.y(24),
        )

    def _draw_result(self) -> None:
        session = self.session
        L = self.layout
        cx = L.width // 2
        pts = session.score if session else 0
        high = (
            self.score_store.high_score(session.difficulty)
            if session
            else 0
        )
        if session and session.phase is SessionPhase.WON:
            title = "クリア！"
            sub = f"{CORRECT_TO_CLEAR}問 正解 おめでとう！"
            color = COLOR_RIGHT
        else:
            title = "ゲームオーバー"
            reason = ""
            if session and session.loss_reason is LossReason.TIME_UP:
                reason = "（タイムアップ）"
            elif session and session.loss_reason is LossReason.NO_LIVES:
                reason = "（ライフが なくなった）"
            sub = f"正解 {session.correct_count if session else 0} 問 {reason}"
            color = COLOR_WRONG

        blit_centered(self.screen, self.fonts.title.render(title, True, color), cx, L.y(180))
        blit_centered(self.screen, self.fonts.body.render(sub, True, COLOR_TEXT), cx, L.y(250))
        blit_centered(
            self.screen,
            self.fonts.heading.render(f"得点 {pts:,}", True, COLOR_CURSOR),
            cx,
            L.y(310),
        )
        blit_centered(
            self.screen,
            self.fonts.body.render(f"最高得点 {high:,}", True, COLOR_TEXT_DIM),
            cx,
            L.y(360),
        )
        blit_centered(
            self.screen,
            self.fonts.small.render("X / Enter で タイトルへ", True, COLOR_TEXT_DIM),
            cx,
            L.height - L.y(80),
        )


def run_app(display: DisplaySettings) -> None:
    KidgameApp(display).run()
