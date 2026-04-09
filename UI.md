# ROTK2 UI Framework Documentation

## Overview

This document describes the custom UI framework for ROTK2 Python, designed to support dual UI modes (Classic EGA 640x400 and Modern 1280x800 Steam Deck) with gamepad, mouse, and keyboard input.

## Architecture

### Core Philosophy

- **Component-based**: All UI elements are reusable components
- **Virtual resolution**: Design at 1280x800, scale to any resolution
- **Input abstraction**: Support mouse, keyboard, and gamepad seamlessly
- **Mode-agnostic**: Same game logic, different presentation
- **Testable**: All components unit-testable with pytest

### Directory Structure

```
Src/UI/
├── __init__.py                    # Package exports
├── core/                          # Core framework
│   ├── __init__.py
│   ├── manager.py                 # UIManager singleton
│   ├── component.py               # UIComponent base class
│   ├── container.py               # UIContainer for layouts
│   ├── anchor.py                  # Positioning system
│   ├── transform.py               # Resolution scaling
│   ├── theme.py                   # Theming system
│   └── input_handler.py           # Input abstraction
├── components/                    # UI components
│   ├── __init__.py
│   ├── label.py                   # Text labels
│   ├── button.py                  # Clickable buttons
│   ├── panel.py                   # Container panels
│   ├── image.py                   # Image display
│   ├── list.py                    # Selection lists
│   ├── grid.py                    # Data tables
│   ├── menu.py                    # Menu/navigation
│   └── tooltip.py                 # Hover tooltips
├── screens/                       # Full screens
│   ├── __init__.py
│   ├── base_screen.py             # Base screen class
│   ├── province_screen.py         # Province info screen
│   ├── map_screen.py              # Strategic map
│   ├── officer_screen.py          # Officer management
│   ├── command_screen.py          # Command menu
│   └── dialog_screen.py           # Modal dialogs
├── themes/                        # Theme files
│   ├── __init__.py
│   ├── modern.json                # Modern theme
│   └── classic.json               # Classic theme
└── tests/                         # UI tests
    ├── __init__.py
    ├── test_component.py
    ├── test_manager.py
    └── test_input.py
```

## Core Classes

### UIManager

Central coordinator for the UI system. Singleton pattern.

```python
class UIManager:
    """
    Central UI manager singleton.
    
    Responsibilities:
    - Manage current screen
    - Handle input events
    - Coordinate rendering
    - Manage theme application
    - Handle resolution scaling
    """
    
    _instance: UIManager | None = None
    
    def __init__(self, virtual_resolution: tuple[int, int] = (1280, 800)):
        self.virtual_resolution = virtual_resolution
        self.actual_resolution = virtual_resolution
        self.current_screen: BaseScreen | None = None
        self.theme = Theme()
        self.input_handler = InputHandler()
        self.focused_component: UIComponent | None = None
        
    def set_screen(self, screen: BaseScreen) -> None:
        """Switch to a new screen."""
        
    def handle_event(self, event: pygame.event.Event) -> None:
        """Process pygame event."""
        
    def update(self, dt: float) -> None:
        """Update all components."""
        
    def render(self, surface: pygame.Surface) -> None:
        """Render current screen."""
        
    def set_resolution(self, width: int, height: int) -> None:
        """Change actual resolution (scaling)."""
```

### UIComponent

Base class for all UI elements.

