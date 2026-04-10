"""
Multi-line label component for the ROTK2 UI.

Renders text with proper line wrapping and multiple lines.
"""

import pygame
from UI.core.component import UIComponent
from UI.core.transform import Transform


class UIMultiLineLabel(UIComponent):
    """
    Multi-line text label component.

    Renders text across multiple lines with proper wrapping.
    Unlike UILabel, this handles newline characters correctly.

    Attributes:
        text: The text to display (can contain \n for line breaks)
        font: Font to use for rendering
        color: Text color
        line_spacing: Pixels between lines
    """

    def __init__(
        self,
        text: str = "",
        font: pygame.font.Font | None = None,
        color: pygame.Color | tuple[int, int, int] = (255, 255, 255),
        align: str = "left",
        line_spacing: int = 4,
        **kwargs,
    ):
        """
        Initialize multi-line label.

        Args:
            text: Text to display (can include \n for line breaks)
            font: Font for text
            color: Text color
            align: Text alignment ('left', 'center', 'right')
            line_spacing: Pixels between lines
            **kwargs: Additional UIComponent arguments
        """
        super().__init__(**kwargs)

        self._text = text
        self.font = font or pygame.font.Font(None, 24)
        self.color = color
        self.align = align
        self.line_spacing = line_spacing

        self._line_surfaces: list[pygame.Surface] = []
        self._needs_render = True

        self._render_lines()

    @property
    def text(self) -> str:
        """Get current text."""
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """Set text and mark for re-render."""
        if value != self._text:
            self._text = value
            self._needs_render = True

    def _wrap_text(self, text: str, max_width: int) -> list[str]:
        """Wrap text to fit within max_width."""
        words = text.split(" ")
        lines = []
        current_line = []

        for word in words:
            # Test if adding this word would exceed width
            test_line = " ".join(current_line + [word])
            test_surface = self.font.render(test_line, True, self.color)

            if test_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                # Line would be too long, start new line
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    # Word is longer than max_width, just add it
                    lines.append(word)

        # Don't forget the last line
        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _render_lines(self) -> None:
        """Render each line of text to a surface."""
        self._line_surfaces = []

        if not self._text:
            return

        # Split by newlines first
        paragraphs = self._text.split("\n")
        all_lines = []

        # Wrap each paragraph
        for paragraph in paragraphs:
            if paragraph.strip():
                wrapped = self._wrap_text(paragraph, self._size[0])
                all_lines.extend(wrapped)

        # Render each line
        for line in all_lines:
            surface = self.font.render(line, True, self.color)
            self._line_surfaces.append(surface)

    def _handle_event(self, event: pygame.event.Event, transform: Transform) -> bool:
        """Handle input events. Labels don't handle events."""
        return False  # Labels don't process events

    def render(self, surface: pygame.Surface, transform: Transform) -> None:
        """Render the multi-line text."""
        if not self.visible:
            return

        # Re-render if needed
        if self._needs_render:
            self._render_lines()
            self._needs_render = False

        if not self._line_surfaces:
            return

        # Get screen position
        abs_x, abs_y = self.get_absolute_position()
        abs_rect = pygame.Rect(abs_x, abs_y, self._size[0], self._size[1])
        screen_rect = transform.to_screen(abs_rect)

        # Calculate starting Y position for vertical centering
        total_height = sum(s.get_height() for s in self._line_surfaces)
        total_height += self.line_spacing * (len(self._line_surfaces) - 1)

        if self.align == "center":
            start_y = screen_rect.centery - total_height // 2
        elif self.align == "right":
            start_y = screen_rect.bottom - total_height
        else:  # left
            start_y = screen_rect.top

        # Draw each line
        current_y = start_y
        for line_surface in self._line_surfaces:
            # Calculate X position based on alignment
            if self.align == "center":
                x = screen_rect.centerx - line_surface.get_width() // 2
            elif self.align == "right":
                x = screen_rect.right - line_surface.get_width()
            else:  # left
                x = screen_rect.left

            # Draw the line
            surface.blit(line_surface, (x, current_y))

            # Move to next line
            current_y += line_surface.get_height() + self.line_spacing
