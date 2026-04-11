#!/usr/bin/env python3
"""
Extract province boundaries from SNES map image.

Uses OpenCV to detect black province borders and extract polygon vertices.
"""

import cv2
import numpy as np
import json
from pathlib import Path


def extract_provinces(image_path: str, output_path: str = "data/province_shapes_extracted.json"):
    """Extract province boundaries from SNES map image."""

    print(f"Loading image: {image_path}")
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    print(f"Image size: {img.shape}")
    height, width = img.shape[:2]

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Create debug image
    debug_img = img.copy()

    # Step 1: Detect black regions
    print("\nStep 1: Detecting black regions...")

    # Threshold to find black/dark regions
    _, black_mask = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)

    # Find all contours
    contours, hierarchy = cv2.findContours(black_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    print(f"Found {len(contours)} total contours")

    # Step 2: Separate number boxes from province borders
    print("\nStep 2: Classifying contours...")

    number_boxes = []
    province_contours = []

    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area < 50:
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = float(w) / h if h > 0 else 0

        # Number boxes: small, roughly square
        if 100 < area < 1500 and 0.5 < aspect_ratio < 2.0 and w > 10 and h > 10:
            number_boxes.append(
                {"idx": i, "bbox": (x, y, w, h), "center": (x + w // 2, y + h // 2), "area": area}
            )
        # Province borders: larger
        elif area > 2000:
            province_contours.append({"idx": i, "contour": cnt, "bbox": (x, y, w, h), "area": area})

    print(f"Found {len(number_boxes)} potential number boxes")
    print(f"Found {len(province_contours)} potential province contours")

    # Step 3: Sort number boxes by position
    number_boxes.sort(key=lambda b: (b["center"][1], b["center"][0]))

    # Draw on debug image
    for i, box in enumerate(number_boxes[:50]):
        x, y, w, h = box["bbox"]
        cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(debug_img, str(i), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Save debug image
    debug_path = Path(image_path).parent / "debug_detection.png"
    cv2.imwrite(str(debug_path), debug_img)
    print(f"Saved debug image: {debug_path}")

    print("\nExtraction complete!")
    print(f"Found {len(number_boxes)} number boxes and {len(province_contours)} province contours")

    return number_boxes, province_contours


if __name__ == "__main__":
    import sys

    image_path = sys.argv[1] if len(sys.argv) > 1 else "./download/snes-map.png"
    extract_provinces(image_path)
