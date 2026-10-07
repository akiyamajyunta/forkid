from __future__ import annotations

import random
from enum import StrEnum, auto

import pygame

from kidgame.data.loader import QuestionRepository
from kidgame.data.models import Difficulty
from kidgame.data.question_runtime import resolve_for_play
from kidgame.system.config import (
    BONUS_GAUGE_MAX,
    CORRECT_TO_CLEAR,
    INITIAL_LIVES,
    RULES_BY_DIFFICULTY,
)
from kidgame.system.game_session import GameSession, LossReason, SessionPhase
from kidgame.ui.display_config import DisplaySettings
from kidgame.data.furigana import RubySegment, segments_or_reading_line
from kidgame.ui.draw_helpers import blit_centered, draw_gauge, draw_option_bar, draw_panel
from kidgame.ui.fonts import FontSet
from kidgame.ui.input import GameAction, InputState
from kidgame.ui.layout import ScreenLayout
from kidgame.ui.ruby_draw import RUBY_MAIN_GAP, draw_text_with_furigana
from kidgame.ui.theme import (
    COLOR_BG,
    COLOR_CURSOR,
    COLOR_FURIGANA,
    COLOR_GAUGE_BONUS,
    COLOR_GAUGE_TIMER,
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
        self.quit_menu = 1  # 0=終了, 1=キャンセル（誤操作防止で既定はキャンセル）

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

    def _open_quit_modal(self) -> None:
        self.quit_modal_open = True
        self.quit_menu = 1

    def _close_quit_modal(self) -> None:
        self.quit_modal_open = False

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

        self.quit_menu = self._nav_vertical(actions, self.quit_menu, 2)
        for a in actions:
            if a is GameAction.CONFIRM:
                if self.quit_menu == 0:
                    self.running = False
                else:
                    self._close_quit_modal()

    def _update(self, dt: float, actions: list[GameAction]) -> None:
        if self.quit_modal_open:
            self._update_quit_modal(actions)
            return

        actions, cancelled = self._split_cancel_actions(actions)
        if cancelled:
            self._open_quit_modal()
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

    def _nav_vertical(self, actions: list[GameAction], cursor: int, count: int) -> int:
        for a in actions:
            if a is GameAction.UP:
                cursor = (cursor - 1) % count
            elif a is GameAction.DOWN:
                cursor = (cursor + 1) % count
        return cursor

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
        self.current = AppScreen.GAME

    def _update_game(self, dt: float, actions: list[GameAction]) -> None:
        session = self.session
        if session is None:
            self.current = AppScreen.TITLE
            return

        session.tick(dt)

        if session.phase in (SessionPhase.WON, SessionPhase.LOST):
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
                session.move_cursor(-1)
            elif a in (GameAction.DOWN, GameAction.RIGHT):
                session.move_cursor(1)
            elif a is GameAction.BOMB:
                session.use_bomb()
            elif a is GameAction.CONFIRM:
                session.confirm_answer()

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
            self._draw_game()
        elif self.current is AppScreen.PAUSE:
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
        box_h = L.y(220)
        box = pygame.Rect(0, 0, box_w, box_h)
        box.center = (L.width // 2, L.height // 2)
        draw_panel(self.screen, box, status=True)

        cx = box.centerx
        blit_centered(
            self.screen,
            self.fonts.heading.render("終了確認", True, COLOR_TEXT),
            cx,
            box.y + L.y(28),
        )
        blit_centered(
            self.screen,
            self.fonts.body.render("ゲームを終了しますか？", True, COLOR_TEXT_DIM),
            cx,
            box.y + L.y(72),
        )
        choices = ["終了する", "キャンセル"]
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
            "Esc … 終了（確認あり）",
            "",
            "ゲームパッドも同じ操作に対応",
            "十字キー / 左スティック … 移動",
            "A ボタン … 決定　Y ボタン … ボム",
            "",
            "10問正解でクリア！",
            "ミスでライフ減少 / ノーマル3分・ハード1分",
            "ノーマル・ハードは残り時間が半分になるとヒント表示",
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
            timer = "時間無制限" if not rules.has_timer else f"{int(rules.time_limit_seconds)}秒"
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
        draw_panel(self.screen, status_rect, status=True)

        q = session.current_question
        rules = session.rules

        inner_pad = L.x(14)
        footer_h = L.y(28)
        play_area = pygame.Rect(
            main_rect.x + inner_pad,
            main_rect.y + inner_pad,
            main_rect.width - inner_pad * 2,
            main_rect.height - inner_pad * 2 - footer_h,
        )
        block_gap = L.y(12)
        question_h = int(play_area.height * 0.50)
        question_rect = pygame.Rect(
            play_area.x,
            play_area.y,
            play_area.width,
            question_h,
        )
        options_rect = pygame.Rect(
            play_area.x,
            question_rect.bottom + block_gap,
            play_area.width,
            play_area.bottom - question_rect.bottom - block_gap,
        )

        draw_panel(self.screen, question_rect, status=False)

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

            q_text_y = question_rect.y + L.y(48)
            clip_prev = self.screen.get_clip()
            clip_rect = pygame.Rect(
                question_rect.x + text_pad,
                q_text_y,
                inner_w,
                max(0, question_rect.bottom - L.y(56) - q_text_y),
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

            if session.show_playing_hint and session.current_hint:
                hint_label = "ヒント: "
                hint_y = question_rect.bottom - L.y(52)
                self.screen.blit(
                    self.fonts.small.render(hint_label, True, COLOR_CURSOR),
                    (question_rect.x + text_pad, hint_y),
                )
                hint_prefix_w = self.fonts.small.size(hint_label)[0]
                draw_text_with_furigana(
                    self.screen,
                    q.hint,
                    q.hint_ruby,
                    question_rect.x + text_pad + hint_prefix_w,
                    hint_y,
                    inner_w - hint_prefix_w,
                    self.fonts.small,
                    self.fonts.ruby,
                    self.fonts.furigana,
                    COLOR_TEXT_DIM,
                    COLOR_RUBY,
                    COLOR_FURIGANA,
                )

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

            entries = session.options_view.visible_entries()
            n = max(1, len(entries))
            row_gap = L.y(8)
            row_h = (options_rect.height - row_gap * (n - 1)) // n
            for i, (orig_idx, text) in enumerate(entries):
                bar = pygame.Rect(
                    options_rect.x,
                    options_rect.y + i * (row_h + row_gap),
                    options_rect.width,
                    row_h,
                )
                is_cursor = i == session.cursor
                draw_option_bar(self.screen, bar, selected=is_cursor)
                color = COLOR_CURSOR if is_cursor else COLOR_TEXT
                label = f"{chr(0x41 + orig_idx)}."
                label_surf = self.fonts.option.render(label, True, color)
                label_w = label_surf.get_width()
                text_x = bar.x + L.x(18) + label_w + L.x(8)
                text_w = bar.width - (text_x - bar.x) - L.x(14)
                ruby_seg = opt_ruby[orig_idx] if orig_idx < len(opt_ruby) else None
                block_h = self._furigana_block_height(
                    text, ruby_seg, self.fonts.option, self.fonts.ruby
                )
                text_y = bar.y + max(L.y(6), (bar.height - block_h) // 2)
                self.screen.blit(label_surf, (bar.x + L.x(18), text_y + L.y(4)))
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

        hint_bar = self.fonts.small.render(
            "↑↓ 選択　X/Enter 決定　Z ボム　Shift ポーズ　Esc 終了",
            True,
            COLOR_TEXT_DIM,
        )
        self.screen.blit(
            hint_bar,
            (main_rect.x + L.x(20), main_rect.bottom - L.y(26)),
        )

        # --- ステータス ---
        sx = status_rect.x + L.x(16)
        sy = status_rect.y + L.y(20)
        self.screen.blit(
            self.fonts.status.render("STATUS", True, COLOR_CURSOR),
            (sx, sy),
        )
        sy += L.y(36)

        life_text = "♥ " * max(0, session.lives) + "♡ " * max(
            0, INITIAL_LIVES - session.lives
        )
        self.screen.blit(
            self.fonts.body.render(f"ライフ {life_text}", True, COLOR_TEXT),
            (sx, sy),
        )
        sy += L.y(40)

        score = self.fonts.body.render(
            f"正解 {session.correct_count} / {CORRECT_TO_CLEAR}",
            True,
            COLOR_TEXT,
        )
        self.screen.blit(score, (sx, sy))
        sy += L.y(44)

        bomb = self.fonts.body.render(f"ボム × {session.bomb_stock}", True, COLOR_TEXT)
        self.screen.blit(bomb, (sx, sy))
        sy += L.y(48)

        gauge_w = status_rect.width - L.x(32)
        gauge_h = max(10, L.y(18))
        if rules.has_timer and session.time_remaining is not None:
            limit = rules.time_limit_seconds or 1.0
            ratio = session.time_remaining / limit
            draw_gauge(
                self.screen,
                pygame.Rect(sx, sy + L.y(18), gauge_w, gauge_h),
                ratio,
                COLOR_GAUGE_TIMER,
                "タイマー",
                self.fonts.small,
            )
            sy += L.y(52)
        else:
            self.screen.blit(
                self.fonts.small.render("タイマー: 無制限", True, COLOR_TEXT_DIM),
                (sx, sy),
            )
            sy += L.y(36)

        draw_gauge(
            self.screen,
            pygame.Rect(sx, sy + L.y(18), gauge_w, gauge_h),
            session.bonus_gauge / BONUS_GAUGE_MAX,
            COLOR_GAUGE_BONUS,
            "ボーナス",
            self.fonts.small,
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
                "Shift / X / Enter で 再開　Esc で終了確認", True, COLOR_TEXT_DIM
            ),
            L.width // 2,
            L.height // 2 + L.y(24),
        )

    def _draw_result(self) -> None:
        session = self.session
        L = self.layout
        cx = L.width // 2
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

        blit_centered(self.screen, self.fonts.title.render(title, True, color), cx, L.y(200))
        blit_centered(self.screen, self.fonts.body.render(sub, True, COLOR_TEXT), cx, L.y(280))
        blit_centered(
            self.screen,
            self.fonts.small.render("X / Enter で タイトルへ", True, COLOR_TEXT_DIM),
            cx,
            L.height - L.y(80),
        )


def run_app(display: DisplaySettings) -> None:
    KidgameApp(display).run()
