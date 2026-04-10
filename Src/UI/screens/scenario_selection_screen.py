"""
Scenario Selection Screen for ROTK2

A modern UI-based scenario selection screen inspired by SNES interface.
Features:
- Scrollable list of 6 historical scenarios
- Scenario details panel
- Year and starting conditions display
- Integration with scenario data from Data.py

Layout:
┌─────────────────────────────────────────┐
│  Select Historical Scenario               │
├─────────────────────────────────────────┤
│                                         │
│  ▶ 1. Dong Zhuo Seizes Power              │
│      AD 189 - Luoyang in chaos            │
│                                         │
│    2. The Anti-Dong Zhuo Coalition        │
│      AD 194 - Warlords divide the land    │
│                                         │
│    3. Battle of Guandu                    │
│      AD 200 - Cao Cao vs Yuan Shao       │
│                                         │
│    4. The Three Kingdoms                  │
│      AD 215 - Three powers emerge         │
│                                         │
│    5. Zhuge Liang's Northern Expeditions  │
│      AD 221 - Shu campaigns begin         │
│                                         │
│    6. The Later Years                     │
│      AD 235 - Final struggles             │
│                                         │
├─────────────────────────────────────────┤
│  [Description panel with scenario info] │
│                                         │
│    [Back]              [Select →]       │
└─────────────────────────────────────────┘
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import pygame

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from UI.core.anchor import Anchor
from UI.core.container import UIContainer
from UI.components.basic import UILabel, UIButton
from UI.components.multiline_label import UIMultiLineLabel
from UI.core.manager import UIManager

if TYPE_CHECKING:
    pass


class ScenarioSelectionScreen(UIContainer):
    """
    Scenario selection screen with list of historical scenarios.

    Features:
    - List of 6 ROTK2 scenarios
    - Scenario preview with description
    - Year and starting conditions
    - Keyboard/gamepad/mouse navigation
    """

    # Scenario data - matches original ROTK2
    SCENARIOS = [
        {
            "id": 1,
            "name": "Dong Zhuo Seizes Power",
            "year": 189,
            "description": "The tyrant Dong Zhuo controls Luoyang and the Emperor. Regional warlords form a coalition to oppose him, but internal conflicts threaten their alliance.",
            "highlight": "Coalition warfare, early heroes emerge",
        },
        {
            "id": 2,
            "name": "The Anti-Dong Zhuo Coalition",
            "year": 194,
            "description": "Following Dong Zhuo's death, the land fragments into warlord territories. Cao Cao, Liu Bei, and Sun Jian begin building their foundations.",
            "highlight": "Warlord consolidation, territory expansion",
        },
        {
            "id": 3,
            "name": "Battle of Guandu",
            "year": 200,
            "description": "Cao Cao faces his greatest challenge against the powerful Yuan Shao. The winner will dominate northern China. Liu Bei wanders seeking opportunity.",
            "highlight": "Epic battle, destiny-defining conflict",
        },
        {
            "id": 4,
            "name": "The Three Kingdoms",
            "year": 215,
            "description": "Three powers have emerged: Wei (Cao Cao), Shu (Liu Bei), and Wu (Sun Quan). Each seeks to unify China under their banner.",
            "highlight": "Three-way warfare, legendary strategies",
        },
        {
            "id": 5,
            "name": "Zhuge Liang's Northern Expeditions",
            "year": 221,
            "description": "Liu Bei has claimed the throne of Shu. His chancellor Zhuge Liang launches campaigns against Wei to fulfill his promise to restore the Han.",
            "highlight": "Brilliant tactics, desperate campaigns",
        },
        {
            "id": 6,
            "name": "The Later Years",
            "year": 235,
            "description": "The great heroes have passed. Their successors struggle to maintain their legacy as the era of the Three Kingdoms nears its end.",
            "highlight": "Succession struggles, final battles",
        },
    ]

    # Visual constants
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 800

    # Colors
    BG_COLOR = (26, 26, 46)
    PANEL_COLOR = (22, 33, 62)
    TITLE_COLOR = (255, 215, 0)
    SCENARIO_NORMAL = (60, 60, 80)
    SCENARIO_SELECTED = (79, 189, 186)
    SCENARIO_HOVER = (80, 80, 110)
    TEXT_COLOR = (232, 232, 232)
    HIGHLIGHT_COLOR = (100, 200, 100)

    def __init__(self):
        """Initialize the scenario selection screen."""
        super().__init__(
            position=(0, 0),
            size=(self.SCREEN_WIDTH, self.SCREEN_HEIGHT),
            background_color=self.BG_COLOR,
            parent=None,
        )

        self._scenario_buttons: list[UIButton] = []
        self._selected_scenario: int = 0  # Index of selected scenario
        self._callback: Callable[[int], None] | None = None

        # Create UI elements (order matters - details panel before scenario list)
        self._create_title()
        self._create_details_panel()
        self._create_scenario_list()
        self._create_buttons()

        # Register with UIManager
        self._register_with_manager()

    def _register_with_manager(self) -> None:
        """Register this screen with the UIManager."""
        try:
            manager = UIManager.get_instance()
            if manager:
                manager.root_component = self
                # Set focus to first scenario
                if self._scenario_buttons:
                    manager.set_focus(self._scenario_buttons[0])
        except Exception as e:
            print(f"Warning: Could not register with UIManager: {e}")

    def _create_title(self) -> None:
        """Create the title bar."""
        title_panel = UIContainer(
            position=(0, 0),
            size=(self.SCREEN_WIDTH, 60),
            background_color=self.PANEL_COLOR,
            border_color=(79, 189, 186),
            border_width=2,
            parent=self,
        )

        title_label = UILabel(
            text="Select Historical Scenario",
            position=(self.SCREEN_WIDTH // 2, 30),
            size=(800, 40),
            font=pygame.font.Font(None, 42),
            color=self.TITLE_COLOR,
            align="center",
            anchor=Anchor.CENTER,
            parent=self,
        )

    def _create_scenario_list(self) -> None:
        """Create the scrollable scenario list."""
        list_x = 80
        list_y = 80
        list_width = 600
        item_height = 90
        item_spacing = 10

        for i, scenario in enumerate(self.SCENARIOS):
            y = list_y + i * (item_height + item_spacing)

            # Create button for this scenario
            btn = UIButton(
                text=f"{i + 1}. {scenario['name']}",
                position=(list_x, y),
                size=(list_width, item_height),
                normal_color=self.SCENARIO_NORMAL,
                hover_color=self.SCENARIO_HOVER,
                text_color=self.TEXT_COLOR,
                font=pygame.font.Font(None, 32),
                on_click=lambda idx=i: self._on_scenario_select(idx, confirm=True),
                parent=self,
            )

            # Add year subtitle
            year_label = UILabel(
                text=f"AD {scenario['year']}",
                position=(list_x + list_width - 100, y + 55),
                size=(90, 25),
                font=pygame.font.Font(None, 22),
                color=(180, 180, 180),
                align="right",
                parent=self,
            )

            self._scenario_buttons.append(btn)

        # Select first scenario by default
        if self._scenario_buttons:
            self._on_scenario_select(0)

        # Track last focused button for gamepad/keyboard navigation
        self._last_focused_button: UIButton | None = None

    def _create_details_panel(self) -> None:
        """Create the details panel on the right."""
        panel_x = 720
        panel_y = 80
        panel_width = 480
        panel_height = 500

        # Panel container
        details_panel = UIContainer(
            position=(panel_x, panel_y),
            size=(panel_width, panel_height),
            background_color=self.PANEL_COLOR,
            border_color=(79, 189, 186),
            border_width=2,
            padding=20,
            parent=self,
        )

        # Selected scenario info (will be updated)
        self._details_title = UILabel(
            text=self.SCENARIOS[0]["name"],
            position=(panel_x + 20, panel_y + 30),
            size=(panel_width - 40, 40),
            font=pygame.font.Font(None, 36),
            color=self.TITLE_COLOR,
            align="left",
            parent=self,
        )

        self._details_year = UILabel(
            text=f"Year: AD {self.SCENARIOS[0]['year']}",
            position=(panel_x + 20, panel_y + 80),
            size=(panel_width - 40, 30),
            font=pygame.font.Font(None, 28),
            color=(200, 200, 100),
            align="left",
            parent=self,
        )

        self._details_highlight = UILabel(
            text=f"Focus: {self.SCENARIOS[0]['highlight']}",
            position=(panel_x + 20, panel_y + 120),
            size=(panel_width - 40, 30),
            font=pygame.font.Font(None, 24),
            color=self.HIGHLIGHT_COLOR,
            align="left",
            parent=self,
        )

        # Description (multi-line, wrapped)
        desc_font = pygame.font.Font(None, 24)
        wrapped_desc = self._wrap_text(
            self.SCENARIOS[0]["description"], desc_font, panel_width - 60
        )
        self._details_desc = UIMultiLineLabel(
            text=wrapped_desc,
            position=(panel_x + 20, panel_y + 170),
            size=(panel_width - 40, 300),
            font=desc_font,
            color=self.TEXT_COLOR,
            align="left",
            line_spacing=6,
            parent=self,
        )

    def _create_buttons(self) -> None:
        """Create Back and Select buttons."""
        button_y = 650
        button_width = 200
        button_height = 60

        # Back button
        back_btn = UIButton(
            text="← Back",
            position=(100, button_y),
            size=(button_width, button_height),
            normal_color=(60, 60, 80),
            hover_color=(80, 80, 110),
            text_color=self.TEXT_COLOR,
            font=pygame.font.Font(None, 32),
            on_click=lambda: self._on_back(),
            parent=self,
        )

        # Select button
        select_btn = UIButton(
            text="Select →",
            position=(self.SCREEN_WIDTH - 100 - button_width, button_y),
            size=(button_width, button_height),
            normal_color=(79, 189, 186),
            hover_color=(100, 210, 200),
            text_color=(0, 0, 0),
            font=pygame.font.Font(None, 32),
            on_click=lambda: self._on_select(),
            parent=self,
        )

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> str:
        """Wrap text to fit within max_width pixels."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            # Try adding this word to current line
            test_line = " ".join(current_line + [word])
            width = font.size(test_line)[0]

            if width <= max_width:
                current_line.append(word)
            else:
                # Line too long, save current line and start new one
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        # Don't forget the last line
        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines)

    def _on_scenario_select(self, index: int, confirm: bool = False) -> None:
        """Handle scenario selection.

        Args:
            index: Selected scenario index
            confirm: If True, immediately confirm selection (for click/enter/gamepad)
        """
        # Update selection
        self._selected_scenario = index

        # Update button visual states (change background color for selected)
        for i, btn in enumerate(self._scenario_buttons):
            if i == index:
                btn.normal_color = self.SCENARIO_SELECTED
                btn.border_color = (255, 255, 255)
                btn.border_width = 3
            else:
                btn.normal_color = self.SCENARIO_NORMAL
                btn.border_color = None
                btn.border_width = 0

        # Update details panel
        scenario = self.SCENARIOS[index]
        self._details_title.text = scenario["name"]
        self._details_year.text = f"Year: AD {scenario['year']}"
        self._details_highlight.text = f"Focus: {scenario['highlight']}"

        # Wrap description text
        desc_font = pygame.font.Font(None, 24)
        wrapped_desc = self._wrap_text(scenario["description"], desc_font, 440)
        self._details_desc.text = wrapped_desc

        print(f"Preview: {scenario['name']} (AD {scenario['year']})")

        # If confirm flag is set (click/enter/gamepad), immediately proceed
        if confirm and self._callback:
            self._callback(scenario["id"])

    def _on_back(self) -> None:
        """Handle back button."""
        print("Back to main menu")
        if self._callback:
            self._callback(0)  # 0 = back/cancel

    def _on_select(self) -> None:
        """Handle select button."""
        scenario_id = self.SCENARIOS[self._selected_scenario]["id"]
        print(f"Starting scenario {scenario_id}")
        if self._callback:
            self._callback(scenario_id)

    def set_callback(self, callback: Callable[[int], None]) -> None:
        """Set callback for scenario selection.

        Args:
            callback: Function called with scenario ID (1-6) or 0 for back
        """
        self._callback = callback

    def get_selected_scenario(self) -> int:
        """Get the selected scenario ID (1-6)."""
        return self.SCENARIOS[self._selected_scenario]["id"]

    def handle_event(self, event: pygame.event.Event, transform=None) -> bool:
        """Handle input events."""
        if super().handle_event(event, transform):
            return True

        # Keyboard navigation
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_back()
                return True
            elif event.key == pygame.K_UP:
                self._navigate(-1)
                return True
            elif event.key == pygame.K_DOWN:
                self._navigate(1)
                return True
            elif event.key == pygame.K_RETURN:
                # Immediate selection on Enter key
                self._on_scenario_select(self._selected_scenario, confirm=True)
                return True

        return False

    def _navigate(self, direction: int) -> None:
        """Navigate scenario list."""
        new_index = (self._selected_scenario + direction) % len(self.SCENARIOS)
        self._on_scenario_select(new_index)

        # Update focus
        try:
            manager = UIManager.get_instance()
            if manager and self._scenario_buttons:
                manager.set_focus(self._scenario_buttons[new_index])
        except:
            pass

    def update(self, dt: float) -> None:
        """Update scenario list - check for mouse hover or focus change to update preview."""
        super().update(dt)

        # Check for gamepad/keyboard focus change
        try:
            from UI.core.manager import UIManager

            manager = UIManager.get_instance()
            if manager and manager.focused_component:
                focused = manager.focused_component
                # Check if focused component is one of our scenario buttons
                if focused in self._scenario_buttons:
                    btn_index = self._scenario_buttons.index(focused)
                    # Update preview if focus moved to a different button
                    if btn_index != self._selected_scenario:
                        self._on_scenario_select(btn_index, confirm=False)
                    # Track that this button now has focus
                    self._last_focused_button = focused
        except:
            pass

        # Check if mouse is hovering over any scenario button
        # This updates the preview as the user moves their mouse
        try:
            import pygame

            mouse_pos = pygame.mouse.get_pos()

            for i, btn in enumerate(self._scenario_buttons):
                # Get button's screen rect
                abs_x, abs_y = btn.get_absolute_position()
                btn_rect = pygame.Rect(abs_x, abs_y, btn._size[0], btn._size[1])

                if btn_rect.collidepoint(mouse_pos):
                    # Mouse is hovering over this button
                    if i != self._selected_scenario:
                        # Update preview (but don't confirm)
                        self._on_scenario_select(i, confirm=False)
                    break
        except:
            pass


