"""
Gamepad input handler for UI navigation.

Maps gamepad buttons to UI actions and handles focus navigation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from enum import Enum, auto

import pygame

if TYPE_CHECKING:
    from UI.core.component import UIComponent
    from UI.core.container import UIContainer


class GamepadButton(Enum):
    """Standardized gamepad button mapping."""

    A = auto()  # Confirm/Select
    B = auto()  # Back/Cancel
    X = auto()  # Action 1
    Y = auto()  # Action 2
    LB = auto()  # Left Bumper
    RB = auto()  # Right Bumper
    START = auto()  # Menu
    SELECT = auto()  # Back/View
    DPAD_UP = auto()
    DPAD_DOWN = auto()
    DPAD_LEFT = auto()
    DPAD_RIGHT = auto()
    LEFT_STICK_UP = auto()
    LEFT_STICK_DOWN = auto()
    LEFT_STICK_LEFT = auto()
    LEFT_STICK_RIGHT = auto()


class GamepadHandler:
    """
    Handles gamepad input for UI navigation.

    Supports Xbox-style controllers and maps to UI actions:
    - D-Pad/Left Stick: Navigate between focusable components
    - A Button: Activate/Click focused component
    - B Button: Back/Cancel
    - Start: Menu/Pause
    """

    def __init__(self):
        """Initialize gamepad handler."""
        self.joystick: pygame.joystick.JoystickType | None = None
        self.deadzone = 0.3  # Analog stick deadzone

        # Track previous states for debouncing
        self._prev_button_states: dict[int, bool] = {}
        self._prev_hat_state: tuple[int, int] = (0, 0)
        self._prev_axis_state: dict[str, bool] = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
        }

        # Cooldown timers for repeatable actions (D-pad/stick)
        self._navigation_cooldown = 0.0
        self._initial_cooldown = 0.25  # Initial delay before repeat
        self._repeat_cooldown = 0.15  # Repeat rate after initial delay
        self._is_repeating = False

        self._init_joystick()

    def _init_joystick(self) -> None:
        """Initialize joystick if available and it's a valid gamepad."""
        pygame.joystick.init()

        # Find first valid gamepad (not macropad/keyboard)
        for i in range(pygame.joystick.get_count()):
            try:
                candidate = pygame.joystick.Joystick(i)
                candidate.init()

                # Filter: valid gamepads have at least 4 axes (2 analog sticks) and 8+ buttons
                num_axes = candidate.get_numaxes()
                num_buttons = candidate.get_numbuttons()
                name = candidate.get_name()

                if num_axes >= 4 and num_buttons >= 8:
                    # This looks like a real gamepad
                    self.joystick = candidate
                    print(f"Gamepad connected: {name} (axes={num_axes}, buttons={num_buttons})")
                    return
                else:
                    # Skip non-gamepad devices (macropads, keyboards, etc.)
                    print(
                        f"Skipping non-gamepad device: {name} (axes={num_axes}, buttons={num_buttons})"
                    )
                    candidate.quit()

            except pygame.error as e:
                print(f"Failed to initialize joystick {i}: {e}")
                continue

        print("No valid gamepad detected")

    def _get_button_edge(self, button_id: int) -> bool:
        """
        Detect button press edge (transition from not pressed to pressed).

        Args:
            button_id: Joystick button ID

        Returns:
            True if button was just pressed this frame
        """
        if not self.joystick:
            return False

        current = self.joystick.get_button(button_id)
        prev = self._prev_button_states.get(button_id, False)
        self._prev_button_states[button_id] = current

        # Return True only on rising edge (not pressed -> pressed)
        return current and not prev

    def update(self, dt: float) -> list[GamepadButton]:
        """
        Update gamepad state and return pressed buttons.

        Args:
            dt: Delta time in seconds

        Returns:
            List of buttons that were just pressed
        """
        pressed: list[GamepadButton] = []

        if not self.joystick:
            return pressed

        try:
            # === ONE-SHOT BUTTONS (debounced, trigger once per press) ===
            # Face buttons (Xbox layout) - with bounds checking
            num_buttons = self.joystick.get_numbuttons()

            if num_buttons > 0 and self._get_button_edge(0):  # A
                pressed.append(GamepadButton.A)
            if num_buttons > 1 and self._get_button_edge(1):  # B
                pressed.append(GamepadButton.B)
            if num_buttons > 2 and self._get_button_edge(2):  # X
                pressed.append(GamepadButton.X)
            if num_buttons > 3 and self._get_button_edge(3):  # Y
                pressed.append(GamepadButton.Y)

            # Bumpers and menu buttons
            if num_buttons > 4 and self._get_button_edge(4):  # LB
                pressed.append(GamepadButton.LB)
            if num_buttons > 5 and self._get_button_edge(5):  # RB
                pressed.append(GamepadButton.RB)
            if num_buttons > 6 and self._get_button_edge(6):  # Back/Select
                pressed.append(GamepadButton.SELECT)
            if num_buttons > 7 and self._get_button_edge(7):  # Start
                pressed.append(GamepadButton.START)

            # === NAVIGATION (D-Pad and Stick with cooldown) ===
            # Update cooldown timer
            if self._navigation_cooldown > 0:
                self._navigation_cooldown -= dt

            # Check D-Pad hat (with bounds checking)
            dpad_pressed = False
            num_hats = self.joystick.get_numhats()

            if num_hats > 0:
                hat = self.joystick.get_hat(0)

                # Check if any D-pad direction is pressed
                if hat[1] != 0 or hat[0] != 0:
                    # D-pad is being held
                    if self._navigation_cooldown <= 0:
                        # Time to trigger
                        if hat[1] > 0:
                            pressed.append(GamepadButton.DPAD_UP)
                        elif hat[1] < 0:
                            pressed.append(GamepadButton.DPAD_DOWN)

                        if hat[0] < 0:
                            pressed.append(GamepadButton.DPAD_LEFT)
                        elif hat[0] > 0:
                            pressed.append(GamepadButton.DPAD_RIGHT)

                        dpad_pressed = True

                        # Set cooldown - use initial delay for first press, then repeat rate
                        if not self._is_repeating:
                            self._navigation_cooldown = self._initial_cooldown
                            self._is_repeating = True
                        else:
                            self._navigation_cooldown = self._repeat_cooldown

                    # Store state for edge detection
                    self._prev_hat_state = hat
                else:
                    # D-pad released - reset repeat state
                    self._is_repeating = False
                    self._prev_hat_state = (0, 0)

            # Check analog stick (only if D-pad not being used) - with bounds checking
            num_axes = self.joystick.get_numaxes()
            if not dpad_pressed and num_axes >= 2:
                axis_x = self.joystick.get_axis(0)
                axis_y = self.joystick.get_axis(1)

                # Determine current stick state
                stick_up = axis_y < -self.deadzone
                stick_down = axis_y > self.deadzone
                stick_left = axis_x < -self.deadzone
                stick_right = axis_x > self.deadzone

                # Check if stick moved in a direction
                if stick_up and not self._prev_axis_state["up"]:
                    pressed.append(GamepadButton.LEFT_STICK_UP)
                if stick_down and not self._prev_axis_state["down"]:
                    pressed.append(GamepadButton.LEFT_STICK_DOWN)
                if stick_left and not self._prev_axis_state["left"]:
                    pressed.append(GamepadButton.LEFT_STICK_LEFT)
                if stick_right and not self._prev_axis_state["right"]:
                    pressed.append(GamepadButton.LEFT_STICK_RIGHT)

                # Update previous states
                self._prev_axis_state["up"] = stick_up
                self._prev_axis_state["down"] = stick_down
                self._prev_axis_state["left"] = stick_left
                self._prev_axis_state["right"] = stick_right

        except pygame.error:
            # Joystick disconnected
            self.joystick = None

        return pressed

    def is_connected(self) -> bool:
        """Check if a gamepad is connected."""
        return self.joystick is not None


