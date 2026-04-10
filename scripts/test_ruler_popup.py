#!/usr/bin/env python3
"""Quick test to verify ruler popup renders correctly."""

import sys
from pathlib import Path

root = Path(__file__).parent.parent
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "Src"))
sys.path.insert(0, str(root / "Src" / "UI"))
sys.path.insert(0, str(root / "Src" / "UI" / "core"))
sys.path.insert(0, str(root / "Src" / "UI" / "screens"))
sys.path.insert(0, str(root / "Src" / "UI" / "map"))

import pygame


def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 800))
    pygame.display.set_caption("Ruler Popup Test")

    from ruler_selection_screen import RulerSelectionScreen
    from UI.core.manager import UIManager
    from UI.core.transform import Transform

    # Create manager
    manager = UIManager.get_instance()
    manager.actual_resolution = (1280, 800)
    manager.transform = Transform((1280, 800), (1280, 800))

    # Create screen
    ruler_screen = RulerSelectionScreen()
    manager.root_component = ruler_screen
    manager.current_screen = ruler_screen

    # Test 1: Show popup with portrait
    ruler_screen._selected_province = 1
    ruler_screen._selected_ruler = "Cao Cao"
    ruler_screen._show_popup()

    # Render one frame
    screen.fill((26, 26, 46))
    manager.render(screen)
    pygame.display.flip()

    # Save screenshot
    pygame.image.save(screen, "docs/ruler_popup_test.png")
    print("✓ Screenshot saved to docs/ruler_popup_test.png")

    # Test 2: Demonstrate keyboard cursor (navigate a few times)
    pygame.time.delay(500)  # Brief pause
    ruler_screen._on_cancel_popup()  # Close popup

    # Navigate with keyboard to show cursor (start with province 1)
    ruler_screen._navigate_to_province(1)
    # Then navigate to an adjacent province
    ruler_screen._navigate_by_direction("right")

    # Render with cursor visible
    screen.fill((26, 26, 46))
    manager.render(screen)
    pygame.display.flip()

    pygame.image.save(screen, "docs/ruler_cursor_test.png")
    print("✓ Cursor screenshot saved to docs/ruler_cursor_test.png")

    pygame.quit()


if __name__ == "__main__":
    main()
