#!/usr/bin/env python3
"""Generate a screenshot of the map for verification."""

import pygame
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, "/home/tom/dev/Rotk2_Python/Src/UI/map")
sys.path.insert(0, "/home/tom/dev/Rotk2_Python/Src/UI/core")

from map_renderer import MapRenderer
from transform import Transform


def main():
    # Initialize pygame FIRST (before any image loading)
    pygame.init()

    # Create off-screen surface (headless rendering)
    screen_size = (1280, 800)
    screen = pygame.Surface(screen_size)

    # Create transform
    transform = Transform((1280, 800), screen_size)

    # Create renderer (after pygame.init)
    renderer = MapRenderer()

    # Load background - check file exists first
    bg_path = Path("download/numbers-removed.jpg")
    print(f"Looking for background at: {bg_path.absolute()}")
    print(f"File exists: {bg_path.exists()}")

    background_loaded = renderer.load_terrain_background(str(bg_path))
    print(f"Background loaded: {background_loaded}")

    # Set some sample rulers with different colors
    renderer.set_province_ruler(1, 0)  # Gray
    renderer.set_province_ruler(2, 1)  # Yellow
    renderer.set_province_ruler(3, 2)  # Olive
    renderer.set_province_ruler(4, 6)  # Green
    renderer.set_province_ruler(5, 3)  # Purple
    renderer.set_province_ruler(6, 7)  # Cyan
    renderer.set_province_ruler(7, 9)  # Blue
    renderer.set_province_ruler(8, 12)  # Orange
    renderer.set_province_ruler(9, 4)  # Magenta
    renderer.set_province_ruler(10, 11)  # Dark Red

    # Fill all provinces for better visualization
    for i in range(1, 42):
        renderer.set_province_ruler(i, (i * 3) % 15)

    # Clear and render
    screen.fill((15, 15, 25))  # Dark background
    renderer.render(screen, transform)

    # Save screenshot
    pygame.image.save(screen, "download/map_test_screenshot.png")
    print("✓ Screenshot saved to: download/map_test_screenshot.png")

    pygame.quit()


if __name__ == "__main__":
    main()
