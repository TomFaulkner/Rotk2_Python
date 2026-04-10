"""
Main Menu Screen for ROTK2

A modern UI-based main menu inspired by the SNES interface.
Features:
- Vertical button list with keyboard/gamepad/mouse support
- Animated transitions
- SNES-style aesthetics with modern polish
- Steam Deck optimized (1280x800)

Layout:
┌─────────────────────────────────────────┐
│  [SNES-style banner/logo]               │
│                                         │
│      Romance of the Three Kingdoms II     │
│                                         │
│         ┌─────────────────┐             │
│         │   New Game      │             │
│         ├─────────────────┤             │
│         │   Continue      │             │
│         ├─────────────────┤             │
│         │   Load Game     │             │
│         ├─────────────────┤             │
│         │   Settings      │             │
│         ├─────────────────┤             │
│         │   Quit          │             │
│         └─────────────────┘             │
│                                         │
└─────────────────────────────────────────┘
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import pygame

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from UI.core.anchor import Anchor
from UI.core.container import UIContainer
from UI.components.basic import UILabel, UIButton
from UI.core.manager import UIManager

if TYPE_CHECKING:
    pass


class MainMenuScreen(UIContainer):
    """
    Main menu screen with SNES-style vertical button layout.

    Features:
    - Vertical menu buttons
    - Keyboard/gamepad navigation
    - Mouse support
    - Animated hover/selection states
    - Integration with UIManager for focus handling
    """

    # Menu button configurations
    MENU_ITEMS = [
        ("New Game", "new_game"),
        ("Continue", "continue"),
        ("Load Game", "load_game"),
        ("Settings", "settings"),
        ("Quit", "quit"),
    ]

    # Visual constants
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 800

    # Colors
    BG_COLOR = (26, 26, 46)  # Dark blue-gray
    PANEL_COLOR = (22, 33, 62)  # Slightly lighter
    TITLE_COLOR = (255, 215, 0)  # Gold
    BUTTON_NORMAL = (60, 60, 80)
    BUTTON_HOVER = (80, 80, 110)
    BUTTON_SELECTED = (79, 189, 186)  # Bright cyan/teal
    TEXT_COLOR = (232, 232, 232)  # Off-white

    def __init__(self):
        """Initialize the main menu screen."""
        super().__init__(
            position=(0, 0),
            size=(self.SCREEN_WIDTH, self.SCREEN_HEIGHT),
            background_color=self.BG_COLOR,
            parent=None,
        )

        self._menu_buttons: dict[str, UIButton] = {}
        self._selected_action: str | None = None
        self._callback: Callable[[str], None] | None = None

        # Create UI elements
        self._create_title()
        self._create_menu_buttons()
        self._create_footer()

        # Register with UIManager
        self._register_with_manager()

    def _register_with_manager(self) -> None:
        """Register this screen with the UIManager."""
        try:
            manager = UIManager.get_instance()
            if manager:
                # Clear any existing root and set this as new root
                manager.root_component = self

                # Set focus to first button
                first_button = self._menu_buttons.get("new_game")
                if first_button:
                    manager.set_focus(first_button)
        except Exception as e:
            print(f"Warning: Could not register with UIManager: {e}")

    def _create_title(self) -> None:
        """Create the title banner."""
        # Title background panel
        title_panel = UIContainer(
            position=(0, 60),
            size=(self.SCREEN_WIDTH, 120),
            background_color=self.PANEL_COLOR,
            border_color=(79, 189, 186),
            border_width=2,
            parent=self,
        )

        # Main title
        title_label = UILabel(
            text="Romance of the Three Kingdoms II",
            position=(self.SCREEN_WIDTH // 2, 60),
            size=(800, 50),
            font=pygame.font.Font(None, 48),
            color=self.TITLE_COLOR,
            align="center",
            anchor=Anchor.TOP_CENTER,
            parent=self,
        )

        # Subtitle
        subtitle_label = UILabel(
            text="Python Remake - Steam Deck Edition",
            position=(self.SCREEN_WIDTH // 2, 110),
            size=(600, 30),
            font=pygame.font.Font(None, 24),
            color=(180, 180, 180),
            align="center",
            anchor=Anchor.TOP_CENTER,
            parent=self,
        )

    def _create_menu_buttons(self) -> None:
        """Create the vertical menu button list."""
        button_width = 400
        button_height = 60
        button_spacing = 15
        start_y = 220
        center_x = self.SCREEN_WIDTH // 2

        for i, (label, action) in enumerate(self.MENU_ITEMS):
            y = start_y + i * (button_height + button_spacing)

            btn = UIButton(
                text=label,
                position=(center_x - button_width // 2, y),
                size=(button_width, button_height),
                normal_color=self.BUTTON_NORMAL,
                hover_color=self.BUTTON_HOVER,
                text_color=self.TEXT_COLOR,
                font=pygame.font.Font(None, 36),
                on_click=lambda act=action: self._on_menu_select(act),
                parent=self,
            )

            self._menu_buttons[action] = btn

    def _create_footer(self) -> None:
        """Create footer with control hints."""
        footer_y = self.SCREEN_HEIGHT - 60

        # Control hints panel
        footer_panel = UIContainer(
            position=(0, footer_y),
            size=(self.SCREEN_WIDTH, 60),
            background_color=self.PANEL_COLOR,
            border_color=(79, 189, 186),
            border_width=1,
            parent=self,
        )

        # Control hints text
        hints_label = UILabel(
            text="↑↓ Navigate  |  Enter/A Select  |  Mouse Click",
            position=(self.SCREEN_WIDTH // 2, footer_y + 30),
            size=(600, 30),
            font=pygame.font.Font(None, 20),
            color=(180, 180, 180),
            align="center",
            anchor=Anchor.CENTER,
            parent=self,
        )

    def _on_menu_select(self, action: str) -> None:
        """Handle menu selection."""
        self._selected_action = action
        print(f"Main Menu: {action} selected")

        # Call callback if set
        if self._callback:
            self._callback(action)

    def set_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for menu actions."""
        self._callback = callback

    def get_selected_action(self) -> str | None:
        """Get the last selected action."""
        return self._selected_action

    def handle_event(self, event: pygame.event.Event, transform=None) -> bool:
        """Handle input events."""
        # Let parent handle first (pass transform if needed)
        if super().handle_event(event, transform):
            return True

        # Keyboard navigation
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # ESC on main menu = quit
                self._on_menu_select("quit")
                return True
            elif event.key == pygame.K_UP:
                self._navigate_menu(-1)
                return True
            elif event.key == pygame.K_DOWN:
                self._navigate_menu(1)
                return True

        return False

    def _navigate_menu(self, direction: int) -> None:
        """Navigate menu with arrow keys."""
        try:
            manager = UIManager.get_instance()
            if not manager:
                return

            current_focus = manager.get_focus()

            # Find current index
            actions = list(self._menu_buttons.keys())
            current_idx = -1

            for i, action in enumerate(actions):
                if self._menu_buttons[action] == current_focus:
                    current_idx = i
                    break

            # Move to next/previous
            new_idx = (current_idx + direction) % len(actions)
            new_button = self._menu_buttons[actions[new_idx]]

            manager.set_focus(new_button)

        except Exception as e:
            print(f"Navigation error: {e}")

    def update(self, dt: float) -> None:
        """Update the screen."""
        super().update(dt)

    def render(self, surface: pygame.Surface, transform=None) -> None:
        """Render the screen."""
        # Clear background
        surface.fill(self.BG_COLOR)

        # Render all children (if transform provided, pass it)
        if transform:
            super().render(surface, transform)
        else:
            # Simple render without transform for testing
            for child in self._children:
                if child.visible:
                    child.render(surface)


