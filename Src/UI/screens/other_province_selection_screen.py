"""Map-based other-province selection screen."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from Province import Province
from UI.components.basic import UIButton, UILabel
from UI.components.province_selector import UIProvinceSelector
from UI.core.anchor import Anchor
from UI.core.container import UIContainer
from UI.core.gamepad_handler import GamepadButton
from UI.core.manager import UIManager


class OtherProvinceSelectionScreen(UIContainer):
    """Select any province on the map, then confirm to view it."""

    handles_own_navigation = True

    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 800

    def __init__(self, excluded_provinces: set[int] | None = None):
        super().__init__(
            position=(0, 0),
            size=(self.SCREEN_WIDTH, self.SCREEN_HEIGHT),
            background_color=(26, 26, 46),
            parent=None,
        )

        self._callback: Callable[[int | None], None] | None = None
        self._selected_province: int | None = None
        self._excluded_provinces = excluded_provinces or set()

        self._create_ui()
        self._set_initial_focus()

    def _set_initial_focus(self) -> None:
        """Keep focus off buttons so map navigation owns arrows/gamepad."""
        manager = UIManager.get_instance()
        if manager:
            manager.set_focus(None)

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
            text="View Other Province",
            position=(self.SCREEN_WIDTH // 2, 30),
            size=(600, 40),
            font=pygame.font.Font(None, 40),
            color=(255, 215, 0),
            align="center",
            anchor=Anchor.CENTER,
            parent=self,
        )

        self._selector = UIProvinceSelector(
            position=(20, 70),
            size=(1240, 620),
            playable_provinces=[
                province.No
                for province in Province.GetList()
                if province.No not in self._excluded_provinces
            ],
            on_province_changed=self._on_province_changed,
            on_province_confirmed=self._on_province_confirmed,
            parent=self,
        )

        for province in Province.GetList():
            if province.RulerNo != 0xFF:
                self._selector.map_renderer.set_province_ruler(province.No, province.RulerNo)

        self._info_label = UILabel(
            text="Select a province to inspect.",
            position=(60, 710),
            size=(700, 40),
            font=pygame.font.Font(None, 28),
            color=(232, 232, 232),
            align="left",
            parent=self,
        )

        UIButton(
            text="← Back",
            position=(60, 745),
            size=(180, 40),
            normal_color=(60, 60, 80),
            hover_color=(80, 80, 110),
            text_color=(232, 232, 232),
            font=pygame.font.Font(None, 26),
            on_click=self._on_back,
            parent=self,
        )

    def _on_province_changed(self, province_no: int | None) -> None:
        self._selected_province = province_no
        if province_no is None:
            self._info_label.text = "Select a province to inspect."
            return

        province = Province.FromSequence(province_no)
        self._info_label.text = (
            f"Province {province.No}: Gold {province.Gold:,}, Rice {province.Food:,}, "
            f"Soldiers {province.Soldiers:,}"
        )

    def _on_province_confirmed(self, province_no: int) -> None:
        if self._callback:
            self._callback(province_no)

    def _on_back(self) -> None:
        if self._callback:
            self._callback(None)

    def set_callback(self, callback: Callable[[int | None], None]) -> None:
        self._callback = callback

    def handle_gamepad_button(self, button: GamepadButton) -> bool:
        """Route gamepad input directly to the map selector."""
        manager = UIManager.get_instance()
        transform = manager.transform if manager else None

        if button == GamepadButton.B:
            self._on_back()
            return True

        return bool(transform and self._selector.handle_gamepad_button(button, transform))

    def handle_event(self, event: pygame.event.Event, transform=None) -> bool:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._on_back()
            return True

        if self._selector.handle_event(event, transform):
            return True

        return bool(super().handle_event(event, transform))
