#!/usr/bin/env python3
"""
ROTK2 Data Extraction Script

Extracts all game data from original binary files to clean JSON format.
This makes development easier by providing structured, human-readable data.

Usage:
    python3 scripts/extract_game_data.py

Output:
    - data/officers.json: All 255 officers with stats
    - data/provinces.json: All 41 provinces with data
    - data/rulers.json: All 16 rulers
    - data/text_en.json: English text mappings
    - data/terrain_data.json: Hex terrain for each province
"""

import sys
import json
import os
from pathlib import Path


def setup_environment():
    """Setup environment and paths."""
    # Get directories
    script_dir = Path(__file__).parent.resolve()
    project_dir = script_dir.parent
    src_dir = project_dir / "Src"
    data_dir = project_dir / "data"

    # Create data directory
    data_dir.mkdir(exist_ok=True)

    # Change to Src directory so Data.py can find Resources
    os.chdir(src_dir)

    # Add Src to path
    sys.path.insert(0, str(src_dir))

    return project_dir, data_dir


def extract_officers(Data, Officer):
    """Extract all officer data to JSON."""
    print("Extracting officer data...")

    officers = []
    max_officers = 255

    for i in range(max_officers):
        try:
            offset = Data.OFFICER_START + Data.OFFICER_SIZE * i
            officer = Officer.FromBuffer(
                Data.BUF[offset : offset + Data.OFFICER_SIZE],
                i,
                Data.BUF[0x45] * 256 + Data.BUF[0x44],  # Current year
            )

            # Extract officer data
            officer_data = {
                "id": i,
                "offset": offset,
                "name_original": officer.GetName(),
                "name_english": None,  # To be filled in later
                "portrait_id": officer.Portrait,
                "stats": {
                    "intelligence": officer.Int,
                    "war": officer.War,
                    "charisma": officer.Chm,
                    "yili": officer.yili,
                    "rende": officer.rende,
                    "yewang": officer.yewang,
                },
                "status": {
                    "ruler_no": officer.RulerNo,
                    "loyalty": officer.Loyalty,
                    "is_sick": officer.IsSick,
                    "sick_month": officer.SickMonth,
                    "can_move": officer.CanMoveNow,
                },
                "military": {
                    "soldiers": officer.Soldiers,
                    "weapons": officer.Weapons,
                    "arms_percentage": officer.Arms,
                    "training": officer.TrainingLevel,
                },
                "personal": {
                    "age": officer.Age,
                    "birth_year": Data.BUF[officer.Offset + 0x19],
                    "compatibility": officer.Compatibility,
                    "xueyuan": officer.xueyuan,
                },
                "special": {
                    "shiwei": officer.shiwei,
                    "spy_ruler": officer.SpyBlongedToRuler,
                    "spy_city": officer.SpyInCityNo,
                },
                "links": {
                    "next_officer_offset": officer.NextOfficerOffset,
                    "is_governor": officer.IsGovernor(),
                    "is_advisor": officer.IsAdvisor(),
                    "is_ruler": officer.IsRuler(),
                },
            }

            officers.append(officer_data)

            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1}/{max_officers} officers...")

        except Exception as e:
            print(f"  Warning: Could not extract officer {i}: {e}")
            continue

    print(f"  ✓ Extracted {len(officers)} officers")
    return officers


