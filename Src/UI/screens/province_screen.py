"""
Province Information Screen

Modern UI screen for displaying province details.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from UI.core.anchor import Anchor
from UI.core.container import UIContainer
from UI.components.basic import UILabel, UIButton

if TYPE_CHECKING:
    from Province import Province
    from UI.core.transform import Transform


class ProvinceInfoScreen(UIContainer):
    """
    Province information display screen.

    Shows province details in a modern, clean layout:
    - Header: Province name and number
    - Stats panel: Two-column layout with resources
    - Officer info: Count of officers
    - Navigation: Buttons to go back or access commands
    """

    def __init__(self, province: Province | None = None):
        """
        Initialize province info screen.

        Args:
            province: Province to display, or None for empty state
        """
        super().__init__(
            position=(0, 0), size=(1280, 800), background_color=(20, 20, 35), parent=None
        )

        self.province = province
        self._create_ui()

    def _create_ui(self) -> None:
        """Create UI components."""
        # Title - positioned higher to avoid overlap
        title_text = self.province.Name if self.province else "No Province"
        title = UILabel(
            text=title_text,
            position=(640, 20),
            size=(400, 50),
            font=pygame.font.Font(None, 48),
            color=(233, 69, 96),  # Accent color
            align="center",
            anchor=Anchor.TOP_CENTER,
        )
        self.add_child(title)

        if not self.province:
            return

        # Left panel - Resources
        left_panel = UIContainer(
            position=(50, 100),
            size=(550, 520),
            background_color=(22, 33, 62),
            border_color=(15, 52, 96),
            border_width=2,
            padding=30,
        )
        self.add_child(left_panel)

        # Resource stats
        resources = [
            ("Gold", f"{self.province.Gold:,}"),
            ("Rice", f"{self.province.Food:,}"),
            ("Population", f"{self.province.Population:,}"),
            ("Soldiers", f"{self.province.Soldiers:,}"),
        ]

        y_offset = 30  # Start after padding
        for label, value in resources:
            # Label
            lbl = UILabel(
                text=f"{label}:",
                position=(30, y_offset),
                size=(150, 40),
                font=pygame.font.Font(None, 28),
                color=(200, 200, 200),
                align="left",
            )
            left_panel.add_child(lbl)

            # Value
            val = UILabel(
                text=value,
                position=(320, y_offset),
                size=(180, 40),
                font=pygame.font.Font(None, 28),
                color=(255, 255, 255),
                align="right",
            )
            left_panel.add_child(val)

            y_offset += 70

        # Right panel - Province stats
        right_panel = UIContainer(
            position=(680, 100),
            size=(550, 520),
            background_color=(22, 33, 62),
            border_color=(15, 52, 96),
            border_width=2,
            padding=30,
        )
        self.add_child(right_panel)

        # Province stats
        stats = [
            ("Loyalty", f"{self.province.Loyalty}"),
            ("Land", f"{self.province.Land}"),
            ("Flood", f"{self.province.Flood}"),
            ("Horses", f"{self.province.Horses}"),
            ("Rice Price", f"{self.province.RicePrice}"),
            ("Officers", f"{self.province.ClaimedOfficerNumber}"),
            ("Free Officers", f"{self.province.UnClaimedOfficerNumber}"),
        ]

        y_offset = 30  # Start after padding
        for label, value in stats:
            # Label
            lbl = UILabel(
                text=f"{label}:",
                position=(30, y_offset),
                size=(180, 40),
                font=pygame.font.Font(None, 28),
                color=(200, 200, 200),
                align="left",
            )
            right_panel.add_child(lbl)

            # Value
            val = UILabel(
                text=value,
                position=(320, y_offset),
                size=(180, 40),
                font=pygame.font.Font(None, 28),
                color=(255, 255, 255),
                align="right",
            )
            right_panel.add_child(val)

            y_offset += 60

        # Bottom buttons - use a button container for better spacing
        button_y = 660
        button_spacing = 200
        start_x = 140

        back_btn = UIButton(
            text="Back",
            position=(start_x, button_y),
            size=(160, 45),
            normal_color=(69, 73, 78),
            hover_color=(100, 100, 110),
            on_click=self._on_back,
        )
        self.add_child(back_btn)

        commands_btn = UIButton(
            text="Commands",
            position=(start_x + button_spacing, button_y),
            size=(160, 45),
            normal_color=(69, 73, 78),
            hover_color=(100, 100, 110),
            on_click=self._on_commands,
        )
        self.add_child(commands_btn)

        officers_btn = UIButton(
            text="Officers",
            position=(start_x + button_spacing * 2, button_y),
            size=(160, 45),
            normal_color=(69, 73, 78),
            hover_color=(100, 100, 110),
            on_click=self._on_officers,
        )
        self.add_child(officers_btn)

        next_prov_btn = UIButton(
            text="Next >",
            position=(start_x + button_spacing * 3, button_y),
            size=(100, 45),
            normal_color=(69, 73, 78),
            hover_color=(100, 100, 110),
            on_click=self._on_next_province,
        )
        self.add_child(next_prov_btn)

        prev_prov_btn = UIButton(
            text="< Prev",
            position=(start_x + button_spacing * 4, button_y),
            size=(100, 45),
            normal_color=(69, 73, 78),
            hover_color=(100, 100, 110),
            on_click=self._on_prev_province,
        )
        self.add_child(prev_prov_btn)

    def _on_back(self) -> None:
        """Handle back button click."""
        print("Back to map clicked")

    def _on_commands(self) -> None:
        """Handle commands button click."""
        print("Commands clicked")

    def _on_officers(self) -> None:
        """Handle officers button click."""
        print("Officers clicked")

    def _on_next_province(self) -> None:
        """Handle next province button click."""
        print("Next province clicked")

    def _on_prev_province(self) -> None:
        """Handle previous province button click."""
        print("Previous province clicked")