```python
class UIComponent:
    """
    Base class for all UI components.
    
    Attributes:
        rect: Position and size (virtual coordinates)
        visible: Whether component is visible
        enabled: Whether component accepts input
        parent: Parent container (if any)
        anchor: Positioning anchor
        theme: Component-specific theme overrides
    """
    
    def __init__(self,
                 position: tuple[float, float] | tuple[int, int],
                 size: tuple[int, int] | None = None,
                 anchor: Anchor = Anchor.TOP_LEFT,
                 parent: UIContainer | None = None):
        self._position = position
        self._size = size or (100, 30)
        self.anchor = anchor
        self.parent = parent
        self.visible = True
        self.enabled = True
        self._absolute_rect = pygame.Rect(0, 0, 0, 0)
        
    @property
    def rect(self) -> pygame.Rect:
        """Get rectangle in virtual coordinates."""
        
    @property
    def absolute_rect(self) -> pygame.Rect:
        """Get rectangle in screen coordinates (cached)."""
        
    def handle_event(self, event: InputEvent) -> bool:
        """
        Handle input event.
        
        Returns:
            True if event was consumed, False to propagate
        """
        
    def update(self, dt: float) -> None:
        """Update component state."""
        
    def render(self, surface: pygame.Surface, transform: Transform) -> None:
        """Render component to surface."""
        
    def get_theme(self) -> Theme:
        """Get effective theme (inherit from parent if needed)."""
        
    def contains_point(self, point: tuple[int, int]) -> bool:
        """Check if point (screen coordinates) is inside component."""
```

### UIContainer

Base class for components that contain other components.

```python
class UIContainer(UIComponent):
    """
    Container for grouping and laying out child components.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.children: list[UIComponent] = []
        self.layout: Layout | None = None
        
    def add_child(self, child: UIComponent) -> None:
        """Add a child component."""
        
    def remove_child(self, child: UIComponent) -> None:
        """Remove a child component."""
        
    def get_children(self) -> list[UIComponent]:
        """Get all child components."""
        
    def apply_layout(self) -> None:
        """Apply layout to children."""
        
    def handle_event(self, event: InputEvent) -> bool:
        """
        Pass event to children in reverse order (topmost first).
        """
```

### Anchor System

Positioning relative to parent/container.

```python
class Anchor(Enum):
    """Position anchor points."""
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"
    
class Position:
    """
    Flexible position specification.
    
    Can be:
    - Absolute: (100, 200) - pixel coordinates
    - Relative: (0.1, 0.2) - percentage of parent size
    - Anchored: Position relative to anchor point
    """
    
    def __init__(self,
                 x: float | int | str,
                 y: float | int | str,
                 anchor: Anchor = Anchor.TOP_LEFT):
        self.x = x
        self.y = y
        self.anchor = anchor
```

### Transform

Resolution scaling and coordinate conversion.

```python
class Transform:
    """
    Handles scaling from virtual to actual resolution.
    
    Maintains aspect ratio by default (letterboxing if needed).
    """
    
    def __init__(self,
                 virtual_size: tuple[int, int],
                 actual_size: tuple[int, int],
                 maintain_aspect: bool = True):
        self.virtual_size = virtual_size
        self.actual_size = actual_size
        self.maintain_aspect = maintain_aspect
        
        # Calculate scales
        if maintain_aspect:
            self.scale = min(
                actual_size[0] / virtual_size[0],
                actual_size[1] / virtual_size[1]
            )
            self.offset_x = (actual_size[0] - virtual_size[0] * self.scale) / 2
            self.offset_y = (actual_size[1] - virtual_size[1] * self.scale) / 2
        else:
            self.scale_x = actual_size[0] / virtual_size[0]
            self.scale_y = actual_size[1] / virtual_size[1]
            self.offset_x = 0
            self.offset_y = 0
            
    def to_screen(self, rect: pygame.Rect) -> pygame.Rect:
        """Convert virtual rect to screen coordinates."""
        
    def to_virtual(self, point: tuple[int, int]) -> tuple[float, float]:
        """Convert screen point to virtual coordinates."""
        
    def get_scale(self) -> float | tuple[float, float]:
        """Get uniform scale or (scale_x, scale_y)."""
```

## Input System

### InputEvent

Unified input event abstraction.

