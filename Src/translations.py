"""
ROTK2 Translation System

Handles loading and lookup of English translations.
Falls back to Chinese text when English translation is not available.
Tracks untranslated strings for future translation work.
"""

from __future__ import annotations

import json
import os
from typing import Any

# Path to translation files
TRANSLATION_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "text_en_translated.json")
UNTRANSLATED_LOG = os.path.join(os.path.dirname(__file__), "..", "untranslated.md")


class TranslationManager:
    """Manages game text translations."""

    def __init__(self) -> None:
        """Initialize the translation manager."""
        self._translations: dict[int, str] = {}  # offset -> english text
        self._untranslated: set[int] = set()  # offsets we've seen that lack translations
        self._untranslated_logged: set[int] = set()  # offsets already logged to file
        self._loaded = False
        self._language = "zh"  # Default to Chinese

    def load_translations(self) -> None:
        """Load English translations from JSON file."""
        if self._loaded:
            return

        try:
            with open(TRANSLATION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Build lookup dictionary from translations array
            for entry in data.get("translations", []):
                offset = entry.get("offset")
                english = entry.get("english", "")

                if offset is not None and english and english != entry.get("chinese", ""):
                    self._translations[offset] = english

            self._loaded = True
            print(f"Loaded {len(self._translations)} English translations")

        except FileNotFoundError:
            print(f"Warning: Translation file not found: {TRANSLATION_FILE}")
        except json.JSONDecodeError as e:
            print(f"Error parsing translation file: {e}")

    def set_language(self, language: str) -> None:
        """
        Set the current language.

        Args:
            language: 'zh' for Chinese, 'en' for English
        """
        self._language = language.lower()
        if self._language == "en" and not self._loaded:
            self.load_translations()

    def get_text(self, offset: int, chinese_text: str) -> str:
        """
        Get text for the given offset.

        Args:
            offset: Byte offset in DSBUF
            chinese_text: The original Chinese text as fallback

        Returns:
            English translation if available and language is English,
            otherwise the original Chinese text
        """
        # If language is Chinese, return Chinese text immediately
        if self._language != "en":
            return chinese_text

        # Ensure translations are loaded
        if not self._loaded:
            self.load_translations()

        # Look up English translation by offset
        english = self._translations.get(offset)

        if english:
            # Post-process English text for rendering compatibility
            # Replace newlines with __ (double underscore) to match Chinese format
            # Chinese text uses [0A][0A] which becomes __ after GetBuiltinText
            processed = english.replace("\n", "__")
            return processed

        # Track untranslated strings
        if offset not in self._untranslated:
            self._untranslated.add(offset)
            self._log_untranslated(offset, chinese_text)

        return chinese_text

    def _log_untranslated(self, offset: int, chinese_text: str) -> None:
        """
        Log an untranslated string to the untranslated.md file.

        Args:
            offset: Byte offset in DSBUF
            chinese_text: The Chinese text that needs translation
        """
        # Avoid logging the same offset twice
        if offset in self._untranslated_logged:
            return

        self._untranslated_logged.add(offset)

        try:
            # Append to untranslated.md
            with open(UNTRANSLATED_LOG, "a", encoding="utf-8") as f:
                # Clean up Chinese text for display
                display_text = chinese_text.replace("_", " ").replace("@", "").strip()
                if display_text:
                    f.write(f"- Offset 0x{offset:04X} ({offset}): `{display_text}`\n")
        except IOError:
            # Silent fail - logging untranslated strings is not critical
            pass

    def get_stats(self) -> dict[str, Any]:
        """
        Get translation statistics.

        Returns:
            Dictionary with translation stats
        """
        return {
            "language": self._language,
            "translations_loaded": len(self._translations),
            "untranslated_encountered": len(self._untranslated),
        }

    def clear_untranslated_log(self) -> None:
        """Clear the untranslated.md file."""
        try:
            with open(UNTRANSLATED_LOG, "w", encoding="utf-8") as f:
                f.write("# Untranslated Strings\n\n")
                f.write("This file tracks Chinese text strings that were encountered ")
                f.write("but do not have English translations yet.\n\n")
                f.write("## Format\n\n")
                f.write("- Offset 0xXXXX (decimal): `Chinese text`\n\n")
                f.write("## Strings\n\n")
            self._untranslated_logged.clear()
        except IOError:
            pass


# Global translation manager instance
_translation_manager: TranslationManager | None = None


def get_translation_manager() -> TranslationManager:
    """
    Get the global translation manager instance.

    Returns:
        TranslationManager instance
    """
    global _translation_manager
    if _translation_manager is None:
        _translation_manager = TranslationManager()
    return _translation_manager


def set_language(language: str) -> None:
    """
    Set the game language.

    Args:
        language: 'zh' for Chinese, 'en' for English
    """
    manager = get_translation_manager()
    manager.set_language(language)

    # Clear and initialize untranslated log when switching to English
    if language.lower() == "en":
        manager.clear_untranslated_log()


def get_text(offset: int, chinese_text: str) -> str:
    """
    Get translated text for the given offset.

    Args:
        offset: Byte offset in DSBUF
        chinese_text: The original Chinese text as fallback

    Returns:
        English translation if available, otherwise Chinese text
    """
    return get_translation_manager().get_text(offset, chinese_text)


def get_stats() -> dict[str, Any]:
    """Get translation statistics."""
    return get_translation_manager().get_stats()


# Initialize on module load
def initialize_from_config() -> None:
    """Initialize translations from config settings."""
    try:
        from config import get_settings

        settings = get_settings()
        set_language(settings.language.value)
    except Exception:
        # Default to Chinese if config fails
        set_language("zh")


# Auto-initialize when module is imported
initialize_from_config()

if __name__ == "__main__":
    # Test the translation system
    print("Testing translation system...")

    # Test Chinese mode
    set_language("zh")
    text = get_text(0x3D7D, "$37802$$37769$$41561$")
    print(f"Chinese mode (0x3D7D): {text}")

    # Test English mode
    set_language("en")
    text = get_text(0x3D7D, "$37802$$37769$$41561$")
    print(f"English mode (0x3D7D): {text}")

    # Test untranslated
    text = get_text(0x9999, "$12345$$67890$")
    print(f"Untranslated (0x9999): {text}")

    # Show stats
    print(f"\nStats: {get_stats()}")
