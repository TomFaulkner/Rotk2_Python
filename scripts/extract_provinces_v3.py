#!/usr/bin/env python3
"""
Extract province boundaries from SNES map image - Version 3.
Detect white province areas instead of black borders.
"""

import cv2
import numpy as np
import json
from pathlib import Path


def extract_provinces(image_path: str):
    """Extract province boundaries from SNES map image."""

    print(f"Loading image: {image_path}")
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    height, width = img.shape[:2]
    print(f"Image size: {width}x{height}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Step 1: Detect province interiors (white/light regions)
    print("\nStep 1: Detecting province interiors...")

    # Threshold for light regions (province interiors)
    _, light_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    # Morphological operations to fill gaps
    kernel = np.ones((5, 5), np.uint8)
    light_mask = cv2.morphologyEx(light_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    light_mask = cv2.morphologyEx(light_mask, cv2.MORPH_OPEN, kernel, iterations=1)

    # Find province contours
    contours, _ = cv2.findContours(light_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    print(f"Found {len(contours)} light region contours")

    # Filter for province-sized contours
    provinces = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 1000:  # Skip small noise
            continue

        x, y, w, h = cv2.boundingRect(cnt)

        # Skip if too small or too large
        if w < 40 or h < 40:
            continue
        if w > 250 or h > 250:
            continue

        # Calculate centroid
        M = cv2.moments(cnt)
        if M["m00"] > 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = x + w // 2, y + h // 2

        provinces.append({"contour": cnt, "bbox": (x, y, w, h), "center": (cx, cy), "area": area})

    print(f"Filtered to {len(provinces)} province candidates")

    # Step 2: Detect number boxes (black rectangles with white numbers)
    print("\nStep 2: Detecting province number boxes...")

    _, num_mask = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)

    num_contours, _ = cv2.findContours(num_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    number_boxes = []
    for cnt in num_contours:
        area = cv2.contourArea(cnt)
        x, y, w, h = cv2.boundingRect(cnt)
        aspect = w / h if h > 0 else 0

        # Number boxes criteria
        if 150 < area < 1000 and 0.7 < aspect < 1.4 and 15 < w < 50 and 15 < h < 50:
            number_boxes.append(
                {"bbox": (x, y, w, h), "center": (x + w // 2, y + h // 2), "area": area}
            )

    print(f"Found {len(number_boxes)} number boxes")

    # Step 3: Match number boxes to provinces
    print("\nStep 3: Matching number boxes to provinces...")

    province_data = {}
    matched_provinces = set()

    for nb in number_boxes:
        nb_center = nb["center"]

        # Find which province contains this number box
        for idx, prov in enumerate(provinces):
            if idx in matched_provinces:
                continue

            # Check if number box center is inside province
            if cv2.pointPolygonTest(prov["contour"], nb_center, False) >= 0:
                # Simplify contour
                epsilon = 0.008 * cv2.arcLength(prov["contour"], True)
                approx = cv2.approxPolyDP(prov["contour"], epsilon, True)

                # Ensure we have reasonable number of points
                if len(approx) < 6:
                    epsilon = 0.005 * cv2.arcLength(prov["contour"], True)
                    approx = cv2.approxPolyDP(prov["contour"], epsilon, True)

                points = [[int(p[0][0]), int(p[0][1])] for p in approx]

                pid = len(province_data) + 1
                province_data[pid] = {
                    "id": pid,
                    "points": points,
                    "center": list(prov["center"]),
                    "number_pos": list(nb_center),
                    "bbox": prov["bbox"],
                    "area": int(prov["area"]),
                }
                matched_provinces.add(idx)
                break

    print(f"Matched {len(province_data)} provinces")

    # Step 4: Determine neighbors
    print("\nStep 4: Determining neighbors...")

    for pid, pdata in province_data.items():
        neighbors = []
        x1, y1, w1, h1 = pdata["bbox"]

        for other_id, other_data in province_data.items():
            if pid == other_id:
                continue

            x2, y2, w2, h2 = other_data["bbox"]

            # Check if bounding boxes overlap or are close
            margin = 25
            if (
                x1 - margin < x2 + w2 + margin
                and x1 + w1 + margin > x2 - margin
                and y1 - margin < y2 + h2 + margin
                and y1 + h1 + margin > y2 - margin
            ):
                neighbors.append(other_id)

        pdata["neighbors"] = neighbors[:8]

    # Step 5: Create debug visualization
    print("\nStep 5: Creating debug visualization...")
    debug_img = img.copy()

    for pid, pdata in province_data.items():
        # Draw province contour
        pts = np.array(pdata["points"], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(debug_img, [pts], True, (0, 255, 0), 2)

        # Draw center
        cx, cy = pdata["center"]
        cv2.circle(debug_img, (cx, cy), 3, (255, 0, 0), -1)

        # Draw number
        nx, ny = pdata["number_pos"]
        cv2.putText(
            debug_img, str(pid), (nx - 8, ny + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2
        )

    debug_path = Path(image_path).parent / "debug_provinces_v3.png"
    cv2.imwrite(str(debug_path), debug_img)
    print(f"Saved: {debug_path}")

    # Save province data
    output = {
        "version": "3.0",
        "description": "SNES map province shapes extracted via image processing",
        "source_image": str(Path(image_path).name),
        "map_dimensions": {"width": width, "height": height, "offset_x": 0, "offset_y": 0},
        "provinces": {},
    }

    for pid, pdata in province_data.items():
        output["provinces"][str(pid)] = {
            "id": pdata["id"],
            "name": f"Province-{pid}",
            "points": pdata["points"],
            "center": pdata["center"],
            "number_position": pdata["number_pos"],
            "neighbors": pdata["neighbors"],
            "terrain_features": [],
        }

    output_path = Path("data/province_shapes_extracted.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Saved {len(province_data)} provinces to {output_path}")

    # Statistics
    point_counts = [len(p["points"]) for p in province_data.values()]
    if point_counts:
        print(f"\nStatistics:")
        print(f"  Min points: {min(point_counts)}")
        print(f"  Max points: {max(point_counts)}")
        print(f"  Avg points: {sum(point_counts) / len(point_counts):.1f}")

    return province_data


if __name__ == "__main__":
    import sys

    image_path = sys.argv[1] if len(sys.argv) > 1 else "./download/snes-map.png"
    extract_provinces(image_path)