```python
class InputEvent:
    """Unified input event for all input types."""
    
    class Type(Enum):
        MOUSE_MOVE = auto()
        MOUSE_DOWN = auto()
        MOUSE_UP = auto()
        MOUSE_WHEEL = auto()
        KEY_DOWN = auto()
        KEY_UP = auto()
        GAMEPAD_BUTTON_DOWN = auto()
        GAMEPAD_BUTTON_UP = auto()
        GAMEPAD_AXIS = auto()
        FOCUS_NEXT = auto()  # Tab / Right / Down
        FOCUS_PREV = auto()  # Shift+Tab / Left / Up
        SELECT = auto()      # Enter / A button
        BACK = auto()        # Escape / B button
        
    def __init__(self,
                 event_type: Type,
                 position: tuple[int, int] | None = None,
                 button: int | str | None = None,
                 value: float | None = None):
        self.type = event_type
        self.position = position  # Screen coordinates
        self.button = button      # Mouse button or gamepad button
        self.value = value        # Axis value or wheel delta
```

### InputHandler

Converts pygame events to InputEvents and manages focus.

```python
class InputHandler:
    """
    Handles all input types and converts to unified InputEvents.
    
    Supports:
    - Mouse (position, clicks, wheel)
    - Keyboard (navigation, shortcuts)
    - Gamepad ( Xbox/PlayStation controller)
    """
    
    def __init__(self):
        self.mode = InputMode.AUTO  # AUTO, MOUSE, GAMEPAD, KEYBOARD
        self.focused_component: UIComponent | None = None
        self.hover_component: UIComponent | None = None
        self.gamepad_enabled = False
        self._init_gamepad()
        
    def _init_gamepad(self) -> None:
        """Initialize gamepad/joystick if available."""
        
    def process_pygame_event(self, event: pygame.event.Event) -> list[InputEvent]:
        """
        Convert pygame event to InputEvent(s).
        
        Returns:
            List of InputEvents (one pygame event may generate multiple)
        """
        
    def update(self, screen: UIScreen) -> None:
        """
        Update input state (called each frame).
        
        Handles:
        - Gamepad axis polling
        - Focus management
        - Hover detection
        """
        
    def set_focus(self, component: UIComponent | None) -> None:
        """Set focused component (for keyboard/gamepad navigation)."""
        
    def move_focus(self, direction: FocusDirection) -> None:
        """Move focus in given direction (for gamepad)."""
        
    def get_component_at(self, position: tuple[int, int], 
                         screen: UIScreen) -> UIComponent | None:
        """Find component at screen position (for mouse)."""
```

### Gamepad Support

```python
class GamepadButton(Enum):
    """Standardized gamepad buttons."""
    A = "a"              # Select/Confirm
    B = "b"              # Back/Cancel
    X = "x"              # Action 1
    Y = "y"              # Action 2
    LB = "lb"            # L1 / Left Bumper
    RB = "rb"            # R1 / Right Bumper
    LT = "lt"            # L2 / Left Trigger
    RT = "rt"            # R2 / Right Trigger
    SELECT = "select"    # View/Back/Share
    START = "start"      # Menu/Options
    LS = "ls"            # L3 / Left Stick
    RS = "rs"            # R3 / Right Stick
    DPAD_UP = "dpad_up"
    DPAD_DOWN = "dpad_down"
    DPAD_LEFT = "dpad_left"
    DPAD_RIGHT = "dpad_right"

class GamepadMapper:
    """
    Maps different gamepad layouts to standard buttons.
    
    Supports:
    - Xbox (A/B/X/Y)
    - PlayStation (×/○/□/△)
    - Nintendo (B/A/Y/X)
    """
    
    def __init__(self, joystick: pygame.joystick.JoystickType):
        self.joystick = joystick
        self.mapping = self._detect_mapping()
        
    def _detect_mapping(self) -> dict[int, GamepadButton]:
        """Auto-detect controller type and map buttons."""
        
    def get_button(self, button_id: int) -> GamepadButton | None:
        """Get standardized button for raw button ID."""
```

## Components

### UILabel

Text display component.

