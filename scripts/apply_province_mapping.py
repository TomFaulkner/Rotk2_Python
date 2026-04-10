#!/usr/bin/env python3
"""
Apply the province mapping to generate the final province_shapes.json.
Run this after you've filled in the mapping.
"""

import json
from pathlib import Path


def apply_mapping():
    # Load raw extraction
    with open("data/provinces_raw_extraction.json") as f:
        raw_provinces = json.load(f)

    # Load mapping
    with open("data/province_mapping.json") as f:
        mapping_data = json.load(f)

    # Build lookup
    temp_to_province = {}
    for m in mapping_data.get("mappings", []):
        temp_id = m.get("temp_id")
        province_id = m.get("province_id")
        if temp_id is not None and province_id is not None:
            temp_to_province[temp_id] = {
                "id": province_id,
                "name": m.get("province_name", f"Province-{province_id}"),
            }

    # Check completeness
    unmapped = [p["temp_id"] for p in raw_provinces if p["temp_id"] not in temp_to_province]
    if unmapped:
        print(f"INFO: {len(unmapped)} regions not mapped (likely fragments): {unmapped}")
        print("Continuing with mapped provinces only...")

    # Build temp_id lookup for raw data
    raw_by_temp = {p["temp_id"]: p for p in raw_provinces}

    # Build final province data
    provinces = {}
    for temp_id, prov_info in temp_to_province.items():
        if temp_id not in raw_by_temp:
            print(f"Warning: temp_id {temp_id} not found in raw data")
            continue

        raw = raw_by_temp[temp_id]
        province_id = prov_info["id"]

        provinces[str(province_id)] = {
            "id": province_id,
            "name": prov_info["name"],
            "points": raw["points"],
            "center": [round(raw["centroid"][0]), round(raw["centroid"][1])],
            "number_position": [round(raw["centroid"][0]), round(raw["centroid"][1])],
            "neighbors": [],  # Will calculate
            "terrain_features": [],
            "area": raw["area"],
        }

    # Calculate neighbors based on proximity
    print("\nCalculating neighbors...")
    province_list = list(provinces.values())
    for i, p1 in enumerate(province_list):
        neighbors = []
        x1, y1 = p1["center"]

        for j, p2 in enumerate(province_list):
            if i == j:
                continue

            x2, y2 = p2["center"]
            dist = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

            # If centers are close, consider them neighbors
            if dist < 180:
                neighbors.append(p2["id"])

        p1["neighbors"] = sorted(neighbors)[:10]

    # Build final output
    output = {
        "version": "6.0",
        "description": "SNES map provinces extracted from clean numbers-removed.jpg with manual mapping",
        "source_image": "numbers-removed.jpg",
        "map_dimensions": {"width": 1024, "height": 896, "offset_x": 0, "offset_y": 0},
        "provinces": provinces,
    }

    # Save
    output_path = Path("data/province_shapes.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved to: {output_path}")
    print(f"  Total provinces: {len(provinces)}")

    # Validate
    ids = sorted([int(k) for k in provinces.keys()])
    print(f"  Province IDs: {ids}")

    missing = set(range(1, 42)) - set(ids)
    if missing:
        print(f"\nWARNING: Missing provinces: {sorted(missing)}")
    else:
        print(f"\nAll 41 provinces present!")


if __name__ == "__main__":
    apply_mapping()