def extract_provinces(Data, Province):
    """Extract all province data to JSON."""
    print("Extracting province data...")

    provinces = []
    max_provinces = 41

    for i in range(1, max_provinces + 1):
        try:
            province = Province.FromSequence(i)

            # Get officer list
            officer_list = province.GetOfficerList()
            officer_offsets = [o.Offset for o in officer_list]

            province_data = {
                "id": i,
                "sequence": province.No,
                "offset": province.Offset,
                "name": province.Name,
                "name_index": province.NameIndex,
                "position": {"x": province.X, "y": province.Y},
                "ruler": {
                    "ruler_no": province.RulerNo,
                    "war_ruler_no": getattr(province, "WarRulerNo", None),
                    "governor_offset": getattr(province, "GovernorOffset", None),
                    "free_officers_offset": getattr(province, "FreeOfficersOffset", None),
                },
                "resources": {
                    "gold": getattr(province, "Gold", 0),
                    "food": getattr(province, "Food", 0),
                    "population": getattr(province, "Population", 0),
                },
                "development": {
                    "land_value": getattr(province, "LandValue", 0),
                    "popularity": getattr(province, "Popularity", 0),
                    "flood_control": getattr(province, "FloodControl", 0),
                    "castle": getattr(province, "Castle", 0),
                    "horse_quality": getattr(province, "HorseQuality", 0),
                },
                "economy": {
                    "rice_price": getattr(province, "RicePrice", 0),
                    "has_merchant": getattr(province, "HasMerchant", False),
                },
                "military": {
                    "officer_count": len(officer_list),
                    "officer_offsets": officer_offsets,
                    "total_soldiers": sum(o.Soldiers for o in officer_list),
                },
                "status": {
                    "delegate_mode": getattr(province, "DelegateMode", 0),
                    "war_province": getattr(province, "WarProvince", None),
                    "transport_target": getattr(province, "TransportTarget", None),
                },
                "links": {"next_province_offset": getattr(province, "NextProvinceOffset", None)},
            }

            provinces.append(province_data)

        except Exception as e:
            print(f"  Warning: Could not extract province {i}: {e}")
            import traceback

            traceback.print_exc()
            continue

    print(f"  ✓ Extracted {len(provinces)} provinces")
    return provinces


def extract_rulers(Data, Ruler, Officer):
    """Extract all ruler data to JSON."""
    print("Extracting ruler data...")

    rulers = []
    max_rulers = 16

    for i in range(max_rulers):
        try:
            ruler = Ruler.FromNo(i)

            if ruler.RulerSelf is None:
                continue

            ruler_data = {
                "id": i,
                "offset": ruler.Offset,
                "name": ruler.RulerSelf.GetName() if ruler.RulerSelf else None,
                "leader": {
                    "ruler_offset": ruler.RulerSelf.Offset if ruler.RulerSelf else None,
                    "ruler_name": ruler.RulerSelf.GetName() if ruler.RulerSelf else None,
                },
                "advisor": {
                    "advisor_offset": ruler.AdvisorOffset
                    if hasattr(ruler, "AdvisorOffset")
                    else None,
                    "advisor_name": Officer.FromOffset(ruler.AdvisorOffset).GetName()
                    if (hasattr(ruler, "AdvisorOffset") and ruler.AdvisorOffset > 0)
                    else None,
                },
                "provinces": {
                    "capital_offset": ruler.CapitalOffset
                    if hasattr(ruler, "CapitalOffset")
                    else None,
                    "province_count": len(ruler.GetProvinceList())
                    if hasattr(ruler, "GetProvinceList")
                    else 0,
                    "province_offsets": ruler.GetProvinceList()
                    if hasattr(ruler, "GetProvinceList")
                    else [],
                },
                "diplomacy": {
                    "trust_levels": list(ruler.TrustLevel) if hasattr(ruler, "TrustLevel") else [],
                    "hostility_levels": list(ruler.HostilityLevel)
                    if hasattr(ruler, "HostilityLevel")
                    else [],
                    "alliances": [],
                },
                "status": {
                    "magic": ruler.Magic if hasattr(ruler, "Magic") else 0,
                    "marriage": ruler.Marriage if hasattr(ruler, "Marriage") else 0,
                    "is_wandering": ruler.IsWandering if hasattr(ruler, "IsWandering") else False,
                },
            }

            rulers.append(ruler_data)

        except Exception as e:
            print(f"  Warning: Could not extract ruler {i}: {e}")
            continue

    print(f"  ✓ Extracted {len(rulers)} rulers")
    return rulers


