"""
PortraitLoader - SNES Portrait Management for ROTK2

Loads and manages officer portraits from the SNES version of the game.
Maps officer IDs to portrait files and provides fallback options.
"""

import csv
import json
import os
from pathlib import Path
import pygame
from typing import Optional, Dict, Tuple


class PortraitLoader:
    """
    Manages loading and caching of officer portraits.

    Usage:
        loader = PortraitLoader()
        portrait_surface = loader.get_portrait(officer_id=0)  # Cao Cao
    """

    def __init__(self, resources_path: str = "../Resources"):
        """
        Initialize the portrait loader.

        Args:
            resources_path: Path to Resources directory
        """
        self.resources_path = Path(resources_path)
        self.portraits_path = self.resources_path / "portraits"

        # Mapping dictionaries
        self.officer_to_portrait: Dict[int, int] = {}  # officer_id -> portrait_id
        self.officer_to_name: Dict[int, str] = {}  # officer_id -> name
        self.portrait_to_file: Dict[int, str] = {}  # portrait_id -> filename

        # Cache for loaded images
        self._cache: Dict[int, pygame.Surface] = {}

        # Load mappings
        self._load_csv_mapping()
        self._build_portrait_index()

        print(f"PortraitLoader: Loaded {len(self.officer_to_portrait)} officer mappings")
        print(f"PortraitLoader: Found {len(self.portrait_to_file)} portrait files")

    def _load_csv_mapping(self):
        """Load officer ID to portrait ID mapping from CSV."""
        # Try multiple locations for the CSV
        csv_paths = [
            self.resources_path / "portraits" / "officer-data.csv",
            Path(
                "../download/romance-of-the-three-kingdoms-ii-portraits-snes/data/officer-data.csv"
            ),
            Path("download/romance-of-the-three-kingdoms-ii-portraits-snes/data/officer-data.csv"),
        ]

        csv_file = None
        for path in csv_paths:
            if path.exists():
                csv_file = path
                break

        if csv_file is None:
            print("Warning: Could not find officer-data.csv, using default mapping")
            self._create_default_mapping()
            return

        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        officer_id = int(row["officer_id"])
                        portrait_id = int(row["portrait_id"])
                        name = row["name"]

                        self.officer_to_portrait[officer_id] = portrait_id
                        self.officer_to_name[officer_id] = name
                    except (KeyError, ValueError) as e:
                        print(f"Warning: Could not parse row: {row}, error: {e}")
                        continue
        except Exception as e:
            print(f"Error loading CSV: {e}")
            self._create_default_mapping()

    def _create_default_mapping(self):
        """Create a basic mapping if CSV is not available."""
        # Some well-known officers
        defaults = {
            0: (103, "Cao Cao"),
            1: (161, "Liu Bei"),
            2: (1, "Sun Jian"),
            3: (3, "Yuan Shao"),
            4: (74, "Yuan Shu"),
        }
        for officer_id, (portrait_id, name) in defaults.items():
            self.officer_to_portrait[officer_id] = portrait_id
            self.officer_to_name[officer_id] = name

    def _build_portrait_index(self):
        """Build index of available portrait files."""
        # Index unique portraits
        unique_path = self.portraits_path / "unique"
        if unique_path.exists():
            for file in unique_path.glob("*.png"):
                # Parse filename: Name_ID_PortraitID.png
                try:
                    parts = file.stem.split("_")
                    if len(parts) >= 3:
                        officer_id = int(parts[-2])
                        portrait_id = int(parts[-1])
                        self.portrait_to_file[portrait_id] = str(file)
                except (ValueError, IndexError):
                    continue

        # Also index by officer ID from filename
        if unique_path.exists():
            for file in unique_path.glob("*.png"):
                try:
                    parts = file.stem.split("_")
                    if len(parts) >= 3:
                        officer_id = int(parts[-2])
                        portrait_id = int(parts[-1])
                        self.portrait_to_file[officer_id] = str(file)
                except (ValueError, IndexError):
                    continue

    def get_portrait(
        self, officer_id: int, size: Optional[Tuple[int, int]] = None
    ) -> Optional[pygame.Surface]:
        """
        Get portrait for an officer by ID.

        Args:
            officer_id: The officer's ID (0-254)
            size: Optional (width, height) to resize to

        Returns:
            pygame.Surface with the portrait, or None if not found
        """
        # Check cache first
        cache_key = (officer_id, size)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Try to find portrait file
        portrait_file = self._find_portrait_file(officer_id)

        if portrait_file is None:
            # Fall back to generic portrait
            portrait_file = self._get_generic_portrait(officer_id)

        if portrait_file is None:
            return None

        try:
            # Load and optionally resize
            image = pygame.image.load(portrait_file)

            if size is not None:
                image = pygame.transform.scale(image, size)

            # Cache and return
            self._cache[cache_key] = image
            return image

        except Exception as e:
            print(f"Error loading portrait for officer {officer_id}: {e}")
            return None

    def _find_portrait_file(self, officer_id: int) -> Optional[str]:
        """Find portrait file for an officer."""
        # Method 1: Direct filename lookup by officer ID
        unique_path = self.portraits_path / "unique"
        if unique_path.exists():
            # Look for file ending with _{officer_id}_{portrait_id}.png
            for file in unique_path.glob(f"*_{officer_id}_*.png"):
                return str(file)

        # Method 2: Look up by portrait ID
        portrait_id = self.officer_to_portrait.get(officer_id)
        if portrait_id is not None:
            # Try to find by portrait ID
            for file in unique_path.glob(f"*_*_{portrait_id}.png"):
                return str(file)

        return None

    def _get_generic_portrait(self, officer_id: int) -> Optional[str]:
        """Get a generic portrait as fallback."""
        generic_path = self.portraits_path / "generic"
        if not generic_path.exists():
            return None

        # Select generic portrait based on officer ID
        # This ensures same officer always gets same generic portrait
        generic_files = sorted(generic_path.glob("*.png"))
        if not generic_files:
            return None

        index = officer_id % len(generic_files)
        return str(generic_files[index])

    def get_officer_name(self, officer_id: int) -> str:
        """Get the English name for an officer."""
        return self.officer_to_name.get(officer_id, f"Officer #{officer_id}")

    def get_portrait_id(self, officer_id: int) -> Optional[int]:
        """Get the portrait ID for an officer."""
        return self.officer_to_portrait.get(officer_id)

    def preload_portraits(self, officer_ids: list):
        """Preload multiple portraits into cache."""
        for officer_id in officer_ids:
            self.get_portrait(officer_id)

    def clear_cache(self):
        """Clear the portrait cache to free memory."""
        self._cache.clear()

    def create_portrait_mapping_json(self, output_path: Optional[str] = None):
        """
        Create a JSON file mapping officer IDs to portrait info.
        Useful for debugging and external tools.
        """
        if output_path is None:
            output_path = self.portraits_path / "portrait_mapping.json"

        mapping = {}
        for officer_id in range(255):
            portrait_id = self.officer_to_portrait.get(officer_id)
            name = self.officer_to_name.get(officer_id)

            if portrait_id is not None:
                mapping[officer_id] = {
                    "name": name,
                    "portrait_id": portrait_id,
                    "file": self._find_portrait_file(officer_id),
                }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=2)

        print(f"Created portrait mapping: {output_path}")
        return mapping


