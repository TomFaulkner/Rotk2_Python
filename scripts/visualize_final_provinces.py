#!/usr/bin/env python3
"""Create a visualization of the final province mapping."""

import cv2
import json
import numpy as np
from pathlib import Path


def create_final_visualization():
    # Load the province data
    with open("data/province_shapes.json") as f:
        data = json.load(f)

    # Load the clean image as background
    img = cv2.imread("download/numbers-removed.jpg")
    if img is None:
        print("Error: Could not load numbers-removed.jpg")
        return

    # Create a colored visualization
    viz = img.copy()
    height, width = viz.shape[:2]

    # Create a color map for provinces (cyclic colors)
    colors = [
        (255, 100, 100),
        (100, 255, 100),
        (100, 100, 255),
        (255, 255, 100),
        (255, 100, 255),
        (100, 255, 255),
        (200, 100, 100),
        (100, 200, 100),
        (100, 100, 200),
        (200, 200, 100),
        (200, 100, 200),
        (100, 200, 200),
    ] * 4  # 48 colors

    # Draw each province
    for pid_str, prov in data["provinces"].items():
        pid = int(pid_str)
        points = np.array(prov["points"], np.int32)
        points = points.reshape((-1, 1, 2))

        color = colors[pid % len(colors)]

        # Fill the province
        cv2.fillPoly(viz, [points], color)

        # Draw border
        cv2.polylines(viz, [points], True, (50, 50, 50), 2)

        # Draw province ID at center
        cx, cy = prov["center"]
        text = str(pid)

        # Get text size
        (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)

        # Draw background for text
        cv2.rectangle(
            viz,
            (cx - text_w // 2 - 4, cy - text_h // 2 - 4),
            (cx + text_w // 2 + 4, cy + text_h // 2 + 4),
            (255, 255, 255),
            -1,
        )

        # Draw text
        cv2.putText(
            viz,
            text,
            (cx - text_w // 2, cy + text_h // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 0),
            2,
        )

    # Save
    output_path = Path("download/provinces_final_visualization.png")
    cv2.imwrite(str(output_path), viz)
    print(f"Visualization saved to: {output_path}")

    # Also create a side-by-side comparison with the clean image
    comparison = np.hstack([img, viz])
    comparison_path = Path("download/provinces_comparison.png")
    cv2.imwrite(str(comparison_path), comparison)
    print(f"Comparison saved to: {comparison_path}")


if __name__ == "__main__":
    create_final_visualization()
