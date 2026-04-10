#!/usr/bin/env python3
"""
Live viewer for province mapping.
Shows the extracted provinces and updates when you edit the mapping file.
"""

import pygame
import json
import sys
from pathlib import Path
from datetime import datetime

# Screen dimensions
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 1000
BG_COLOR = (30, 30, 30)
BORDER_COLOR = (50, 50, 50)
TEXT_COLOR = (255, 255, 255)
MAPPED_COLOR = (100, 200, 100)
UNMAPPED_COLOR = (200, 100, 100)
SELECTED_COLOR = (100, 100, 200)


class ProvinceMappingViewer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Province Mapping Viewer - Edit data/province_mapping.json")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 14)
        self.font_large = pygame.font.SysFont("monospace", 16, bold=True)

        self.provinces = []
        self.mapping = {}
        self.temp_to_province = {}
        self.show_province_ids = False  # Toggle between temp_id and province_id
        self.last_check = 0
        self.mapping_mtime = 0

        self.load_provinces()
        self.load_mapping()

    def load_provinces(self):
        """Load extracted province data."""
        try:
            with open("data/provinces_raw_extraction.json") as f:
                self.provinces = json.load(f)
                print(f"Loaded {len(self.provinces)} provinces")
        except Exception as e:
            print(f"Error loading provinces: {e}")
            print("Run: python scripts/extract_clean_provinces.py first")
            sys.exit(1)

    def load_mapping(self):
        """Load the mapping file."""
        try:
            mapping_path = Path("data/province_mapping.json")
            mtime = mapping_path.stat().st_mtime

            if mtime != self.mapping_mtime:
                self.mapping_mtime = mtime

                with open(mapping_path) as f:
                    self.mapping = json.load(f)

                # Build temp_id -> province_id lookup
                self.temp_to_province = {}
                for m in self.mapping.get("mappings", []):
                    temp_id = m.get("temp_id")
                    province_id = m.get("province_id")
                    if temp_id is not None and province_id is not None:
                        self.temp_to_province[temp_id] = province_id

                mapped = sum(
                    1 for m in self.mapping.get("mappings", []) if m.get("province_id") is not None
                )
                total = len(self.mapping.get("mappings", []))
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] Mapping reloaded: {mapped}/{total} mapped"
                )

        except Exception as e:
            print(f"Error loading mapping: {e}")

    def draw(self):
        self.screen.fill(BG_COLOR)

        # Draw title
        title = self.font_large.render(
            "Province Mapping Viewer - SPACE: toggle IDs | R: reload | ESC: exit", True, TEXT_COLOR
        )
        self.screen.blit(title, (10, 10))

        # Draw legend
        legend_y = 40
        mapped = sum(
            1 for m in self.mapping.get("mappings", []) if m.get("province_id") is not None
        )
        total = len(self.mapping.get("mappings", []))

        status_color = MAPPED_COLOR if mapped == 41 else (255, 200, 100)
        status = self.font.render(f"Mapped: {mapped}/{total} provinces", True, status_color)
        self.screen.blit(status, (10, legend_y))

        mode_text = "Province IDs" if self.show_province_ids else "Temp IDs"
        mode = self.font.render(f"Showing: {mode_text} (press SPACE)", True, TEXT_COLOR)
        self.screen.blit(mode, (300, legend_y))

        # Calculate scale to fit provinces on screen
        if not self.provinces:
            return

        max_x = max(max(p[0] for p in prov["points"]) for prov in self.provinces)
        max_y = max(max(p[1] for p in prov["points"]) for prov in self.provinces)

        padding = 50
        top_margin = 80
        scale_x = (SCREEN_WIDTH - padding * 2) / max_x
        scale_y = (SCREEN_HEIGHT - top_margin - padding) / max_y
        scale = min(scale_x, scale_y)

        offset_x = padding
        offset_y = top_margin

        # Draw provinces
        for prov in self.provinces:
            temp_id = prov["temp_id"]
            province_id = self.temp_to_province.get(temp_id)

            # Scale points
            points = [
                (int(p[0] * scale + offset_x), int(p[1] * scale + offset_y)) for p in prov["points"]
            ]

            # Choose color based on mapping status
            if province_id:
                color = MAPPED_COLOR
            else:
                color = UNMAPPED_COLOR

            # Draw filled polygon
            if len(points) >= 3:
                pygame.draw.polygon(self.screen, color, points)
                pygame.draw.polygon(self.screen, BORDER_COLOR, points, 2)

            # Draw ID
            cx = int(prov["centroid"][0] * scale + offset_x)
            cy = int(prov["centroid"][1] * scale + offset_y)

            if self.show_province_ids and province_id:
                text = str(province_id)
                text_color = (0, 100, 0)
            else:
                text = str(temp_id)
                text_color = (100, 0, 0)

            # Draw text with background
            text_surf = self.font.render(text, True, text_color)
            text_rect = text_surf.get_rect(center=(cx, cy))
            pygame.draw.rect(self.screen, (255, 255, 255), text_rect.inflate(6, 4))
            self.screen.blit(text_surf, text_rect)

        # Draw unmapped list
        list_x = SCREEN_WIDTH - 280
        list_y = 80

        # Background for list
        pygame.draw.rect(
            self.screen, (40, 40, 40), (list_x - 10, list_y - 5, 270, SCREEN_HEIGHT - list_y - 50)
        )

        unmapped_title = self.font_large.render("Unmapped Regions:", True, UNMAPPED_COLOR)
        self.screen.blit(unmapped_title, (list_x, list_y))

        list_y += 25
        for prov in self.provinces:
            temp_id = prov["temp_id"]
            if temp_id not in self.temp_to_province:
                cx, cy = prov["centroid"]
                text = self.font.render(
                    f"temp_{temp_id}: ({cx:.0f}, {cy:.0f})", True, UNMAPPED_COLOR
                )
                self.screen.blit(text, (list_x, list_y))
                list_y += 18
                if list_y > SCREEN_HEIGHT - 80:
                    more = self.font.render("...", True, UNMAPPED_COLOR)
                    self.screen.blit(more, (list_x, list_y))
                    break

        # Draw mapped summary
        if mapped > 0:
            list_y += 30
            mapped_title = self.font_large.render(f"Mapped ({mapped}):", True, MAPPED_COLOR)
            self.screen.blit(mapped_title, (list_x, list_y))
            list_y += 25

            for prov in self.provinces:
                temp_id = prov["temp_id"]
                province_id = self.temp_to_province.get(temp_id)
                if province_id:
                    text = self.font.render(
                        f"temp_{temp_id} -> prov_{province_id}", True, MAPPED_COLOR
                    )
                    self.screen.blit(text, (list_x, list_y))
                    list_y += 18
                    if list_y > SCREEN_HEIGHT - 50:
                        break

        pygame.display.flip()

    def run(self):
        running = True
        check_interval = 30  # Check for file changes every 30 frames (~1 sec)
        frame_count = 0

        print("\n" + "=" * 60)
        print("Province Mapping Viewer")
        print("=" * 60)
        print("Controls:")
        print("  SPACE - Toggle between temp_id and province_id display")
        print("  R     - Reload mapping file manually")
        print("  ESC   - Exit")
        print("=" * 60)
        print("\nEdit data/province_mapping.json in your editor,")
        print("save it, and this viewer will update automatically.")
        print("=" * 60 + "\n")

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.show_province_ids = not self.show_province_ids
                    elif event.key == pygame.K_r:
                        self.load_mapping()

            # Check for file changes periodically
            frame_count += 1
            if frame_count >= check_interval:
                self.load_mapping()
                frame_count = 0

            self.draw()
            self.clock.tick(30)

        pygame.quit()


if __name__ == "__main__":
    try:
        viewer = ProvinceMappingViewer()
        viewer.run()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
