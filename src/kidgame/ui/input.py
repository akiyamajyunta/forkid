from __future__ import annotations

from enum import StrEnum, auto

import pygame


class GameAction(StrEnum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    CONFIRM = auto()
    BOMB = auto()
    MENU = auto()
    CANCEL = auto()


class InputState:
    """キーボード + 最初のゲームパッドからアクションを生成。"""

    def __init__(self) -> None:
        self._joystick: pygame.joystick.Joystick | None = None
        self._hat_prev = (0, 0)
        self._stick_cooldown = 0.0

    def attach_joystick(self) -> None:
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self._joystick = pygame.joystick.Joystick(0)
            self._joystick.init()

    def poll(self, events: list[pygame.event.Event], dt: float) -> list[GameAction]:
        actions: list[GameAction] = []
        self._stick_cooldown = max(0.0, self._stick_cooldown - dt)

        for event in events:
            if event.type == pygame.KEYDOWN:
                actions.extend(_key_down(event.key))
            elif event.type == pygame.JOYBUTTONDOWN:
                actions.extend(_joy_button(event.button))
            elif event.type == pygame.JOYHATMOTION and self._joystick:
                hat = event.value
                if hat[1] > self._hat_prev[1]:
                    actions.append(GameAction.UP)
                elif hat[1] < self._hat_prev[1]:
                    actions.append(GameAction.DOWN)
                if hat[0] < self._hat_prev[0]:
                    actions.append(GameAction.LEFT)
                elif hat[0] > self._hat_prev[0]:
                    actions.append(GameAction.RIGHT)
                self._hat_prev = hat

        if self._joystick and self._stick_cooldown <= 0:
            axis_y = self._joystick.get_axis(1)
            axis_x = self._joystick.get_axis(0)
            threshold = 0.55
            if axis_y < -threshold:
                actions.append(GameAction.UP)
                self._stick_cooldown = 0.18
            elif axis_y > threshold:
                actions.append(GameAction.DOWN)
                self._stick_cooldown = 0.18
            elif axis_x < -threshold:
                actions.append(GameAction.LEFT)
                self._stick_cooldown = 0.18
            elif axis_x > threshold:
                actions.append(GameAction.RIGHT)
                self._stick_cooldown = 0.18

        return actions


def _key_down(key: int) -> list[GameAction]:
    mapping: dict[int, GameAction] = {
        pygame.K_UP: GameAction.UP,
        pygame.K_DOWN: GameAction.DOWN,
        pygame.K_LEFT: GameAction.LEFT,
        pygame.K_RIGHT: GameAction.RIGHT,
        pygame.K_x: GameAction.CONFIRM,
        pygame.K_RETURN: GameAction.CONFIRM,
        pygame.K_KP_ENTER: GameAction.CONFIRM,
        pygame.K_z: GameAction.BOMB,
        pygame.K_LSHIFT: GameAction.MENU,
        pygame.K_RSHIFT: GameAction.MENU,
        pygame.K_ESCAPE: GameAction.CANCEL,
    }
    action = mapping.get(key)
    return [action] if action else []


def _joy_button(button: int) -> list[GameAction]:
    # 一般的な Xbox 風: 0=A/決定, 3=Y/ボム, 7=Start/メニュー
    if button == 0:
        return [GameAction.CONFIRM]
    if button in (3, 2):
        return [GameAction.BOMB]
    if button in (7, 6):
        return [GameAction.MENU]
    return []
