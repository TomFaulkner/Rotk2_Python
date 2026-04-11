"""Modern officer picker used before officer-driven actions."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from officer_display import get_officer_display_name
from UI.components.basic import UIButton, UILabel
from UI.core.anchor import Anchor
from UI.core.container import UIContainer
from UI.core.gamepad_handler import GamepadButton
from UI.core.manager import UIManager


class OfficerSelectionScreen(UIContainer):
    """Select an officer from the active province for a command."""

    handles_own_navigation = True

    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 800
    MAX_VISIBLE_ROWS = 12
    COLUMN_X = [20, 620, 740, 820, 900, 1010]
    COLUMN_WIDTHS = [560, 90, 70, 70, 90, 130]

    def __init__(
        self,
        officers: list,
        title: str,
        subtitle: str,
        on_select: Callable[[object | None], None] | None = None,
    ):
        super().__init__(
            position=(0, 0),
            size=(self.SCREEN_WIDTH, self.SCREEN_HEIGHT),
            background_color=(18, 18, 30),
            parent=None,
        )

        self._officers = officers
        self._title = title
        self._subtitle = subtitle
        self._on_select_callback = on_select
        self._selected_index = 0
        self._scroll_offset = 0
        self._buttons: list[UIButton] = []
        self._row_labels: list[list[UILabel]] = []

        self._create_ui()
        self._update_button_labels()
        self._sync_focus()

    def _create_ui(self) -> None:
        UIContainer(
            position=(0, 0),
            size=(self.SCREEN_WIDTH, 60),
            background_color=(22, 33, 62),
            border_color=(79, 189, 186),
            border_width=2,
            parent=self,
        )

        UILabel(
            text=self._title,
            position=(self.SCREEN_WIDTH // 2, 30),
            size=(700, 40),
            font=pygame.font.Font(None, 38),
            color=(255, 215, 0),
            align="center",
            anchor=Anchor.CENTER,
            parent=self,
        )

        UILabel(
            text=self._subtitle,
            position=(60, 80),
            size=(1160, 28),
            font=pygame.font.Font(None, 28),
            color=(220, 220, 220),
            align="left",
            parent=self,
        )

        table = UIContainer(
            position=(40, 130),
            size=(1200, 580),
            background_color=(24, 28, 44),
            border_color=(79, 189, 186),
            border_width=2,
            parent=self,
        )

        headers = [
            ("Officer", 30),
            ("Loyalty", 610),
            ("Int", 730),
            ("War", 810),
            ("Charm", 890),
            ("Soldiers", 1010),
        ]
        for text, x in headers:
            UILabel(
                text=text,
                position=(x, 20),
                size=(150, 32),
                font=pygame.font.Font(None, 28),
                color=(255, 215, 0),
                align="left",
                parent=table,
            )

        row_y = 62
        row_height = 40
        for visible_index in range(self.MAX_VISIBLE_ROWS):
            button = UIButton(
                text="",
                position=(18, row_y + visible_index * row_height),
                size=(1164, 34),
                normal_color=(40, 46, 68),
                hover_color=(65, 72, 102),
                pressed_color=(55, 62, 92),
                text_color=(232, 232, 232),
                font=pygame.font.Font(None, 24),
                on_click=lambda idx=visible_index: self._activate_visible_index(idx),
                parent=table,
            )
            button.label.visible = False
            self._buttons.append(button)

            row_labels: list[UILabel] = []
            for x, width in zip(self.COLUMN_X, self.COLUMN_WIDTHS, strict=True):
                label = UILabel(
                    text="",
                    position=(x, button.size[1] // 2),
                    size=(width, button.size[1]),
                    font=pygame.font.Font(None, 24),
                    color=(232, 232, 232),
                    align="left",
                    anchor=Anchor.CENTER_LEFT,
                    parent=button,
                )
                row_labels.append(label)
            self._row_labels.append(row_labels)

        self._footer_label = UILabel(
            text="",
            position=(60, 722),
            size=(900, 30),
            font=pygame.font.Font(None, 24),
            color=(190, 190, 190),
            align="left",
            parent=self,
        )

        UIButton(
            text="← Cancel",
            position=(40, 745),
            size=(180, 40),
            normal_color=(60, 60, 80),
            hover_color=(80, 80, 110),
            text_color=(232, 232, 232),
            font=pygame.font.Font(None, 26),
            on_click=self._cancel,
            parent=self,
        )

    def _get_row_values(self, officer) -> list[str]:
        return [
            get_officer_display_name(officer),
            str(officer.Loyalty),
            str(officer.Int),
            str(officer.War),
            str(officer.Chm),
            f"{officer.Soldiers:,}",
        ]

    def _update_button_labels(self) -> None:
        if not self._officers:
            for button, row_labels in zip(self._buttons, self._row_labels, strict=True):
                button.enabled = False
                for label in row_labels:
                    label.text = ""
            self._footer_label.text = "No officers available."
            return

        total = len(self._officers)
        end_index = min(self._scroll_offset + self.MAX_VISIBLE_ROWS, total)
        self._footer_label.text = (
            f"Use Up/Down to choose, PageUp/PageDown to scroll, Enter to confirm, Esc to cancel. "
            f"Showing {self._scroll_offset + 1}-{end_index} of {total}."
        )

        for visible_index, (button, row_labels) in enumerate(
            zip(self._buttons, self._row_labels, strict=True)
        ):
            officer_index = self._scroll_offset + visible_index
            if officer_index >= total:
                button.enabled = False
                for label in row_labels:
                    label.text = ""
                continue

            button.enabled = True
            row_values = self._get_row_values(self._officers[officer_index])
            for label, value in zip(row_labels, row_values, strict=True):
                label.text = value

    def _sync_focus(self) -> None:
        manager = UIManager.get_instance()
        if not manager or not self._officers:
            return

        visible_index = self._selected_index - self._scroll_offset
        if 0 <= visible_index < len(self._buttons):
            manager.set_focus(self._buttons[visible_index])

    def _ensure_visible(self) -> None:
        if self._selected_index < self._scroll_offset:
            self._scroll_offset = self._selected_index
        elif self._selected_index >= self._scroll_offset + self.MAX_VISIBLE_ROWS:
            self._scroll_offset = self._selected_index - self.MAX_VISIBLE_ROWS + 1

    def _move_selection(self, delta: int) -> None:
        if not self._officers:
            return

        new_index = max(0, min(len(self._officers) - 1, self._selected_index + delta))
        if new_index == self._selected_index:
            return

        self._selected_index = new_index
        self._ensure_visible()
        self._update_button_labels()
        self._sync_focus()

    def _page_selection(self, delta: int) -> None:
        if not self._officers:
            return

        self._selected_index = max(
            0, min(len(self._officers) - 1, self._selected_index + delta * self.MAX_VISIBLE_ROWS)
        )
        self._ensure_visible()
        self._update_button_labels()
        self._sync_focus()

    def _activate_visible_index(self, visible_index: int) -> None:
        officer_index = self._scroll_offset + visible_index
        if officer_index >= len(self._officers):
            return

        self._selected_index = officer_index
        self._ensure_visible()
        self._update_button_labels()
        self._sync_focus()
        self._confirm()

    def _confirm(self) -> None:
        if self._on_select_callback and self._officers:
            self._on_select_callback(self._officers[self._selected_index])

    def _cancel(self) -> None:
        if self._on_select_callback:
            self._on_select_callback(None)

    def handle_gamepad_button(self, button: GamepadButton) -> bool:
        """Handle gamepad navigation directly for the picker."""
        if button in (GamepadButton.B,):
            self._cancel()
            return True
        if button in (GamepadButton.DPAD_UP, GamepadButton.LEFT_STICK_UP):
            self._move_selection(-1)
            return True
        if button in (GamepadButton.DPAD_DOWN, GamepadButton.LEFT_STICK_DOWN):
            self._move_selection(1)
            return True
        if button == GamepadButton.LB:
            self._page_selection(-1)
            return True
        if button == GamepadButton.RB:
            self._page_selection(1)
            return True
        if button == GamepadButton.A:
            self._confirm()
            return True
        return False

    def handle_event(self, event: pygame.event.Event, transform=None) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._cancel()
                return True
            if event.key == pygame.K_UP:
                self._move_selection(-1)
                return True
            if event.key == pygame.K_DOWN:
                self._move_selection(1)
                return True
            if event.key == pygame.K_PAGEUP:
                self._page_selection(-1)
                return True
            if event.key == pygame.K_PAGEDOWN:
                self._page_selection(1)
                return True
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._confirm()
                return True

        return bool(super().handle_event(event, transform))
