"""
ROTK2 Main Entry Point

Supports both Classic (DOS CGA-style) and Modern (Steam Deck optimized) UI modes.
UI mode is controlled via ROTK2_UI_MODE environment variable or .env file.

Usage:
    python Src/main.py                    # Uses default from config (modern)
    ROTK2_UI_MODE=classic python Src/main.py  # Force classic UI
    ROTK2_UI_MODE=modern python Src/main.py     # Force modern UI

    # Or run from project root:
    cd /home/tom/dev/Rotk2_Python && python Src/main.py
"""

import random
import sys
import os
from pathlib import Path

# Handle running from different directories
# If running from project root, ensure Src is in path
script_dir = Path(__file__).parent.resolve()
cwd = Path.cwd()

# If we're in the project root (not in Src), add Src to path
if script_dir.name == "Src" and str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

# Also ensure we can find Resources and other project files
if script_dir.name == "Src":
    # We're in Src, project root is parent
    project_root = script_dir.parent
else:
    # Assume we're already in project root or somewhere else
    project_root = cwd

# Change to project root for file access if needed
if cwd != project_root and (project_root / "Resources").exists():
    os.chdir(project_root)

import pygame.display

from Helper import Helper, Province, Officer, Ruler
from Command1 import Command1
from Command2 import Command2
from Command3 import Command3
from Command4 import Command4
from Command5 import Command5
from Command8 import Command8
from Command9_10_12 import Command9, Command10, Command12
from Command11 import Command11
from Command13 import Command13
from Command14 import Command14
from Command15 import Command15
from Command16 import Command16
from Command18 import Command18
from Command19 import Command19
from Data import Data
from Open import Open
from MainMenu import MainMenu

# Import configuration
from config import get_settings, UIMode
from game_start import (
    clear_player_rulers,
    initialize_new_game_state,
    load_scenario_into_buffer,
    mark_player_ruler,
)


