#!/usr/bin/env python3
"""
Extract province boundaries from SNES map image - Version 4.
Use connected components and watershed approach.
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
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Step 1: Create a mask for province areas
    # Provinces are the white regions bounded by black lines
    print("\nStep 1: Creating province mask...")
    
    # Detect edges (black lines)
    edges = cv2.Canny(gray, 50, 150)
    
    # Dilate edges to close gaps
    kernel = np.ones((3, 3), np.uint8)
    edges_dilated = cv2.dilate(edges, kernel, iterations=2)
    
    # Invert to get province regions
    province_mask = cv2.bitwise_not(edges_dilated)
    
    # Clean up with morphological operations
    province_mask = cv2.morphologyEx(province_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    province_mask = cv2.morphologyEx(province_mask, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # Step 2: Find connected components (individual provinces)
    print("\nStep 2: Finding connected components...")
    
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(province_mask, connectivity=8)
    
    print(f"Found {num_labels - 1} connected components (excluding background)")
    
    # Filter components by size
    provinces = []
    for i in range(1, num_labels):  # Skip background (0)
        area = stats[i, cv2.CC_STAT_AREA]
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        
        # Skip small components (noise) and very large ones (background)
        if area < 800:
            continue
        if w > 300 or h > 300:
            continue
        
        # Get contour of this component
        component_mask = (labels == i).astype(np.uint8) * 255
        contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            provinces.append({
                'contour': contours[0],
                'bbox': (x, y, w, h),
                'center': (int(centroids[i][0]), int(centroids[i][1])),
                'area': area
            })
    
    print(f"Filtered to {len(provinces)} province candidates")
    
    # Step 3: Detect number boxes
    print("\nStep 3: Detecting number boxes...")
    
    # Number boxes are black rectangles
    _, black_mask = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)
    
    # Find black regions
    num_labels_black, labels_black, stats_black, centroids_black = cv2.connectedComponentsWithStats(black_mask, connectivity=8)
    
    number_boxes = []
    for i in range(1, num_labels_black):
        area = stats_black[i, cv2.CC_STAT_AREA]
        x = stats_black[i, cv2.CC_STAT_LEFT]
        y = stats_black[i, cv2.CC_STAT_TOP]
        w = stats_black[i, cv2.CC_STAT_WIDTH]
        h = stats_black[i, cv2.CC_STAT_HEIGHT]
        aspect = w/h if h > 0 else 0
        
        # Filter for number box characteristics
        if 150 < area < 1200 and 0.6 < aspect < 1.5 and 12 < w < 45 and 12 < h < 45:
            number_boxes.append({
                'center': (int(centroids_black[i][0]), int(centroids_black[i][1])),
                'bbox': (x, y, w, h),
                'area': area
            })
    
    print(f"Found {len(number_boxes)} number boxes")
    
    # Step 4: Match number boxes to provinces
    print("\nStep 4: Matching number boxes to provinces...")
    
    province_data = {}
    matched_provinces = set()
    
    for nb in number_boxes:
        nb_center = nb['center']
        
        for idx, prov in enumerate(provinces):
            if idx in matched_provinces:
                continue
            
            # Check if number box is inside province
            if cv2.pointPolygonTest(prov['contour'], nb_center, False) >= 0:
                # Simplify contour
                epsilon = 0.01 * cv2.arcLength(prov['contour'], True)
                approx = cv2.approxPolyDP(prov['contour'], epsilon, True)
                
                # Get points
                points = [[int(p[0][0]), int(p[0][1])] for p in approx]
                
                pid = len(province_data) + 1
                province_data[pid] = {
                    'id': pid,
                    'points': points,
                    'center': list(prov['center']),
                    'number_pos': list(nb_center),
                    'bbox': prov['bbox'],
                    'area': int(prov['area'])
                }
                matched_provinces.add(idx)
                break
    
    print(f"Matched {len(province_data)} provinces")
    
    # Step 5: Visualize results
    print("\nStep 5: Creating visualization...")
    debug_img = img.copy()
    
    # Draw all detected provinces
    for pid, pdata in province_data.items():
        pts = np.array(pdata['points'], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(debug_img, [pts], True, (0, 255, 0), 2)
        
        # Draw province ID
        nx, ny = pdata['number_pos']
        cv2.putText(debug_img, str(pid), (nx-8, ny+5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    debug_path = Path(image_path).parent / "debug_provinces_v4.png"
    cv2.imwrite(str(debug_path), debug_img)
    print(f"Saved: {debug_path}")
    
    print(f"\n✓ Extracted {len(province_data)} provinces")
    
    return province_data


if __name__ == "__main__":
    import sys
    image_path = sys.argv[1] if len(sys.argv) > 1 else "./download/snes-map.png"
    extract_provinces(image_path)
