#!/usr/bin/env python3
"""
ROTK2 Text Extraction Script

Extracts all Chinese text from the game by:
1. Scanning source code for GetBuiltinText() calls
2. Reading text from DSBUF.DAT
3. Categorizing text by usage context
4. Creating a structured JSON file ready for LLM translation

Output: data/text_extraction.json
"""

import sys
import json
import re
from pathlib import Path
from collections import defaultdict


def setup_environment():
    """Setup paths and change to Src directory."""
    script_dir = Path(__file__).parent.resolve()
    project_dir = script_dir.parent
    src_dir = project_dir / "Src"
    data_dir = project_dir / "data"

    data_dir.mkdir(exist_ok=True)

    # Change to Src directory for imports
    import os

    os.chdir(src_dir)
    sys.path.insert(0, str(src_dir))

    return project_dir, data_dir


def scan_source_files(src_dir):
    """Scan all Python source files for GetBuiltinText calls."""
    print("Scanning source files for text usage...")

    text_usages = defaultdict(list)  # offset -> list of (file, line, context)
    pattern = r"GetBuiltinText\(([^)]+)\)"

    for py_file in src_dir.glob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    matches = re.findall(pattern, line)
                    for match in matches:
                        # Parse offset(s) from match
                        offsets = parse_offset(match)
                        for offset in offsets:
                            # Get context (function/class name if possible)
                            context = get_context(lines, line_num)
                            text_usages[offset].append(
                                {
                                    "file": py_file.name,
                                    "line": line_num,
                                    "context": context,
                                    "code": line.strip(),
                                }
                            )
        except Exception as e:
            print(f"  Warning: Could not read {py_file}: {e}")

    print(f"  Found {len(text_usages)} unique text offsets")
    return text_usages


def parse_offset(match_str):
    """Parse offset value(s) from GetBuiltinText argument."""
    offsets = []

    # Remove spaces
    match_str = match_str.replace(" ", "")

    # Handle range format: 0x609d, 0x60c0
    if "," in match_str:
        parts = match_str.split(",")
        if len(parts) == 2:
            try:
                start = parse_single_offset(parts[0])
                end = parse_single_offset(parts[1])
                # Return just the start offset for text extraction
                offsets.append(start)
            except:
                pass
    else:
        try:
            offset = parse_single_offset(match_str)
            offsets.append(offset)
        except:
            pass

    return offsets


def parse_single_offset(value_str):
    """Parse a single offset value."""
    value_str = value_str.strip()

    # Hex format
    if value_str.startswith("0x"):
        return int(value_str, 16)

    # Try direct integer
    try:
        return int(value_str)
    except:
        pass

    # Handle expressions like 0x609d+5
    if "+" in value_str:
        base, offset = value_str.split("+")
        return parse_single_offset(base) + int(offset)

    raise ValueError(f"Cannot parse offset: {value_str}")


def get_context(lines, line_num):
    """Get function/class context for a line."""
    # Look backward for function/class definition
    for i in range(line_num - 1, max(0, line_num - 20), -1):
        line = lines[i]
        if "def " in line or "class " in line:
            return line.strip()
    return "unknown"


def extract_text_from_databuf(text_usages, Data):
    """Extract actual text from DSBUF.DAT for each offset."""
    print("Extracting Chinese text from DSBUF.DAT...")

    extracted = {}

    for offset in sorted(text_usages.keys()):
        # Validate offset
        if offset < 0 or offset >= len(Data.DSBUF):
            continue

        # Read until null terminator (0x00)
        text_bytes = []
        i = offset
        while i < len(Data.DSBUF) and Data.DSBUF[i] != 0:
            text_bytes.append(Data.DSBUF[i])
            i += 1
            # Safety limit
            if len(text_bytes) > 200:
                break

        # Convert to string representation
        text_str = decode_text_bytes(text_bytes)

        extracted[offset] = {
            "offset": offset,
            "offset_hex": f"0x{offset:04X}",
            "chinese": text_str,
            "length": len(text_bytes),
            "usages": text_usages[offset],
        }

    print(f"  Extracted text for {len(extracted)} offsets")
    return extracted


