"""Combined province officer summary screen."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from officer_display import get_officer_display_name
from UI.components.basic import UIButton, UILabel
from UI.core.anchor import Anchor
from UI.core.container import UIContainer
from UI.core.gamepad_handler import GamepadButton

if TYPE_CHECKING:
    from Officer import Officer
    from Province import Province


class OfficerSummaryScreen(UIContainer):
    """Modern screen showing both Summary 1 and Summary 2 officer fields."""

    handles_own_navigation = True
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 800
    PAGE_SIZE = 16

    def __init__(self, province: Province, on_back: Callable[[], None] | None = None):
        super().__init__(
            position=(0, 0),
            size=(self.SCREEN_WIDTH, self.SCREEN_HEIGHT),
            background_color=(18, 18, 30),
            parent=None,
        )

        self.province = province
        self._on_back_callback = on_back
        self._officers = self.province.GetOfficerList()
        self._page = 0
        self._row_labels: list[list[UILabel]] = []
        self._create_ui()
        self._refresh_page()

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
            text=f"Province {self.province.No} Officer Summary",
            position=(self.SCREEN_WIDTH // 2, 30),
            size=(700, 40),
            font=pygame.font.Font(None, 38),
            color=(255, 215, 0),
            align="center",
            anchor=Anchor.CENTER,
            parent=self,
        )

        UIButton(
            text="← Back",
            position=(40, 745),
            size=(180, 40),
            normal_color=(60, 60, 80),
            hover_color=(80, 80, 110),
            text_color=(232, 232, 232),
            font=pygame.font.Font(None, 26),
            on_click=self._on_back,
            parent=self,
        )

        self._table = UIContainer(
            position=(30, 90),
            size=(1220, 620),
            background_color=(24, 28, 44),
            border_color=(79, 189, 186),
            border_width=2,
            parent=self,
        )

        headers = [
            ("Officer", 25),
            ("Loyalty", 270),
            ("Int", 390),
            ("War", 470),
            ("Charm", 550),
            ("Service", 670),
            ("Soldiers", 790),
            ("Arms", 940),
            ("Training", 1050),
        ]

        for text, x in headers:
            UILabel(
                text=text,
                position=(x, 20),
                size=(130, 32),
                font=pygame.font.Font(None, 28),
                color=(255, 215, 0),
                align="left",
                parent=self._table,
            )

        row_y = 65
        row_height = 34

        for _ in range(self.PAGE_SIZE):
            self._row_labels.append(self._add_officer_row(self._table, row_y))
            row_y += row_height

        self._page_label = UILabel(
            text="",
            position=(820, 745),
            size=(220, 40),
            font=pygame.font.Font(None, 24),
            color=(232, 232, 232),
            align="center",
            parent=self,
        )

        UIButton(
            text="Prev",
            position=(1040, 745),
            size=(90, 40),
            normal_color=(60, 60, 80),
            hover_color=(80, 80, 110),
            text_color=(232, 232, 232),
            font=pygame.font.Font(None, 24),
            on_click=self._prev_page,
            parent=self,
        )

        UIButton(
            text="Next",
            position=(1145, 745),
            size=(90, 40),
            normal_color=(60, 60, 80),
            hover_color=(80, 80, 110),
            text_color=(232, 232, 232),
            font=pygame.font.Font(None, 24),
            on_click=self._next_page,
            parent=self,
        )

    def _add_officer_row(self, parent: UIContainer, y: int) -> list[UILabel]:
        columns = [
            (25, 220),
            (270, 90),
            (390, 60),
            (470, 60),
            (550, 80),
            (670, 90),
            (790, 120),
            (940, 70),
            (1050, 110),
        ]
        row_labels: list[UILabel] = []
        for x, width in columns:
            row_labels.append(
                UILabel(
                    text="",
                    position=(x, y),
                    size=(width, 28),
                    font=pygame.font.Font(None, 24),
                    color=(232, 232, 232),
                    align="left",
                    parent=parent,
                )
            )
        return row_labels

    def _get_page_count(self) -> int:
        return max(1, (len(self._officers) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)

    def _refresh_page(self) -> None:
        start = self._page * self.PAGE_SIZE
        page_officers = self._officers[start : start + self.PAGE_SIZE]
        for row_labels, officer in zip(self._row_labels, page_officers, strict=False):
            values = [
                self._get_officer_name(officer),
                str(officer.Loyalty),
                str(officer.Int),
                str(officer.War),
                str(officer.Chm),
                str(getattr(officer, "Age", 0)),
                f"{officer.Soldiers:,}",
                str(officer.Arms),
                str(officer.TrainingLevel),
            ]
            for label, value in zip(row_labels, values, strict=True):
                label.text = value

        for row_labels in self._row_labels[len(page_officers) :]:
            for label in row_labels:
                label.text = ""

        self._page_label.text = f"Page {self._page + 1}/{self._get_page_count()}"

    def _prev_page(self) -> None:
        if self._page <= 0:
            return
        self._page -= 1
        self._refresh_page()

    def _next_page(self) -> None:
        if self._page >= self._get_page_count() - 1:
            return
        self._page += 1
        self._refresh_page()

    def _get_officer_name(self, officer: Officer) -> str:
        return get_officer_display_name(officer)

    def _on_back(self) -> None:
        if self._on_back_callback:
            self._on_back_callback()

    def handle_gamepad_button(self, button: GamepadButton) -> bool:
        if button == GamepadButton.B:
            self._on_back()
            return True
        if button in (GamepadButton.DPAD_LEFT, GamepadButton.LEFT_STICK_LEFT, GamepadButton.LB):
            self._prev_page()
            return True
        if button in (GamepadButton.DPAD_RIGHT, GamepadButton.LEFT_STICK_RIGHT, GamepadButton.RB):
            self._next_page()
            return True
        return False

    def handle_event(self, event: pygame.event.Event, transform=None) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_back()
                return True
            if event.key in (pygame.K_LEFT, pygame.K_PAGEUP):
                self._prev_page()
                return True
            if event.key in (pygame.K_RIGHT, pygame.K_PAGEDOWN):
                self._next_page()
                return True
        return bool(super().handle_event(event, transform))
