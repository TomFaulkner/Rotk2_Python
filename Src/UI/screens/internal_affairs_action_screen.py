"""Reusable modern internal-affairs action flow screen."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from officer_display import get_officer_display_name
from UI.components.basic import UIButton, UILabel
from UI.core.anchor import Anchor
from UI.core.container import UIContainer
from UI.core.gamepad_handler import GamepadButton
from UI.core.manager import UIManager
from services import province_command_service as province_service


class InternalAffairsActionScreen(UIContainer):
    """Run a province improvement action with advisor preview and confirmation."""

    handles_own_navigation = True
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 800
    OFFICERS_PER_PAGE = 10

    def __init__(
        self,
        province_no: int,
        title: str,
        action_name: str,
        resource_name: str,
        stat_name: str,
        calculate_estimate: Callable,
        apply_action: Callable,
        on_back: Callable[[], None] | None = None,
    ):
        super().__init__(
            position=(0, 0),
            size=(self.SCREEN_WIDTH, self.SCREEN_HEIGHT),
            background_color=(18, 18, 30),
            parent=None,
        )

        self._province_no = province_no
        self._title = title
        self._action_name = action_name
        self._resource_name = resource_name
        self._stat_name = stat_name
        self._calculate_estimate = calculate_estimate
        self._apply_action = apply_action
        self._on_back_callback = on_back
        self._selected_officer = None
        self._estimate = None
        self._advisor_opinion = None
        self._mode = "selection"
        self._available_officers: list = []
        self._entry_officer_buttons: list[UIButton] = []
        self._control_buttons: list[UIButton] = []
        self._preview_buttons: list[UIButton] = []
        self._result_buttons: list[UIButton] = []
        self._focus_region = "officers"
        self._control_focus_index = 0
        self._selected_officer_index = 0
        self._selected_officer_offsets: set[int] = set()
        self._focused_officer_offset: int | None = None
        self._lead_officer_offset: int | None = None
        self._max_spend = 0
        self._current_spend = 0

        self._create_base_ui()
        self._show_selection_state()

    def _create_base_ui(self) -> None:
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

        self._body = UIContainer(
            position=(40, 90),
            size=(1200, 620),
            background_color=(24, 28, 44),
            border_color=(79, 189, 186),
            border_width=2,
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

    def _clear_body(self) -> None:
        self._body.clear_children()

    def _show_selection_state(self) -> None:
        self._mode = "selection"
        self._clear_body()
        province = province_service.get_province(self._province_no)
        resource_amount = province.Gold if self._resource_name == "Gold" else province.Food
        self._available_officers = province_service.get_actionable_officers(self._province_no)
        available_offsets = {officer.Offset for officer in self._available_officers}
        self._selected_officer_offsets &= available_offsets
        if self._lead_officer_offset not in available_offsets:
            self._lead_officer_offset = None
        if self._focused_officer_offset not in available_offsets:
            self._focused_officer_offset = None
        if self._focused_officer_offset is None and self._available_officers:
            self._focused_officer_offset = self._available_officers[0].Offset
        selected_count = len(self._selected_officer_offsets)
        max_spend = province_service.get_internal_affairs_max_spend_for_selection(
            resource_amount, selected_count
        )
        self._max_spend = max_spend
        self._current_spend = min(self._current_spend, self._max_spend)
        actionable_count = province_service.get_actionable_officer_count(self._province_no)
        advisor = province_service.get_advisor_in_province(self._province_no)
        self._entry_officer_buttons = []
        self._control_buttons = []
        self._preview_buttons = []
        self._result_buttons = []
        self._focus_region = "officers"
        self._control_focus_index = 0

        UILabel(
            text=(f"Choose one or more officers for {self._action_name}."),
            position=(30, 40),
            size=(1100, 32),
            font=pygame.font.Font(None, 30),
            color=(232, 232, 232),
            align="left",
            parent=self._body,
        )

        UILabel(
            text=(
                f"Province {province.No}  {self._resource_name}: {resource_amount:,}  "
                f"Actionable Officers: {actionable_count}  Selected: {selected_count}  Max Spend: {max_spend:,}"
            ),
            position=(30, 85),
            size=(1100, 28),
            font=pygame.font.Font(None, 26),
            color=(200, 200, 180),
            align="left",
            parent=self._body,
        )

        if advisor:
            UILabel(
                text=f"Advisor present: {get_officer_display_name(advisor)} (Int {advisor.Int})",
                position=(30, 120),
                size=(1100, 28),
                font=pygame.font.Font(None, 24),
                color=(100, 200, 200),
                align="left",
                parent=self._body,
            )

        if not self._available_officers:
            UILabel(
                text="No officers in this province can act this month.",
                position=(30, 180),
                size=(1100, 32),
                font=pygame.font.Font(None, 30),
                color=(255, 140, 140),
                align="left",
                parent=self._body,
            )
            return

        if selected_count < 1:
            UILabel(
                text="Select at least one officer, then press Enter or Right to continue.",
                position=(30, 180),
                size=(1100, 32),
                font=pygame.font.Font(None, 30),
                color=(255, 215, 0),
                align="left",
                parent=self._body,
            )
        elif max_spend < 1:
            UILabel(
                text=f"Not enough {self._resource_name.lower()} for this action.",
                position=(30, 180),
                size=(1100, 32),
                font=pygame.font.Font(None, 30),
                color=(255, 140, 140),
                align="left",
                parent=self._body,
            )
            return

        if self._available_officers:
            focused_officer = self._get_focused_officer()
            self._selected_officer = focused_officer
            if focused_officer is not None:
                self._selected_officer_index = self._available_officers.index(focused_officer)

        UILabel(
            text="Officer:",
            position=(30, 190),
            size=(160, 32),
            font=pygame.font.Font(None, 28),
            color=(255, 215, 0),
            align="left",
            parent=self._body,
        )

        visible_officers = self._get_visible_officers()
        page_index = self._get_selection_page_index()
        page_count = self._get_selection_page_count()

        UILabel(
            text=f"Page {page_index + 1}/{page_count}  Showing {page_index * self.OFFICERS_PER_PAGE + 1}-{page_index * self.OFFICERS_PER_PAGE + len(visible_officers)} of {len(self._available_officers)}",
            position=(270, 190),
            size=(380, 32),
            font=pygame.font.Font(None, 24),
            color=(190, 190, 190),
            align="left",
            parent=self._body,
        )

        officer_y = 235
        officer_height = 40
        start_index = page_index * self.OFFICERS_PER_PAGE
        for local_index, officer in enumerate(visible_officers, start=1):
            officer_index = start_index + local_index
            button = UIButton(
                text=(
                    f"{officer_index}. {'[x]' if officer.Offset in self._selected_officer_offsets else '[ ]'} {get_officer_display_name(officer)}   "
                    f"Int {officer.Int}  Charm {officer.Chm}"
                ),
                position=(30, officer_y + (local_index - 1) * officer_height),
                size=(520, 34),
                normal_color=(40, 46, 68),
                hover_color=(65, 72, 102),
                pressed_color=(55, 62, 92),
                text_color=(232, 232, 232),
                font=pygame.font.Font(None, 24),
                on_click=lambda selected=officer: self._toggle_officer(selected),
                parent=self._body,
            )
            button.label.align = "left"
            self._entry_officer_buttons.append(button)

        UILabel(
            text=(
                "Up/Down moves through all officers, Right focuses Continue, Enter toggles or activates, Esc goes back."
            ),
            position=(620, 220),
            size=(520, 56),
            font=pygame.font.Font(None, 24),
            color=(190, 190, 190),
            align="left",
            parent=self._body,
        )

        self._selection_label = UILabel(
            text="Select one or more officers, then continue to spend entry.",
            position=(620, 320),
            size=(520, 60),
            font=pygame.font.Font(None, 28),
            color=(220, 220, 220),
            align="left",
            parent=self._body,
        )

        continue_button = UIButton(
            text="Continue",
            position=(620, 420),
            size=(180, 40),
            normal_color=(70, 100, 70),
            hover_color=(90, 130, 90),
            text_color=(255, 255, 255),
            font=pygame.font.Font(None, 28),
            on_click=self._continue_to_spend_entry,
            parent=self._body,
        )
        self._control_buttons.append(continue_button)

        self._sync_entry_focus()

    def _show_spend_entry_state(self) -> None:
        self._mode = "spend"
        self._clear_body()
        province = province_service.get_province(self._province_no)
        resource_amount = province.Gold if self._resource_name == "Gold" else province.Food
        selected_officers = self._get_selected_officers()
        selected_count = len(selected_officers)
        self._max_spend = province_service.get_internal_affairs_max_spend_for_selection(
            resource_amount, selected_count
        )
        if self._current_spend < 1 and self._max_spend > 0:
            self._current_spend = min(self._max_spend, selected_count * 100)
        self._current_spend = min(self._current_spend, self._max_spend)
        self._entry_officer_buttons = []
        self._control_buttons = []
        self._preview_buttons = []
        self._result_buttons = []
        self._focus_region = "controls"
        self._control_focus_index = 0

        lead_officer = self._get_lead_officer()
        lead_name = get_officer_display_name(lead_officer) if lead_officer else "None"

        UILabel(
            text=(f"Enter {self._resource_name.lower()} to spend for {self._action_name}."),
            position=(30, 40),
            size=(1100, 32),
            font=pygame.font.Font(None, 30),
            color=(232, 232, 232),
            align="left",
            parent=self._body,
        )

        UILabel(
            text=(
                f"Selected: {selected_count} officer(s)  Lead: {lead_name}  {self._resource_name}: {resource_amount:,}  Max Spend: {self._max_spend:,}"
            ),
            position=(30, 85),
            size=(1100, 28),
            font=pygame.font.Font(None, 26),
            color=(200, 200, 180),
            align="left",
            parent=self._body,
        )

        UILabel(
            text=f"Spend {self._resource_name}:",
            position=(30, 170),
            size=(220, 32),
            font=pygame.font.Font(None, 28),
            color=(255, 215, 0),
            align="left",
            parent=self._body,
        )

        self._spend_value_label = UILabel(
            text=f"{self._current_spend:,}",
            position=(30, 215),
            size=(320, 48),
            font=pygame.font.Font(None, 42),
            color=(255, 255, 255),
            align="left",
            parent=self._body,
        )

        UILabel(
            text="Type numbers, arrows move menu focus, Q / gamepad X toggles Max/0, E / gamepad Y adds 100.",
            position=(30, 275),
            size=(900, 32),
            font=pygame.font.Font(None, 24),
            color=(190, 190, 190),
            align="left",
            parent=self._body,
        )

        spend_options = self._build_spend_options(self._max_spend)
        spend_y = 345
        for index, amount in enumerate(spend_options):
            button = UIButton(
                text=f"{amount:,}",
                position=(30 + (index % 3) * 150, spend_y + (index // 3) * 48),
                size=(120, 34),
                normal_color=(60, 60, 80),
                hover_color=(80, 80, 110),
                pressed_color=(55, 62, 92),
                text_color=(232, 232, 232),
                font=pygame.font.Font(None, 24),
                on_click=lambda value=amount: self._choose_spend(value),
                parent=self._body,
            )
            self._control_buttons.append(button)

        preview_button = UIButton(
            text="Preview",
            position=(30, 500),
            size=(180, 40),
            normal_color=(70, 100, 70),
            hover_color=(90, 130, 90),
            text_color=(255, 255, 255),
            font=pygame.font.Font(None, 28),
            on_click=self._preview_current_selection,
            parent=self._body,
        )
        self._control_buttons.append(preview_button)

        max_button = UIButton(
            text="Max",
            position=(230, 500),
            size=(120, 40),
            normal_color=(60, 60, 80),
            hover_color=(80, 80, 110),
            text_color=(232, 232, 232),
            font=pygame.font.Font(None, 24),
            on_click=self._set_spend_to_max,
            parent=self._body,
        )
        self._control_buttons.append(max_button)

        clear_button = UIButton(
            text="Clear",
            position=(370, 500),
            size=(120, 40),
            normal_color=(60, 60, 80),
            hover_color=(80, 80, 110),
            text_color=(232, 232, 232),
            font=pygame.font.Font(None, 24),
            on_click=self._clear_spend,
            parent=self._body,
        )
        self._control_buttons.append(clear_button)

        back_button = UIButton(
            text="Change Officers",
            position=(510, 500),
            size=(220, 40),
            normal_color=(60, 60, 80),
            hover_color=(80, 80, 110),
            text_color=(232, 232, 232),
            font=pygame.font.Font(None, 26),
            on_click=self._show_selection_state,
            parent=self._body,
        )
        self._control_buttons.append(back_button)

        self._selection_label = UILabel(
            text="Enter a spend amount, then preview the result.",
            position=(30, 575),
            size=(720, 60),
            font=pygame.font.Font(None, 28),
            color=(220, 220, 220),
            align="left",
            parent=self._body,
        )

        self._sync_entry_focus()

    def _build_spend_options(self, max_spend: int) -> list[int]:
        base_values = [100, 200, 300, 400, 500, 700, 1000, max_spend]
        spend_options: list[int] = []
        for value in base_values:
            capped = min(max_spend, value)
            if capped > 0 and capped not in spend_options:
                spend_options.append(capped)
        return spend_options[:8]

    def _get_selection_page_index(self) -> int:
        if not self._available_officers:
            return 0
        return self._selected_officer_index // self.OFFICERS_PER_PAGE

    def _get_selection_page_count(self) -> int:
        if not self._available_officers:
            return 1
        return (
            len(self._available_officers) + self.OFFICERS_PER_PAGE - 1
        ) // self.OFFICERS_PER_PAGE

    def _get_visible_officers(self) -> list:
        page_index = self._get_selection_page_index()
        start = page_index * self.OFFICERS_PER_PAGE
        end = start + self.OFFICERS_PER_PAGE
        return self._available_officers[start:end]

    def _toggle_officer(self, officer) -> None:
        officer_offset = officer.Offset
        self._focused_officer_offset = officer_offset
        self._selected_officer = officer
        if officer_offset in self._selected_officer_offsets:
            self._selected_officer_offsets.remove(officer_offset)
            if self._lead_officer_offset == officer_offset:
                self._lead_officer_offset = next(iter(self._selected_officer_offsets), None)
        else:
            self._selected_officer_offsets.add(officer_offset)
            self._lead_officer_offset = officer_offset

        self._show_selection_state()

    def _sync_entry_focus(self) -> None:
        if self._mode == "selection" and self._entry_officer_buttons:
            manager = UIManager.get_instance()
            if manager:
                if self._focus_region == "controls" and self._control_buttons:
                    visible_index = min(self._control_focus_index, len(self._control_buttons) - 1)
                    manager.set_focus(self._control_buttons[visible_index])
                else:
                    visible_index = self._selected_officer_index % self.OFFICERS_PER_PAGE
                    visible_index = min(visible_index, len(self._entry_officer_buttons) - 1)
                    manager.set_focus(self._entry_officer_buttons[visible_index])
            return
        if self._mode == "spend" and self._control_buttons:
            manager = UIManager.get_instance()
            if manager:
                visible_index = min(self._control_focus_index, len(self._control_buttons) - 1)
                manager.set_focus(self._control_buttons[visible_index])
            return

    def _update_spend_display(self) -> None:
        if hasattr(self, "_spend_value_label"):
            self._spend_value_label.text = f"{self._current_spend:,}"

    def _set_current_spend(self, spend: int) -> None:
        self._current_spend = max(0, min(self._max_spend, spend))
        self._update_spend_display()

    def _set_spend_to_max(self) -> None:
        self._set_current_spend(self._max_spend)

    def _clear_spend(self) -> None:
        self._set_current_spend(0)

    def _toggle_max_zero(self) -> None:
        if self._current_spend != self._max_spend:
            self._set_current_spend(self._max_spend)
        else:
            self._set_current_spend(0)

    def _increment_spend(self, delta: int) -> None:
        self._set_current_spend(self._current_spend + delta)

    def _append_digit(self, digit: str) -> None:
        proposed = f"{self._current_spend}{digit}" if self._current_spend != 0 else digit
        self._set_current_spend(int(proposed))

    def _backspace_spend(self) -> None:
        self._set_current_spend(int(str(self._current_spend)[:-1] or "0"))

    def _move_officer_selection(self, delta: int) -> None:
        if not self._available_officers:
            return
        previous_page_index = self._get_selection_page_index()
        self._selected_officer_index = max(
            0, min(len(self._available_officers) - 1, self._selected_officer_index + delta)
        )
        self._selected_officer = self._available_officers[self._selected_officer_index]
        self._focused_officer_offset = self._selected_officer.Offset
        current_page_index = self._get_selection_page_index()
        if current_page_index != previous_page_index:
            self._show_selection_state()
            return
        self._sync_entry_focus()
        if hasattr(self, "_selection_label"):
            self._selection_label.text = (
                f"Focused {get_officer_display_name(self._selected_officer)}. "
                f"Press Enter/A to toggle selection. Current spend: {self._current_spend:,}."
            )

    def _move_control_focus(self, delta: int) -> None:
        if not self._control_buttons:
            return
        self._control_focus_index = max(
            0, min(len(self._control_buttons) - 1, self._control_focus_index + delta)
        )
        self._sync_entry_focus()

    def _focus_controls(self) -> None:
        if self._mode != "spend":
            return
        if not self._control_buttons:
            return
        self._focus_region = "controls"
        self._sync_entry_focus()

    def _focus_officers(self) -> None:
        if self._mode != "selection":
            return
        if not self._entry_officer_buttons:
            return
        self._focus_region = "officers"
        self._sync_entry_focus()

    def _get_focused_officer(self):
        for officer in self._available_officers:
            if officer.Offset == self._focused_officer_offset:
                return officer
        return self._available_officers[0] if self._available_officers else None

    def _get_selected_officers(self) -> list:
        return [
            officer
            for officer in self._available_officers
            if officer.Offset in self._selected_officer_offsets
        ]

    def _get_lead_officer(self):
        for officer in self._available_officers:
            if officer.Offset == self._lead_officer_offset:
                return officer
        selected = self._get_selected_officers()
        return selected[0] if selected else None

    def _preview_current_selection(self) -> None:
        self._choose_spend(self._current_spend)

    def _continue_to_spend_entry(self) -> None:
        selected_officers = self._get_selected_officers()
        if not selected_officers:
            if hasattr(self, "_selection_label"):
                self._selection_label.text = "Select at least one officer before continuing."
            return
        if self._max_spend < 1:
            if hasattr(self, "_selection_label"):
                self._selection_label.text = (
                    f"Not enough {self._resource_name.lower()} to continue with this selection."
                )
            return
        self._show_spend_entry_state()

    def _choose_spend(self, spend: int) -> None:
        selected_officers = self._get_selected_officers()
        if not selected_officers:
            if hasattr(self, "_selection_label"):
                self._selection_label.text = (
                    "Select at least one officer before setting the spend amount."
                )
            return
        if spend < 1:
            if hasattr(self, "_selection_label"):
                self._selection_label.text = (
                    f"Current spend is 0. Press Q or use the Max button, or enter at least 1 "
                    f"{self._resource_name.lower()} before previewing."
                )
            return

        primary_officer = self._get_lead_officer() or selected_officers[0]
        self._estimate = self._calculate_estimate(
            self._province_no, primary_officer, spend, selected_officers
        )
        self._advisor_opinion = province_service.get_advisor_opinion(self._estimate)
        self._show_preview_state()

    def _show_preview_state(self) -> None:
        self._mode = "preview"
        self._clear_body()
        if self._estimate is None:
            self._show_spend_entry_state()
            return

        UILabel(
            text=(
                f"{len(self._selected_officer_offsets)} selected officer(s) led by {self._estimate.officer_name} will spend {self._estimate.cost_amount:,} "
                f"{self._resource_name.lower()} on {self._action_name}."
            ),
            position=(30, 40),
            size=(1100, 32),
            font=pygame.font.Font(None, 30),
            color=(232, 232, 232),
            align="left",
            parent=self._body,
        )

        UILabel(
            text=(
                f"{self._stat_name}: {self._estimate.current_value} -> {self._estimate.projected_value} "
                f"(gain {self._estimate.projected_gain})"
            ),
            position=(30, 95),
            size=(1100, 32),
            font=pygame.font.Font(None, 28),
            color=(255, 215, 0),
            align="left",
            parent=self._body,
        )

        if self._advisor_opinion is not None:
            accuracy = "exact" if self._advisor_opinion.exact else "expected"
            UILabel(
                text=(
                    f"Advisor {self._advisor_opinion.advisor_name} ({accuracy}) expects "
                    f"{self._stat_name} to reach {self._advisor_opinion.predicted_value} "
                    f"(gain {self._advisor_opinion.predicted_gain})."
                ),
                position=(30, 160),
                size=(1100, 60),
                font=pygame.font.Font(None, 28),
                color=(100, 200, 200),
                align="left",
                parent=self._body,
            )

        UILabel(
            text="Original behavior is preserved: resources are spent even if the gain is 0.",
            position=(30, 260),
            size=(1100, 32),
            font=pygame.font.Font(None, 24),
            color=(255, 150, 150),
            align="left",
            parent=self._body,
        )

        confirm_button = UIButton(
            text="Confirm",
            position=(30, 340),
            size=(180, 40),
            normal_color=(70, 100, 70),
            hover_color=(90, 130, 90),
            text_color=(255, 255, 255),
            font=pygame.font.Font(None, 28),
            on_click=self._confirm_action,
            parent=self._body,
        )
        self._preview_buttons = [confirm_button]

        change_button = UIButton(
            text="Change Selection",
            position=(230, 340),
            size=(220, 40),
            normal_color=(60, 60, 80),
            hover_color=(80, 80, 110),
            text_color=(232, 232, 232),
            font=pygame.font.Font(None, 26),
            on_click=self._show_selection_state,
            parent=self._body,
        )
        self._preview_buttons.append(change_button)

        manager = UIManager.get_instance()
        if manager:
            manager.set_focus(confirm_button)

    def _confirm_action(self) -> None:
        if self._estimate is None:
            return
        result = self._apply_action(
            self._estimate.province_no,
            self._estimate.officer,
            self._estimate.cost_amount,
            self._get_selected_officers(),
        )
        self._estimate = result
        self._show_result_state()

    def _show_result_state(self) -> None:
        self._mode = "result"
        self._clear_body()
        if self._estimate is None:
            self._show_selection_state()
            return

        UILabel(
            text=f"{self._action_name} complete.",
            position=(30, 40),
            size=(1100, 40),
            font=pygame.font.Font(None, 34),
            color=(255, 215, 0),
            align="left",
            parent=self._body,
        )

        UILabel(
            text=(
                f"{len(self._selected_officer_offsets)} officer(s) spent {self._estimate.cost_amount:,} {self._resource_name.lower()}."
            ),
            position=(30, 110),
            size=(1100, 32),
            font=pygame.font.Font(None, 28),
            color=(232, 232, 232),
            align="left",
            parent=self._body,
        )

        UILabel(
            text=(
                f"{self._stat_name}: {self._estimate.current_value} -> {self._estimate.projected_value} "
                f"(gain {self._estimate.projected_gain})"
            ),
            position=(30, 160),
            size=(1100, 32),
            font=pygame.font.Font(None, 30),
            color=(100, 220, 120) if self._estimate.projected_gain > 0 else (255, 160, 160),
            align="left",
            parent=self._body,
        )

        back_button = UIButton(
            text="Back to Province",
            position=(30, 250),
            size=(240, 40),
            normal_color=(60, 60, 80),
            hover_color=(80, 80, 110),
            text_color=(232, 232, 232),
            font=pygame.font.Font(None, 26),
            on_click=self._on_back,
            parent=self._body,
        )
        self._result_buttons = [back_button]

        manager = UIManager.get_instance()
        if manager:
            manager.set_focus(back_button)

    def _on_back(self) -> None:
        if self._on_back_callback:
            self._on_back_callback()

    def handle_gamepad_button(self, button: GamepadButton) -> bool:
        if button == GamepadButton.B:
            self._on_back()
            return True
        if self._mode == "selection":
            if self._focus_region == "officers" and button in (
                GamepadButton.DPAD_UP,
                GamepadButton.LEFT_STICK_UP,
            ):
                self._move_officer_selection(-1)
                return True
            if self._focus_region == "officers" and button in (
                GamepadButton.DPAD_DOWN,
                GamepadButton.LEFT_STICK_DOWN,
            ):
                self._move_officer_selection(1)
                return True
            if self._focus_region == "officers" and button == GamepadButton.A:
                if self._available_officers:
                    self._toggle_officer(self._available_officers[self._selected_officer_index])
                return True
            if self._focus_region == "officers" and button in (
                GamepadButton.DPAD_LEFT,
                GamepadButton.LEFT_STICK_LEFT,
            ):
                return True
            if self._focus_region == "officers" and button in (
                GamepadButton.DPAD_RIGHT,
                GamepadButton.LEFT_STICK_RIGHT,
            ):
                self._focus_region = "controls"
                self._control_focus_index = 0
                self._sync_entry_focus()
                return True
            if self._focus_region == "controls" and button in (
                GamepadButton.DPAD_LEFT,
                GamepadButton.LEFT_STICK_LEFT,
            ):
                self._focus_region = "officers"
                self._sync_entry_focus()
                return True
            if (
                self._focus_region == "controls"
                and button == GamepadButton.A
                and self._control_buttons
            ):
                self._control_buttons[self._control_focus_index].on_click()
                return True
        elif self._mode == "spend":
            if button in (GamepadButton.DPAD_LEFT, GamepadButton.LEFT_STICK_LEFT):
                self._move_control_focus(-1)
                return True
            if button in (GamepadButton.DPAD_RIGHT, GamepadButton.LEFT_STICK_RIGHT):
                self._move_control_focus(1)
                return True
            if button in (GamepadButton.DPAD_UP, GamepadButton.LEFT_STICK_UP):
                self._move_control_focus(-3)
                return True
            if button in (GamepadButton.DPAD_DOWN, GamepadButton.LEFT_STICK_DOWN):
                self._move_control_focus(3)
                return True
            if button == GamepadButton.X:
                self._toggle_max_zero()
                return True
            if button == GamepadButton.Y:
                self._increment_spend(100)
                return True
            if button == GamepadButton.RB:
                self._preview_current_selection()
                return True
            if button == GamepadButton.A and self._control_buttons:
                self._control_buttons[self._control_focus_index].on_click()
                return True
        elif self._mode == "preview" and button == GamepadButton.A:
            self._confirm_action()
            return True
        elif self._mode == "result" and button == GamepadButton.A:
            self._on_back()
            return True
        return False

    def handle_event(self, event: pygame.event.Event, transform=None) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_back()
                return True
            if self._mode == "selection":
                if event.key == pygame.K_TAB:
                    return True
                if self._focus_region == "officers" and event.key == pygame.K_UP:
                    self._move_officer_selection(-1)
                    return True
                if self._focus_region == "officers" and event.key == pygame.K_DOWN:
                    self._move_officer_selection(1)
                    return True
                if self._focus_region == "officers" and event.key == pygame.K_RETURN:
                    if self._available_officers:
                        self._toggle_officer(self._available_officers[self._selected_officer_index])
                    return True
                if self._focus_region == "officers" and event.key == pygame.K_LEFT:
                    return True
                if self._focus_region == "officers" and event.key == pygame.K_RIGHT:
                    self._focus_region = "controls"
                    self._control_focus_index = 0
                    self._sync_entry_focus()
                    return True
                if self._focus_region == "controls" and event.key == pygame.K_LEFT:
                    self._focus_region = "officers"
                    self._sync_entry_focus()
                    return True
                if (
                    self._focus_region == "controls"
                    and event.key == pygame.K_RETURN
                    and self._control_buttons
                ):
                    self._control_buttons[self._control_focus_index].on_click()
                    return True
            elif self._mode == "spend":
                if event.key == pygame.K_TAB:
                    return True
                if event.key == pygame.K_LEFT:
                    self._move_control_focus(-1)
                    return True
                if event.key == pygame.K_RIGHT:
                    self._move_control_focus(1)
                    return True
                if event.key == pygame.K_UP:
                    self._move_control_focus(-3)
                    return True
                if event.key == pygame.K_DOWN:
                    self._move_control_focus(3)
                    return True
                if event.key == pygame.K_q:
                    self._toggle_max_zero()
                    return True
                if event.key == pygame.K_e:
                    self._increment_spend(100)
                    return True
                if event.key == pygame.K_BACKSPACE:
                    self._backspace_spend()
                    return True
                if event.key == pygame.K_SPACE:
                    self._preview_current_selection()
                    return True
                if event.key == pygame.K_RETURN and self._control_buttons:
                    self._control_buttons[self._control_focus_index].on_click()
                    return True
                if pygame.K_0 <= event.key <= pygame.K_9:
                    self._append_digit(chr(event.key))
                    return True
                if pygame.K_KP0 <= event.key <= pygame.K_KP9:
                    self._append_digit(chr(event.key - pygame.K_KP0 + ord("0")))
                    return True
            elif self._mode == "preview" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._confirm_action()
                return True
            elif self._mode == "result" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._on_back()
                return True
        return bool(super().handle_event(event, transform))
