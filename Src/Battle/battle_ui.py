"""
Battle UI - Handles rendering and input for the battle system.

This module provides the UI layer for the hex-based battle system,
separating presentation from game logic.
"""

from typing import List, Optional, Dict, Any
from enum import Enum


class BattlePhaseUI(Enum):
    """UI phases for battle display."""

    PLACEMENT = "placement"
    PERSONAL_COMBAT_OFFER = "personal_combat_offer"
    BATTLE = "battle"
    ENDED = "ended"


class BattleUI:
    """
    Handles battle rendering and UI state.

    This class manages:
    - Rendering the battle field, units, and UI elements
    - UI state (selected units, reachable hexes, etc.)
    - Visual feedback (placement zones, combat markers, etc.)

    Game logic is handled by BattleEngine; this is purely presentation.
    """

    def __init__(self, screen, battle_engine, renderer):
        """
        Initialize battle UI.

        Args:
            screen: Pygame surface to render to
            battle_engine: BattleEngine instance with game state
            renderer: BattleRenderer for hex grid rendering
        """
        self.screen = screen
        self.battle = battle_engine
        self.renderer = renderer

        # UI State
        self.phase = BattlePhaseUI.PLACEMENT
        self.placement_side = "attacker"  # "attacker" or "defender"
        self.selected_unit = None
        self.reachable_hexes: list = []
        self.valid_placement_hexes: list = []
        self.adjacent_enemies: list = []
        self.combat_log: list = []

        # Attack selection state
        self.attack_target = None
        self.attack_options: list = []
        self.helping_allies: list = []

        # Mode flags
        self.fire_mode = False

    def set_phase(self, phase: BattlePhaseUI):
        """Set the current UI phase."""
        self.phase = phase
        # Clear placement zones when not in placement phase
        if phase != BattlePhaseUI.PLACEMENT:
            self.valid_placement_hexes = []

    def update_valid_placement_zones(self):
        """Update valid placement hexes for current side."""
        is_attacker = self.placement_side == "attacker"
        self.valid_placement_hexes = self.battle.get_valid_placement_hexes(is_attacker)

    def get_hex_at_pixel(self, x: int, y: int):
        """Get hex coordinate at screen position."""
        return self.renderer.get_hex_at_pixel(self.battle.grid, x, y)

    def add_combat_message(self, message: str):
        """Add a message to the combat log."""
        self.combat_log.append(message)

    def clear_selection(self):
        """Clear current unit selection."""
        self.selected_unit = None
        self.reachable_hexes = []
        self.adjacent_enemies = []
        self.attack_target = None
        self.attack_options = []
        self.helping_allies = []

    def render(self):
        """Render the complete battle UI."""
        import pygame

        # Get all units
        all_units = self.battle.get_all_units_on_map()

        # Build highlight list
        highlight_hexes = self.reachable_hexes.copy()
        if (
            self.phase == BattlePhaseUI.BATTLE
            and self.selected_unit
            and self.adjacent_enemies
        ):
            for enemy in self.adjacent_enemies:
                if enemy.position:
                    highlight_hexes.append(enemy.position)

        # Render base battle view
        self.renderer.render(
            self.battle.grid,
            all_units,
            self.selected_unit,
            highlight_hexes,
            self.battle,
        )

        # Render phase-specific overlays
        if self.phase == BattlePhaseUI.PLACEMENT:
            self._render_placement_ui()
        elif self.phase == BattlePhaseUI.PERSONAL_COMBAT_OFFER:
            self._render_personal_combat_ui()
        elif self.phase == BattlePhaseUI.BATTLE:
            self._render_battle_ui()
        elif self.phase == BattlePhaseUI.ENDED:
            self._render_end_screen()

        # Render mode indicators
        if self.fire_mode:
            self._render_fire_mode_indicator()

        # Render combat log
        if self.combat_log:
            self._render_combat_log()

        # Render attack selection if active
        if self.attack_target:
            self._render_attack_selection()

        # Note: pygame.display.flip() should be called by the main game loop
        # after all rendering is complete (including any overlays)

    def _render_placement_ui(self):
        """Render placement phase UI elements."""
        import pygame

        # Safety check: only render if in placement phase and has zones
        if self.phase != BattlePhaseUI.PLACEMENT or not self.valid_placement_hexes:
            return

        # Draw placement zones
        for coord in self.valid_placement_hexes:
            points = self.renderer.get_hex_polygon(coord)
            s = pygame.Surface(
                (self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA
            )
            color = (
                (0, 255, 0, 64)
                if self.placement_side == "attacker"
                else (255, 255, 0, 64)
            )
            pygame.draw.polygon(s, color, points)
            self.screen.blit(s, (0, 0))
            pygame.draw.polygon(
                self.screen,
                (0, 200, 0) if self.placement_side == "attacker" else (200, 200, 0),
                points,
                2,
            )

        # Draw unit counter
        self._render_placement_counter()

        # Draw instructions
        self._render_placement_instructions()

    def _render_placement_counter(self):
        """Render unit placement counter."""
        import pygame

        font = pygame.font.SysFont(None, 28)
        small_font = pygame.font.SysFont(None, 20)

        if self.placement_side == "attacker":
            placed = len(self.battle.get_attacking_units_on_map())
            total = len(self.battle.attacking_units)
            counter_text = f"Placed: {placed}/{total}"
            req_met = placed >= total
        else:
            placed = len(self.battle.get_defending_units_on_map())
            commander_placed = any(
                u.is_commander for u in self.battle.get_defending_units_on_map()
            )
            counter_text = (
                f"Placed: {placed} (Cmdr: {'OK' if commander_placed else 'NEEDED'})"
            )
            req_met = commander_placed

        # Background
        counter_bg = pygame.Surface((200, 60))
        counter_bg.set_alpha(200)
        counter_bg.fill((32, 32, 32))
        self.screen.blit(counter_bg, (self.screen.get_width() - 210, 10))

        # Text
        color = (100, 255, 100) if req_met else (255, 200, 100)
        text = font.render(counter_text, True, color)
        self.screen.blit(text, (self.screen.get_width() - 200, 15))

        # Hint
        if self.placement_side == "attacker":
            hint = "All units required" if not req_met else "Ready!"
        else:
            hint = "Commander required!" if not req_met else "Ready!"

        text = small_font.render(hint, True, (200, 200, 200))
        self.screen.blit(text, (self.screen.get_width() - 200, 45))

    def _render_placement_instructions(self):
        """Render placement instruction panel."""
        import pygame

        y = self.screen.get_height() - 140
        s = pygame.Surface((400, 130))
        s.set_alpha(200)
        s.fill((0, 0, 0))
        self.screen.blit(s, (10, y))

        font = pygame.font.SysFont(None, 24)
        small_font = pygame.font.SysFont(None, 20)

        side = "Attacker" if self.placement_side == "attacker" else "Defender"
        text = font.render(f"PLACEMENT PHASE - {side}'s turn", True, (255, 255, 255))
        self.screen.blit(text, (20, y + 5))

        if self.placement_side == "attacker":
            zone_text = "Place on green edge zones (attack direction)"
        else:
            zone_text = f"Place in yellow zones near castle ({len(self.valid_placement_hexes)} valid)"

        text = small_font.render(zone_text, True, (255, 255, 0))
        self.screen.blit(text, (20, y + 28))

        if self.placement_side == "attacker":
            req_text = "REQUIRED: Place ALL units"
            req_color = (255, 100, 100)
        else:
            req_text = "REQUIRED: Place commander (leader)"
            req_color = (255, 200, 100)

        text = small_font.render(req_text, True, req_color)
        self.screen.blit(text, (20, y + 48))

        lines = [
            "Click hexes to place units",
            "SPACE: Auto-place remaining",
            "ENTER: Start battle",
            "ESC: Exit",
        ]

        for i, line in enumerate(lines):
            text = small_font.render(line, True, (200, 200, 200))
            self.screen.blit(text, (20, y + 68 + i * 18))

    def _render_battle_ui(self):
        """Render battle phase UI elements with integrated weather info."""
        import pygame

        y = self.screen.get_height() - 140
        panel_width = 400
        panel_height = 130

        # Main battle status panel
        s = pygame.Surface((panel_width, panel_height))
        s.set_alpha(200)
        s.fill((0, 0, 0))
        self.screen.blit(s, (10, y))

        font = pygame.font.SysFont(None, 20)
        small_font = pygame.font.SysFont(None, 18)

        att_rice = self.battle.attacker_supplies.get("rice", 0)
        def_rice = self.battle.defender_supplies.get("rice", 0)

        # Weather info integrated into battle status
        weather_colors = {
            "sunny": (255, 255, 100),
            "light_clouds": (220, 220, 200),
            "dark_clouds": (150, 150, 150),
            "storm": (100, 100, 200),
        }
        weather_display = self.battle.weather.replace("_", " ").title()
        weather_color = weather_colors.get(self.battle.weather, (200, 200, 200))

        wind_text = (
            f"Wind: {self.battle.wind_direction}"
            if self.battle.wind_direction
            else "Wind: Calm"
        )

        turn_text = "ATTACKER" if self.battle.turn == 0 else "DEFENDER"

        lines = [
            f"BATTLE PHASE - DAY {self.battle.day} - {turn_text} TURN",
            f"Rice: ATT {att_rice} | DEF {def_rice} | Weather: {weather_display} | {wind_text}",
            "Click unit: Select | Click hex: Move | Adjacent: Attack",
            "ENTER: End | ESC: Exit | F: Fire | B: Bribe",
        ]

        for i, line in enumerate(lines):
            if i == 1 and "Weather" in line:  # Weather line gets special coloring
                text = font.render(line, True, weather_color)
            else:
                text = font.render(line, True, (255, 255, 255))
            self.screen.blit(text, (20, y + 8 + i * 22))

        # Render adjacent enemy markers
        if self.adjacent_enemies:
            for enemy in self.adjacent_enemies:
                if enemy.position:
                    cx, cy = self.renderer.hex_to_pixel(enemy.position)
                    pygame.draw.line(
                        self.screen, (255, 0, 0), (cx - 8, cy - 8), (cx + 8, cy + 8), 3
                    )
                    pygame.draw.line(
                        self.screen, (255, 0, 0), (cx + 8, cy - 8), (cx - 8, cy + 8), 3
                    )
                    pygame.draw.circle(self.screen, (255, 0, 0), (cx, cy), 15, 2)

    def _render_personal_combat_ui(self):
        """Render personal combat offer UI - to be customized by caller."""
        # This is a base implementation; specific rendering should be done by
        # the game-specific UI code that knows about personal_combat_step, etc.
        pass

    def _render_fire_mode_indicator(self):
        """Render fire mode indicator."""
        import pygame

        font = pygame.font.SysFont(None, 28)
        text = font.render("FIRE MODE - Click adjacent hex", True, (255, 100, 0))
        x = (self.screen.get_width() - text.get_width()) // 2
        self.screen.blit(text, (x, 50))

    def _render_combat_log(self):
        """Render recent combat messages."""
        import pygame

        y = 150
        font = pygame.font.SysFont(None, 18)

        s = pygame.Surface((350, 120))
        s.set_alpha(180)
        s.fill((0, 0, 0))
        self.screen.blit(s, (10, y - 10))

        title = font.render("Combat Log:", True, (255, 255, 100))
        self.screen.blit(title, (15, y - 5))

        for i, msg in enumerate(self.combat_log[-5:]):
            text = font.render(msg, True, (200, 200, 200))
            self.screen.blit(text, (15, y + 15 + i * 18))

    def _render_attack_selection(self):
        """Render attack selection menu."""
        import pygame

        # Darken screen
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(100)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        if not self.attack_target:
            return

        # Menu box
        menu_width = 350
        base_height = 140
        if "simultaneous" in self.attack_options:
            base_height += 35
        if "fire" in self.attack_options:
            base_height += 35
        menu_height = base_height
        x = (self.screen.get_width() - menu_width) // 2
        y = (self.screen.get_height() - menu_height) // 2

        s = pygame.Surface((menu_width, menu_height))
        s.set_alpha(240)
        s.fill((30, 30, 30))
        self.screen.blit(s, (x, y))
        pygame.draw.rect(
            self.screen, (200, 200, 200), (x, y, menu_width, menu_height), 2
        )

        font = pygame.font.SysFont(None, 24)
        small_font = pygame.font.SysFont(None, 20)

        # Title
        target_name = self.attack_target.get_officer_name()
        title = font.render(f"Attack {target_name}", True, (255, 255, 100))
        self.screen.blit(title, (x + 20, y + 15))

        # Options
        options = [
            ("1", "Normal Attack", "Standard damage to both sides"),
            ("2", "Charge Attack", "Heavy damage, risky, may pass through"),
        ]

        if "simultaneous" in self.attack_options:
            ally_count = len(self.helping_allies)
            options.append(
                ("3", f"Simultaneous ({ally_count} ally)", "Allies attack together")
            )

        if "fire" in self.attack_options:
            int_stat = (
                self.selected_unit.get_intelligence() if self.selected_unit else 0
            )
            options.append(("4", "Fire Attack", f"Set hex on fire (Int: {int_stat})"))

        for i, (key, name, desc) in enumerate(options):
            opt_y = y + 50 + i * 35
            key_text = small_font.render(f"[{key}]", True, (100, 255, 100))
            self.screen.blit(key_text, (x + 20, opt_y))
            name_text = font.render(name, True, (255, 255, 255))
            self.screen.blit(name_text, (x + 60, opt_y))
            desc_text = small_font.render(desc, True, (180, 180, 180))
            self.screen.blit(desc_text, (x + 60, opt_y + 18))

        # Cancel
        cancel_text = small_font.render("[ESC] Cancel", True, (200, 200, 200))
        self.screen.blit(cancel_text, (x + 20, y + menu_height - 25))

    def _render_end_screen(self):
        """Render battle ended screen."""
        import pygame

        s = pygame.Surface((400, 200))
        s.set_alpha(230)
        s.fill((0, 0, 0))
        x = (self.screen.get_width() - 400) // 2
        y = (self.screen.get_height() - 200) // 2
        self.screen.blit(s, (x, y))

        font = pygame.font.SysFont(None, 36)
        text = font.render("BATTLE ENDED", True, (255, 255, 0))
        self.screen.blit(text, (x + 100, y + 50))

        font = pygame.font.SysFont(None, 24)
        text = font.render("Press ESC to exit", True, (200, 200, 200))
        self.screen.blit(text, (x + 130, y + 120))
