"""Modern province training flow."""

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


class TrainingActionScreen(UIContainer):
    """Choose one or more trainers, preview province training, and apply it."""

    handles_own_navigation = True
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 800
    OFFICERS_PER_PAGE = 10

    def __init__(self, province_no: int, on_back: Callable[[], None] | None = None):
        super().__init__(
            position=(0, 0),
            size=(self.SCREEN_WIDTH, self.SCREEN_HEIGHT),
            background_color=(18, 18, 30),
            parent=None,
        )

        self._province_no = province_no
        self._on_back_callback = on_back
        self._mode = "selection"
        self._trainer_candidates: list = []
        self._buttons: list[UIButton] = []
        self._trainer_buttons: list[UIButton] = []
        self._control_buttons: list[UIButton] = []
        self._selected_index = 0
        self._control_index = 0
        self._focus_region = "trainers"
        self._selected_trainer_offsets: set[int] = set()
        self._estimate = None

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
            text="Training",
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
            on_click=self._handle_back,
            parent=self,
        )

    def _clear_body(self) -> None:
        self._body.clear_children()
        self._buttons = []
        self._trainer_buttons = []
        self._control_buttons = []

    def _sync_focus(self) -> None:
        manager = UIManager.get_instance()
        if not manager:
            return
        if self._mode == "selection":
            if self._focus_region == "controls" and self._control_buttons:
                visible_index = min(self._control_index, len(self._control_buttons) - 1)
                manager.set_focus(self._control_buttons[visible_index])
                return
            if self._trainer_buttons:
                visible_index = self._selected_index % self.OFFICERS_PER_PAGE
                visible_index = min(visible_index, len(self._trainer_buttons) - 1)
                manager.set_focus(self._trainer_buttons[visible_index])
                return
        if self._buttons:
            visible_index = min(
                self._selected_index % max(1, len(self._buttons)), len(self._buttons) - 1
            )
            manager.set_focus(self._buttons[visible_index])

    def _show_selection_state(self) -> None:
        self._mode = "selection"
        self._clear_body()
        self._trainer_candidates = province_service.get_training_candidates(self._province_no)
        self._selected_index = max(0, min(len(self._trainer_candidates) - 1, self._selected_index))
        self._control_index = 0
        self._focus_region = "trainers"
        province = province_service.get_province(self._province_no)
        province_officers = province_service.get_province_officers(self._province_no)
        available_offsets = {officer.Offset for officer in self._trainer_candidates}
        self._selected_trainer_offsets &= available_offsets

        UILabel(
            text=(
                f"Province {province.No}  Officers: {len(province_officers)}  "
                f"Best Training: {max((officer.TrainingLevel for officer in province_officers), default=0)}  "
                f"Selected Trainers: {len(self._selected_trainer_offsets)}"
            ),
            position=(30, 40),
            size=(1040, 30),
            font=pygame.font.Font(None, 28),
            color=(220, 220, 220),
            align="left",
            parent=self._body,
        )

        if not province_service.can_train_province(self._province_no):
            UILabel(
                text="This province is already fully trained.",
                position=(30, 120),
                size=(900, 36),
                font=pygame.font.Font(None, 30),
                color=(255, 140, 140),
                align="left",
                parent=self._body,
            )
            return

        if not self._trainer_candidates:
            UILabel(
                text="No officers in this province can lead training this month.",
                position=(30, 120),
                size=(900, 36),
                font=pygame.font.Font(None, 30),
                color=(255, 140, 140),
                align="left",
                parent=self._body,
            )
            return

        UILabel(
            text="Choose one or more officers to lead training.",
            position=(30, 100),
            size=(900, 32),
            font=pygame.font.Font(None, 30),
            color=(255, 215, 0),
            align="left",
            parent=self._body,
        )

        visible_candidates = self._get_visible_candidates()
        page_index = self._selected_index // self.OFFICERS_PER_PAGE
        page_count = (
            len(self._trainer_candidates) + self.OFFICERS_PER_PAGE - 1
        ) // self.OFFICERS_PER_PAGE
        start_index = page_index * self.OFFICERS_PER_PAGE

        UILabel(
            text=(
                f"Page {page_index + 1}/{page_count}  Showing {start_index + 1}-{start_index + len(visible_candidates)} of {len(self._trainer_candidates)}"
            ),
            position=(760, 105),
            size=(380, 28),
            font=pygame.font.Font(None, 24),
            color=(190, 190, 190),
            align="left",
            parent=self._body,
        )

        for visible_index, officer in enumerate(visible_candidates):
            officer_number = start_index + visible_index + 1
            button = UIButton(
                text=(
                    f"{officer_number}. {'[x]' if officer.Offset in self._selected_trainer_offsets else '[ ]'} {get_officer_display_name(officer)}   "
                    f"War {officer.War}  Training {officer.TrainingLevel}  Soldiers {officer.Soldiers:,}"
                ),
                position=(30, 160 + visible_index * 42),
                size=(920, 34),
                normal_color=(40, 46, 68),
                hover_color=(65, 72, 102),
                pressed_color=(55, 62, 92),
                text_color=(232, 232, 232),
                font=pygame.font.Font(None, 24),
                on_click=lambda selected=officer: self._toggle_trainer(selected),
                parent=self._body,
            )
            button.label.align = "left"
            self._trainer_buttons.append(button)

        UILabel(
            text="Up/Down moves through all officers, Enter toggles trainer, Right focuses Continue, Esc goes back.",
            position=(30, 610),
            size=(920, 28),
            font=pygame.font.Font(None, 24),
            color=(190, 190, 190),
            align="left",
            parent=self._body,
        )

        continue_button = UIButton(
            text="Continue",
            position=(980, 180),
            size=(180, 40),
            normal_color=(70, 100, 70),
            hover_color=(90, 130, 90),
            text_color=(255, 255, 255),
            font=pygame.font.Font(None, 28),
            on_click=self._preview_current_selection,
            parent=self._body,
        )
        self._control_buttons.append(continue_button)

        if not self._selected_trainer_offsets:
            UILabel(
                text="Select at least one trainer to continue.",
                position=(980, 240),
                size=(180, 80),
                font=pygame.font.Font(None, 26),
                color=(255, 215, 0),
                align="left",
                parent=self._body,
            )

        self._sync_focus()

    def _get_visible_candidates(self) -> list:
        page_index = self._selected_index // self.OFFICERS_PER_PAGE
        start = page_index * self.OFFICERS_PER_PAGE
        end = start + self.OFFICERS_PER_PAGE
        return self._trainer_candidates[start:end]

    def _move_selection(self, delta: int) -> None:
        if not self._trainer_candidates:
            return
        previous_page_index = self._selected_index // self.OFFICERS_PER_PAGE
        self._selected_index = max(
            0, min(len(self._trainer_candidates) - 1, self._selected_index + delta)
        )
        current_page_index = self._selected_index // self.OFFICERS_PER_PAGE
        if current_page_index != previous_page_index:
            self._show_selection_state()
            return
        self._sync_focus()

    def _preview_current_selection(self) -> None:
        selected_trainers = self._get_selected_trainers()
        if not selected_trainers:
            return
        self._preview_training(selected_trainers)

    def _toggle_trainer(self, officer) -> None:
        if officer.Offset in self._selected_trainer_offsets:
            self._selected_trainer_offsets.remove(officer.Offset)
        else:
            self._selected_trainer_offsets.add(officer.Offset)
        self._show_selection_state()

    def _get_selected_trainers(self) -> list:
        return [
            officer
            for officer in self._trainer_candidates
            if officer.Offset in self._selected_trainer_offsets
        ]

    def _preview_training(self, selected_trainers: list) -> None:
        lead_officer = selected_trainers[-1]
        self._estimate = province_service.calculate_training(
            self._province_no, lead_officer, selected_trainers
        )
        self._show_preview_state()

    def _show_preview_state(self) -> None:
        self._mode = "preview"
        self._clear_body()
        estimate = self._estimate
        if estimate is None:
            self._show_selection_state()
            return

        UILabel(
            text=(
                f"{estimate.officer_count} selected officer(s) led by {estimate.officer_name} will train Province {estimate.province_no}."
            ),
            position=(30, 60),
            size=(960, 36),
            font=pygame.font.Font(None, 32),
            color=(255, 215, 0),
            align="left",
            parent=self._body,
        )

        UILabel(
            text=(
                f"Training: {estimate.current_training} -> {estimate.projected_training} "
                f"(gain {estimate.projected_gain})"
            ),
            position=(30, 140),
            size=(960, 32),
            font=pygame.font.Font(None, 30),
            color=(232, 232, 232),
            align="left",
            parent=self._body,
        )

        UILabel(
            text=(
                f"Total soldier weight: {estimate.total_soldier_hundreds * 100:,}. "
                f"Legacy formula uses average War * 2 / sqrt(total soldiers/100 + 1)."
            ),
            position=(30, 200),
            size=(1100, 32),
            font=pygame.font.Font(None, 24),
            color=(190, 190, 190),
            align="left",
            parent=self._body,
        )

        confirm_button = UIButton(
            text="Confirm",
            position=(30, 300),
            size=(180, 40),
            normal_color=(70, 100, 70),
            hover_color=(90, 130, 90),
            text_color=(255, 255, 255),
            font=pygame.font.Font(None, 28),
            on_click=self._confirm_training,
            parent=self._body,
        )
        self._buttons.append(confirm_button)

        change_button = UIButton(
            text="Change Trainer",
            position=(230, 300),
            size=(220, 40),
            normal_color=(60, 60, 80),
            hover_color=(80, 80, 110),
            text_color=(232, 232, 232),
            font=pygame.font.Font(None, 26),
            on_click=self._show_selection_state,
            parent=self._body,
        )
        self._buttons.append(change_button)

        manager = UIManager.get_instance()
        if manager:
            manager.set_focus(confirm_button)

    def _confirm_training(self) -> None:
        if self._estimate is None:
            return
        self._estimate = province_service.apply_training(
            self._province_no, self._estimate.officer, self._get_selected_trainers()
        )
        self._show_result_state()

    def _show_result_state(self) -> None:
        self._mode = "result"
        self._clear_body()
        estimate = self._estimate
        if estimate is None:
            self._show_selection_state()
            return

        UILabel(
            text="Training complete.",
            position=(30, 60),
            size=(960, 36),
            font=pygame.font.Font(None, 34),
            color=(255, 215, 0),
            align="left",
            parent=self._body,
        )

        UILabel(
            text=(
                f"{estimate.officer_count} trainer(s) improved province training from {estimate.current_training} to {estimate.projected_training}."
            ),
            position=(30, 140),
            size=(1040, 32),
            font=pygame.font.Font(None, 30),
            color=(100, 220, 120),
            align="left",
            parent=self._body,
        )

        back_button = UIButton(
            text="Back to Province",
            position=(30, 240),
            size=(240, 40),
            normal_color=(60, 60, 80),
            hover_color=(80, 80, 110),
            text_color=(232, 232, 232),
            font=pygame.font.Font(None, 26),
            on_click=self._handle_back,
            parent=self._body,
        )
        self._buttons.append(back_button)

        manager = UIManager.get_instance()
        if manager:
            manager.set_focus(back_button)

    def _handle_back(self) -> None:
        if self._mode == "preview":
            self._show_selection_state()
            return
        if self._on_back_callback:
            self._on_back_callback()

    def handle_gamepad_button(self, button: GamepadButton) -> bool:
        if button == GamepadButton.B:
            self._handle_back()
            return True
        if self._mode == "selection":
            if self._focus_region == "trainers" and button in (
                GamepadButton.DPAD_UP,
                GamepadButton.LEFT_STICK_UP,
            ):
                self._move_selection(-1)
                return True
            if self._focus_region == "trainers" and button in (
                GamepadButton.DPAD_DOWN,
                GamepadButton.LEFT_STICK_DOWN,
            ):
                self._move_selection(1)
                return True
            if self._focus_region == "trainers" and button == GamepadButton.A:
                if self._trainer_candidates:
                    self._toggle_trainer(self._trainer_candidates[self._selected_index])
                return True
            if self._focus_region == "trainers" and button in (
                GamepadButton.DPAD_RIGHT,
                GamepadButton.LEFT_STICK_RIGHT,
            ):
                if self._control_buttons:
                    self._focus_region = "controls"
                    self._sync_focus()
                return True
            if self._focus_region == "controls" and button in (
                GamepadButton.DPAD_LEFT,
                GamepadButton.LEFT_STICK_LEFT,
            ):
                self._focus_region = "trainers"
                self._sync_focus()
                return True
            if self._focus_region == "controls" and button == GamepadButton.A:
                self._preview_current_selection()
                return True
            return False
        if button == GamepadButton.A and self._buttons:
            self._buttons[0].on_click()
            return True
        return False

    def handle_event(self, event: pygame.event.Event, transform=None) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._handle_back()
                return True
            if self._mode == "selection":
                if self._focus_region == "trainers" and event.key == pygame.K_UP:
                    self._move_selection(-1)
                    return True
                if self._focus_region == "trainers" and event.key == pygame.K_DOWN:
                    self._move_selection(1)
                    return True
                if self._focus_region == "trainers" and event.key == pygame.K_RETURN:
                    if self._trainer_candidates:
                        self._toggle_trainer(self._trainer_candidates[self._selected_index])
                    return True
                if self._focus_region == "trainers" and event.key == pygame.K_RIGHT:
                    if self._control_buttons:
                        self._focus_region = "controls"
                        self._sync_focus()
                    return True
                if self._focus_region == "controls" and event.key == pygame.K_LEFT:
                    self._focus_region = "trainers"
                    self._sync_focus()
                    return True
                if self._focus_region == "controls" and event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                ):
                    self._preview_current_selection()
                    return True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and self._buttons:
                self._buttons[0].on_click()
                return True
        return bool(super().handle_event(event, transform))