def test_portrait_loader():
    """Test the portrait loader."""
    import sys

    print("Testing PortraitLoader...")
    print(f"Python path: {sys.path}")

    # Initialize pygame
    pygame.init()

    # Create loader
    loader = PortraitLoader()

    # Test loading some portraits
    test_officers = [0, 1, 2, 3, 4]  # Cao Cao, Liu Bei, Sun Jian, Yuan Shao, Yuan Shu

    print("\nTesting portrait loading:")
    for officer_id in test_officers:
        name = loader.get_officer_name(officer_id)
        portrait_id = loader.get_portrait_id(officer_id)
        portrait = loader.get_portrait(officer_id)

        if portrait:
            print(
                f"  Officer {officer_id} ({name}): Portrait {portrait_id}, Size {portrait.get_size()} - ✓"
            )
        else:
            print(f"  Officer {officer_id} ({name}): Portrait {portrait_id} - ✗ Not found")

    # Test generic fallback
    print("\nTesting generic fallback (officer 100):")
    portrait = loader.get_portrait(100)
    if portrait:
        print(f"  Generic portrait loaded: Size {portrait.get_size()} - ✓")

    # Create mapping file
    print("\nCreating portrait mapping JSON...")
    loader.create_portrait_mapping_json()

    print("\nTest complete!")
    pygame.quit()


if __name__ == "__main__":
    test_portrait_loader()
