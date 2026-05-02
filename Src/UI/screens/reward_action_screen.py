"""Modern reward flow for gold and horse awards."""

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


class RewardActionScreen(UIContainer):
    """Run the province reward flow using the governor's monthly reward quota."""

    handles_own_navigation = True
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 800
    TARGETS_PER_PAGE = 10

    def __init__(self, province_no: int, on_back: Callable[[], None] | None = None):
        super().__init__(
            position=(0, 0),
            size=(self.SCREEN_WIDTH, self.SCREEN_HEIGHT),
            background_color=(18, 18, 30),
            parent=None,
        )

        self._province_no = province_no
        self._on_back_callback = on_back
        self._mode = "select_type"
        self._reward_type = "gold"
        self._target_officer = None
        self._estimate = None
        self._body = None
        self._buttons: list[UIButton] = []
        self._button_index = 0
        self._spend_amount = 100
        self._target_candidates: list = []
        self._target_index = 0

        self._create_base_ui()
        self._show_reward_type_state()

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
            text="Rewards",
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
        self._button_index = 0

    def _sync_focus(self) -> None:
        manager = UIManager.get_instance()
        if manager and self._buttons:
            manager.set_focus(self._buttons[min(self._button_index, len(self._buttons) - 1)])

    def _sync_target_focus(self) -> None:
        manager = UIManager.get_instance()
        if manager and self._buttons:
            visible_index = self._target_index % self.TARGETS_PER_PAGE
            visible_index = min(visible_index, len(self._buttons) - 1)
            manager.set_focus(self._buttons[visible_index])

    def _add_standard_header(self) -> None:
        province = province_service.get_province(self._province_no)
        governor = province_service.get_reward_governor(self._province_no)
        reward_limit = province_service.get_reward_turn_limit()
        reward_remaining = province_service.get_reward_turns_remaining(self._province_no)
        UILabel(
            text=(
                f"Province {province.No}  Governor: {get_officer_display_name(governor)}  "
                f"Gold: {province.Gold:,}  Horses: {province.Horses}  "
                f"Reward Uses: {reward_remaining}/{reward_limit}"
            ),
            position=(30, 35),
            size=(1140, 30),
            font=pygame.font.Font(None, 28),
            color=(220, 220, 220),
            align="left",
            parent=self._body,
        )

    def _show_reward_type_state(self) -> None:
        self._mode = "select_type"
        self._clear_body()
        self._add_standard_header()

        UILabel(
            text="Choose reward type.",
            position=(30, 110),
            size=(700, 36),
            font=pygame.font.Font(None, 32),
            color=(255, 215, 0),
            align="left",
            parent=self._body,
        )

        if not province_service.can_governor_reward(self._province_no):
            UILabel(
                text="This province's governor has no reward uses remaining this month.",
                position=(30, 180),
                size=(900, 36),
                font=pygame.font.Font(None, 30),
                color=(255, 140, 140),
                align="left",
                parent=self._body,
            )
            return

        gold_button = UIButton(
            text="Gold Reward",
            position=(30, 200),
            size=(220, 44),
            normal_color=(60, 60, 80),
            hover_color=(80, 80, 110),
            text_color=(232, 232, 232),
            font=pygame.font.Font(None, 28),
            on_click=lambda: self._open_target_selection("gold"),
            parent=self._body,
        )
        self._buttons.append(gold_button)

        horse_button = UIButton(
            text="Horse Reward",
            position=(30, 260),
            size=(220, 44),
            normal_color=(60, 60, 80),
            hover_color=(80, 80, 110),
            text_color=(232, 232, 232),
            font=pygame.font.Font(None, 28),
            on_click=lambda: self._open_target_selection("horse"),
            parent=self._body,
        )
        if province_service.get_province(self._province_no).Horses < 1:
            horse_button.enabled = False
        self._buttons.append(horse_button)

        UILabel(
            text=(
                f"Horse rewards use an effective gold value of {province_service.get_horse_reward_gold_value():,}."
            ),
            position=(300, 205),
            size=(700, 32),
            font=pygame.font.Font(None, 26),
            color=(190, 190, 190),
            align="left",
            parent=self._body,
        )

        self._sync_focus()

    def _open_target_selection(self, reward_type: str) -> None:
        if not province_service.can_governor_reward(self._province_no):
            self._show_reward_type_state()
            return

        self._reward_type = reward_type
        self._show_target_selection_state()

    def _show_target_selection_state(self) -> None:
        self._mode = "select_target"
        self._clear_body()
        self._add_standard_header()
        self._target_candidates = province_service.get_rewardable_officers(self._province_no)
        if not self._target_candidates:
            self._mode = "select_target"
            UILabel(
                text="No officers in this province can receive rewards.",
                position=(30, 180),
                size=(900, 36),
                font=pygame.font.Font(None, 30),
                color=(255, 140, 140),
                align="left",
                parent=self._body,
            )
            return
        self._target_index = max(0, min(len(self._target_candidates) - 1, self._target_index))

        UILabel(
            text="Choose the officer to reward.",
            position=(30, 110),
            size=(700, 36),
            font=pygame.font.Font(None, 32),
            color=(255, 215, 0),
            align="left",
            parent=self._body,
        )

        visible_candidates = self._get_visible_targets()
        page_index = self._target_index // self.TARGETS_PER_PAGE
        page_count = (
            len(self._target_candidates) + self.TARGETS_PER_PAGE - 1
        ) // self.TARGETS_PER_PAGE
        start_index = page_index * self.TARGETS_PER_PAGE

        UILabel(
            text=(
                f"Page {page_index + 1}/{page_count}  Showing {start_index + 1}-{start_index + len(visible_candidates)} of {len(self._target_candidates)}"
            ),
            position=(760, 115),
            size=(380, 28),
            font=pygame.font.Font(None, 24),
            color=(190, 190, 190),
            align="left",
            parent=self._body,
        )

        row_height = 42
        for visible_index, officer in enumerate(visible_candidates):
            officer_number = start_index + visible_index + 1
            button = UIButton(
                text=(
                    f"{officer_number}. {get_officer_display_name(officer)}   "
                    f"Loyalty {officer.Loyalty}  Int {officer.Int}  War {officer.War}  Charm {officer.Chm}"
                ),
                position=(30, 180 + visible_index * row_height),
                size=(920, 34),
                normal_color=(40, 46, 68),
                hover_color=(65, 72, 102),
                pressed_color=(55, 62, 92),
                text_color=(232, 232, 232),
                font=pygame.font.Font(None, 24),
                on_click=lambda selected=officer: self._set_target_officer(selected),
                parent=self._body,
            )
            button.label.align = "left"
            self._buttons.append(button)

        UILabel(
            text="Up/Down moves through all officers, Enter selects, Esc returns to reward type.",
            position=(30, 610),
            size=(920, 28),
            font=pygame.font.Font(None, 24),
            color=(190, 190, 190),
            align="left",
            parent=self._body,
        )

        self._sync_target_focus()

    def _get_visible_targets(self) -> list:
        page_index = self._target_index // self.TARGETS_PER_PAGE
        start = page_index * self.TARGETS_PER_PAGE
        end = start + self.TARGETS_PER_PAGE
        return self._target_candidates[start:end]

    def _set_target_officer(self, officer) -> None:
        self._target_officer = officer
        if self._reward_type == "gold":
            self._show_gold_amount_state()
        else:
            self._build_reward_preview()

    def _move_target_selection(self, delta: int) -> None:
        if not self._target_candidates:
            return
        previous_page_index = self._target_index // self.TARGETS_PER_PAGE
        self._target_index = max(
            0, min(len(self._target_candidates) - 1, self._target_index + delta)
        )
        current_page_index = self._target_index // self.TARGETS_PER_PAGE
        if current_page_index != previous_page_index:
            self._show_target_selection_state()
            return
        self._sync_target_focus()

    def _select_current_target(self) -> None:
        if not self._target_candidates:
            return
        self._set_target_officer(self._target_candidates[self._target_index])

    def _show_gold_amount_state(self) -> None:
        self._mode = "enter_gold"
        self._clear_body()
        self._add_standard_header()
        target_name = get_officer_display_name(self._target_officer)

        UILabel(
            text=f"Enter gold to reward {target_name}.",
            position=(30, 110),
            size=(700, 36),
            font=pygame.font.Font(None, 32),
            color=(255, 215, 0),
            align="left",
            parent=self._body,
        )

        self._amount_label = UILabel(
            text=f"{self._spend_amount:,}",
            position=(30, 190),
            size=(240, 48),
            font=pygame.font.Font(None, 44),
            color=(255, 255, 255),
            align="left",
            parent=self._body,
        )

        UILabel(
            text="Type digits, Backspace edits, Q sets Max, E adds 100.",
            position=(30, 250),
            size=(700, 28),
            font=pygame.font.Font(None, 24),
            color=(190, 190, 190),
            align="left",
            parent=self._body,
        )

        options = []
        for amount in [
            100,
            300,
            500,
            700,
            1000,
            province_service.get_province(self._province_no).Gold,
        ]:
            capped = min(province_service.get_province(self._province_no).Gold, amount)
            if capped > 0 and capped not in options:
                options.append(capped)

        for index, amount in enumerate(options):
            button = UIButton(
                text=f"{amount:,}",
                position=(30 + (index % 3) * 150, 320 + (index // 3) * 50),
                size=(120, 36),
                normal_color=(60, 60, 80),
                hover_color=(80, 80, 110),
                pressed_color=(55, 62, 92),
                text_color=(232, 232, 232),
                font=pygame.font.Font(None, 24),
                on_click=lambda value=amount: self._set_spend_amount(value),
                parent=self._body,
            )
            self._buttons.append(button)

        preview_button = UIButton(
            text="Preview",
            position=(30, 470),
            size=(180, 40),
            normal_color=(70, 100, 70),
            hover_color=(90, 130, 90),
            text_color=(255, 255, 255),
            font=pygame.font.Font(None, 28),
            on_click=self._build_reward_preview,
            parent=self._body,
        )
        self._buttons.append(preview_button)

        self._sync_focus()

    def _set_spend_amount(self, amount: int) -> None:
        self._spend_amount = max(
            1, min(province_service.get_province(self._province_no).Gold, amount)
        )
        if hasattr(self, "_amount_label"):
            self._amount_label.text = f"{self._spend_amount:,}"

    def _append_digit(self, digit: str) -> None:
        proposed = f"{self._spend_amount}{digit}" if self._spend_amount != 0 else digit
        self._set_spend_amount(int(proposed))

    def _backspace_amount(self) -> None:
        self._spend_amount = int(str(self._spend_amount)[:-1] or "0")
        self._spend_amount = max(
            0, min(province_service.get_province(self._province_no).Gold, self._spend_amount)
        )
        if hasattr(self, "_amount_label"):
            self._amount_label.text = f"{self._spend_amount:,}"

    def _build_reward_preview(self) -> None:
        if self._target_officer is None:
            return
        if self._reward_type == "gold":
            if self._spend_amount < 1:
                return
            self._estimate = province_service.calculate_gold_reward(
                self._province_no, self._target_officer, self._spend_amount
            )
        else:
            self._estimate = province_service.calculate_horse_reward(
                self._province_no, self._target_officer
            )
        self._show_preview_state()

    def _show_preview_state(self) -> None:
        self._mode = "preview"
        self._clear_body()
        self._add_standard_header()
        estimate = self._estimate
        if estimate is None:
            return

        UILabel(
            text=(
                f"{estimate.governor_name} will give a {estimate.reward_type.lower()} reward to {estimate.target_officer_name}."
            ),
            position=(30, 110),
            size=(960, 36),
            font=pygame.font.Font(None, 32),
            color=(255, 215, 0),
            align="left",
            parent=self._body,
        )

        UILabel(
            text=(
                f"Cost: {estimate.cost_amount:,} {estimate.cost_field.lower()}  "
                f"Loyalty: {estimate.current_loyalty} -> {estimate.projected_loyalty}"
            ),
            position=(30, 180),
            size=(960, 32),
            font=pygame.font.Font(None, 28),
            color=(232, 232, 232),
            align="left",
            parent=self._body,
        )

        UILabel(
            text=(
                "If the reward fails to raise loyalty, the resource and reward use are still spent."
            ),
            position=(30, 230),
            size=(1000, 32),
            font=pygame.font.Font(None, 24),
            color=(255, 150, 150),
            align="left",
            parent=self._body,
        )

        UILabel(
            text=(
                f"After this reward: uses this month {estimate.reward_turns_used}, remaining {estimate.reward_turns_remaining}."
            ),
            position=(30, 280),
            size=(960, 32),
            font=pygame.font.Font(None, 24),
            color=(190, 190, 190),
            align="left",
            parent=self._body,
        )

        confirm_button = UIButton(
            text="Confirm",
            position=(30, 360),
            size=(180, 40),
            normal_color=(70, 100, 70),
            hover_color=(90, 130, 90),
            text_color=(255, 255, 255),
            font=pygame.font.Font(None, 28),
            on_click=self._confirm_reward,
            parent=self._body,
        )
        self._buttons.append(confirm_button)

        change_button = UIButton(
            text="Change",
            position=(230, 360),
            size=(180, 40),
            normal_color=(60, 60, 80),
            hover_color=(80, 80, 110),
            text_color=(232, 232, 232),
            font=pygame.font.Font(None, 26),
            on_click=self._return_from_preview,
            parent=self._body,
        )
        self._buttons.append(change_button)

        self._sync_focus()

    def _return_from_preview(self) -> None:
        if self._reward_type == "gold":
            self._show_gold_amount_state()
        else:
            self._show_target_selection_state()

    def _confirm_reward(self) -> None:
        if self._estimate is None or self._target_officer is None:
            return
        if self._reward_type == "gold":
            self._estimate = province_service.apply_gold_reward(
                self._province_no,
                self._target_officer,
                self._spend_amount,
                self._estimate,
            )
        else:
            self._estimate = province_service.apply_horse_reward(
                self._province_no,
                self._target_officer,
                self._estimate,
            )
        self._show_result_state()

    def _show_result_state(self) -> None:
        self._mode = "result"
        self._clear_body()
        self._add_standard_header()
        estimate = self._estimate
        if estimate is None:
            return

        result_text = "Loyalty increased." if estimate.success else "No loyalty increase."
        result_color = (100, 220, 120) if estimate.success else (255, 160, 160)

        UILabel(
            text=f"{estimate.reward_type} reward complete.",
            position=(30, 110),
            size=(800, 36),
            font=pygame.font.Font(None, 34),
            color=(255, 215, 0),
            align="left",
            parent=self._body,
        )

        UILabel(
            text=(
                f"{estimate.target_officer_name}: loyalty {estimate.current_loyalty} -> {estimate.projected_loyalty}."
            ),
            position=(30, 180),
            size=(900, 32),
            font=pygame.font.Font(None, 30),
            color=result_color,
            align="left",
            parent=self._body,
        )

        UILabel(
            text=(
                f"{estimate.cost_amount:,} {estimate.cost_field.lower()} spent. {result_text} "
                f"Reward uses remaining this month: {estimate.reward_turns_remaining}."
            ),
            position=(30, 230),
            size=(1020, 32),
            font=pygame.font.Font(None, 26),
            color=(232, 232, 232),
            align="left",
            parent=self._body,
        )

        back_button = UIButton(
            text="Back to Province",
            position=(30, 320),
            size=(240, 40),
            normal_color=(60, 60, 80),
            hover_color=(80, 80, 110),
            text_color=(232, 232, 232),
            font=pygame.font.Font(None, 26),
            on_click=self._handle_back,
            parent=self._body,
        )
        self._buttons.append(back_button)

        self._sync_focus()

    def _handle_back(self) -> None:
        if self._mode == "select_target":
            self._show_reward_type_state()
            return
        if self._mode == "enter_gold":
            self._show_target_selection_state()
            return
        if self._mode == "preview":
            self._return_from_preview()
            return
        if self._on_back_callback:
            self._on_back_callback()

    def _move_button_focus(self, delta: int) -> None:
        if not self._buttons:
            return
        self._button_index = max(0, min(len(self._buttons) - 1, self._button_index + delta))
        self._sync_focus()

    def handle_gamepad_button(self, button: GamepadButton) -> bool:
        if button == GamepadButton.B:
            self._handle_back()
            return True
        if self._mode == "select_target":
            if button in (GamepadButton.DPAD_UP, GamepadButton.LEFT_STICK_UP):
                self._move_target_selection(-1)
                return True
            if button in (GamepadButton.DPAD_DOWN, GamepadButton.LEFT_STICK_DOWN):
                self._move_target_selection(1)
                return True
            if button == GamepadButton.A:
                self._select_current_target()
                return True
            return False
        if button in (GamepadButton.DPAD_UP, GamepadButton.LEFT_STICK_UP):
            self._move_button_focus(-1)
            return True
        if button in (GamepadButton.DPAD_DOWN, GamepadButton.LEFT_STICK_DOWN):
            self._move_button_focus(1)
            return True
        if button == GamepadButton.X and self._mode == "enter_gold":
            self._set_spend_amount(province_service.get_province(self._province_no).Gold)
            return True
        if button == GamepadButton.Y and self._mode == "enter_gold":
            self._set_spend_amount(self._spend_amount + 100)
            return True
        if button == GamepadButton.A and self._buttons:
            self._buttons[self._button_index].on_click()
            return True
        return False

    def handle_event(self, event: pygame.event.Event, transform=None) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._handle_back()
                return True
            if self._mode == "select_target":
                if event.key == pygame.K_UP:
                    self._move_target_selection(-1)
                    return True
                if event.key == pygame.K_DOWN:
                    self._move_target_selection(1)
                    return True
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._select_current_target()
                    return True
                return bool(super().handle_event(event, transform))
            if event.key == pygame.K_UP:
                self._move_button_focus(-1)
                return True
            if event.key == pygame.K_DOWN:
                self._move_button_focus(1)
                return True
            if self._mode == "enter_gold":
                if event.key == pygame.K_q:
                    self._set_spend_amount(province_service.get_province(self._province_no).Gold)
                    return True
                if event.key == pygame.K_e:
                    self._set_spend_amount(self._spend_amount + 100)
                    return True
                if event.key == pygame.K_BACKSPACE:
                    self._backspace_amount()
                    return True
                if pygame.K_0 <= event.key <= pygame.K_9:
                    self._append_digit(chr(event.key))
                    return True
                if pygame.K_KP0 <= event.key <= pygame.K_KP9:
                    self._append_digit(chr(event.key - pygame.K_KP0 + ord("0")))
                    return True
            if event.key in (pygame.K_RETURN, pygame.K_SPACE) and self._buttons:
                self._buttons[self._button_index].on_click()
                return True
        return bool(super().handle_event(event, transform))
