"""Shared officer display helpers for non-battle UI."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from Battle.officer_names import get_officer_name
from Data import Data


def _load_raw_name_map() -> dict[str, str]:
    """Load raw runtime-name token to English name mapping."""
    project_root = Path(__file__).resolve().parent.parent
    officers_json_path = project_root / "data" / "officers.json"
    officer_csv_path = (
        project_root
        / "download"
        / "romance-of-the-three-kingdoms-ii-portraits-snes"
        / "data"
        / "officer-data.csv"
    )

    if not officers_json_path.exists() or not officer_csv_path.exists():
        return {}

    try:
        with officers_json_path.open("r", encoding="utf-8") as officers_file:
            officers_data = json.load(officers_file)
        with officer_csv_path.open("r", encoding="utf-8") as csv_file:
            csv_rows = list(csv.DictReader(csv_file))
    except Exception:
        return {}

    english_by_id: dict[int, str] = {}
    for row in csv_rows:
        try:
            officer_id = int(row["officer_id"])
        except (KeyError, TypeError, ValueError):
            continue

        name = row.get("name")
        if name:
            english_by_id[officer_id] = name

    raw_name_map: dict[str, str] = {}
    for officer_entry in officers_data:
        officer_id = officer_entry.get("id")
        raw_name = officer_entry.get("name_original")
        english_name = english_by_id.get(officer_id)
        if isinstance(raw_name, str) and english_name:
            raw_name_map[raw_name] = english_name

    return raw_name_map


RAW_NAME_MAP = _load_raw_name_map()


def get_officer_display_name(officer) -> str:
    """Return a display-safe officer name, preferring English mappings."""
    if not officer:
        return "Unknown"

    raw_name = getattr(officer, "Name", None)
    if isinstance(raw_name, str):
        mapped_name = RAW_NAME_MAP.get(raw_name)
        if mapped_name:
            return mapped_name

    try:
        officer_id = (officer.Offset - Data.OFFICER_START) // Data.OFFICER_SIZE
        return get_officer_name(officer_id)
    except Exception:
        return getattr(officer, "Name", "Unknown")
