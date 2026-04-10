#!/usr/bin/env python3
"""
Extract province polygons from the clean numbers-removed.jpg image.
Creates a mapping template that the user can fill in to assign province IDs.
"""

import cv2
import json
import numpy as np
from pathlib import Path
from typing import List, Dict


def extract_provinces_clean(image_path: str) -> List[Dict]:
    """
    Extract province polygons from the clean black-and-white border image.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    print(f"Image loaded: {img.shape}")

    # Convert to grayscale and binary
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    # Use connected components to find white regions
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

    print(f"Found {num_labels - 1} white regions (excluding background)")

    provinces = []

    for i in range(1, num_labels):  # Skip background (0)
        area = stats[i, cv2.CC_STAT_AREA]
        x, y, w, h = (
            stats[i, cv2.CC_STAT_LEFT],
            stats[i, cv2.CC_STAT_TOP],
            stats[i, cv2.CC_STAT_WIDTH],
            stats[i, cv2.CC_STAT_HEIGHT],
        )
        cx, cy = centroids[i]

        # Filter out very small regions (noise) and very large regions (background)
        if area < 800:  # Too small
            print(f"  Skipping small region {i}: area={area}")
            continue
        if area > 50000:  # Too large - likely background
            print(f"  Skipping large region {i}: area={area}")
            continue
        if w > 400 or h > 400:  # Unusually large
            print(f"  Skipping oversized region {i}: {w}x{h}")
            continue

        # Create mask for this component
        mask = (labels == i).astype(np.uint8) * 255

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            continue

        # Get the main contour
        contour = max(contours, key=cv2.contourArea)

        # Simplify the contour
        epsilon = 0.005 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # Extract points
        points = [[int(pt[0][0]), int(pt[0][1])] for pt in approx]

        if len(points) < 3:
            print(f"  Region {i}: too few points ({len(points)}), skipping")
            continue

        province = {
            "temp_id": i,
            "area": int(area),
            "centroid": [float(cx), float(cy)],
            "bbox": [int(x), int(y), int(w), int(h)],
            "points": points,
            "num_points": len(points),
        }
        provinces.append(province)
        print(f"  Region {i}: area={area}, points={len(points)}, at ({cx:.0f}, {cy:.0f})")

    print(f"\nTotal provinces found: {len(provinces)}")

    if len(provinces) != 41:
        print(f"WARNING: Expected 41 provinces, found {len(provinces)}")

    return sorted(provinces, key=lambda p: p["area"], reverse=True)


def create_mapping_template(provinces: List[Dict]) -> Dict:
    """Create a template JSON for mapping temp_ids to province_ids."""

    mapping = {
        "description": "Map temp_id (from extraction) to province_id (1-41)",
        "instructions": "Edit the 'province_id' field for each entry. Use the preview image to identify provinces.",
        "image": "download/province_mapping_preview.png",
        "mappings": [],
    }

    for p in provinces:
        mapping["mappings"].append(
            {
                "temp_id": p["temp_id"],
                "area": p["area"],
                "centroid": [round(p["centroid"][0]), round(p["centroid"][1])],
                "province_id": None,
                "province_name": "",
            }
        )

    return mapping


def create_preview_image(image_path: str, provinces: List[Dict]):
    """Create a visualization with temp_ids labeled."""
    img = cv2.imread(image_path)
    viz = img.copy()

    # Sort provinces by temp_id for consistent display
    sorted_provinces = sorted(provinces, key=lambda p: p["temp_id"])

    for p in sorted_provinces:
        # Draw polygon outline
        points = np.array(p["points"], np.int32)
        points = points.reshape((-1, 1, 2))
        cv2.polylines(viz, [points], True, (0, 255, 0), 2)

        # Draw centroid
        cx, cy = int(p["centroid"][0]), int(p["centroid"][1])
        cv2.circle(viz, (cx, cy), 5, (0, 0, 255), -1)

        # Draw temp_id
        text = str(p["temp_id"])
        (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(
            viz,
            (cx - text_w // 2 - 3, cy - text_h // 2 - 3),
            (cx + text_w // 2 + 3, cy + text_h // 2 + 3),
            (255, 255, 255),
            -1,
        )
        cv2.putText(
            viz,
            text,
            (cx - text_w // 2, cy + text_h // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 0, 0),
            2,
        )

    output_path = Path("download/province_mapping_preview.png")
    cv2.imwrite(str(output_path), viz)
    print(f"\nPreview saved to: {output_path}")
    print("Use this image to identify which temp_id corresponds to which province 1-41")


def main():
    image_path = "download/numbers-removed.jpg"
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("Province Extraction from Clean Image")
    print("=" * 60)

    # Extract provinces
    print("\nExtracting provinces...")
    provinces = extract_provinces_clean(image_path)

    # Save raw extraction
    raw_output = output_dir / "provinces_raw_extraction.json"
    with open(raw_output, "w") as f:
        json.dump(provinces, f, indent=2)
    print(f"\nRaw extraction saved to: {raw_output}")

    # Create mapping template
    mapping = create_mapping_template(provinces)
    mapping_output = output_dir / "province_mapping.json"
    with open(mapping_output, "w") as f:
        json.dump(mapping, f, indent=2)
    print(f"Mapping template saved to: {mapping_output}")

    # Create preview image
    create_preview_image(image_path, provinces)

    print("\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Open: download/province_mapping_preview.png")
    print("   This shows each extracted province with its temp_id")
    print("2. Edit: data/province_mapping.json")
    print("   Fill in 'province_id' (1-41) for each temp_id")
    print("3. Run: python scripts/apply_province_mapping.py")
    print("   This creates the final data/province_shapes.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