```python
class UILabel(UIComponent):
    """
    Text label component.
    
    Features:
    - Word wrap
    - Multi-line text
    - Text alignment
    - Auto-sizing (fit to content)
    - Text truncation with ellipsis
    """
    
    def __init__(self,
                 text: str = "",
                 font: Font | None = None,
                 color: Color | None = None,
                 max_width: int | None = None,
                 wrap: bool = False,
                 align: TextAlign = TextAlign.LEFT,
                 **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.font = font
        self.color = color
        self.max_width = max_width
        self.wrap = wrap
        self.align = align
        self._rendered_text: pygame.Surface | None = None
        self._needs_update = True
        
    def set_text(self, text: str) -> None:
        """Update label text."""
        
    def get_preferred_size(self) -> tuple[int, int]:
        """Calculate size needed to display text."""
        
    def render(self, surface: pygame.Surface, transform: Transform) -> None:
        """Render text."""
```

### UIButton

Clickable button component.

```python
class UIButton(UIComponent):
    """
    Button component.
    
    States:
    - Normal
    - Hover (mouse over)
    - Pressed (mouse down / button held)
    - Focused (keyboard/gamepad navigation)
    - Disabled
    
    Callbacks:
    - on_click: Called when button is activated
    - on_hover: Called when mouse enters
    - on_leave: Called when mouse exits
    """
    
    def __init__(self,
                 text: str = "",
                 icon: pygame.Surface | None = None,
                 on_click: Callable | None = None,
                 shortcut_key: int | None = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.icon = icon
        self.on_click = on_click
        self.shortcut_key = shortcut_key
        self._state = ButtonState.NORMAL
        
    def press(self) -> None:
        """Programmatically press button."""
        
    def set_enabled(self, enabled: bool) -> None:
        """Enable/disable button."""
        
    def render(self, surface: pygame.Surface, transform: Transform) -> None:
        """Render button with current state visual."""
```

### UIPanel

Container with background/border.

```python
class UIPanel(UIContainer):
    """
    Panel container with visual styling.
    
    Can have:
    - Background color/image
    - Border
    - Padding (space inside border)
    - Margin (space outside)
    - Scrollbars (if content overflows)
    """
    
    def __init__(self,
                 background_color: Color | None = None,
                 background_image: pygame.Surface | None = None,
                 border_width: int = 0,
                 border_color: Color | None = None,
                 border_radius: int = 0,
                 padding: Padding | tuple[int, ...] = (0, 0, 0, 0),
                 **kwargs):
        super().__init__(**kwargs)
        self.background_color = background_color
        self.background_image = background_image
        self.border_width = border_width
        self.border_color = border_color
        self.border_radius = border_radius
        self.padding = Padding(padding)
        
    def get_content_rect(self) -> pygame.Rect:
        """Get rectangle available for children (accounting for padding)."""
        
    def render(self, surface: pygame.Surface, transform: Transform) -> None:
        """Render panel background and border."""
```

## Layouts

### Layout Base Class

```python
class Layout(ABC):
    """Abstract base class for layouts."""
    
    @abstractmethod
    def apply(self, container: UIContainer) -> None:
        """Apply layout to container's children."""
        
    @abstractmethod
    def get_preferred_size(self, container: UIContainer) -> tuple[int, int]:
        """Calculate preferred size for container."""
```

### Grid Layout

```python
class GridLayout(Layout):
    """
    Grid-based layout.
    
    Properties:
    - rows: Number of rows (None for auto)
    - cols: Number of columns (None for auto)
    - spacing: Gap between cells
    - row_weights: Relative row heights
    - col_weights: Relative column widths
    """
    
    def __init__(self,
                 rows: int | None = None,
                 cols: int | None = None,
                 spacing: tuple[int, int] = (0, 0),
                 row_weights: list[float] | None = None,
                 col_weights: list[float] | None = None):
        self.rows = rows
        self.cols = cols
        self.spacing = spacing
        self.row_weights = row_weights
        self.col_weights = col_weights
        
    def add_component(self, component: UIComponent, 
                      row: int, col: int,
                      row_span: int = 1, col_span: int = 1) -> None:
        """Add component to specific grid cell."""
```

