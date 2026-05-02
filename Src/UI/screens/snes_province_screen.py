"""
SNES-Style Province Information Screen

Layout similar to the SNES version with:
- Two rows of menu buttons at top
- Portrait on the left
- Stats panel in center
- Command prompt at bottom
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING
from pathlib import Path

import pygame

from officer_display import get_officer_display_name
from UI.core.anchor import Anchor
from UI.core.container import UIContainer
from UI.core.manager import UIManager
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

    # View submenu items
    VIEW_SUBMENU = [
        ("Back", "back"),
        ("Other Province", "other_province"),
        ("General", "general"),
        ("Summary", "summary"),
        ("Territory", "territory"),
    ]

    ARMY_SUBMENU = [
        ("Army Overview", "army_overview"),
        ("Training", "army_training"),
        ("Recruit", "army_recruit"),
    ]

    PERSON_SUBMENU = [
        ("Officer List", "person_officers"),
        ("Rewards", "person_awards"),
        ("Search", "person_search"),
    ]

    INTERNAL_SUBMENU = [
        ("Develop Land", "internal_land"),
        ("Flood Control", "internal_flood"),
        ("Give Food", "internal_loyalty"),
    ]

    MOVE_SUBMENU = [
        ("Next Province", "move_next_province"),
        ("Move Officers", "move_officers"),
        ("Transport", "move_transport"),
        ("Travel", "move_travel"),
    ]

    MENU_SUBMENUS = {
        "view": VIEW_SUBMENU,
        "army": ARMY_SUBMENU,
        "person": PERSON_SUBMENU,
        "internal": INTERNAL_SUBMENU,
        "move": MOVE_SUBMENU,
    }

    DEFAULT_ENABLED_MENUS = {"view", "army", "person", "internal", "move"}

    DEFAULT_ENABLED_SUBMENU_ACTIONS = {
        "army_training",
        "general",
        "internal_flood",
        "internal_land",
        "internal_loyalty",
        "move_next_province",
        "other_province",
        "person_awards",
        "summary",
        "territory",
    }

    def __init__(
        self,
        province: Province | None = None,
        enabled_menus: set[str] | None = None,
        enabled_submenu_actions: set[str] | None = None,
        prompt_text: str | None = None,
        on_back: Callable[[], None] | None = None,
    ):
        """
        Initialize SNES-style province screen.

        Args:
            province: Province to display
        """
        super().__init__(
            position=(0, 0), size=(1280, 800), background_color=(15, 15, 25), parent=None
        )

        self.province = province
        self.enabled_menus = enabled_menus or self.DEFAULT_ENABLED_MENUS.copy()
        self.enabled_submenu_actions = (
            enabled_submenu_actions or self.DEFAULT_ENABLED_SUBMENU_ACTIONS.copy()
        )
        self._prompt_override = prompt_text
        self._on_back_callback = on_back
        self.portrait_loader = SnesPortraitLoader()
        self._selected_menu: str | None = None
        self._submenu_container: UIContainer | None = None
        self._submenu_parent_button: UIButton | None = None
        self._menu_buttons: dict[str, UIButton] = {}
        self._submenu_actions: dict[str, UIButton] = {}
        self._menu_action_callback: Callable[[str], None] | None = None
        self._create_ui()
        self._set_initial_focus()

    def _set_initial_focus(self) -> None:
        """Set initial focus to the first enabled top-level menu button."""
        manager = UIManager.get_instance()
        if not manager:
            return

        for action in self.MENUS_ROW1 + self.MENUS_ROW2:
            button = self._menu_buttons.get(action[1])
            if button and button.enabled:
                manager.set_focus(button)
                return

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

    # Province name mappings (Chinese -> English)
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

    def _get_province_name_english(self) -> str:
        """Get English province name."""
        if not self.province:
            return "Unknown Province"
        # Parse the Chinese name (e.g., "幽州-1" -> "Youzhou-1")
        chinese_name = self.province.Name
        for cn, en in self.PROVINCE_NAMES.items():
            if cn in chinese_name:
                return chinese_name.replace(cn, en)
        return chinese_name

    def _get_current_date(self) -> str:
        """Get current game date as string."""
        try:
            from Data import Data

            year = Data.BUF[0x44] + Data.BUF[0x45] * 256
            month = Data.BUF[0x46] + 1
            # Get month name
            months = [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ]
            month_name = months[month - 1] if 1 <= month <= 12 else str(month)
            return f"{month_name} {year}"
        except:
            return "Unknown Date"

    def _create_title_bar(self) -> None:
        """Create the province name and date title bar."""
        province_text = self._get_province_name_english()
        date_text = self._get_current_date()

        title_bg = UIContainer(
            position=(0, 0), size=(1280, 50), background_color=(30, 30, 50), parent=self
        )

        # Province name on left
        province_label = UILabel(
            text=province_text,
            position=(20, 25),
            size=(400, 40),
            font=pygame.font.Font(None, 36),
            color=(233, 69, 96),
            align="left",
            anchor=Anchor.CENTER_LEFT,
            parent=title_bg,
        )

        # Date on right
        date_label = UILabel(
            text=date_text,
            position=(1260, 25),
            size=(200, 40),
            font=pygame.font.Font(None, 32),
            color=(200, 200, 200),
            align="right",
            anchor=Anchor.CENTER_RIGHT,
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
                on_click=lambda act=action: self._on_menu_click(act),
                parent=self,
            )
            if action not in self.enabled_menus:
                btn.enabled = False
                btn.normal_color = (45, 45, 55)
                btn.hover_color = (45, 45, 55)
                btn.text_color = (140, 140, 150)
            self._menu_buttons[action] = btn

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
                on_click=lambda act=action: self._on_menu_click(act),
                parent=self,
            )
            if action not in self.enabled_menus:
                btn.enabled = False
                btn.normal_color = (45, 45, 55)
                btn.hover_color = (45, 45, 55)
                btn.text_color = (140, 140, 150)
            self._menu_buttons[action] = btn

    def _create_main_content(self) -> None:
        """Create portrait, personnel section, and stats panel."""
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

        # Personnel section under portrait
        personnel_y = portrait_y + portrait_size[1] + 20
        self._create_personnel_section(self, portrait_x, personnel_y)

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
            ("Free Generals", f"{self.province.UnClaimedOfficerNumber}"),
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
        prompt_text = (
            self._prompt_override or f"{ruler_name}, your orders for Province {province_num}?"
        )

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
        return get_officer_display_name(officer)

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

    def _show_submenu(
        self, parent_action: str, items: list[tuple[str, str]], x: int, y: int
    ) -> None:
        """
        Show a submenu below the specified position.

        Args:
            parent_action: The parent menu action that opened this submenu
            items: List of (label, action) tuples for submenu items
            x: X position for submenu
            y: Y position for submenu
        """
        # Hide any existing submenu
        self._hide_submenu()

        # Track the parent button that opened this submenu
        self._submenu_parent_button = self._menu_buttons.get(parent_action)

        # Create submenu container
        button_height = 40
        button_width = 200
        padding = 5

        submenu_height = len(items) * (button_height + padding) + padding

        self._submenu_container = UIContainer(
            position=(x, y),
            size=(button_width + 20, submenu_height),
            background_color=(35, 35, 50),
            border_color=(80, 80, 100),
            border_width=2,
            padding=10,
            parent=self,
        )

        # Add submenu buttons
        self._submenu_actions.clear()
        first_button = None
        for i, (label, action) in enumerate(items):
            btn = UIButton(
                text=label,
                position=(10, 10 + i * (button_height + padding)),
                size=(button_width, button_height),
                normal_color=(50, 50, 70),
                hover_color=(70, 70, 90),
                text_color=(255, 255, 255),
                on_click=lambda act=action: self._on_submenu_click(act),
                parent=self._submenu_container,
            )
            if action not in self.enabled_submenu_actions:
                btn.enabled = False
                btn.normal_color = (45, 45, 55)
                btn.hover_color = (45, 45, 55)
                btn.text_color = (140, 140, 150)
            if first_button is None and btn.enabled:
                first_button = btn
            self._submenu_actions[action] = btn

        # Move focus to first submenu item
        if first_button:
            from UI.core.manager import UIManager

            ui_manager = UIManager.get_instance()
            if ui_manager:
                ui_manager.set_focus(first_button)

    def close_submenu(self) -> bool:
        """Close the submenu (called by UIManager when B button is pressed)."""
        if self._submenu_container:
            self._hide_submenu()
            # Return focus to the parent button
            if self._submenu_parent_button:
                from UI.core.manager import UIManager

                ui_manager = UIManager.get_instance()
                if ui_manager:
                    ui_manager.set_focus(self._submenu_parent_button)
            return True

        if self._on_back_callback:
            self._on_back_callback()
            return True

        return False

    def is_submenu_open(self) -> bool:
        """Check if a submenu is currently open."""
        return self._submenu_container is not None

    def _hide_submenu(self) -> None:
        """Hide the current submenu."""
        if self._submenu_container:
            self.remove_child(self._submenu_container)
            self._submenu_container = None

    def _on_submenu_click(self, action: str) -> None:
        """Handle submenu item click."""
        if action not in self.enabled_submenu_actions:
            return

        self._hide_submenu()
        # Return focus to the parent button
        if self._submenu_parent_button:
            from UI.core.manager import UIManager

            ui_manager = UIManager.get_instance()
            if ui_manager:
                ui_manager.set_focus(self._submenu_parent_button)

        if self._menu_action_callback:
            self._menu_action_callback(action)

    def _on_menu_click(self, action: str) -> None:
        """Handle menu button click."""
        if action not in self.enabled_menus:
            return

        self._selected_menu = action

        # Hide any existing submenu
        self._hide_submenu()

        items = self.MENU_SUBMENUS.get(action)
        button = self._menu_buttons.get(action)
        if items and button:
            self._show_submenu(action, items, button.rect.x, button.rect.y + 55)
            return

        if self._menu_action_callback:
            self._menu_action_callback(action)

    def set_action_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for enabled menu and submenu actions."""
        self._menu_action_callback = callback