def test_scenario_selection():
    """Test the scenario selection screen."""
    pygame.init()

    screen = pygame.display.set_mode((1280, 800))
    pygame.display.set_caption("ROTK2 - Scenario Selection Test")

    clock = pygame.time.Clock()

    # Create UIManager
    manager = UIManager.get_instance()
    manager.actual_resolution = (1280, 800)
    from UI.core.transform import Transform

    manager.transform = Transform((1280, 800), (1280, 800))

    # Create screen
    screen_obj = ScenarioSelectionScreen()
    manager.root_component = screen_obj
    manager.current_screen = screen_obj

    selected_scenario = None

    def on_select(scenario_id: int):
        nonlocal selected_scenario
        selected_scenario = scenario_id
        print(f"\n>>> Scenario selected: {scenario_id}")
        if scenario_id == 0:
            print("Going back to main menu...")

    screen_obj.set_callback(on_select)

    print("\n" + "=" * 50)
    print("Scenario Selection Test")
    print("=" * 50)
    print("Controls:")
    print("  ↑/↓ - Navigate scenarios")
    print("  Enter - Select scenario")
    print("  ESC - Back")
    print("  Click - Select with mouse")
    print("=" * 50)

    running = True
    frame_count = 0
    while running:
        dt = clock.tick(60) / 1000.0
        frame_count += 1

        # Process events with error handling
        try:
            events = pygame.event.get()
        except (SystemError, KeyError) as e:
            print(f"Warning: Event system hiccup (frame {frame_count}): {e}")
            events = []

        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    running = False

            try:
                manager.handle_event(event)
            except Exception as e:
                print(f"Event handling error (non-fatal): {e}")

        # Check if scenario selected
        if selected_scenario is not None:
            if selected_scenario == 0:
                running = False  # Back selected
            else:
                print(f"Would start scenario {selected_scenario}")
                running = False

        # Update and render
        try:
            manager.update(dt)
        except Exception as e:
            print(f"Update error (non-fatal): {e}")

        try:
            screen.fill((15, 15, 25))
            manager.render(screen)
            pygame.display.flip()
        except Exception as e:
            print(f"Render error: {e}")
            running = False

    pygame.quit()
    print("\nTest complete!")


if __name__ == "__main__":
    test_scenario_selection()