### Stack Layout

```python
class StackLayout(Layout):
    """
    Vertical or horizontal stack layout.
    
    Like flexbox: components flow in one direction with optional spacing.
    """
    
    class Direction(Enum):
        VERTICAL = auto()
        HORIZONTAL = auto()
        
    def __init__(self,
                 direction: Direction = Direction.VERTICAL,
                 spacing: int = 0,
                 alignment: Alignment = Alignment.START):
        self.direction = direction
        self.spacing = spacing
        self.alignment = alignment
```

## Screens

### BaseScreen

```python
class BaseScreen(UIContainer):
    """
    Base class for full screens.
    
    Screens are top-level containers that fill the entire window.
    Examples: ProvinceScreen, MapScreen, OfficerScreen
    """
    
    def __init__(self, game_state: GameState):
        super().__init__(position=(0, 0), size=(1280, 800))
        self.game_state = game_state
        self.modal_dialog: UIDialog | None = None
        
    def on_enter(self) -> None:
        """Called when screen becomes active."""
        
    def on_exit(self) -> None:
        """Called when screen is deactivated."""
        
    def show_dialog(self, dialog: UIDialog) -> None:
        """Show modal dialog on top of screen."""
        
    def close_dialog(self) -> None:
        """Close current modal dialog."""
```

## Theming

### Theme System

```python
class Theme:
    """
    Hierarchical theming system.
    
    Themes can be loaded from JSON and support:
    - Color definitions
    - Font specifications
    - Component-specific styling
    - Prototypes (reusable style blocks)
    """
    
    def __init__(self, theme_file: str | None = None):
        self.colors: dict[str, Color] = {}
        self.fonts: dict[str, Font] = {}
        self.styles: dict[str, dict] = {}
        
        if theme_file:
            self.load(theme_file)
            
    def load(self, filepath: str) -> None:
        """Load theme from JSON file."""
        
    def get_color(self, name: str, fallback: Color | None = None) -> Color:
        """Get color by name."""
        
    def get_font(self, name: str, fallback: Font | None = None) -> Font:
        """Get font by name."""
        
    def get_style(self, component_type: str) -> dict:
        """Get style for component type."""
```

### Theme JSON Format

```json
{
  "colors": {
    "background": "#1a1a2e",
    "panel": "#16213e",
    "text_primary": "#e94560",
    "text_secondary": "#eaeaea",
    "accent": "#0f3460",
    "border": "#0f3460",
    "button_normal": "#16213e",
    "button_hover": "#0f3460",
    "button_pressed": "#e94560",
    "button_disabled": "#2a2a3e"
  },
  "fonts": {
    "body": {
      "family": "NotoSansCJK",
      "size": 16,
      "bold": false
    },
    "heading": {
      "family": "NotoSansCJK",
      "size": 24,
      "bold": true
    },
    "small": {
      "family": "NotoSansCJK",
      "size": 12,
      "bold": false
    }
  },
  "prototypes": {
    "panel_base": {
      "background_color": "panel",
      "border_width": 1,
      "border_color": "border",
      "border_radius": 4,
      "padding": [10, 10, 10, 10]
    }
  },
  "components": {
    "button": {
      "extends": "panel_base",
      "background_color": "button_normal",
      "hover_background": "button_hover",
      "pressed_background": "button_pressed",
      "text_color": "text_secondary",
      "font": "body",
      "padding": [8, 16]
    },
    "label": {
      "text_color": "text_secondary",
      "font": "body"
    },
    "panel": {
      "extends": "panel_base"
    }
  }
}
```

## Configuration

### UI Settings in config.py

