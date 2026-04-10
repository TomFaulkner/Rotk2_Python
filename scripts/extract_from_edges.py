#!/usr/bin/env python3
"""
Extract provinces using edge detection instead of region detection.
This should work better with the number boxes present.
"""

import cv2
import numpy as np
import json
from pathlib import Path


def extract_from_edges(image_path: str):
    """Extract provinces using edge-based approach."""
    
    print(f"Loading image: {image_path}")
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    height, width = img.shape[:2]
    
    # Step 1: Detect edges (province borders)
    print("\nStep 1: Detecting province borders...")
    
    # Use Canny edge detection
    edges = cv2.Canny(gray, 30, 100)
    
    # Dilate edges to make them continuous
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=2)
    
    # Step 2: Find enclosed regions (provinces)
    print("\nStep 2: Finding enclosed regions...")
    
    # Invert edges to get province interiors
    province_mask = cv2.bitwise_not(edges)
    
    # Fill small holes
    province_mask = cv2.morphologyEx(province_mask, cv2.MORPH_CLOSE, kernel, iterations=3)
    
    # Find connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(province_mask, connectivity=8)
    
    print(f"Found {num_labels - 1} regions")
    
    # Step 3: Filter provinces by size and location
    print("\nStep 3: Filtering province candidates...")
    
    provinces = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        
        # Skip background and very small regions
        if area < 400 or w < 30 or h < 30:
            continue
        if w > 300 or h > 300:  # Likely background
            continue
        
        # Get contour
        component_mask = (labels == i).astype(np.uint8) * 255
        contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Simplify contour
            epsilon = 0.005 * cv2.arcLength(contours[0], True)
            approx = cv2.approxPolyDP(contours[0], epsilon, True)
            
            points = [[int(p[0][0]), int(p[0][1])] for p in approx]
            
            provinces.append({
                'id': len(provinces) + 1,
                'points': points,
                'center': [int(centroids[i][0]), int(centroids[i][1])],
                'bbox': (x, y, w, h),
                'area': area
            })
    
    print(f"Found {len(provinces)} province candidates")
    
    # Step 4: Visualize
    print("\nStep 4: Creating visualization...")
    debug_img = img.copy()
    
    for prov in provinces:
        pts = np.array(prov['points'], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(debug_img, [pts], True, (0, 255, 0), 2)
        
        cx, cy = prov['center']
        cv2.putText(debug_img, str(prov['id']), (cx-10, cy),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    debug_path = Path(image_path).parent / "debug_edges.png"
    cv2.imwrite(str(debug_path), debug_img)
    print(f"Saved: {debug_path}")
    
    return provinces


if __name__ == "__main__":
    import sys
    image_path = sys.argv[1] if len(sys.argv) > 1 else "./download/snes-map.png"
    extract_from_edges(image_path)
