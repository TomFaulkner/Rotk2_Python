"""
SNES-Style Province Information Screen

Layout similar to the SNES version with:
- Two rows of menu buttons at top
- Portrait on the left
- Stats panel in center
- Command prompt at bottom
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from pathlib import Path

import pygame

from UI.core.anchor import Anchor
from UI.core.container import UIContainer
from UI.components.basic import UILabel, UIButton

if TYPE_CHECKING:
    from Province import Province
    from Officer import Officer
    from UI.core.transform import Transform


class SnesPortraitLoader:
    """Simple loader for SNES-style portraits."""

    def __init__(self, resources_path: str = "../Resources"):
        self.resources_path = Path(resources_path)
        self.portraits_path = self.resources_path / "portraits"
        self._cache: dict[int, pygame.Surface] = {}
        self._mapping = self._load_mapping()

    def _load_mapping(self) -> dict:
        """Load officer ID to portrait file mapping."""
        import json

        mapping_file = self.portraits_path / "portrait_mapping.json"
        if mapping_file.exists():
            with open(mapping_file, "r") as f:
                return json.load(f)
        return {}

    def get_portrait(
        self, officer_id: int, size: tuple[int, int] = (120, 120)
    ) -> pygame.Surface | None:
        """
        Get portrait for an officer.

        Args:
            officer_id: Officer ID
            size: Desired size (width, height)

        Returns:
            Portrait surface or None if not found
        """
        # Check cache
        if officer_id in self._cache:
            return pygame.transform.scale(self._cache[officer_id], size)

        # Look up mapping
        officer_key = str(officer_id)
        if officer_key not in self._mapping:
            return None

        mapping = self._mapping[officer_key]
        portrait_file = mapping.get("file")

        if not portrait_file:
            return None

        # Remove leading ../ if present
        if portrait_file.startswith("../"):
            portrait_file = portrait_file[3:]

        # Try to load
        full_path = self.resources_path.parent / portrait_file
        if not full_path.exists():
            # Try alternative path
            full_path = self.portraits_path / portrait_file.replace("../Resources/portraits/", "")

        if full_path.exists():
            try:
                image = pygame.image.load(str(full_path))
                self._cache[officer_id] = image
                return pygame.transform.scale(image, size)
            except pygame.error:
                pass

        return None


class SnesProvinceScreen(UIContainer):
    """
    SNES-style province information screen.

    Layout:
        [Row 1: View] [Army] [Person] [Trade]
        [Row 2: Internal] [Diplomacy] [Espionage] [Move]

        [Portrait] [Stats Panel]

        "Commander, your orders for Province X?"
    """

    # Menu configuration: (label, action_name)
    MENUS_ROW1 = [
        ("View", "view"),
        ("Army", "army"),
        ("Person", "person"),
        ("Trade", "trade"),
    ]

    MENUS_ROW2 = [
        ("Internal Affairs", "internal"),
        ("Diplomacy", "diplomacy"),
        ("Espionage", "espionage"),
        ("Move", "move"),
    ]

    def __init__(self, province: Province | None = None):
        """
        Initialize SNES-style province screen.

        Args:
            province: Province to display
        """
        super().__init__(
            position=(0, 0), size=(1280, 800), background_color=(15, 15, 25), parent=None
        )

        self.province = province
        self.portrait_loader = SnesPortraitLoader()
        self._selected_menu: str | None = None
        self._create_ui()

    def _create_ui(self) -> None:
        """Create the SNES-style UI layout."""
        # Title bar
        self._create_title_bar()

        # Menu rows
        self._create_menu_rows()

        # Main content area (portrait + stats)
        self._create_main_content()

        # Command prompt at bottom
        self._create_command_prompt()

    def _create_title_bar(self) -> None:
        """Create the province name title at top."""
        title_text = self.province.Name if self.province else "Unknown Province"

        title_bg = UIContainer(
            position=(0, 0), size=(1280, 50), background_color=(30, 30, 50), parent=self
        )

        title = UILabel(
            text=title_text,
            position=(640, 25),
            size=(400, 40),
            font=pygame.font.Font(None, 36),
            color=(233, 69, 96),
            align="center",
            anchor=Anchor.CENTER,
            parent=title_bg,
        )

    def _create_menu_rows(self) -> None:
        """Create the two rows of menu buttons."""
        menu_y_start = 60
        menu_height = 45
        menu_width = 280
        menu_spacing = 20

        # Row 1
        row1_y = menu_y_start
        start_x = 80

        for i, (label, action) in enumerate(self.MENUS_ROW1):
            btn = UIButton(
                text=label,
                position=(start_x + i * (menu_width + menu_spacing), row1_y),
                size=(menu_width, menu_height),
                normal_color=(60, 60, 80),
                hover_color=(80, 80, 110),
                text_color=(255, 255, 255),
                on_click=lambda a=action: self._on_menu_click(a),
                parent=self,
            )

        # Row 2
        row2_y = menu_y_start + menu_height + 10

        for i, (label, action) in enumerate(self.MENUS_ROW2):
            btn = UIButton(
                text=label,
                position=(start_x + i * (menu_width + menu_spacing), row2_y),
                size=(menu_width, menu_height),
                normal_color=(60, 60, 80),
                hover_color=(80, 80, 110),
                text_color=(255, 255, 255),
                on_click=lambda a=action: self._on_menu_click(a),
                parent=self,
            )

    def _create_main_content(self) -> None:
        """Create portrait and stats panel."""
        if not self.province:
            return

        content_y = 180

        # Portrait area (left side)
        portrait_size = (200, 200)
        portrait_x = 80
        portrait_y = content_y

        # Try to get governor portrait
        governor = self._get_governor()
        if governor:
            portrait = self.portrait_loader.get_portrait(
                self._get_officer_id(governor), portrait_size
            )

            if portrait:
                from UI.components.image import UIImage

                portrait_img = UIImage(
                    image=portrait,
                    position=(portrait_x, portrait_y),
                    size=portrait_size,
                    parent=self,
                )
            else:
                # Placeholder
                placeholder = UIContainer(
                    position=(portrait_x, portrait_y),
                    size=portrait_size,
                    background_color=(40, 40, 60),
                    border_color=(100, 100, 120),
                    border_width=2,
                    parent=self,
                )

        # Stats panel (right of portrait)
        self._create_stats_panel(portrait_x + portrait_size[0] + 40, content_y)

    def _create_stats_panel(self, x: int, y: int) -> None:
        """Create the statistics panel."""
        if not self.province:
            return

        panel_width = 880
        panel_height = 400

        # Stats container
        stats_container = UIContainer(
            position=(x, y),
            size=(panel_width, panel_height),
            background_color=(25, 25, 40),
            border_color=(50, 50, 80),
            border_width=2,
            padding=30,
            parent=self,
        )

        # Two-column layout
        col1_x = 30
        col2_x = 450
        row_y = 30
        row_height = 45

        # Column 1 - Resources
        col1_stats = [
            ("Gold", f"{self.province.Gold:,}"),
            ("Rice", f"{self.province.Food:,}"),
            ("Population", f"{self.province.Population:,}"),
            ("Soldiers", f"{self.province.Soldiers:,}"),
            ("Loyalty", f"{self.province.Loyalty}"),
        ]

        for label, value in col1_stats:
            lbl = UILabel(
                text=f"{label}:",
                position=(col1_x, row_y),
                size=(150, 35),
                font=pygame.font.Font(None, 28),
                color=(180, 180, 180),
                align="left",
                parent=stats_container,
            )

            val = UILabel(
                text=value,
                position=(col1_x + 160, row_y),
                size=(200, 35),
                font=pygame.font.Font(None, 28),
                color=(255, 255, 255),
                align="right",
                parent=stats_container,
            )

            row_y += row_height

        # Column 2 - Other stats
        row_y = 30
        col2_stats = [
            ("Land", f"{self.province.Land}"),
            ("Flood", f"{self.province.Flood}"),
            ("Horses", f"{self.province.Horses}"),
            ("Rice Price", f"{self.province.RicePrice}"),
            ("Officers", f"{self.province.ClaimedOfficerNumber}"),
        ]

        for label, value in col2_stats:
            lbl = UILabel(
                text=f"{label}:",
                position=(col2_x, row_y),
                size=(150, 35),
                font=pygame.font.Font(None, 28),
                color=(180, 180, 180),
                align="left",
                parent=stats_container,
            )

            val = UILabel(
                text=value,
                position=(col2_x + 160, row_y),
                size=(200, 35),
                font=pygame.font.Font(None, 28),
                color=(255, 255, 255),
                align="right",
                parent=stats_container,
            )

            row_y += row_height

        # Personnel section at bottom of stats panel
        self._create_personnel_section(stats_container, 30, 280)

    def _create_command_prompt(self) -> None:
        """Create command prompt at bottom."""
        prompt_y = 620

        # Get ruler name for prompt
        ruler_name = "Commander"
        if self.province:
            ruler = self._get_ruler()
            if ruler and ruler.RulerSelf:
                ruler_name = self._get_officer_display_name(ruler.RulerSelf)

        province_num = self.province.No if self.province else "?"
        prompt_text = f"{ruler_name}, your orders for Province {province_num}?"

        prompt = UILabel(
            text=prompt_text,
            position=(640, prompt_y),
            size=(800, 50),
            font=pygame.font.Font(None, 32),
            color=(255, 255, 255),
            align="center",
            anchor=Anchor.TOP_CENTER,
            parent=self,
        )

    def _create_personnel_section(self, parent: UIContainer, x: int, y: int) -> None:
        """Create the personnel section showing Ruler, Governor, and Advisor."""
        if not self.province:
            return

        row_y = y

        # Ruler info
        ruler = self._get_ruler()
        if ruler:
            ruler_name = (
                self._get_officer_display_name(ruler.RulerSelf) if ruler.RulerSelf else "Unknown"
            )
            ruler_label = UILabel(
                text=f"Ruler: {ruler_name}",
                position=(x, row_y),
                size=(380, 35),
                font=pygame.font.Font(None, 26),
                color=(255, 215, 0),  # Gold color for ruler
                align="left",
                parent=parent,
            )
            row_y += 35

        # Governor info
        governor = self._get_governor()
        if governor:
            gov_name = self._get_officer_display_name(governor)
            gov_label = UILabel(
                text=f"Governor: {gov_name}",
                position=(x, row_y),
                size=(380, 35),
                font=pygame.font.Font(None, 26),
                color=(200, 200, 100),
                align="left",
                parent=parent,
            )
            row_y += 35

        # Advisor info (if advisor is in this province)
        advisor = self._get_advisor_in_province()
        if advisor:
            adv_name = self._get_officer_display_name(advisor)
            adv_label = UILabel(
                text=f"Advisor: {adv_name}",
                position=(x, row_y),
                size=(380, 35),
                font=pygame.font.Font(None, 26),
                color=(100, 200, 200),  # Cyan for advisor
                align="left",
                parent=parent,
            )

    def _get_officer_display_name(self, officer: Officer) -> str:
        """Get a displayable name for an officer (English only for UI)."""
        if not officer:
            return "Unknown"

        try:
            # Try to get English name directly
            from Battle.officer_names import get_officer_name
            from Data import Data

            officer_id = (officer.Offset - Data.OFFICER_START) // Data.OFFICER_SIZE
            english_name = get_officer_name(officer_id)

            # If it's not the default "Officer_X" format, use it
            if not english_name.startswith("Officer_"):
                return english_name

            # Fall back to any name attribute
            if hasattr(officer, "Name") and officer.Name:
                return officer.Name

            return f"Officer {officer_id}"
        except Exception:
            # Last resort
            return getattr(officer, "Name", "Unknown")

    def _get_ruler(self):
        """Get the ruler of this province."""
        if not self.province or self.province.RulerNo == 0xFF:
            return None
        try:
            from Ruler import Ruler

            return Ruler.FromNo(self.province.RulerNo)
        except:
            return None

    def _get_governor(self) -> Officer | None:
        """Get the province governor officer."""
        if not self.province or self.province.GovernorOffset == 0:
            return None
        try:
            from Officer import Officer

            return Officer.FromOffset(self.province.GovernorOffset)
        except:
            return None

    def _get_advisor_in_province(self) -> Officer | None:
        """Get the advisor if they are in this province."""
        if not self.province:
            return None

        try:
            from Officer import Officer
            from Ruler import Ruler

            # Get current ruler's advisor
            if self.province.RulerNo == 0xFF:
                return None

            ruler = Ruler.FromNo(self.province.RulerNo)
            if not ruler or not ruler.Advisor:
                return None

            # Check if advisor is in this province
            # Advisor's location is determined by their SpyInCityNo or by checking officer list
            advisor = ruler.Advisor

            # Check if advisor is in province's officer list
            province_officers = self.province.GetOfficerList()
            for officer in province_officers:
                if officer.Offset == advisor.Offset:
                    return advisor

            return None
        except:
            return None

    def _get_officer_id(self, officer: Officer) -> int:
        """Get officer ID from officer object."""
        try:
            from Data import Data

            return (officer.Offset - Data.OFFICER_START) // Data.OFFICER_SIZE
        except:
            return 0

    def _on_menu_click(self, action: str) -> None:
        """Handle menu button click."""
        self._selected_menu = action
        print(f"Menu selected: {action}")
