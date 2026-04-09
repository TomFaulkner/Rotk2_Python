"""
ROTK2 UI Framework

A custom UI framework for ROTK2 Python supporting dual modes
(Classic 640x400 and Modern 1280x800) with gamepad support.
"""

from __future__ import annotations

# Core exports
from UI.core.anchor import Anchor, Alignment, FocusDirection, InputMode, UIMode

__version__ = "0.1.0"
__all__ = [
    "Anchor",
    "Alignment",
    "FocusDirection",
    "InputMode",
    "UIMode",
]