def test_main_menu():
    """Test the main menu screen."""
    pygame.init()

    # Create window at Steam Deck resolution
    screen_size = (1280, 800)
    virtual_size = (1280, 800)
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("ROTK2 - Main Menu Test")

    clock = pygame.time.Clock()

    # Create UIManager with proper resolution
    manager = UIManager.get_instance()
    manager.actual_resolution = screen_size
    # Recreate transform with correct resolution
    from UI.core.transform import Transform

    manager.transform = Transform(virtual_size, screen_size)

    # Create menu
    menu = MainMenuScreen()
    manager.root_component = menu
    manager.current_screen = menu

    # Track selections
    selected_action = None

    def on_action(action: str):
        nonlocal selected_action
        selected_action = action
        print(f"\n>>> Action selected: {action}")

        if action == "quit":
            print("Quitting...")

    menu.set_callback(on_action)

    print("\n" + "=" * 50)
    print("Main Menu Test")
    print("=" * 50)
    print("Controls:")
    print("  ↑/↓ - Navigate menu")
    print("  Enter or Click - Select")
    print("  ESC - Quit")
    print("=" * 50)

    running = True
    frame_count = 0
    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds
        frame_count += 1

        # Process events with extra error handling
        try:
            events = pygame.event.get()
        except (SystemError, KeyError) as e:
            # Gamepad-related errors in pygame.event.get() - skip this frame
            print(f"Warning: Event system hiccup (frame {frame_count}): {e}")
            events = []

        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    running = False

            # Pass events to manager (which dispatches to focused component)
            try:
                manager.handle_event(event)
            except Exception as e:
                print(f"Event handling error (non-fatal): {e}")
                # Don't crash on event handling errors
                pass

        # Check if quit was selected
        if selected_action == "quit":
            running = False

        # Update
        try:
            manager.update(dt)
        except Exception as e:
            print(f"Update error (non-fatal): {e}")
            pass

        # Render
        try:
            screen.fill((15, 15, 25))  # Clear screen
            manager.render(screen)
            pygame.display.flip()
        except Exception as e:
            print(f"Render error: {e}")
            import traceback

            traceback.print_exc()
            running = False

    pygame.quit()
    print("\nTest complete!")


if __name__ == "__main__":
    test_main_menu()
