#!/usr/bin/env python3
"""
Find the missing province 40.
"""

import cv2
import numpy as np
import json
from pathlib import Path


def find_missing_province(image_path: str):
    """Try to detect province 40 specifically."""

    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    height, width = img.shape[:2]

    # Province 40 should be in the bottom center area
    # Based on the map, it's roughly at (400, 650) to (480, 720)

    # Define ROI for province 40 area
    roi_y1, roi_y2 = 600, 750
    roi_x1, roi_x2 = 350, 520

    roi = gray[roi_y1:roi_y2, roi_x1:roi_x2]

    print(f"Searching for province 40 in ROI: ({roi_x1}, {roi_y1}) to ({roi_x2}, {roi_y2})")

    # Edge detection in ROI
    edges = cv2.Canny(roi, 20, 80)
    kernel = np.ones((3, 3), np.uint8)
    edges_dilated = cv2.dilate(edges, kernel, iterations=2)

    # Fill regions
    mask = cv2.bitwise_not(edges_dilated)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=3)

    # Find components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)

    print(f"Found {num_labels - 1} regions in ROI")

    candidates = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        x = stats[i, cv2.CC_STAT_LEFT] + roi_x1
        y = stats[i, cv2.CC_STAT_TOP] + roi_y1
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]

        if 300 < area < 4000 and 30 < w < 120 and 30 < h < 120:
            candidates.append(
                {
                    "id": i,
                    "area": area,
                    "bbox": (x, y, w, h),
                    "center": (int(centroids[i][0]) + roi_x1, int(centroids[i][1]) + roi_y1),
                }
            )

    print(f"Found {len(candidates)} candidates")

    # Visualize
    debug_img = img.copy()
    cv2.rectangle(debug_img, (roi_x1, roi_y1), (roi_x2, roi_y2), (255, 0, 0), 2)

    for i, cand in enumerate(candidates):
        x, y, w, h = cand["bbox"]
        cx, cy = cand["center"]
        cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(
            debug_img, f"Cand {i}", (cx - 20, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2
        )

    debug_path = Path(image_path).parent / "debug_province40.png"
    cv2.imwrite(str(debug_path), debug_img)
    print(f"Saved: {debug_path}")

    return candidates


if __name__ == "__main__":
    import sys

    image_path = sys.argv[1] if len(sys.argv) > 1 else "./download/snes-map.png"
    find_missing_province(image_path)
