"""Modern in-game province hub controller."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from Officer import Officer
from Province import Province
from Ruler import Ruler
from UI.core.manager import UIManager
from UI.screens.officer_list_screen import OfficerListScreen
from UI.screens.officer_selection_screen import OfficerSelectionScreen
from UI.screens.officer_summary_screen import OfficerSummaryScreen
from UI.screens.other_province_selection_screen import OtherProvinceSelectionScreen
from UI.screens.snes_province_screen import SnesProvinceScreen
from UI.screens.territory_screen import TerritoryScreen

if TYPE_CHECKING:
    from UI.core.transform import Transform


class ModernGameHub:
    """Owns the modern province hub and refreshes it from active game state."""

    def __init__(self):
        self._screen: SnesProvinceScreen | None = None
        self.refresh()

    @property
    def screen(self) -> SnesProvinceScreen | None:
        """Return the active province hub screen."""
        return self._screen

    def refresh(self) -> None:
        """Rebuild the province hub from the current active province."""
        province = Province.FromSequence(Province.GetActiveNo())
        self._screen = SnesProvinceScreen(province)
        self._screen.set_action_callback(self._handle_action)

        manager = UIManager.get_instance()
        manager.root_component = self._screen
        manager.current_screen = self._screen

    def _handle_action(self, action: str) -> None:
        """Handle currently enabled modern hub actions."""
        if action == "other_province":
            self._show_other_province_selector()
            return
        if action == "summary":
            self._show_officer_summary(Province.GetActiveNo(), self.refresh)
            return
        if action == "general":
            self._show_officer_list(Province.GetActiveNo(), self.refresh)
            return
        if action == "territory":
            self._show_territory(self.refresh)
            return

        print(f"Unhandled modern hub action: {action}")

    def _show_other_province_selector(self) -> None:
        """Open province selection, then require an officer only for foreign provinces."""
        selector = OtherProvinceSelectionScreen()
        active_ruler_no = Ruler.GetActiveNo()

        def on_select(province_no: int | None) -> None:
            if province_no is None:
                self.refresh()
                return

            selected_province = Province.FromSequence(province_no)
            if selected_province.RulerNo == active_ruler_no:
                self._show_other_province_view(province_no)
                return

            self._show_other_province_officer_picker(province_no)

        selector.set_callback(on_select)

        manager = UIManager.get_instance()
        manager.root_component = selector
        manager.current_screen = selector
        self._screen = selector

    def _show_other_province_officer_picker(self, province_no: int) -> None:
        """Choose the officer who will spend their action to inspect a foreign province."""
        active_province = Province.FromSequence(Province.GetActiveNo())
        available_officers = [
            officer for officer in active_province.GetOfficerList() if officer.CanAction()
        ]

        if not available_officers:
            print("No officers can act this month.")
            self._show_other_province_selector()
            return

        picker = OfficerSelectionScreen(
            available_officers,
            title="Choose General",
            subtitle=(
                f"Viewing Province {province_no} is a foreign inspection. "
                "Select the officer who will spend their action."
            ),
            on_select=lambda officer: self._on_other_province_officer_selected(
                province_no, officer
            ),
        )

        manager = UIManager.get_instance()
        manager.root_component = picker
        manager.current_screen = picker
        self._screen = picker

    def _on_other_province_officer_selected(
        self, province_no: int, officer: Officer | None
    ) -> None:
        """Consume an officer action, then open the selected foreign province."""
        if officer is None:
            self._show_other_province_selector()
            return

        officer.SetActionStatus()
        self._show_other_province_view(province_no)

    def _show_other_province_view(self, province_no: int) -> None:
        """Show a restricted province view for a non-active province."""
        province = Province.FromSequence(province_no)
        view_screen = SnesProvinceScreen(
            province,
            enabled_menus={"view"},
            enabled_submenu_actions={"back", "general", "summary"},
            prompt_text=f"Viewing Province {province.No}",
            on_back=self._show_other_province_selector,
        )

        def on_action(action: str) -> None:
            if action == "back":
                self._show_other_province_selector()
            elif action == "summary":
                self._show_officer_summary(
                    province_no, lambda: self._show_other_province_view(province_no)
                )
            elif action == "general":
                self._show_officer_list(
                    province_no, lambda: self._show_other_province_view(province_no)
                )

        view_screen.set_action_callback(on_action)

        manager = UIManager.get_instance()
        manager.root_component = view_screen
        manager.current_screen = view_screen
        self._screen = view_screen

    def _show_officer_summary(self, province_no: int, on_back) -> None:
        """Show the combined officer summary screen for a province."""
        province = Province.FromSequence(province_no)
        summary_screen = OfficerSummaryScreen(province, on_back=on_back)

        manager = UIManager.get_instance()
        manager.root_component = summary_screen
        manager.current_screen = summary_screen
        self._screen = summary_screen

    def _show_officer_list(self, province_no: int, on_back) -> None:
        """Show the officer list screen for a province."""
        province = Province.FromSequence(province_no)
        officer_screen = OfficerListScreen(province, on_back=on_back)

        manager = UIManager.get_instance()
        manager.root_component = officer_screen
        manager.current_screen = officer_screen
        self._screen = officer_screen

    def _show_territory(self, on_back) -> None:
        """Show a list of all provinces controlled by the active ruler."""
        territory_screen = TerritoryScreen(on_back=on_back)

        manager = UIManager.get_instance()
        manager.root_component = territory_screen
        manager.current_screen = territory_screen
        self._screen = territory_screen

    def handle_event(self, event: pygame.event.Event, transform: Transform | None = None) -> bool:
        """Forward events to the current province screen."""
        if not self._screen:
            return False
        return self._screen.handle_event(event, transform)

    def update(self, dt: float) -> None:
        """Update the current screen."""
        if self._screen:
            self._screen.update(dt)

    def render(self, surface: pygame.Surface, transform: Transform) -> None:
        """Render the current screen."""
        if self._screen:
            self._screen.render(surface, transform)
