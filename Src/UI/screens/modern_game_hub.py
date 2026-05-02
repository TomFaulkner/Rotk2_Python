"""Modern in-game province hub controller."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from Officer import Officer
from UI.core.manager import UIManager
from UI.screens.officer_list_screen import OfficerListScreen
from UI.screens.internal_affairs_action_screen import InternalAffairsActionScreen
from UI.screens.officer_selection_screen import OfficerSelectionScreen
from UI.screens.officer_summary_screen import OfficerSummaryScreen
from UI.screens.other_province_selection_screen import OtherProvinceSelectionScreen
from UI.screens.reward_action_screen import RewardActionScreen
from UI.screens.snes_province_screen import SnesProvinceScreen
from UI.screens.territory_screen import TerritoryScreen
from services import province_command_service as province_service

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
        province = province_service.get_active_province()
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
            self._show_officer_summary(province_service.get_active_province_no(), self.refresh)
            return
        if action == "general":
            self._show_officer_list(province_service.get_active_province_no(), self.refresh)
            return
        if action == "territory":
            self._show_territory(self.refresh)
            return
        if action == "internal_land":
            self._show_improve_land(self.refresh)
            return
        if action == "internal_flood":
            self._show_flood_control(self.refresh)
            return
        if action == "internal_loyalty":
            self._show_give_food(self.refresh)
            return
        if action == "person_awards":
            self._show_rewards(self.refresh)
            return

        print(f"Unhandled modern hub action: {action}")

    def _show_other_province_selector(self) -> None:
        """Open province selection, then require an officer only for foreign provinces."""
        selector = OtherProvinceSelectionScreen()

        def on_select(province_no: int | None) -> None:
            if province_no is None:
                self.refresh()
                return

            if province_service.can_view_province_freely(province_no):
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
        available_officers = province_service.get_actionable_officers(
            province_service.get_active_province_no()
        )

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

        province_service.consume_action_for_foreign_view(province_no, officer)
        self._show_other_province_view(province_no)

    def _show_other_province_view(self, province_no: int) -> None:
        """Show a restricted province view for a non-active province."""
        province = province_service.get_province(province_no)
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
        province = province_service.get_province(province_no)
        summary_screen = OfficerSummaryScreen(province, on_back=on_back)

        manager = UIManager.get_instance()
        manager.root_component = summary_screen
        manager.current_screen = summary_screen
        self._screen = summary_screen

    def _show_officer_list(self, province_no: int, on_back) -> None:
        """Show the officer list screen for a province."""
        province = province_service.get_province(province_no)
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

    def _show_improve_land(self, on_back) -> None:
        """Show the modern Improve Land flow."""
        screen = InternalAffairsActionScreen(
            province_no=province_service.get_active_province_no(),
            title="Improve Land",
            action_name="Improve Land",
            resource_name="Gold",
            stat_name="Land",
            calculate_estimate=province_service.calculate_improve_land,
            apply_action=province_service.apply_improve_land_with_officers,
            on_back=on_back,
        )

        manager = UIManager.get_instance()
        manager.root_component = screen
        manager.current_screen = screen
        self._screen = screen

    def _show_give_food(self, on_back) -> None:
        """Show the modern Give Food flow."""
        screen = InternalAffairsActionScreen(
            province_no=province_service.get_active_province_no(),
            title="Give Food",
            action_name="Give Food",
            resource_name="Food",
            stat_name="Loyalty",
            calculate_estimate=province_service.calculate_give_food,
            apply_action=province_service.apply_give_food_with_officers,
            on_back=on_back,
        )

        manager = UIManager.get_instance()
        manager.root_component = screen
        manager.current_screen = screen
        self._screen = screen

    def _show_flood_control(self, on_back) -> None:
        """Show the modern Flood Control flow."""
        screen = InternalAffairsActionScreen(
            province_no=province_service.get_active_province_no(),
            title="Flood Control",
            action_name="Flood Control",
            resource_name="Gold",
            stat_name="Flood Control",
            calculate_estimate=province_service.calculate_flood_control,
            apply_action=province_service.apply_flood_control_with_officers,
            on_back=on_back,
        )

        manager = UIManager.get_instance()
        manager.root_component = screen
        manager.current_screen = screen
        self._screen = screen

    def _show_rewards(self, on_back) -> None:
        """Show the modern reward flow."""
        screen = RewardActionScreen(
            province_no=province_service.get_active_province_no(),
            on_back=on_back,
        )

        manager = UIManager.get_instance()
        manager.root_component = screen
        manager.current_screen = screen
        self._screen = screen

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