class FocusNavigator:
    """
    Navigates focus between UI components.

    Finds the nearest focusable component in a given direction.
    """

    def __init__(self, container: UIContainer):
        """
        Initialize navigator.

        Args:
            container: Root container to search for focusable components
        """
        self.container = container

    def get_focusable_components(self) -> list[UIComponent]:
        """
        Get all focusable components in the container.

        Returns:
            List of focusable components
        """
        focusable = []
        self._collect_focusable(self.container, focusable)
        return focusable

    def _collect_focusable(self, component: UIComponent, result: list) -> None:
        """Recursively collect focusable components."""
        from UI.core.container import UIContainer
        from UI.components.basic import UIButton

        # Check if component can receive focus
        if isinstance(component, UIButton) and component.enabled:
            result.append(component)

        # Recurse into containers
        if isinstance(component, UIContainer):
            for child in component.children:
                self._collect_focusable(child, result)

    def find_next_focus(self, current: UIComponent | None, direction: str) -> UIComponent | None:
        """
        Find the next component to focus in a direction.

        Args:
            current: Currently focused component
            direction: 'up', 'down', 'left', 'right', 'next', 'previous'

        Returns:
            Next focusable component or None
        """
        focusable = self.get_focusable_components()

        if not focusable:
            return None

        if current is None:
            # No current focus, return first focusable
            return focusable[0]

        if current not in focusable:
            return focusable[0]

        current_index = focusable.index(current)

        if direction == "next":
            return focusable[(current_index + 1) % len(focusable)]
        elif direction == "previous":
            return focusable[(current_index - 1) % len(focusable)]
        elif direction in ("up", "down", "left", "right"):
            # Find nearest component in that direction
            return self._find_nearest_in_direction(current, direction, focusable)

        return None

    def _find_nearest_in_direction(
        self, current: UIComponent, direction: str, candidates: list[UIComponent]
    ) -> UIComponent | None:
        """
        Find the nearest component in a spatial direction.

        Args:
            current: Current component
            direction: 'up', 'down', 'left', 'right'
            candidates: List of focusable components

        Returns:
            Nearest component in that direction
        """
        current_center = current.rect.center

        best_candidate = None
        best_distance = float("inf")

        for candidate in candidates:
            if candidate is current:
                continue

            candidate_center = candidate.rect.center

            # Check if candidate is in the right direction
            dx = candidate_center[0] - current_center[0]
            dy = candidate_center[1] - current_center[1]

            is_valid = False
            if direction == "up" and dy < 0:
                is_valid = True
            elif direction == "down" and dy > 0:
                is_valid = True
            elif direction == "left" and dx < 0:
                is_valid = True
            elif direction == "right" and dx > 0:
                is_valid = True

            if is_valid:
                # Calculate distance
                distance = (dx**2 + dy**2) ** 0.5
                if distance < best_distance:
                    best_distance = distance
                    best_candidate = candidate

        return best_candidate