def decode_text_bytes(byte_list):
    """Decode text bytes to string, handling $index$ format."""
    result = []
    i = 0

    while i < len(byte_list):
        b = byte_list[i]

        # ASCII printable range
        if 0x20 <= b <= 0x7E:
            # Special characters used for formatting
            if b == 0x24:  # '$'
                result.append("$")
            elif b == 0x25:  # '%' - format specifier
                result.append("%")
            elif b == 0x5F:  # '_' - line break
                result.append("_")
            elif b == 0x40:  # '@' - special marker
                result.append("@")
            else:
                result.append(chr(b))
            i += 1

        # Chinese characters (high bytes)
        elif b >= 0x80 and i + 1 < len(byte_list):
            # Two-byte Chinese character reference
            b2 = byte_list[i + 1]
            char_code = b * 256 + b2
            result.append(f"${char_code}$")
            i += 2

        # Control characters
        elif b < 0x20:
            result.append(f"[{b:02X}]")
            i += 1

        else:
            result.append(f"[{b:02X}]")
            i += 1

    return "".join(result)


def categorize_text(extracted_text):
    """Categorize text by usage context and content."""
    print("Categorizing text...")

    categories = {
        "commands": [],
        "prompts": [],
        "labels": [],
        "messages": [],
        "battle": [],
        "time": [],
        "misc": [],
    }

    # Known offset ranges
    command_offsets = list(range(0x609D, 0x60D0, 5))  # Main commands
    month_offsets = list(range(0x5849, 0x5860, 5))  # Month/day

    for offset, data in extracted_text.items():
        category = determine_category(offset, data)
        categories[category].append(data)

    # Print summary
    for cat, items in categories.items():
        print(f"  {cat}: {len(items)} entries")

    return categories


def determine_category(offset, data):
    """Determine text category based on offset and context."""
    # Check context clues
    usages = data.get("usages", [])
    context_str = " ".join([u.get("context", "") for u in usages]).lower()
    code_str = " ".join([u.get("code", "") for u in usages]).lower()

    # Commands (main menu)
    if 0x6090 <= offset <= 0x60F0:
        return "commands"

    # Time/Date
    if 0x5840 <= offset <= 0x5870:
        return "time"

    # Battle-related
    if any(kw in code_str for kw in ["war", "battle", "attack", "fire", "duel"]):
        return "battle"

    # Labels (status display)
    if any(kw in context_str for kw in ["information", "status", "display"]):
        return "labels"

    # Prompts (questions)
    if "?" in data["chinese"] or any(
        kw in code_str for kw in ["input", "select", "choose"]
    ):
        return "prompts"

    # Messages (results, events)
    if any(kw in code_str for kw in ["showdelayedtext", "message", "result"]):
        return "messages"

    return "misc"


def create_translation_template(categories, province_names, officer_names):
    """Create final translation template."""
    print("Creating translation template...")

    template = {
        "metadata": {
            "game": "Romance of the Three Kingdoms II (PC)",
            "source": "DSBUF.DAT",
            "total_entries": 0,
            "created_date": "2026-04-01",
            "translation_status": "pending",
        },
        "glossary": {
            "commands": {
                "command_1": "Move",
                "command_2": "Send",
                "command_3": "War",
                "command_4": "Recruit",
                "command_5": "Personnel",
                "command_8": "Intelligence",
                "command_13": "Diplomatic Negotiations",
                "command_14": "Authorization",
                "command_15": "Trade",
                "command_16": "Territory",
                "command_18": "Map",
                "command_19": "Pass",
            },
            "tactics": {
                "fire": "Fire Attack",
                "ambush": "Ambush",
                "duel": "Duel",
                "rally": "Rally",
                "defend": "Defend",
                "retreat": "Retreat",
            },
            "provinces": province_names,
            "officers_sample": dict(list(officer_names.items())[:10]),  # First 10
        },
        "translations": [],
    }

    # Add all categorized text
    for category, items in categories.items():
        for item in items:
            translation_entry = {
                "text_id": item["offset_hex"],
                "offset": item["offset"],
                "category": category,
                "chinese": item["chinese"],
                "english": "",  # To be filled by LLM
                "context": item["usages"][0]["context"]
                if item["usages"]
                else "unknown",
                "length": item["length"],
                "files": list(set([u["file"] for u in item["usages"]])),
            }
            template["translations"].append(translation_entry)
            template["metadata"]["total_entries"] += 1

    return template


