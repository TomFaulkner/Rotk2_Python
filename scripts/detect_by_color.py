#!/usr/bin/env python3
"""
Detect number boxes by their black-and-white signature.
Number boxes only contain black and white pixels, unlike colored provinces.
"""

import cv2
import numpy as np
from pathlib import Path


def is_black_and_white(region_img, threshold=10):
    """Check if image region only contains black and white (no colors)."""
    # Convert to HSV to check for color saturation
    hsv = cv2.cvtColor(region_img, cv2.COLOR_BGR2HSV)

    # Saturation channel - low saturation means grayscale/black/white
    saturation = hsv[:, :, 1]

    # If most pixels have very low saturation, it's black and white
    # Also check value to ensure we have both black and white (not just gray)
    value = hsv[:, :, 2]

    # Count pixels that are either:
    # - Low saturation (grayscale) AND (very dark OR very bright)
    bw_mask = (saturation < 30) & ((value < 80) | (value > 180))
    bw_ratio = np.sum(bw_mask) / bw_mask.size

    return bw_ratio > 0.85  # 85% black and white


def detect_number_boxes(image_path: str):
    """Detect number boxes using black-and-white signature."""

    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    height, width = img.shape[:2]

    print(f"Image size: {width}x{height}")

    # Step 1: Find all black rectangular regions
    _, black_mask = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)

    # Find connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        black_mask, connectivity=8
    )

    print(f"Found {num_labels - 1} black regions")

    # Step 2: Filter by shape and black-and-white content
    number_boxes = []

    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]

        # Basic size/shape filter
        if not (150 < area < 1500 and 0.6 < w / h < 1.5 and 12 < w < 45 and 12 < h < 45):
            continue

        # Extract region from original image
        region = img[y : y + h, x : x + w]

        # Check if it's black and white only
        if is_black_and_white(region):
            number_boxes.append(
                {"bbox": (x, y, w, h), "center": (int(centroids[i][0]), int(centroids[i][1]))}
            )

    print(f"Found {len(number_boxes)} black-and-white boxes")

    # Step 3: Visualize
    debug_img = img.copy()

    for i, box in enumerate(number_boxes):
        x, y, w, h = box["bbox"]
        cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(debug_img, str(i), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    output_path = Path(image_path).parent / "debug_number_boxes_v2.png"
    cv2.imwrite(str(output_path), debug_img)
    print(f"Saved: {output_path}")

    return number_boxes


if __name__ == "__main__":
    import sys

    image_path = sys.argv[1] if len(sys.argv) > 1 else "./download/snes-map.png"
    detect_number_boxes(image_path)