def extract_terrain_data(Data):
    """Extract hex terrain data for all provinces."""
    print("Extracting terrain data...")

    terrain_data = {}
    max_provinces = 41

    terrain_names = {
        0x00: "plains",
        0x01: "forest",
        0x02: "hills",
        0x03: "water",
        0x04: "castle",
        0x05: "special",
        0x06: "obstacle",
        0x09: "edge",
        0x99: "empty",
    }

    for province_no in range(1, max_provinces + 1):
        try:
            # Read 156 bytes (12x13 grid)
            index = 0x33B9 + 156 * (province_no - 1) + 0x38
            map_bytes = Data.BUF[index : index + 156]

            # Convert to 12x13 grid
            grid = []
            for row in range(12):
                row_data = []
                for col in range(13):
                    byte_idx = row * 13 + col
                    if byte_idx < len(map_bytes):
                        terrain_code = map_bytes[byte_idx]
                        row_data.append(
                            {
                                "code": terrain_code,
                                "name": terrain_names.get(terrain_code, "unknown"),
                            }
                        )
                    else:
                        row_data.append({"code": 0x99, "name": "empty"})
                grid.append(row_data)

            terrain_data[province_no] = {
                "province_id": province_no,
                "grid_size": {"rows": 12, "cols": 13},
                "terrain_grid": grid,
                "terrain_counts": {},
            }

            # Count terrain types
            terrain_counts = {}
            for row in grid:
                for cell in row:
                    name = cell["name"]
                    terrain_counts[name] = terrain_counts.get(name, 0) + 1
            terrain_data[province_no]["terrain_counts"] = terrain_counts

        except Exception as e:
            print(f"  Warning: Could not extract terrain for province {province_no}: {e}")
            continue

    print(f"  ✓ Extracted terrain data for {len(terrain_data)} provinces")
    return terrain_data


def create_english_mappings():
    """Create template for English text mappings."""
    print("Creating English text template...")

    english_names = {}

    english_commands = {
        "command_1": "Move",
        "command_2": "Transport",
        "command_3": "War",
        "command_4": "Recruit",
        "command_5": "Personnel",
        "command_6": "Council",
        "command_7": "Strategy",
        "command_8": "Intelligence",
        "command_9": "View",
        "command_10": "View2",
        "command_11": "Orders",
        "command_12": "View3",
        "command_13": "Diplomacy",
        "command_14": "Delegate",
        "command_15": "Market",
        "command_16": "Territory",
        "command_17": "Save",
        "command_18": "Map",
        "command_19": "End",
    }

    text_data = {
        "officer_names": english_names,
        "commands": english_commands,
        "ui_text": {},
        "tactics": {
            "fire": "Fire Attack",
            "ambush": "Ambush",
            "duel": "Duel",
            "rally": "Rally",
            "defend": "Defend",
            "retreat": "Retreat",
        },
    }

    print("  ✓ Created English text template")
    return text_data


def save_json(data, filename, data_dir):
    """Save data to JSON file with nice formatting."""
    filepath = data_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    file_size = filepath.stat().st_size
    print(f"  Saved: {filename} ({file_size:,} bytes)")


def main():
    """Main extraction function."""
    print("=" * 60)
    print("ROTK2 Game Data Extraction")
    print("=" * 60)
    print()

    # Setup environment
    project_dir, data_dir = setup_environment()
    print(f"Project directory: {project_dir}")
    print(f"Data directory: {data_dir}")
    print()

    # Now import the game modules (after changing to Src directory)
    print("Loading game data modules...")
    try:
        from Data import Data
        from Officer import Officer
        from Province import Province
        from Ruler import Ruler

        print("  ✓ Modules loaded successfully")
        print()
    except Exception as e:
        print(f"  ❌ Failed to load modules: {e}")
        import traceback

        traceback.print_exc()
        return 1

    # Extract all data
    try:
        officers = extract_officers(Data, Officer)
        save_json(officers, "officers.json", data_dir)
        print()

        provinces = extract_provinces(Data, Province)
        save_json(provinces, "provinces.json", data_dir)
        print()

        rulers = extract_rulers(Data, Ruler, Officer)
        save_json(rulers, "rulers.json", data_dir)
        print()

        terrain = extract_terrain_data(Data)
        save_json(terrain, "terrain_data.json", data_dir)
        print()

        english_text = create_english_mappings()
        save_json(english_text, "text_en.json", data_dir)
        print()

        # Create summary
        summary = {
            "extraction_date": "2026-04-01",
            "total_officers": len(officers),
            "total_provinces": len(provinces),
            "total_rulers": len(rulers),
            "terrain_provinces": len(terrain),
            "notes": [
                "English names need to be filled in manually",
                "Some officer data may be missing or corrupted",
                "Terrain data extracted from hex maps",
            ],
        }
        save_json(summary, "extraction_summary.json", data_dir)
        print()

        print("=" * 60)
        print("Extraction Complete!")
        print("=" * 60)
        print(f"\nAll files saved to: {data_dir}")
        print("\nNext steps:")
        print("  1. Fill in English officer names in data/text_en.json")
        print("  2. Begin battle system implementation")
        print("  3. Test data loading in new modules")

    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
