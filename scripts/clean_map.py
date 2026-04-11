#!/usr/bin/env python3
"""
Clean the map image by removing province number boxes.
This will give us cleaner province boundaries for extraction.
"""

import cv2
import numpy as np
from pathlib import Path


def clean_map(image_path: str):
    """Remove number boxes from map image."""

    print(f"Loading image: {image_path}")
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    height, width = img.shape[:2]
    print(f"Image size: {width}x{height}")

    # Create a copy to work with
    cleaned = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Step 1: Detect number boxes (black rectangles)
    print("\nStep 1: Detecting number boxes...")

    # Threshold to find black regions
    _, black_mask = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)

    # Find connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        black_mask, connectivity=8
    )

    number_boxes = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        aspect = w / h if h > 0 else 0

        # Number box criteria (similar to before but slightly relaxed)
        if 100 < area < 1500 and 0.5 < aspect < 2.0 and 10 < w < 50 and 10 < h < 50:
            number_boxes.append(
                {"bbox": (x, y, w, h), "center": (int(centroids[i][0]), int(centroids[i][1]))}
            )

    print(f"Found {len(number_boxes)} number boxes")

    # Step 2: Remove number boxes by filling with white
    print("\nStep 2: Removing number boxes...")

    # Expand the boxes slightly to catch the borders
    expand = 3

    for box in number_boxes:
        x, y, w, h = box["bbox"]

        # Expand the rectangle
        x1 = max(0, x - expand)
        y1 = max(0, y - expand)
        x2 = min(width, x + w + expand)
        y2 = min(height, y + h + expand)

        # Fill with white (province color)
        cv2.rectangle(cleaned, (x1, y1), (x2, y2), (255, 255, 255), -1)

    # Step 3: Optional - also remove very small black specks
    print("\nStep 3: Cleaning up small artifacts...")

    gray_cleaned = cv2.cvtColor(cleaned, cv2.COLOR_BGR2GRAY)
    _, small_black = cv2.threshold(gray_cleaned, 50, 255, cv2.THRESH_BINARY_INV)

    # Find small black regions
    num_labels_small, labels_small, stats_small, _ = cv2.connectedComponentsWithStats(
        small_black, connectivity=8
    )

    removed_small = 0
    for i in range(1, num_labels_small):
        area = stats_small[i, cv2.CC_STAT_AREA]
        if area < 100:  # Very small
            x = stats_small[i, cv2.CC_STAT_LEFT]
            y = stats_small[i, cv2.CC_STAT_TOP]
            w = stats_small[i, cv2.CC_STAT_WIDTH]
            h = stats_small[i, cv2.CC_STAT_HEIGHT]
            cv2.rectangle(cleaned, (x, y), (x + w, y + h), (255, 255, 255), -1)
            removed_small += 1

    print(f"Removed {removed_small} small artifacts")

    # Step 4: Save cleaned image
    output_path = Path(image_path).parent / "snes-map-cleaned.png"
    cv2.imwrite(str(output_path), cleaned)
    print(f"\n✓ Saved cleaned image: {output_path}")

    # Step 5: Create comparison
    print("\nStep 5: Creating comparison image...")
    comparison = np.hstack((img, cleaned))

    # Add labels
    cv2.putText(comparison, "Original", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    cv2.putText(
        comparison, "Cleaned", (width + 20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2
    )

    comparison_path = Path(image_path).parent / "comparison.png"
    cv2.imwrite(str(comparison_path), comparison)
    print(f"✓ Saved comparison: {comparison_path}")

    return str(output_path)


if __name__ == "__main__":
    import sys

    image_path = sys.argv[1] if len(sys.argv) > 1 else "./download/snes-map.png"
    clean_map(image_path)