class KeyboardDrivenFramework(object):
    """Main game framework supporting both Classic and Modern UI modes."""

    def generate_images(self):
        msg = Data.DSBUF.copy()
        buf = []
        buf2 = []

        i = 0x3000
        start = i
        while True:
            if i >= len(msg):
                break

            b = msg[i]
            if b == 0:
                text = "".join(buf2)
                if len(text) > 0:
                    buf.append(text)
                    print(text)
                    img = Helper.DrawText(text, scaled=True)
                    pygame.image.save(img, "images/{0}.png".format((hex(start)[2:]).upper()))
                buf2 = []
                i += 1
                start = i
            elif b == 0x0A:
                buf2.append("_")
                i += 1
            elif b < 0x20:
                buf2.append(".")
                i += 1
            elif b == 0x24:
                buf2.append(".")
                i += 1
            elif b < 0x80:
                buf2.append(chr(b))
                i += 1
            elif b >= 0x80:
                b2 = msg[i + 1]
                zh_cn = Data.CNINDEX.get(b * 256 + b2)
                if zh_cn is not None:
                    buf2.append("$")
                    buf2.append(str(zh_cn))
                    i += 2
                    buf2.append("$")
                else:
                    i += 1
            else:
                i += 1
                continue

    def __init__(self):
        Helper.Init(2, 4)

        self.mappings = {
            -1: None,
            1: Command1(),
            2: Command2(),
            3: Command3(),
            4: Command4(),
            5: Command5(),
            8: Command8(),
            9: Command9(),
            10: Command10(),
            11: Command11(),
            12: Command12(),
            13: Command13(),
            14: Command14(),
            15: Command15(),
            16: Command16(),
            18: Command18(),
            19: Command19(),
        }
        self.map_command_switch = True

    def switch_map_command(self):
        if self.map_command_switch is True:
            Helper.ShowMap(Province.GetActiveNo())
        else:
            bmp = self.GetAll20Commands()
            Helper.Screen.blit(bmp, (300 * Helper.Scale, 130 * Helper.Scale))
            pygame.display.flip()

        self.map_command_switch = not self.map_command_switch

    def get_palettes(self):
        with open("palettes", "rb") as f:
            palettes = f.read()
            for i in range(0, 4):
                p = palettes[48 * i : 48 * (i + 1)]

                bmp = pygame.Surface((60, 60))

                for j in range(0, 16):
                    p2 = p[3 * j : 3 * (j + 1)]

                    bmp.fill((p2[0], p2[1], p2[2]))
                    pygame.image.save(
                        bmp, "./palette{0}/change{2}/序号{1}.png".format(i + 1, j + 1, 1)
                    )

                    bmp.fill((p2[0], p2[2], p2[1]))
                    pygame.image.save(
                        bmp, "./palette{0}/change{2}/序号{1}.png".format(i + 1, j + 1, 2)
                    )

                    bmp.fill((p2[1], p2[0], p2[2]))
                    pygame.image.save(
                        bmp, "./palette{0}/change{2}/序号{1}.png".format(i + 1, j + 1, 3)
                    )

                    bmp.fill((p2[1], p2[2], p2[0]))
                    pygame.image.save(
                        bmp, "./palette{0}/change{2}/序号{1}.png".format(i + 1, j + 1, 4)
                    )

                    bmp.fill((p2[2], p2[0], p2[1]))
                    pygame.image.save(
                        bmp, "./palette{0}/change{2}/序号{1}.png".format(i + 1, j + 1, 5)
                    )

                    bmp.fill((p2[2], p2[1], p2[0]))
                    pygame.image.save(
                        bmp, "./palette{0}/change{2}/序号{1}.png".format(i + 1, j + 1, 6)
                    )

    def validate_helper_palettes(self):
        for i in range(0, 16):
            bmp = pygame.Surface((60, 60))
            bmp.fill(Helper.RulerPalettes[i])
            pygame.image.save(bmp, "palette_{0}.png".format(i))

    def Start(self):
        """Start the game using Classic UI mode."""
        # self.get_fonts()
        # self.get_palettes()
        # self.validate_helper_palettes()
        splash = Open()
        splash.Start()

        main = MainMenu()
        ret = main.Start()

        if ret == -1:
            return

        self.run_game_loop()

    def run_game_loop(self):
        """Run the classic in-game command loop using the current active state."""
        while True:
            cmd = (
                Helper.GetBuiltinText(0x5CEB)
                .replace("%d-%d", "0-19")
                .replace("%d", str(Province.GetActiveNo()))
            )
            gov_off = Province.FromSequence(Province.GetActiveNo()).GovernorOffset
            prompt = cmd.replace("%s", Officer.FromOffset(gov_off).GetName())

            self.switch_map_command()
            Helper.ClearInputArea()
            input = Helper.GetInput(
                prompt,
                300,
                295,
                "",
                required_number_min=0,
                required_number_max=19,
                allow_enter_exit=True,
            )

            if input > -1:
                cmd = self.mappings.get(input)
                if cmd is None:
                    Helper.ShowDelayedText("$685$$545$$97$$854$$825$!")
                    continue
                ret = cmd.Start(Province.GetActiveNo())
                self.map_command_switch = True
                if ret == -1:
                    return

    def GetAll20Commands(self):
        bmp = pygame.Surface((330, 160))
        bmp.fill((0, 0, 0))

        top = 5
        left = 5

        for i in range(0, 20):
            cmd_no = i

            row = cmd_no % 4
            col = int(cmd_no / 4)

            cmd_bmp = Helper.DrawText(
                Helper.GetBuiltinText(0x609D + cmd_no * 5), back_color=(0, 0, 0), palette_no=7
            )
            num_bmp = Helper.DrawText("{0:2}.".format(cmd_no), (0, 0, 0), 3, scaled=False)

            bmp.blit(num_bmp, (left + 65 * (col + 0) + (24 - num_bmp.get_width()), top + 38 * row))
            bmp.blit(cmd_bmp, (left + 65 * col + 24, top + 38 * row))

        return pygame.transform.scale(
            bmp, (bmp.get_width() * Helper.Scale, bmp.get_height() * Helper.Scale)
        )


