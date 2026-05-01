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


def _get_raw_officer_name(officer) -> str | None:
    """Read the officer's raw runtime name token from the legacy buffer."""
    offset = getattr(officer, "Offset", 0)
    if not isinstance(offset, int) or offset <= 0:
        return None

    raw_name = ""
    index = 0
    while True:
        if index > 12:
            break
        value = Data.BUF[offset + 0x1C + index]
        if value == 0:
            break

        if value < 0x80:
            raw_name += chr(value)
            index += 1
            continue

        pair = value * 256 + Data.BUF[offset + 0x1C + index + 1]
        if pair not in [0xD8F0, 0xD8F1, 0xD8F2, 0xD8F3, 0xD8F4, 0xD8F5]:
            raw_name += "$" + str(Data.CNINDEX[pair]) + "$"
        else:
            raw_name += "$" + str(pair) + "$"
        index += 2

    return raw_name or None


def get_officer_display_name(officer) -> str:
    """Return a display-safe officer name, preferring English mappings."""
    if not officer:
        return "Unknown"

    raw_name = _get_raw_officer_name(officer) or getattr(officer, "Name", None)
    if isinstance(raw_name, str):
        mapped_name = RAW_NAME_MAP.get(raw_name)
        if mapped_name:
            return mapped_name

    try:
        officer_id = (officer.Offset - Data.OFFICER_START) // Data.OFFICER_SIZE
        return get_officer_name(officer_id)
    except Exception:
        return getattr(officer, "Name", "Unknown")
