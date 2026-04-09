#!/usr/bin/env python3
"""
Test script for SNES-Style Province Screen

Loads a province and displays the new SNES-style UI screen.
Usage: python scripts/test_snes_province_screen.py [province_number]

Example:
    python scripts/test_snes_province_screen.py 1    # Show province 1
    python scripts/test_snes_province_screen.py      # Show province 1 by default
"""

import sys
import os

# Change to Src directory for proper imports
src_dir = os.path.join(os.path.dirname(__file__), "..", "Src")
os.chdir(src_dir)
sys.path.insert(0, src_dir)

import pygame

# Initialize pygame first
pygame.init()
pygame.font.init()

# Set language to English for testing
import translations

translations.set_language("en")

# Now import UI components
from UI.core.manager import UIManager
from UI.core.anchor import UIMode
from UI.screens.snes_province_screen import SnesProvinceScreen
from Province import Province


def main():
    """Main test function."""
    # Get province number from command line
    province_num = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    print(f"Loading Province {province_num}...")

    # Load province
    try:
        province = Province.FromSequence(province_num)
        if not province:
            print(f"Error: Province {province_num} not found")
            return 1

        print(f"Province: {province.Name}")
        print(f"  Gold: {province.Gold}")
        print(f"  Rice: {province.Food}")
        print(f"  Population: {province.Population}")
        print(f"  Soldiers: {province.Soldiers}")

        # Set up an advisor for testing
        # Get the ruler and assign an advisor from the province
        from Ruler import Ruler
        from Officer import Officer

        if province.RulerNo != 0xFF:
            ruler = Ruler.FromNo(province.RulerNo)
            if ruler:
                # Get officers in the province
                officers = province.GetOfficerList()
                if len(officers) > 1:
                    # Set the second officer as advisor (skip governor if possible)
                    advisor_candidate = officers[1] if len(officers) > 1 else officers[0]
                    advisor_candidate.SetAdvisor()
                    print(f"  Set advisor: {advisor_candidate.GetName()}")
                else:
                    print("  Not enough officers to assign advisor")

    except Exception as e:
        print(f"Error loading province: {e}")
        import traceback

        traceback.print_exc()
        return 1

    # Create window (1280x800 for modern mode)
    screen_width = 1280
    screen_height = 800
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption(f"ROTK2 - SNES Style Province {province_num}")

    # Initialize UI Manager
    ui_manager = UIManager(virtual_resolution=(1280, 800), mode=UIMode.MODERN)
    ui_manager.set_resolution(screen_width, screen_height)

    # Create and set SNES-style province screen
    province_screen = SnesProvinceScreen(province)
    ui_manager.set_screen(province_screen)

    print("\nControls:")
    print("  Click menu buttons to select commands")
    print("  Close window to exit")
    print("\nRunning display loop...")

    # Main loop
    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.tick(60) / 1000.0  # Delta time in seconds

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Pass events to UI manager
            ui_manager.handle_event(event)

        # Update UI
        ui_manager.update(dt)

        # Render
        screen.fill((0, 0, 0))  # Clear screen
        ui_manager.render(screen)
        pygame.display.flip()

    print("\nExiting...")
    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