def start_modern_ui():
    """
    Start the game using Modern UI mode (Steam Deck optimized).

    Flow:
    1. Splash screen (reuse existing Open)
    2. Main Menu Screen
    3. Scenario Selection Screen
    4. Ruler Selection Screen (interactive map)
    5. Start game with selected scenario and ruler
    """
    print("Starting ROTK2 with Modern UI...")

    # Ensure Helper is initialized (needed for splash screen and data)
    Helper.Init(2, 4)

    # Import UI components
    sys.path.insert(0, str(Path(__file__).parent / "UI"))
    from UI.screens.main_menu_screen import MainMenuScreen
    from UI.screens.modern_game_hub import ModernGameHub
    from UI.screens.new_game_options_screen import NewGameOptionsScreen
    from UI.screens.scenario_selection_screen import ScenarioSelectionScreen
    from UI.screens.ruler_selection_screen import RulerSelectionScreen
    from UI.core.manager import UIManager
    from UI.core.transform import Transform

    # Initialize pygame display
    pygame.init()
    screen = pygame.display.set_mode((1280, 800))
    pygame.display.set_caption("ROTK2 - Romance of the Three Kingdoms II (Modern UI)")

    # 1. Splash screen (reuse existing) - skip if palettes not available
    print("Showing splash screen...")
    try:
        splash = Open()
        splash.Start()
    except Exception as e:
        print(f"Warning: Splash screen error: {e}")
        print("Continuing without splash screen...")

    # Create UIManager
    manager = UIManager.get_instance()
    manager.actual_resolution = (1280, 800)
    manager.transform = Transform((1280, 800), (1280, 800))

    # 2. Main Menu
    print("Showing main menu...")
    menu = MainMenuScreen()
    manager.root_component = menu
    manager.current_screen = menu

    menu_result = None

    def on_menu_action(action: str):
        nonlocal menu_result
        menu_result = action
        print(f"Main menu action: {action}")

    menu.set_callback(on_menu_action)

    # Run main menu loop
    clock = pygame.time.Clock()
    running = True
    while running and menu_result is None:
        dt = clock.tick(60) / 1000.0

        # Process events
        try:
            events = pygame.event.get()
        except (SystemError, KeyError) as e:
            print(f"Warning: Event hiccup: {e}")
            events = []

        for event in events:
            if event.type == pygame.QUIT:
                running = False
                menu_result = "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    running = False
                    menu_result = "quit"

            try:
                manager.handle_event(event)
            except Exception as e:
                print(f"Event error (non-fatal): {e}")

        # Update
        try:
            manager.update(dt)
        except Exception as e:
            print(f"Update error (non-fatal): {e}")

        # Render
        try:
            screen.fill((26, 26, 46))
            manager.render(screen)
            pygame.display.flip()
        except Exception as e:
            print(f"Render error: {e}")
            running = False

    # Handle menu result
    if menu_result == "quit":
        print("Quitting...")
        pygame.quit()
        return

    if menu_result == "new_game":
        # 3. Scenario Selection
        print("Showing scenario selection...")
        scenario_screen = ScenarioSelectionScreen()
        manager.root_component = scenario_screen
        manager.current_screen = scenario_screen

        scenario_result = None

        def on_scenario_select(scenario_id: int):
            nonlocal scenario_result
            scenario_result = scenario_id

        scenario_screen.set_callback(on_scenario_select)

        # Run scenario selection loop
        running = True
        while running and scenario_result is None:
            dt = clock.tick(60) / 1000.0

            try:
                events = pygame.event.get()
            except (SystemError, KeyError) as e:
                print(f"Warning: Event hiccup: {e}")
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
                    print(f"Event error (non-fatal): {e}")

            if scenario_result == 0:  # Back selected
                # Go back to main menu
                print("Going back to main menu...")
                start_modern_ui()  # Recursive, but simple
                return

            try:
                manager.update(dt)
                screen.fill((26, 26, 46))
                manager.render(screen)
                pygame.display.flip()
            except Exception as e:
                print(f"Loop error: {e}")
                running = False

        if scenario_result and scenario_result > 0:
            print(f"Selected scenario: {scenario_result}")
            load_scenario_into_buffer(scenario_result - 1)

            # 4. Ruler Selection (with full-screen map and popup)
            print("Showing ruler selection...")
            ruler_screen = RulerSelectionScreen()
            manager.root_component = ruler_screen
            manager.current_screen = ruler_screen

            ruler_result = None

            def on_ruler_select(ruler):
                nonlocal ruler_result
                ruler_result = ruler

            ruler_screen.set_callback(on_ruler_select)

            # Run ruler selection loop
            running = True
            while running and ruler_result is None:
                dt = clock.tick(60) / 1000.0

                try:
                    events = pygame.event.get()
                except (SystemError, KeyError) as e:
                    print(f"Warning: Event hiccup: {e}")
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
                        print(f"Event error (non-fatal): {e}")

                try:
                    manager.update(dt)
                    screen.fill((26, 26, 46))
                    manager.render(screen)
                    pygame.display.flip()
                except Exception as e:
                    print(f"Loop error: {e}")
                    running = False

            if ruler_result:
                print(
                    f"Selected ruler: {ruler_result.ruler_name} "
                    f"(province {ruler_result.province_no}, ruler {ruler_result.ruler_no})"
                )

                print("Showing new game options...")
                options_screen = NewGameOptionsScreen()
                manager.root_component = options_screen
                manager.current_screen = options_screen

                options_result = None

                def on_options_select(options):
                    nonlocal options_result
                    options_result = options

                options_screen.set_callback(on_options_select)

                running = True
                while running and options_result is None:
                    dt = clock.tick(60) / 1000.0

                    try:
                        events = pygame.event.get()
                    except (SystemError, KeyError) as e:
                        print(f"Warning: Event hiccup: {e}")
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
                            print(f"Event error (non-fatal): {e}")

                    try:
                        manager.update(dt)
                        screen.fill((26, 26, 46))
                        manager.render(screen)
                        pygame.display.flip()
                    except Exception as e:
                        print(f"Loop error: {e}")
                        running = False

                if options_result is None:
                    pygame.quit()
                    return

                clear_player_rulers()
                mark_player_ruler(ruler_result.ruler_no, 1)
                initialize_new_game_state(
                    level=options_result.level,
                    see_war=options_result.see_war,
                    history=options_result.history,
                )

                print("Starting modern province hub...")
                game_hub = ModernGameHub()

                running = True
                while running:
                    dt = clock.tick(60) / 1000.0

                    try:
                        events = pygame.event.get()
                    except (SystemError, KeyError) as e:
                        print(f"Warning: Event hiccup: {e}")
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
                            print(f"Event error (non-fatal): {e}")

                    try:
                        manager.update(dt)
                        screen.fill((15, 15, 25))
                        manager.render(screen)
                        pygame.display.flip()
                    except Exception as e:
                        print(f"Modern hub loop error: {e}")
                        running = False

                pygame.quit()
                return

    elif menu_result == "continue":
        print("Continue not yet implemented in Modern UI")

    elif menu_result == "load_game":
        print("Load Game not yet implemented in Modern UI")

    elif menu_result == "settings":
        print("Settings not yet implemented in Modern UI")

    pygame.quit()


def start_classic_ui():
    """Start the game using Classic UI mode (DOS CGA-style)."""
    kdf = KeyboardDrivenFramework()
    kdf.Start()


def main():
    """Main entry point - selects UI mode based on config."""
    # Get configuration
    settings = get_settings()
    ui_mode = settings.ui_mode

    print(f"ROTK2 Python Remake")
    print(f"UI Mode: {ui_mode.value}")
    print(f"=" * 50)

    # Route to appropriate UI
    if ui_mode == UIMode.MODERN:
        start_modern_ui()
    else:
        start_classic_ui()


if __name__ == "__main__":
    main()
