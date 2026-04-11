"""
Ruler Selection Screen for ROTK2 - Popup Overlay Design

Interactive map-based ruler selection with popup overlay.
Features:
- Full-screen interactive world map
- Click on a province OR use keyboard/gamepad to navigate
- Popup shows ruler info over the map
- Keyboard/Gamepad: Arrow keys/D-pad to cycle provinces, A/Enter to select

Layout:
┌────────────────────────────────────────────┐
│  Select Your Ruler - Click or Navigate       │
├────────────────────────────────────────────┤
│                                             │
│  ┌─────────────────────────────────────────┐│
│  │                                         ││
│  │         [FULL SCREEN WORLD MAP]         ││
│  │                                         ││
│  │  Provinces shown with ruler colors     ││
│  │  Selected province highlighted         ││
│  │                                         ││
│  │  [POPUP - appears when province         ││
│  │   selected]:                            ││
│  │   ┌─────────────────────────────────┐  ││
│  │   │  [Portrait]  Ruler Name         │  ││
│  │   │            Officers: X          │  ││
│  │   │            Soldiers: X            │  ││
│  │   │            [Confirm] [Cancel]   │  ││
│  │   └─────────────────────────────────┘  ││
│  │                                         ││
│  └─────────────────────────────────────────┘│
│                                             │
│  [🎲 Random]  [← Back]                     │
└────────────────────────────────────────────┘
"""

from __future__ import annotations

from dataclasses import dataclass
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from Officer import Officer
from Province import Province
from Ruler import Ruler
from officer_display import get_officer_display_name

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from UI.components.basic import UIButton, UILabel
from UI.components.image import UIImage
from UI.components.multiline_label import UIMultiLineLabel
from UI.components.province_selector import UIProvinceSelector
from UI.core.anchor import Anchor
from UI.core.container import UIContainer
from UI.core.gamepad_handler import GamepadButton
from UI.core.manager import UIManager
from UI.screens.snes_province_screen import SnesPortraitLoader

if TYPE_CHECKING:
    pass


@dataclass
class RulerSelectionResult:
    """Structured result returned from the ruler selection screen."""

    province_no: int
    ruler_no: int
    ruler_name: str