```python
class UISettings(BaseSettings):
    """UI-specific settings."""
    
    # Mode
    ui_mode: Literal["classic", "modern"] = "modern"
    
    # Resolution (modern mode)
    screen_width: int = 1280
    screen_height: int = 800
    fullscreen: bool = False
    maintain_aspect_ratio: bool = True
    
    # Input
    input_mode: Literal["auto", "mouse", "gamepad", "keyboard"] = "auto"
    gamepad_enabled: bool = True
    gamepad_sensitivity: float = 1.0
    
    # Theme
    theme_file: str = "themes/modern.json"
    
    # Fonts
    font_body: str = "fonts/NotoSansCJK-Regular.otf"
    font_heading: str = "fonts/NotoSansCJK-Bold.otf"
    
    # Classic mode (uses existing settings)
    classic_scale: float = 2.0
```

## Testing

### Testing Strategy

All UI components should be testable without pygame display:

```python
# tests/test_component.py
import pytest
from UI.core.component import UIComponent
from UI.core.anchor import Anchor

class TestUIComponent:
    def test_position_calculation(self):
        comp = UIComponent(position=(100, 200), size=(50, 30))
        assert comp.rect == pygame.Rect(100, 200, 50, 30)
        
    def test_anchor_top_left(self):
        parent = MockContainer(size=(400, 300))
        comp = UIComponent(
            position=(10, 20),
            size=(100, 50),
            anchor=Anchor.TOP_LEFT,
            parent=parent
        )
        assert comp.absolute_rect.topleft == (10, 20)
        
    def test_anchor_center(self):
        parent = MockContainer(size=(400, 300))
        comp = UIComponent(
            position=(0, 0),
            size=(100, 50),
            anchor=Anchor.CENTER,
            parent=parent
        )
        # Should be centered in parent
        assert comp.absolute_rect.center == (200, 150)
        
    def test_event_propagation(self):
        parent = UIContainer()
        child = UIComponent(parent=parent)
        parent.add_child(child)
        
        event = InputEvent(InputEvent.Type.MOUSE_DOWN, position=(50, 50))
        
        # Child should receive event before parent
        assert child.handle_event(event) == True  # Consumed
```

### Mock Objects

```python
# tests/mocks.py
class MockSurface:
    """Mock pygame.Surface for testing without display."""
    
    def __init__(self, size: tuple[int, int]):
        self.size = size
        self.blit_calls: list[tuple] = []
        
    def blit(self, source, dest, area=None):
        self.blit_calls.append((source, dest, area))
        
class MockContainer:
    """Mock container for testing."""
    
    def __init__(self, size: tuple[int, int] = (800, 600)):
        self._rect = pygame.Rect(0, 0, *size)
        
    @property
    def rect(self):
        return self._rect
```

## Migration Strategy

### Phase 1: Framework (1-2 weeks)
- Create core classes (UIManager, UIComponent, Transform)
- Implement basic components (Label, Button, Panel)
- Set up input handling
- Write tests

### Phase 2: Screens (2-3 weeks)
- Implement ProvinceScreen as proof-of-concept
- Port existing functionality
- Ensure parity with classic mode

### Phase 3: Integration (1 week)
- Add UI mode switching
- Settings persistence
- Classic mode compatibility testing

### Phase 4: Polish (ongoing)
- Animations and transitions
- Sound effects
- Additional screens
- Performance optimization

## Open Questions

1. **Font Loading**: How to handle missing fonts gracefully?
2. **Asset Management**: Should we implement an asset loader/cache?
3. **Animation**: Do we want animated transitions between screens?
4. **Accessibility**: Colorblind modes? High contrast themes?
5. **Localization**: How to handle text direction (RTL for Arabic/Hebrew)?

---

## References

- Pygame documentation: https://www.pygame.org/docs/
- Steam Deck resolution: 1280x800 (16:10 aspect ratio)
- Open source fonts: Noto Sans CJK (Chinese, Japanese, Korean)
- Controller mapping guidelines: SDL GameController DB
