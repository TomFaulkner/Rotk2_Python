"""Map renderer for SNES-style world map."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pygame

try:
    from .map_geometry import ProvinceShape, ProvinceShapeManager
except ImportError:
    # Fallback for direct execution
    from map_geometry import ProvinceShape, ProvinceShapeManager

if TYPE_CHECKING:
    from UI.core.transform import Transform


class MapRenderer:
    """Renders the SNES-style world map with provinces, borders, and overlays.

    The renderer supports:
    - Background terrain layer (mountains, ocean)
    - Province fills colored by ruler
    - Province borders
    - Optional province number overlays
    - Province highlighting on hover
    - Event overlays (locusts, plague, etc.)

    The map is designed at 1000x650 resolution and scaled to fit the
    target screen size using the Transform system.
    """

    # Ruler colors from Helper.RulerPalettes
    RULER_COLORS = [
        (170, 170, 170),  # 0 - Gray
        (255, 255, 85),  # 1 - Yellow
        (170, 170, 85),  # 2 - Olive
        (170, 85, 255),  # 3 - Purple
        (255, 85, 255),  # 4 - Magenta
        (170, 85, 255),  # 5 - Purple (duplicate)
        (85, 255, 128),  # 6 - Green
        (85, 255, 255),  # 7 - Cyan
        (170, 255, 255),  # 8 - Light Cyan
        (85, 85, 255),  # 9 - Blue
        (255, 85, 255),  # 10 - Magenta (duplicate)
        (170, 0, 85),  # 11 - Dark Red
        (255, 170, 85),  # 12 - Orange
        (170, 170, 85),  # 13 - Olive (duplicate)
        (0, 128, 0),  # 14 - Dark Green
        (255, 170, 0),  # 15 - Orange/Gold
    ]

    # Unruled provinces use transparency (no fill)
    UNRULED_COLOR = None

    # Border styling
    BORDER_COLOR = (40, 40, 40)
    BORDER_WIDTH = 2

    # Highlight styling
    HIGHLIGHT_COLOR = (255, 255, 200)  # Light yellow
    HIGHLIGHT_ALPHA = 128  # Semi-transparent
    HIGHLIGHT_BORDER_WIDTH = 3

    # Number overlay styling
    NUMBER_BG_COLOR = (0, 0, 0)
    NUMBER_TEXT_COLOR = (255, 255, 255)
    NUMBER_BOX_SIZE = (24, 24)

    # Steam Deck optimized dimensions - uses original coordinate system
    # Background is 1088x944, provinces are within it at their original positions
    DEFAULT_DESIGN_SIZE: tuple[int, int] = (1088, 944)
    DEFAULT_MAP_OFFSET: tuple[int, int] = (96, -72)  # Center in 1280x800

    def __init__(self, design_size: tuple[int, int] | None = None, shapes_file: str | None = None):
        """Initialize the map renderer.

        Args:
            design_size: The design resolution for the map area (width, height).
                        Defaults to Steam Deck optimized (1050, 720).
            shapes_file: Path to province_shapes.json. Uses default if None.
        """
        if design_size is None:
            design_size = self.DEFAULT_DESIGN_SIZE
        self.design_width, self.design_height = design_size
        self.shape_manager = ProvinceShapeManager(shapes_file)

        # Background terrain image
        self.terrain_background: pygame.Surface | None = None

        # Province state
        self.province_rulers: dict[int, int] = {}  # province_id -> ruler_no (-1 for unruled)
        self.highlighted_province: int | None = None
        self.show_numbers = True

        # Cached surfaces for performance
        self._cached_background: pygame.Surface | None = None
        self._cached_map: pygame.Surface | None = None
        self._cache_dirty = True

        # Load default rulers (unruled)
        self._init_default_rulers()

    def _init_default_rulers(self) -> None:
        """Initialize all provinces as unruled (-1)."""
        for province_id in self.shape_manager.shapes:
            self.province_rulers[province_id] = -1

    def load_terrain_background(self, image_path: str) -> bool:
        """Load the terrain background image.

        Args:
            image_path: Path to the background image (PNG, JPG, etc.)

        Returns:
            True if loaded successfully, False otherwise
        """
        path = Path(image_path)

        if not path.exists():
            # Try relative to project root
            path = Path("/home/tom/dev/Rotk2_Python") / image_path

        if not path.exists():
            print(f"Warning: Terrain background not found: {image_path}")
            return False

        try:
            # Load image - try convert() for performance, fallback to no convert
            try:
                self.terrain_background = pygame.image.load(str(path)).convert()
            except (pygame.error, TypeError):
                # Headless environment or other issue - load without convert
                self.terrain_background = pygame.image.load(str(path))

            # Keep background at original size - provinces align with it naturally
            # The background is 1088x944, same as design_size
            # No scaling needed since coordinates match the original image
            self._cache_dirty = True
            return True
        except pygame.error as e:
            print(f"Error loading terrain background: {e}")
            return False

    def set_province_ruler(self, province_id: int, ruler_no: int | None) -> None:
        """Set the ruler for a province.

        Args:
            province_id: Province number (1-41)
            ruler_no: Ruler number (0-15), or None/-1 for unruled
        """
        if province_id not in self.shape_manager.shapes:
            print(f"Warning: Invalid province ID: {province_id}")
            return

        new_ruler = -1 if ruler_no is None else ruler_no

        if self.province_rulers.get(province_id) != new_ruler:
            self.province_rulers[province_id] = new_ruler
            self._cache_dirty = True

    def set_rulers_from_game_state(self, game_data: dict[int, int]) -> None:
        """Bulk update rulers from game state.

        Args:
            game_data: Dictionary mapping province_id -> ruler_no
        """
        for province_id, ruler_no in game_data.items():
            self.province_rulers[province_id] = ruler_no if ruler_no is not None else -1
        self._cache_dirty = True

    def highlight_province(self, province_id: int | None) -> None:
        """Set which province to highlight.

        Args:
            province_id: Province to highlight, or None to clear
        """
        if self.highlighted_province != province_id:
            self.highlighted_province = province_id
            # Note: We don't mark cache dirty for highlight changes
            # since highlight is rendered dynamically on top

    def set_show_numbers(self, show: bool) -> None:
        """Toggle province number overlay.

        Args:
            show: True to show numbers, False to hide
        """
        if self.show_numbers != show:
            self.show_numbers = show
            self._cache_dirty = True

    def _get_ruler_color(self, ruler_no: int) -> tuple[int, int, int] | None:
        """Get the color for a ruler.

        Args:
            ruler_no: Ruler number (0-15), or -1 for unruled

        Returns:
            RGB color tuple, or None for unruled (transparent)
        """
        if ruler_no < 0 or ruler_no >= len(self.RULER_COLORS):
            return None
        return self.RULER_COLORS[ruler_no]

    def _render_to_cache(self) -> pygame.Surface:
        """Render the static map content to a cached surface.

        Returns:
            Cached surface with map content
        """
        # Create surface with alpha support
        surface = pygame.Surface((self.design_width, self.design_height), pygame.SRCALPHA)

        # 1. Draw terrain background
        if self.terrain_background:
            surface.blit(self.terrain_background, (0, 0))
        else:
            # Default background (light beige for land, blue for water)
            surface.fill((220, 210, 180))

        # 2. Draw province fills
        for province_id, shape in self.shape_manager.shapes.items():
            ruler_no = self.province_rulers.get(province_id, -1)
            color = self._get_ruler_color(ruler_no)

            if color:
                self._render_province_fill(surface, shape, color)

        # 3. Draw province borders (only if no background image - avoid double-drawing)
        if not self.terrain_background:
            for shape in self.shape_manager.shapes.values():
                self._render_province_border(surface, shape)

        # 4. Draw province numbers
        if self.show_numbers:
            for shape in self.shape_manager.shapes.values():
                self._render_province_number(surface, shape)

        return surface

    # Province fill alpha (0-255) - 210 is ~82% opaque, lets background borders show through
    FILL_ALPHA = 210

    def _render_province_fill(
        self, surface: pygame.Surface, shape: ProvinceShape, color: tuple[int, int, int]
    ) -> None:
        """Render a filled province polygon.

        Args:
            surface: Surface to render to
            shape: Province shape
            color: Fill color
        """
        points = shape.points

        # If we have a background image, use alpha blending so borders show through
        if self.terrain_background:
            # Create a temporary surface for alpha blending
            fill_surface = pygame.Surface((self.design_width, self.design_height), pygame.SRCALPHA)
            fill_color = (*color, self.FILL_ALPHA)
            pygame.draw.polygon(fill_surface, fill_color, points)
            surface.blit(fill_surface, (0, 0))
        else:
            # Solid fill when no background
            pygame.draw.polygon(surface, color, points)

    def _render_province_border(self, surface: pygame.Surface, shape: ProvinceShape) -> None:
        """Render a province border.

        Args:
            surface: Surface to render to
            shape: Province shape
        """
        points = shape.points
        pygame.draw.polygon(surface, self.BORDER_COLOR, points, width=self.BORDER_WIDTH)

    def _render_province_number(self, surface: pygame.Surface, shape: ProvinceShape) -> None:
        """Render province number overlay.

        Args:
            surface: Surface to render to
            shape: Province shape
        """
        num_x, num_y = shape.number_position

        # Draw black background box
        box_width, box_height = self.NUMBER_BOX_SIZE
        box_x = num_x - box_width // 2
        box_y = num_y - box_height // 2

        pygame.draw.rect(surface, self.NUMBER_BG_COLOR, (box_x, box_y, box_width, box_height))

        # Draw white number text
        font = pygame.font.Font(None, 20)
        text = font.render(str(shape.province_id), True, self.NUMBER_TEXT_COLOR)
        text_rect = text.get_rect(center=(num_x, num_y))
        surface.blit(text, text_rect)

    def _render_highlight(self, surface: pygame.Surface, shape: ProvinceShape) -> None:
        """Render highlight overlay for a province.

        Args:
            surface: Surface to render to
            shape: Province shape to highlight
        """
        points = shape.points

        # Draw filled highlight with alpha
        highlight_surface = pygame.Surface((self.design_width, self.design_height), pygame.SRCALPHA)
        highlight_color = (*self.HIGHLIGHT_COLOR, self.HIGHLIGHT_ALPHA)
        pygame.draw.polygon(highlight_surface, highlight_color, points)
        surface.blit(highlight_surface, (0, 0))

        # Draw brighter border
        pygame.draw.polygon(
            surface, self.HIGHLIGHT_COLOR, points, width=self.HIGHLIGHT_BORDER_WIDTH
        )

    def _get_screen_map_origin(
        self, transform: Transform, screen_offset: tuple[int, int] = (0, 0)
    ) -> tuple[int, int]:
        """Get the top-left screen position where the map is drawn."""
        scale = transform.get_scale()
        letterbox = transform.get_letterbox_rect()
        map_offset_x, map_offset_y = self.DEFAULT_MAP_OFFSET
        screen_x = int(letterbox.x + map_offset_x * scale + screen_offset[0])
        screen_y = int(letterbox.y + map_offset_y * scale + screen_offset[1])
        return (screen_x, screen_y)

    def render(
        self,
        surface: pygame.Surface,
        transform: Transform,
        screen_offset: tuple[int, int] = (0, 0),
    ) -> None:
        """Render the map to a surface.

        Args:
            surface: Target surface (screen or buffer)
            transform: Transform for scaling from design to screen coordinates
            screen_offset: Additional screen-space offset in pixels
        """
        # Update cache if needed
        if self._cache_dirty or self._cached_map is None:
            self._cached_map = self._render_to_cache()
            self._cache_dirty = False

        # Get the letterbox/scaling info
        scale = transform.get_scale()
        screen_x, screen_y = self._get_screen_map_origin(transform, screen_offset)

        # Scale the cached map to screen size
        scaled_width = int(self.design_width * scale)
        scaled_height = int(self.design_height * scale)

        if scaled_width != self.design_width or scaled_height != self.design_height:
            scaled_map = pygame.transform.scale(self._cached_map, (scaled_width, scaled_height))
        else:
            scaled_map = self._cached_map

        # Draw the base map
        surface.blit(scaled_map, (screen_x, screen_y))

        # Render highlight on top (if any)
        if self.highlighted_province:
            shape = self.shape_manager.get_shape(self.highlighted_province)
            if shape:
                self._render_highlight_scaled(surface, shape, scale, screen_x, screen_y)

    def _render_highlight_scaled(
        self,
        surface: pygame.Surface,
        shape: ProvinceShape,
        scale: float,
        offset_x: int,
        offset_y: int,
    ) -> None:
        """Render highlight for a province at screen scale.

        Args:
            surface: Target surface
            shape: Province shape
            scale: Scale factor
            offset_x: Screen X offset
            offset_y: Screen Y offset
        """
        # Scale points to screen coordinates
        scaled_points = [
            (int(x * scale) + offset_x, int(y * scale) + offset_y) for x, y in shape.points
        ]

        # Draw filled highlight with alpha
        # Create a temporary surface for the highlight
        temp_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        highlight_color = (*self.HIGHLIGHT_COLOR, self.HIGHLIGHT_ALPHA)
        pygame.draw.polygon(temp_surface, highlight_color, scaled_points)
        surface.blit(temp_surface, (0, 0))

        # Draw brighter border
        pygame.draw.polygon(
            surface,
            self.HIGHLIGHT_COLOR,
            scaled_points,
            width=int(self.HIGHLIGHT_BORDER_WIDTH * scale),
        )

    def get_province_at_screen_point(
        self,
        screen_point: tuple[int, int],
        transform: Transform,
        screen_offset: tuple[int, int] = (0, 0),
    ) -> int | None:
        """Find which province is at a screen position.

        Args:
            screen_point: Screen coordinates (x, y)
            transform: Transform for coordinate conversion
            screen_offset: Additional screen-space offset in pixels

        Returns:
            Province ID or None if not on a province
        """
        adjusted_point = (screen_point[0] - screen_offset[0], screen_point[1] - screen_offset[1])

        # Convert screen to virtual coordinates
        virtual_x, virtual_y = transform.to_virtual(adjusted_point)

        # Adjust for map offset within virtual space
        map_offset_x, map_offset_y = self.DEFAULT_MAP_OFFSET

        map_x = virtual_x - map_offset_x
        map_y = virtual_y - map_offset_y

        # Check bounds
        if map_x < 0 or map_x >= self.design_width:
            return None
        if map_y < 0 or map_y >= self.design_height:
            return None

        # Find province at point
        return self.shape_manager.get_province_at_point(map_x, map_y)

    def get_province_screen_position(
        self,
        province_id: int,
        transform: Transform,
        anchor: str = "center",
        screen_offset: tuple[int, int] = (0, 0),
    ) -> tuple[int, int] | None:
        """Get the screen coordinates of a province anchor point.

        Args:
            province_id: Province number
            transform: Transform for coordinate conversion
            anchor: Either "center" or "number"
            screen_offset: Additional screen-space offset in pixels

        Returns:
            Screen coordinates (x, y) or None if province not found
        """
        shape = self.shape_manager.get_shape(province_id)
        if not shape:
            return None

        if anchor == "number":
            map_x, map_y = shape.number_position
        else:
            map_x, map_y = shape.center

        scale = transform.get_scale()
        screen_origin_x, screen_origin_y = self._get_screen_map_origin(transform, screen_offset)
        screen_x = int(screen_origin_x + map_x * scale)
        screen_y = int(screen_origin_y + map_y * scale)

        return (screen_x, screen_y)

    def get_province_center_screen(
        self,
        province_id: int,
        transform: Transform,
        screen_offset: tuple[int, int] = (0, 0),
    ) -> tuple[int, int] | None:
        """Get the screen coordinates of a province center."""
        return self.get_province_screen_position(
            province_id, transform, anchor="center", screen_offset=screen_offset
        )

    def get_province_number_screen(
        self,
        province_id: int,
        transform: Transform,
        screen_offset: tuple[int, int] = (0, 0),
    ) -> tuple[int, int] | None:
        """Get the screen coordinates of a province number position."""
        return self.get_province_screen_position(
            province_id, transform, anchor="number", screen_offset=screen_offset
        )

    def render_province_highlight(
        self,
        surface: pygame.Surface,
        province_id: int,
        transform: Transform,
        screen_offset: tuple[int, int] = (0, 0),
    ) -> None:
        """Render a highlight overlay for a single province."""
        shape = self.shape_manager.get_shape(province_id)
        if not shape:
            return

        scale = transform.get_scale()
        screen_x, screen_y = self._get_screen_map_origin(transform, screen_offset)
        self._render_highlight_scaled(surface, shape, scale, screen_x, screen_y)


def test_renderer():
    """Test the map renderer with a simple display."""
    pygame.init()

    # Create window - Steam Deck native resolution
    screen_size = (1280, 800)
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("Map Renderer Test - Steam Deck (1280x800)")

    # Import transform
    import sys

    sys.path.insert(0, "/home/tom/dev/Rotk2_Python/Src/UI/core")
    from transform import Transform

    # Create transform
    transform = Transform((1280, 800), screen_size)

    # Create renderer
    renderer = MapRenderer()

    # Load the clean province border background (eliminates gaps)
    background_loaded = renderer.load_terrain_background("download/numbers-removed.jpg")
    if background_loaded:
        print("✓ Loaded clean province border background")
    else:
        print("⚠ Could not load background, using default beige color")

    # Set some sample rulers
    renderer.set_province_ruler(1, 0)  # Gray
    renderer.set_province_ruler(2, 1)  # Yellow
    renderer.set_province_ruler(3, 2)  # Olive
    renderer.set_province_ruler(4, 6)  # Green
    renderer.set_province_ruler(9, 3)  # Purple
    renderer.set_province_ruler(16, 12)  # Orange
    renderer.set_province_ruler(17, 7)  # Cyan
    renderer.set_province_ruler(21, 9)  # Blue
    renderer.set_province_ruler(24, 11)  # Dark Red
    renderer.set_province_ruler(28, 14)  # Dark Green

    clock = pygame.time.Clock()
    running = True
    hovered_province = None

    print("Map Renderer Test")
    print("- Mouse over provinces to highlight")
    print("- Click a province to print its ID")
    print("- Press N to toggle numbers")
    print("- Press Q to quit")

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_n:
                    renderer.set_show_numbers(not renderer.show_numbers)
            elif event.type == pygame.MOUSEMOTION:
                # Check for hover
                province_id = renderer.get_province_at_screen_point(event.pos, transform)
                if province_id != hovered_province:
                    hovered_province = province_id
                    renderer.highlight_province(province_id)
                    if province_id:
                        shape = renderer.shape_manager.get_shape(province_id)
                        print(f"Hovering: {shape.name} (ID: {province_id})")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                province_id = renderer.get_province_at_screen_point(event.pos, transform)
                if province_id:
                    shape = renderer.shape_manager.get_shape(province_id)
                    ruler_no = renderer.province_rulers.get(province_id, -1)
                    print(f"Clicked: {shape.name} (ID: {province_id}, Ruler: {ruler_no})")

        # Clear screen
        screen.fill((15, 15, 25))

        # Render map
        renderer.render(screen, transform)

        # Update display
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    print("Test complete!")


if __name__ == "__main__":
    test_renderer()
