"""Modern war-spoils announcement and result screen."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from UI.components.basic import UIButton, UILabel
from UI.core.anchor import Anchor
from UI.core.container import UIContainer
from UI.core.gamepad_handler import GamepadButton
from UI.core.manager import UIManager
from services.province_command_service import SpecialItemAwardResult


class WarSpoilsScreen(UIContainer):
    """Show either the found-item announcement or the final award result."""

    handles_own_navigation = True

    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 800

    def __init__(
        self,
        title: str,
        body_lines: list[str],
        continue_text: str,
        on_continue: Callable[[], None],
    ):
        super().__init__(
            position=(0, 0),
            size=(self.SCREEN_WIDTH, self.SCREEN_HEIGHT),
            background_color=(18, 18, 30),
            parent=None,
        )

        self._on_continue = on_continue
        self._button: UIButton | None = None
        self._title = title
        self._body_lines = body_lines
        self._continue_text = continue_text

        self._create_ui()
        self._sync_focus()

    @classmethod
    def for_announcement(cls, item_name: str, on_continue: Callable[[], None]) -> "WarSpoilsScreen":
        """Create the initial found-item announcement screen."""
        return cls(
            title="War Spoils",
            body_lines=[f"You found {item_name} as war spoils!"],
            continue_text="Choose Province",
            on_continue=on_continue,
        )

    @classmethod
    def for_result(
        cls,
        result: SpecialItemAwardResult,
        on_continue: Callable[[], None],
    ) -> "WarSpoilsScreen":
        """Create the result screen shown after awarding the item."""
        body_lines = [
            f"{result.officer_name} in Province {result.province_no} receives {result.item_name}.",
            f"Loyalty: {result.current_loyalty} -> {result.projected_loyalty}",
        ]
        if result.stat_name:
            body_lines.insert(
                1,
                f"{result.stat_name}: {result.current_stat_value} -> {result.projected_stat_value}",
            )
        if result.advisor_text:
            body_lines.append(result.advisor_text)
        if result.detail_text:
            body_lines.append(result.detail_text)
        return cls(
            title="War Spoils Awarded",
            body_lines=body_lines,
            continue_text="Return",
            on_continue=on_continue,
        )

    def _create_ui(self) -> None:
        panel = UIContainer(
            position=(140, 130),
            size=(1000, 500),
            background_color=(24, 28, 44),
            border_color=(79, 189, 186),
            border_width=2,
            parent=self,
        )

        UILabel(
            text=self._title,
            position=(500, 56),
            size=(800, 44),
            font=pygame.font.Font(None, 42),
            color=(255, 215, 0),
            align="center",
            anchor=Anchor.CENTER,
            parent=panel,
        )

        for index, line in enumerate(self._body_lines):
            UILabel(
                text=line,
                position=(60, 140 + index * 52),
                size=(880, 42),
                font=pygame.font.Font(None, 32),
                color=(232, 232, 232) if index < 3 else (190, 220, 220),
                align="left",
                parent=panel,
            )

        self._button = UIButton(
            text=self._continue_text,
            position=(400, 420),
            size=(200, 46),
            normal_color=(60, 60, 80),
            hover_color=(80, 80, 110),
            text_color=(232, 232, 232),
            font=pygame.font.Font(None, 28),
            on_click=self._continue,
            anchor=Anchor.CENTER,
            parent=panel,
        )

    def _sync_focus(self) -> None:
        manager = UIManager.get_instance()
        if manager and self._button is not None:
            manager.set_focus(self._button)

    def _continue(self) -> None:
        self._on_continue()

    def handle_gamepad_button(self, button: GamepadButton) -> bool:
        if button in (GamepadButton.A, GamepadButton.B):
            self._continue()
            return True
        return False

    def handle_event(self, event: pygame.event.Event, transform=None) -> bool:
        if event.type == pygame.KEYDOWN and event.key in (
            pygame.K_RETURN,
            pygame.K_SPACE,
            pygame.K_ESCAPE,
        ):
            self._continue()
            return True

        return bool(super().handle_event(event, transform))
