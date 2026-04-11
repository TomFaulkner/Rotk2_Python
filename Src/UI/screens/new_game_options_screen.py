"""Modern new-game options screen for difficulty and startup flags."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pygame

from UI.components.basic import UIButton, UILabel
from UI.core.anchor import Anchor
from UI.core.container import UIContainer
from UI.core.manager import UIManager

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class NewGameOptionsResult:
    """Structured result from the options screen."""

    level: int
    see_war: int
    history: int


class NewGameOptionsScreen(UIContainer):
    """Simple options screen used before entering the classic game loop."""

    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 800

    BG_COLOR = (26, 26, 46)
    PANEL_COLOR = (22, 33, 62)
    TITLE_COLOR = (255, 215, 0)
    TEXT_COLOR = (232, 232, 232)
    BUTTON_NORMAL = (60, 60, 80)
    BUTTON_HOVER = (80, 80, 110)
    BUTTON_SELECTED = (79, 189, 186)

    def __init__(self):
        super().__init__(
            position=(0, 0),
            size=(self.SCREEN_WIDTH, self.SCREEN_HEIGHT),
            background_color=self.BG_COLOR,
            parent=None,
        )

        self._callback: Callable[[NewGameOptionsResult | None], None] | None = None
        self._difficulty = 1
        self._see_war = 0
        self._history = 2

        self._difficulty_buttons: list[UIButton] = []
        self._see_war_buttons: list[UIButton] = []
        self._history_buttons: list[UIButton] = []

        self._create_ui()
        self._register_with_manager()
        self._refresh_button_states()

    def _register_with_manager(self) -> None:
        try:
            manager = UIManager.get_instance()
            if manager:
                manager.root_component = self
        except Exception as e:
            print(f"Warning: Could not register options screen with UIManager: {e}")

    def _create_ui(self) -> None:
        UIContainer(
            position=(0, 0),
            size=(self.SCREEN_WIDTH, 60),
            background_color=self.PANEL_COLOR,
            border_color=(79, 189, 186),
            border_width=2,
            parent=self,
        )

        UILabel(
            text="New Game Options",
            position=(self.SCREEN_WIDTH // 2, 30),
            size=(600, 40),
            font=pygame.font.Font(None, 40),
            color=self.TITLE_COLOR,
            align="center",
            anchor=Anchor.CENTER,
            parent=self,
        )

        panel = UIContainer(
            position=(200, 120),
            size=(880, 460),
            background_color=self.PANEL_COLOR,
            border_color=(79, 189, 186),
            border_width=2,
            parent=self,
        )

        self._create_option_row(
            parent=panel,
            title="Difficulty",
            y=40,
            options=[("Easy", 1), ("Normal", 2), ("Hard", 3)],
            button_store=self._difficulty_buttons,
            setter=self._set_difficulty,
        )
        self._create_option_row(
            parent=panel,
            title="See War",
            y=170,
            options=[("No", 0), ("Yes", 1)],
            button_store=self._see_war_buttons,
            setter=self._set_see_war,
        )
        self._create_option_row(
            parent=panel,
            title="History",
            y=300,
            options=[("No", 2), ("Yes", 1)],
            button_store=self._history_buttons,
            setter=self._set_history,
        )

        UIButton(
            text="← Back",
            position=(200, 650),
            size=(180, 55),
            normal_color=self.BUTTON_NORMAL,
            hover_color=self.BUTTON_HOVER,
            text_color=self.TEXT_COLOR,
            font=pygame.font.Font(None, 30),
            on_click=self._on_back,
            parent=self,
        )
        UIButton(
            text="Start Game →",
            position=(self.SCREEN_WIDTH - 380, 650),
            size=(180, 55),
            normal_color=self.BUTTON_SELECTED,
            hover_color=(100, 210, 200),
            text_color=(0, 0, 0),
            font=pygame.font.Font(None, 30),
            on_click=self._on_confirm,
            parent=self,
        )

    def _create_option_row(
        self,
        parent: UIContainer,
        title: str,
        y: int,
        options: list[tuple[str, int]],
        button_store: list[UIButton],
        setter,
    ) -> None:
        UILabel(
            text=title,
            position=(60, y + 25),
            size=(220, 40),
            font=pygame.font.Font(None, 32),
            color=self.TITLE_COLOR,
            align="left",
            parent=parent,
        )

        button_x = 320
        for label, value in options:
            button = UIButton(
                text=label,
                position=(button_x, y),
                size=(180, 55),
                normal_color=self.BUTTON_NORMAL,
                hover_color=self.BUTTON_HOVER,
                text_color=self.TEXT_COLOR,
                font=pygame.font.Font(None, 28),
                on_click=lambda selected=value, handler=setter: handler(selected),
                parent=parent,
            )
            button_store.append(button)
            button_x += 210

    def _set_difficulty(self, value: int) -> None:
        self._difficulty = value
        self._refresh_button_states()

    def _set_see_war(self, value: int) -> None:
        self._see_war = value
        self._refresh_button_states()

    def _set_history(self, value: int) -> None:
        self._history = value
        self._refresh_button_states()

    def _refresh_button_states(self) -> None:
        self._set_selected_button(self._difficulty_buttons, self._difficulty, [1, 2, 3])
        self._set_selected_button(self._see_war_buttons, self._see_war, [0, 1])
        self._set_selected_button(self._history_buttons, self._history, [2, 1])

    def _set_selected_button(
        self, buttons: list[UIButton], current_value: int, values: list[int]
    ) -> None:
        for button, value in zip(buttons, values, strict=False):
            button.normal_color = (
                self.BUTTON_SELECTED if value == current_value else self.BUTTON_NORMAL
            )
            button.text_color = (0, 0, 0) if value == current_value else self.TEXT_COLOR

    def _on_confirm(self) -> None:
        if self._callback:
            self._callback(
                NewGameOptionsResult(
                    level=self._difficulty,
                    see_war=self._see_war,
                    history=self._history,
                )
            )

    def _on_back(self) -> None:
        if self._callback:
            self._callback(None)

    def set_callback(self, callback: Callable[[NewGameOptionsResult | None], None]) -> None:
        self._callback = callback

    def handle_event(self, event: pygame.event.Event, transform=None) -> bool:
        if super().handle_event(event, transform):
            return True

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._on_back()
            return True

        return False
