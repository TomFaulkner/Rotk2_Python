#!/usr/bin/env python3
"""Simple screenshot test for MainMenuScreen (headless)."""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "Src" / "UI" / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent / "Src" / "UI" / "screens"))
sys.path.insert(0, str(Path(__file__).parent.parent / "Src"))

import pygame


def main():
    """Generate a screenshot of the main menu."""
    pygame.init()

    # Create off-screen surface
    screen = pygame.Surface((1280, 800))

    # Import and create menu
    from main_menu_screen import MainMenuScreen
    from UI.core.transform import Transform

    menu = MainMenuScreen()

    # Create identity transform (1:1 mapping)
    transform = Transform((1280, 800), (1280, 800))

    # Render
    screen.fill((26, 26, 46))  # Background color
    menu.render(screen, transform)

    # Save screenshot
    pygame.image.save(screen, "docs/main_menu_preview.png")
    print("✓ Screenshot saved to: docs/main_menu_preview.png")

    pygame.quit()


if __name__ == "__main__":
    main()