def load_province_names():
    """Load province names from user-provided mapping."""
    # Based on user's list
    province_names = {
        "1": "Youzhou",
        "2": "Youzhou",
        "3": "Youzhou",
        "4": "Bingzhou",
        "5": "Bingzhou",
        "6": "Jizhou",
        "7": "Jizhou",
        "8": "Qingzhou",
        "9": "Yanzhou",
        "10": "Sili",
        "11": "Sili",
        "12": "Sili",
        "13": "Liangzhou",
        "14": "Liangzhou",
        "15": "Liangzhou",
        "16": "Xuzhou",
        "17": "Yuzhou",
        "18": "Yangzhou",
        "19": "Jingzhou",
        "20": "Jingzhou",
        "21": "Jingzhou",
        "22": "Jingzhou",
        "23": "Jingzhou",
        "24": "Yangzhou",
        "25": "Yangzhou",
        "26": "Yangzhou",
        "27": "Yangzhou",
        "28": "Yangzhou",
        "29": "Yizhou",
        "30": "Yizhou",
        "31": "Yizhou",
        "32": "Yizhou",
        "33": "Yizhou",
        "34": "Jiaozhou",
        "35": "Jiaozhou",
        "36": "Jiaozhou",
        "37": "Jiaozhou",
        "38": "Jiaozhou",
        "39": "Jiaozhou",
        "40": "Jiaozhou",
        "41": "Jiaozhou",
    }
    return province_names


def load_officer_names():
    """Load officer names from portrait mapping."""
    project_dir = Path(__file__).parent.parent
    mapping_file = project_dir / "Resources" / "portraits" / "portrait_mapping.json"

    officer_names = {}
    if mapping_file.exists():
        with open(mapping_file, "r", encoding="utf-8") as f:
            mapping = json.load(f)
            for officer_id, data in mapping.items():
                officer_names[officer_id] = data.get("name", f"Officer_{officer_id}")

    return officer_names


def main():
    """Main extraction process."""
    print("=" * 60)
    print("ROTK2 Text Extraction")
    print("=" * 60)
    print()

    # Setup
    project_dir, data_dir = setup_environment()
    src_dir = project_dir / "Src"

    print(f"Project directory: {project_dir}")
    print(f"Source directory: {src_dir}")
    print(f"Data directory: {data_dir}")
    print()

    # Import Data module
    try:
        from Data import Data

        print("✓ Data module loaded")
        print(f"  DSBUF size: {len(Data.DSBUF)} bytes")
        print()
    except Exception as e:
        print(f"✗ Failed to load Data module: {e}")
        return 1

    try:
        # Step 1: Scan source files
        text_usages = scan_source_files(src_dir)
        print()

        # Step 2: Extract text from DSBUF
        extracted_text = extract_text_from_databuf(text_usages, Data)
        print()

        # Step 3: Categorize text
        categories = categorize_text(extracted_text)
        print()

        # Step 4: Load reference data
        province_names = load_province_names()
        officer_names = load_officer_names()
        print(f"✓ Loaded {len(province_names)} province names")
        print(f"✓ Loaded {len(officer_names)} officer names")
        print()

        # Step 5: Create template
        template = create_translation_template(
            categories, province_names, officer_names
        )
        print()

        # Step 6: Save output
        output_file = data_dir / "text_extraction.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=2, ensure_ascii=False)

        file_size = output_file.stat().st_size
        print(f"✓ Saved: {output_file}")
        print(f"  Size: {file_size:,} bytes")
        print(f"  Total text entries: {template['metadata']['total_entries']}")
        print()

        # Summary
        print("=" * 60)
        print("Extraction Complete!")
        print("=" * 60)
        print()
        print("Categories extracted:")
        for cat, items in categories.items():
            print(f"  {cat:12s}: {len(items):3d} entries")
        print()
        print("Next steps:")
        print("  1. Review text_extraction.json")
        print("  2. Use TRANSLATE_PROMPT.md for LLM translation")
        print("  3. Save translated output as text_en_translated.json")
        print()

    except Exception as e:
        print(f"\n✗ Error during extraction: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
