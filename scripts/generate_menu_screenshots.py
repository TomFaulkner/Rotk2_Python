#!/usr/bin/env python3
"""Generate screenshots of all menu screens."""

import sys
from pathlib import Path

# Add all necessary paths
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "Src"))
sys.path.insert(0, str(root / "Src" / "UI"))
sys.path.insert(0, str(root / "Src" / "UI" / "core"))
sys.path.insert(0, str(root / "Src" / "UI" / "screens"))
sys.path.insert(0, str(root / "Src" / "UI" / "map"))

import pygame


def main():
    """Generate screenshots of menu screens."""
    pygame.init()

    screen = pygame.Surface((1280, 800))
    from UI.core.transform import Transform

    transform = Transform((1280, 800), (1280, 800))

    # 1. Main Menu Screenshot
    print("Generating Main Menu screenshot...")
    from main_menu_screen import MainMenuScreen

    menu = MainMenuScreen()
    screen.fill((26, 26, 46))
    menu.render(screen, transform)
    pygame.image.save(screen, "docs/screenshot_main_menu.png")
    print("✓ docs/screenshot_main_menu.png")

    # 2. Scenario Selection Screenshot
    print("\nGenerating Scenario Selection screenshot...")
    from scenario_selection_screen import ScenarioSelectionScreen

    scenario_screen = ScenarioSelectionScreen()
    screen.fill((26, 26, 46))
    scenario_screen.render(screen, transform)
    pygame.image.save(screen, "docs/screenshot_scenario.png")
    print("✓ docs/screenshot_scenario.png")

    # 3. Ruler Selection Screenshot (may need special handling)
    print("\nGenerating Ruler Selection screenshot...")
    try:
        from ruler_selection_screen import RulerSelectionScreen

        ruler_screen = RulerSelectionScreen()
        screen.fill((26, 26, 46))
        # Ruler screen has complex map rendering, may need different approach
        ruler_screen.render(screen, transform)
        pygame.image.save(screen, "docs/screenshot_ruler.png")
        print("✓ docs/screenshot_ruler.png")
    except Exception as e:
        print(f"⚠ Ruler screenshot skipped: {e}")

    pygame.quit()
    print("\nAll screenshots generated!")


if __name__ == "__main__":
    main()
