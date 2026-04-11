"""Modern territory overview screen for all ruler provinces."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from Officer import Officer
from Province import Province
from Ruler import Ruler
from officer_display import get_officer_display_name
from UI.components.basic import UIButton, UILabel
from UI.core.anchor import Anchor
from UI.core.container import UIContainer
from UI.core.gamepad_handler import GamepadButton


class TerritoryScreen(UIContainer):
    """Show all provinces controlled by the active ruler in a paged list."""

    handles_own_navigation = True
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 800
    PAGE_SIZE = 15

    PROVINCE_NAMES = {
        "幽州": "Youzhou",
        "幷州": "Bingzhou",
        "冀州": "Jizhou",
        "青州": "Qingzhou",
        "兗州": "Yanzhou",
        "司州": "Sizhou",
        "雍州": "Yongzhou",
        "涼州": "Liangzhou",
        "徐州": "Xuzhou",
        "予州": "Yuzhou",
        "荊州": "Jingzhou",
        "揚州": "Yangzhou",
        "益州": "Yizhou",
        "交州": "Jiaozhou",
    }

    def __init__(self, on_back: Callable[[], None] | None = None):
        super().__init__(
            position=(0, 0),
            size=(self.SCREEN_WIDTH, self.SCREEN_HEIGHT),
            background_color=(18, 18, 30),
            parent=None,
        )

        active_ruler_no = Ruler.GetActiveNo()
        self._ruler = Ruler.FromNo(active_ruler_no)
        self._provinces = sorted(Province.GetListByRulerNo(active_ruler_no), key=lambda p: p.No)
        self._on_back_callback = on_back
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
            text=f"{get_officer_display_name(self._ruler.RulerSelf if self._ruler else None)} Territory",
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
            position=(25, 90),
            size=(1230, 620),
            background_color=(24, 28, 44),
            border_color=(79, 189, 186),
            border_width=2,
            parent=self,
        )

        headers = [
            ("Province", 20, 220),
            ("Governor", 250, 250),
            ("Gold", 510, 110),
            ("Rice", 630, 150),
            ("Soldiers", 790, 130),
            ("Generals", 930, 100),
            ("Loyalty", 1040, 100),
        ]

        for text, x, width in headers:
            UILabel(
                text=text,
                position=(x, 20),
                size=(width, 32),
                font=pygame.font.Font(None, 28),
                color=(255, 215, 0),
                align="left",
                parent=self._table,
            )

        row_y = 65
        row_height = 36
        for _ in range(self.PAGE_SIZE):
            self._row_labels.append(self._add_row(self._table, row_y))
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

    def _add_row(self, parent: UIContainer, y: int) -> list[UILabel]:
        columns = [
            (20, 220),
            (250, 250),
            (510, 110),
            (630, 150),
            (790, 130),
            (930, 100),
            (1040, 100),
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
        return max(1, (len(self._provinces) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)

    def _get_province_name(self, province: Province) -> str:
        name = province.Name
        for chinese, english in self.PROVINCE_NAMES.items():
            if chinese in name:
                return name.replace(chinese, english)
        return name

    def _get_governor_name(self, province: Province) -> str:
        governor = Officer.FromOffset(province.GovernorOffset)
        return get_officer_display_name(governor)

    def _refresh_page(self) -> None:
        start = self._page * self.PAGE_SIZE
        page_provinces = self._provinces[start : start + self.PAGE_SIZE]
        for row_labels, province in zip(self._row_labels, page_provinces, strict=False):
            values = [
                self._get_province_name(province),
                self._get_governor_name(province),
                f"{province.Gold:,}",
                f"{province.Food:,}",
                f"{province.Soldiers:,}",
                str(len(province.GetOfficerList())),
                str(province.Loyalty),
            ]
            for label, value in zip(row_labels, values, strict=True):
                label.text = value

        for row_labels in self._row_labels[len(page_provinces) :]:
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
