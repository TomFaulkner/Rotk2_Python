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
    REINFORCEMENT_PLACEMENT = "reinforcement_placement"
    BATTLE = "battle"
    ENDED = "ended"


class ScrollableListOverlay:
    """
    A scrollable list overlay for selecting items from a long list.

    Supports keyboard navigation (UP/DOWN, number keys) and displays
    items in a scrollable view with visible range indicators.
    """

    def __init__(
        self,
        screen,
        items: List[Dict[str, Any]],
        title: str = "Select Item",
        visible_count: int = 10,
        width: int = 550,
        item_height: int = 28,
        border_color: tuple = (200, 180, 100),
    ):
        """
        Initialize scrollable list overlay.

        Args:
            screen: Pygame surface to render to
            items: List of item dicts with 'id', 'name', 'stats' keys
            title: Title to display at top
            visible_count: Number of items visible at once
            width: Width of the overlay in pixels
            item_height: Height of each item row
            border_color: RGB tuple for border color
        """
        self.screen = screen
        self.items = items
        self.title = title
        self.visible_count = visible_count
        self.width = width
        self.item_height = item_height
        self.border_color = border_color

        self.scroll_offset = 0
        self.selected_index = 0  # Currently highlighted item
        self.confirmed_selection: Optional[int] = None  # Final selection

        # Calculate dimensions
        self.height = 80 + (visible_count * item_height)  # Header + items + padding
        self.x = (screen.get_width() - width) // 2
        self.y = (screen.get_height() - self.height) // 2

        # Key mapping for number selection (1-9, 0)
        self.number_keys = {}

    def handle_key(self, key) -> bool:
        """
        Handle keyboard input.

        Args:
            key: Pygame key constant

        Returns:
            True if selection confirmed, False to continue
        """
        import pygame

        if key == pygame.K_UP:
            self.selected_index = max(0, self.selected_index - 1)
            self._ensure_visible()
            return False
        elif key == pygame.K_DOWN:
            self.selected_index = min(len(self.items) - 1, self.selected_index + 1)
            self._ensure_visible()
            return False
        elif key == pygame.K_PAGEUP:
            self.selected_index = max(0, self.selected_index - self.visible_count)
            self._ensure_visible()
            return False
        elif key == pygame.K_PAGEDOWN:
            self.selected_index = min(len(self.items) - 1, self.selected_index + self.visible_count)
            self._ensure_visible()
            return False
        elif key == pygame.K_HOME:
            self.selected_index = 0
            self._ensure_visible()
            return False
        elif key == pygame.K_END:
            self.selected_index = len(self.items) - 1
            self._ensure_visible()
            return False
        elif key == pygame.K_RETURN:
            if self.selected_index < len(self.items):
                self.confirmed_selection = self.selected_index
                return True
            return False
        elif key == pygame.K_ESCAPE:
            self.confirmed_selection = None
            return True
        elif key in (
            pygame.K_1,
            pygame.K_2,
            pygame.K_3,
            pygame.K_4,
            pygame.K_5,
            pygame.K_6,
            pygame.K_7,
            pygame.K_8,
            pygame.K_9,
        ):
            # Number keys select visible items 1-9
            visible_idx = key - pygame.K_1  # 0-8
            actual_idx = self.scroll_offset + visible_idx
            if actual_idx < len(self.items):
                self.selected_index = actual_idx
                self.confirmed_selection = actual_idx
                return True
            return False
        elif key == pygame.K_0:
            # 0 selects the 10th visible item
            actual_idx = self.scroll_offset + 9
            if actual_idx < len(self.items):
                self.selected_index = actual_idx
                self.confirmed_selection = actual_idx
                return True
            return False

        return False

    def _ensure_visible(self):
        """Ensure selected index is within visible range."""
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + self.visible_count:
            self.scroll_offset = self.selected_index - self.visible_count + 1

        # Clamp scroll offset
        max_scroll = max(0, len(self.items) - self.visible_count)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

    def render(self):
        """Render the scrollable list overlay."""
        import pygame

        # Darken background
        overlay = pygame.Surface(
            (self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        # Main dialog box
        dialog = pygame.Surface((self.width, self.height))
        dialog.set_alpha(240)
        dialog.fill((30, 30, 35))
        self.screen.blit(dialog, (self.x, self.y))
        pygame.draw.rect(
            self.screen, self.border_color, (self.x, self.y, self.width, self.height), 3
        )

        font = pygame.font.SysFont(None, 28)
        item_font = pygame.font.SysFont(None, 22)
        small_font = pygame.font.SysFont(None, 18)

        # Title
        title_text = font.render(self.title, True, (255, 255, 200))
        title_x = self.x + (self.width - title_text.get_width()) // 2
        self.screen.blit(title_text, (title_x, self.y + 15))

        # Scroll indicators
        if self.scroll_offset > 0:
            up_text = small_font.render("▲ More above", True, (200, 200, 150))
            self.screen.blit(up_text, (self.x + 20, self.y + 45))

        visible_end = min(self.scroll_offset + self.visible_count, len(self.items))
        if visible_end < len(self.items):
            down_text = small_font.render("▼ More below", True, (200, 200, 150))
            self.screen.blit(down_text, (self.x + 20, self.y + self.height - 55))

        # Item list
        list_y = self.y + 50
        for i in range(self.scroll_offset, visible_end):
            item = self.items[i]
            row_y = list_y + (i - self.scroll_offset) * self.item_height

            # Selection highlight
            if i == self.selected_index:
                highlight = pygame.Surface((self.width - 20, self.item_height - 2))
                highlight.fill((60, 80, 120))
                self.screen.blit(highlight, (self.x + 10, row_y))

            # Number key hint (1-9, 0 for visible items)
            visible_idx = i - self.scroll_offset
            if visible_idx < 9:
                key_num = str(visible_idx + 1)
            elif visible_idx == 9:
                key_num = "0"
            else:
                key_num = " "

            key_text = item_font.render(f"[{key_num}]", True, (150, 255, 150))
            self.screen.blit(key_text, (self.x + 20, row_y + 3))

            # Name
            name = item.get("name", "Unknown")
            name_text = item_font.render(name, True, (255, 255, 255))
            self.screen.blit(name_text, (self.x + 65, row_y + 3))

            # Stats (right-aligned)
            stats = item.get("stats", "")
            if stats:
                stats_text = item_font.render(stats, True, (200, 200, 200))
                stats_x = self.x + self.width - stats_text.get_width() - 20
                self.screen.blit(stats_text, (stats_x, row_y + 3))

        # Instructions
        instr_y = self.y + self.height - 35
        instr_text = small_font.render(
            "[↑↓] Navigate  [1-9,0] Select  [Enter] Confirm  [ESC] Cancel",
            True,
            (180, 180, 180),
        )
        self.screen.blit(instr_text, (self.x + 20, instr_y))

    def get_selection(self) -> Optional[Dict[str, Any]]:
        """
        Get the confirmed selection.

        Returns:
            Selected item dict or None if cancelled
        """
        if self.confirmed_selection is not None and self.confirmed_selection < len(self.items):
            return self.items[self.confirmed_selection]
        return None


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
        """Get tile coordinate at screen position."""
        return self.renderer.get_tile_at_pixel(self.battle.grid, x, y)

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
        if self.phase == BattlePhaseUI.BATTLE and self.selected_unit and self.adjacent_enemies:
            for enemy in self.adjacent_enemies:
                # Skip hidden enemies - don't highlight their position
                if enemy.is_hidden():
                    continue
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

        # Draw placement zones (using rectangles for tiles)
        for coord in self.valid_placement_hexes:
            x, y, width, height = self.renderer.get_tile_rect(coord)
            s = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
            color = (0, 255, 0, 64) if self.placement_side == "attacker" else (255, 255, 0, 64)
            pygame.draw.rect(s, color, (x, y, width, height))
            self.screen.blit(s, (0, 0))
            pygame.draw.rect(
                self.screen,
                (0, 200, 0) if self.placement_side == "attacker" else (200, 200, 0),
                (x, y, width, height),
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
            commander_placed = any(u.is_commander for u in self.battle.get_defending_units_on_map())
            counter_text = f"Placed: {placed} (Cmdr: {'OK' if commander_placed else 'NEEDED'})"
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
            zone_text = (
                f"Place in yellow zones near castle ({len(self.valid_placement_hexes)} valid)"
            )

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
            f"Wind: {self.battle.wind_direction}" if self.battle.wind_direction else "Wind: Calm"
        )

        turn_text = "ATTACKER" if self.battle.turn == 0 else "DEFENDER"

        # Check if defender can reinforce
        can_reinforce = (
            self.battle.turn == 1  # Defender's turn
            and self.battle.defender_reserve.get_available()
            and len([u for u in self.battle.get_defending_units_on_map() if not u.is_defeated()])
            < self.battle.MAX_UNITS_ON_MAP
        )

        lines = [
            f"BATTLE PHASE - DAY {self.battle.day} - {turn_text} TURN",
            f"Rice: ATT {att_rice} | DEF {def_rice} | Weather: {weather_display} | {wind_text}",
            "Click unit: Select | Click hex: Move | Adjacent: Attack | A: Attack Dir",
            "ENTER: End | ESC: Exit | F: Fire | B: Bribe"
            + (" | R: Reinforce" if can_reinforce else ""),
        ]

        for i, line in enumerate(lines):
            if i == 1 and "Weather" in line:  # Weather line gets special coloring
                text = font.render(line, True, weather_color)
            else:
                text = font.render(line, True, (255, 255, 255))
            self.screen.blit(text, (20, y + 8 + i * 22))

        # Render adjacent enemy markers (but NOT for hidden units)
        if self.adjacent_enemies:
            for enemy in self.adjacent_enemies:
                # Skip hidden enemies - don't reveal their position
                if enemy.is_hidden():
                    continue
                if enemy.position:
                    x, y = self.renderer.coord_to_pixel(enemy.position)
                    cx = x + self.renderer.tile_width // 2
                    cy = y + self.renderer.tile_height // 2
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
        pygame.draw.rect(self.screen, (200, 200, 200), (x, y, menu_width, menu_height), 2)

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
            options.append(("3", f"Simultaneous ({ally_count} ally)", "Allies attack together"))

        if "fire" in self.attack_options:
            int_stat = self.selected_unit.get_intelligence() if self.selected_unit else 0
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