class RulerSelectionScreen(UIContainer):
    """Ruler selection screen with full-screen map and popup overlay."""

    # Tell UIManager we handle our own keyboard/gamepad navigation
    handles_own_navigation = True

    # Visual constants
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 800

    # Colors
    BG_COLOR = (26, 26, 46)
    PANEL_COLOR = (22, 33, 62)
    POPUP_COLOR = (30, 35, 55)
    TITLE_COLOR = (255, 215, 0)
    BUTTON_NORMAL = (60, 60, 80)
    BUTTON_HOVER = (80, 80, 110)
    BUTTON_SELECT = (79, 189, 186)
    TEXT_COLOR = (232, 232, 232)
    HIGHLIGHT_COLOR = (100, 200, 100)
    HIGHLIGHT_BORDER = (255, 255, 100)

    def __init__(self):
        """Initialize the ruler selection screen."""
        super().__init__(
            position=(0, 0),
            size=(self.SCREEN_WIDTH, self.SCREEN_HEIGHT),
            background_color=self.BG_COLOR,
            parent=None,
        )

        self._selected_province: int | None = None
        self._selected_ruler: str | None = None
        self._selected_result: RulerSelectionResult | None = None
        self._callback: Callable[[RulerSelectionResult | None], None] | None = None
        self._showing_popup: bool = False

        self._playable_provinces: list[int] = self._get_playable_provinces()

        # Focus management for popup
        self._popup_buttons: list[UIButton] = []
        self._focused_popup_button: int = 0  # 0 = Select, 1 = Cancel

        # Portrait loader for ruler portraits
        # Get absolute path to Resources directory
        resources_path = Path(__file__).parent.parent.parent.parent / "Resources"
        self._portrait_loader = SnesPortraitLoader(str(resources_path))
        self._portrait_image: UIImage | None = None

        # Create UI elements
        self._create_title()
        self._create_map()
        self._create_popup()  # Hidden initially
        self._create_bottom_buttons()

        # Register with UIManager
        self._register_with_manager()

    def _register_with_manager(self) -> None:
        """Register this screen with the UIManager."""
        try:
            manager = UIManager.get_instance()
            if manager:
                manager.root_component = self
        except Exception as e:
            print(f"Warning: Could not register with UIManager: {e}")

    def _create_title(self) -> None:
        """Create the title bar."""
        UIContainer(
            position=(0, 0),
            size=(self.SCREEN_WIDTH, 50),
            background_color=self.PANEL_COLOR,
            border_color=(79, 189, 186),
            border_width=2,
            parent=self,
        )

        UILabel(
            text="Select Your Ruler - Click on Map or Use ↑↓←→ to Navigate",
            position=(self.SCREEN_WIDTH // 2, 25),
            size=(1000, 40),
            font=pygame.font.Font(None, 36),
            color=self.TITLE_COLOR,
            align="center",
            anchor=Anchor.CENTER,
            parent=self,
        )

    def _create_map(self) -> None:
        """Create the full-screen interactive world map."""
        # Map takes up most of screen below title
        map_x = 20
        map_y = 60
        map_width = 1240
        map_height = 680

        self._province_selector = UIProvinceSelector(
            position=(map_x, map_y),
            size=(map_width, map_height),
            playable_provinces=self._playable_provinces,
            on_province_changed=self._on_province_changed,
            on_province_confirmed=self._on_province_confirmed,
            parent=self,
        )

        for province in Province.GetList():
            if province.RulerNo != 0xFF:
                self._province_selector.map_renderer.set_province_ruler(
                    province.No, province.RulerNo
                )

    def _get_playable_provinces(self) -> list[int]:
        """Return provinces controlled by a ruler in the loaded scenario."""
        return [province.No for province in Province.GetList() if province.RulerNo != 0xFF]

    def _build_selection_result(self, province_id: int) -> RulerSelectionResult | None:
        """Build real scenario selection data for the chosen province."""
        province = Province.FromSequence(province_id)
        if province.RulerNo == 0xFF:
            return None

        ruler = Ruler.FromNo(province.RulerNo)
        if ruler is None or ruler.RulerSelf is None:
            return None

        return RulerSelectionResult(
            province_no=province.No,
            ruler_no=province.RulerNo,
            ruler_name=self._get_display_name(ruler.RulerSelf),
        )

    def _get_display_name(self, officer: Officer) -> str:
        """Get a display-safe officer name for the modern UI."""
        return get_officer_display_name(officer)

    def _create_popup(self) -> None:
        """Create the ruler info popup (initially hidden)."""
        popup_width = 450
        popup_height = 320
        popup_x = (self.SCREEN_WIDTH - popup_width) // 2
        popup_y = (self.SCREEN_HEIGHT - popup_height) // 2

        # Popup container - positioned at center
        self._popup = UIContainer(
            position=(popup_x, popup_y),
            size=(popup_width, popup_height),
            background_color=self.POPUP_COLOR,
            border_color=(255, 255, 255),
            border_width=3,
            padding=20,
            parent=self,
        )
        self._popup.visible = False  # Hidden initially

        # Portrait area - positioned inside popup (relative coords)
        portrait_size = 110
        self._portrait_area = UIContainer(
            position=(20, 20),  # Relative to popup
            size=(portrait_size, portrait_size),
            background_color=(50, 50, 70),
            border_color=(100, 100, 120),
            border_width=2,
            parent=self._popup,
        )

        # Portrait image (will be set when ruler is selected)
        self._portrait_image = None

        # Ruler name - to the right of portrait
        self._popup_ruler_name = UILabel(
            text="Select a Province",
            position=(20 + portrait_size + 15, 25),
            size=(popup_width - portrait_size - 55, 35),
            font=pygame.font.Font(None, 28),
            color=self.TITLE_COLOR,
            align="left",
            parent=self._popup,
        )

        # Province info - below ruler name
        self._popup_province = UILabel(
            text="Use arrow keys or click",
            position=(20 + portrait_size + 15, 65),
            size=(popup_width - portrait_size - 55, 25),
            font=pygame.font.Font(None, 20),
            color=(180, 180, 180),
            align="left",
            parent=self._popup,
        )

        # Stats - below province info (using multi-line for proper newline handling)
        self._popup_stats = UIMultiLineLabel(
            text="Officers: -\nSoldiers: -",
            position=(20 + portrait_size + 15, 95),
            size=(popup_width - portrait_size - 55, 50),
            font=pygame.font.Font(None, 20),
            color=self.HIGHLIGHT_COLOR,
            align="left",
            parent=self._popup,
        )

        # Bio - below portrait (full width, using multi-line with wrapping)
        self._popup_bio = UIMultiLineLabel(
            text="Navigate to a province to see ruler information.",
            position=(20, 145),
            size=(popup_width - 40, 90),
            font=pygame.font.Font(None, 20),  # Smaller font for better fit
            color=self.TEXT_COLOR,
            align="left",
            line_spacing=2,
            parent=self._popup,
        )

        # Confirm button - bottom left
        self._popup_select_btn = UIButton(
            text="✓ Select",
            position=(popup_width // 2 - 100, popup_height - 55),
            size=(90, 40),
            normal_color=self.BUTTON_SELECT,
            hover_color=(100, 210, 200),
            text_color=(0, 0, 0),
            font=pygame.font.Font(None, 22),
            on_click=self._on_confirm_selection,
            parent=self._popup,
        )

        # Cancel button - bottom right
        self._popup_cancel_btn = UIButton(
            text="✕ Cancel",
            position=(popup_width // 2 + 10, popup_height - 55),
            size=(90, 40),
            normal_color=(100, 60, 60),
            hover_color=(120, 80, 80),
            text_color=self.TEXT_COLOR,
            font=pygame.font.Font(None, 22),
            on_click=self._on_cancel_popup,
            parent=self._popup,
        )

        # Store popup buttons for focus navigation
        self._popup_buttons = [self._popup_select_btn, self._popup_cancel_btn]

    def _create_bottom_buttons(self) -> None:
        """Create bottom action buttons."""
        button_y = self.SCREEN_HEIGHT - 50
        button_width = 150
        button_height = 40

        # Random button
        UIButton(
            text="🎲 Random",
            position=(30, button_y),
            size=(button_width, button_height),
            normal_color=(100, 80, 120),
            hover_color=(120, 100, 140),
            text_color=self.TEXT_COLOR,
            font=pygame.font.Font(None, 22),
            on_click=self._on_random,
            parent=self,
        )

        # Back button
        UIButton(
            text="← Back",
            position=(self.SCREEN_WIDTH - 30 - button_width, button_y),
            size=(button_width, button_height),
            normal_color=self.BUTTON_NORMAL,
            hover_color=self.BUTTON_HOVER,
            text_color=self.TEXT_COLOR,
            font=pygame.font.Font(None, 22),
            on_click=self._on_back,
            parent=self,
        )

    def _on_province_changed(self, province_id: int | None) -> None:
        """Update ruler preview state when the selected province changes."""
        if province_id is None:
            self._selected_province = None
            self._selected_ruler = None
            self._selected_result = None
            return

        result = self._build_selection_result(province_id)
        if result is None:
            self._selected_province = None
            self._selected_ruler = None
            self._selected_result = None
            return

        self._selected_province = province_id
        self._selected_ruler = result.ruler_name
        self._selected_result = result

    def _on_province_confirmed(self, province_id: int) -> None:
        """Show the ruler popup when the current province is confirmed."""
        self._on_province_changed(province_id)
        if self._selected_ruler:
            self._show_popup()
            self._focused_popup_button = 0
            self._update_popup_focus()

    def _show_popup(self) -> None:
        """Show the ruler info popup."""
        if not self._selected_ruler:
            return

        self._showing_popup = True
        self._popup.visible = True

        # Update popup content
        self._popup_ruler_name.text = self._selected_ruler
        self._popup_province.text = f"Province {self._selected_province}"

        province = Province.FromSequence(self._selected_province)
        officers = len(province.GetOfficerList())
        soldiers = province.Soldiers
        self._popup_stats.text = f"Officers: {officers}\nSoldiers: {soldiers:,}"

        bio = self._build_ruler_bio(province)
        self._popup_bio.text = bio

        # Load and display portrait
        self._update_portrait()

    def _build_ruler_bio(self, province: Province) -> str:
        """Build a lightweight real-data bio for the selected ruler."""
        ruler = Ruler.FromNo(province.RulerNo)
        governor = Officer.FromOffset(province.GovernorOffset)
        if ruler is None or ruler.RulerSelf is None or governor is None:
            return "No ruler information available."

        trust = getattr(ruler, "TrustRating", 0)
        return (
            f"Ruler of province {province.No}. "
            f"Governor: {self._get_display_name(governor)}. "
            f"Trust: {trust}. "
            f"Home province: {ruler.HomeCity.No if ruler.HomeCity else province.No}."
        )

    def _update_portrait(self) -> None:
        """Load and display the ruler's portrait."""
        if not self._selected_result or not self._portrait_loader:
            return

        # Remove existing portrait image if any
        if self._portrait_image:
            if self._portrait_image in self._popup.children:
                self._popup.children.remove(self._portrait_image)
            self._portrait_image = None

        province = Province.FromSequence(self._selected_result.province_no)
        governor = Officer.FromOffset(province.GovernorOffset)
        if governor is None:
            return

        officer_id = (governor.Offset - Data.OFFICER_START) // Data.OFFICER_SIZE

        # Load portrait
        portrait_size = (100, 100)
        portrait_surface = self._portrait_loader.get_portrait(officer_id, portrait_size)

        if portrait_surface:
            # Create UIImage with the portrait
            self._portrait_image = UIImage(
                image=portrait_surface,
                position=(25, 25),  # Slightly inside the portrait area
                size=portrait_size,
                parent=self._popup,
            )

    def _update_popup_focus(self) -> None:
        """Update visual focus on popup buttons."""
        if not self._popup_buttons:
            return

        # Clear focus from all buttons
        for btn in self._popup_buttons:
            btn.border_width = 0
            btn.border_color = None

        # Set focus on current button
        if 0 <= self._focused_popup_button < len(self._popup_buttons):
            focused_btn = self._popup_buttons[self._focused_popup_button]
            focused_btn.border_width = 3
            focused_btn.border_color = (255, 255, 255)

            # Also update UIManager focus for consistency
            try:
                manager = UIManager.get_instance()
                if manager:
                    manager.set_focus(focused_btn)
            except Exception:
                pass

    def _on_confirm_selection(self) -> None:
        """Confirm ruler selection."""
        if self._selected_result and self._callback:
            print(f"Confirmed ruler: {self._selected_ruler}")
            self._callback(self._selected_result)

    def _on_cancel_popup(self) -> None:
        """Cancel/hide popup."""
        self._showing_popup = False
        self._popup.visible = False

    def _on_random(self) -> None:
        """Select random ruler."""
        import random

        if not self._playable_provinces:
            return

        province_id = random.choice(self._playable_provinces)
        manager = UIManager.get_instance()
        self._province_selector.set_selected_province(
            province_id, manager.transform if manager else None
        )
        print(f"Random selection: {self._selected_ruler} (Province {self._selected_province})")
        self._show_popup()

    def _on_back(self) -> None:
        """Handle back button."""
        print("Back to scenario selection")
        if self._callback:
            self._callback(None)

    def set_callback(self, callback: Callable[[RulerSelectionResult | None], None]) -> None:
        """Set callback for ruler selection."""
        self._callback = callback

    def get_selected_ruler(self) -> RulerSelectionResult | None:
        """Get the selected ruler result."""
        return self._selected_result

    def handle_gamepad_button(self, button: GamepadButton) -> bool:
        """Handle gamepad input for province selection and popup navigation."""
        manager = UIManager.get_instance()
        transform = manager.transform if manager else None

        if self._showing_popup:
            if button == GamepadButton.B:
                self._on_cancel_popup()
                return True
            if button in (GamepadButton.DPAD_LEFT, GamepadButton.LEFT_STICK_LEFT):
                self._focused_popup_button = max(0, self._focused_popup_button - 1)
                self._update_popup_focus()
                return True
            if button in (GamepadButton.DPAD_RIGHT, GamepadButton.LEFT_STICK_RIGHT):
                self._focused_popup_button = min(1, self._focused_popup_button + 1)
                self._update_popup_focus()
                return True
            if button == GamepadButton.A:
                if self._focused_popup_button == 0:
                    self._on_confirm_selection()
                else:
                    self._on_cancel_popup()
                return True
            return False

        if button == GamepadButton.B:
            self._on_back()
            return True

        return bool(transform and self._province_selector.handle_gamepad_button(button, transform))

    def render(self, surface: pygame.Surface, transform=None) -> None:
        """Render the screen."""
        surface.fill(self.BG_COLOR)

        for child in self.children:
            if child != self._popup and child.visible:
                child.render(surface, transform)

        if self._showing_popup:
            overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(128)
            surface.blit(overlay, (0, 0))
            self._popup.render(surface, transform)

    def handle_event(self, event: pygame.event.Event, transform=None) -> bool:
        """Handle input events."""
        if self._showing_popup:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._on_cancel_popup()
                    return True
                elif event.key == pygame.K_LEFT:
                    # Move focus between popup buttons
                    self._focused_popup_button = max(0, self._focused_popup_button - 1)
                    self._update_popup_focus()
                    return True
                elif event.key == pygame.K_RIGHT:
                    # Move focus between popup buttons
                    self._focused_popup_button = min(1, self._focused_popup_button + 1)
                    self._update_popup_focus()
                    return True
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    # Activate focused popup button
                    if self._focused_popup_button == 0:
                        self._on_confirm_selection()
                    else:
                        self._on_cancel_popup()
                    return True

            # Let popup handle its own button clicks
            if self._popup.handle_event(event, transform):
                return True

            # Click outside popup closes it
            if event.type == pygame.MOUSEBUTTONDOWN:
                popup_rect = pygame.Rect(self._popup.position, self._popup.size)
                if not popup_rect.collidepoint(event.pos):
                    self._on_cancel_popup()
                    return True
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_back()
                return True
            if event.key == pygame.K_r:
                self._on_random()
                return True

        if self._province_selector.handle_event(event, transform):
            return True

        return bool(super().handle_event(event, transform))

    def update(self, dt: float) -> None:
        """Update screen."""
        super().update(dt)


def test_ruler_selection():
    """Test the ruler selection screen."""
    pygame.init()

    screen = pygame.display.set_mode((1280, 800))
    pygame.display.set_caption("ROTK2 - Ruler Selection Test")

    clock = pygame.time.Clock()

    # Create UIManager
    manager = UIManager.get_instance()
    manager.actual_resolution = (1280, 800)
    from UI.core.transform import Transform

    manager.transform = Transform((1280, 800), (1280, 800))

    # Create screen
    screen_obj = RulerSelectionScreen()
    manager.root_component = screen_obj
    manager.current_screen = screen_obj

    selected_ruler = None

    def on_select(ruler: RulerSelectionResult | None):
        nonlocal selected_ruler
        selected_ruler = ruler
        if ruler:
            print(f"\n>>> Ruler selected: {ruler.ruler_name}")
        else:
            print("\n>>> Back to scenario selection")

    screen_obj.set_callback(on_select)

    print("\n" + "=" * 50)
    print("Ruler Selection Test")
    print("=" * 50)
    print("Controls:")
    print("  Click on map - Select/cycle province")
    print("  Arrow keys - Navigate provinces")
    print("  Enter/Space - Show ruler info popup")
    print("  R - Random ruler")
    print("  ESC - Back")
    print("=" * 50)

    running = True
    frame_count = 0
    while running:
        dt = clock.tick(60) / 1000.0
        frame_count += 1

        # Process events
        try:
            events = pygame.event.get()
        except (SystemError, KeyError) as e:
            print(f"Warning: Event hiccup (frame {frame_count}): {e}")
            events = []

        for event in events:
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_q
                and pygame.key.get_mods() & pygame.KMOD_CTRL
            ):
                running = False

            try:
                manager.handle_event(event)
            except Exception as e:
                print(f"Event error (non-fatal): {e}")

        if selected_ruler is not None:
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
    test_ruler_selection()
