#!/usr/bin/env python3
"""
Extract provinces while preserving borders - minimal morphological operations.
"""

import cv2
import numpy as np
import json
from pathlib import Path


def extract_provinces(image_path: str):
    """Extract provinces while preserving borders."""
    
    print(f"Loading image: {image_path}")
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    height, width = img.shape[:2]
    
    print(f"Image size: {width}x{height}")
    
    # Step 1: Detect edges with minimal processing
    print("\nStep 1: Detecting edges...")
    
    # Use Canny with lower thresholds to catch thin borders
    edges = cv2.Canny(gray, 20, 60)
    
    # Very light dilation to connect broken border segments
    kernel = np.ones((2, 2), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    
    # Step 2: Find regions
    print("\nStep 2: Finding regions...")
    
    province_mask = cv2.bitwise_not(edges)
    
    # Very light closing to fix small gaps
    province_mask = cv2.morphologyEx(province_mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    # Step 3: Find connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(province_mask, connectivity=8)
    
    print(f"Found {num_labels - 1} regions")
    
    # Step 4: Filter provinces
    print("\nStep 3: Filtering provinces...")
    
    provinces = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        
        # More permissive size filter
        if area < 400:
            continue
        if w < 20 or h < 20:
            continue
        if w > 350 or h > 350:
            continue
        
        # Get contour
        component_mask = (labels == i).astype(np.uint8) * 255
        contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            epsilon = 0.01 * cv2.arcLength(contours[0], True)
            approx = cv2.approxPolyDP(contours[0], epsilon, True)
            
            points = [[int(p[0][0]), int(p[0][1])] for p in approx]
            
            provinces.append({
                'id': len(provinces) + 1,
                'points': points,
                'center': [int(centroids[i][0]), int(centroids[i][1])],
                'bbox': (x, y, w, h),
                'area': int(area)
            })
    
    print(f"Found {len(provinces)} province candidates")
    
    # Step 5: Visualize
    print("\nStep 4: Creating visualization...")
    debug_img = img.copy()
    
    for prov in provinces:
        pts = np.array(prov['points'], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(debug_img, [pts], True, (0, 255, 0), 2)
        
        cx, cy = prov['center']
        cv2.putText(debug_img, str(prov['id']), (cx-8, cy+4),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    debug_path = Path(image_path).parent / "debug_preserve_borders.png"
    cv2.imwrite(str(debug_path), debug_img)
    print(f"Saved: {debug_path}")
    
    print(f"\n✓ Extracted {len(provinces)} provinces")
    
    return provinces


if __name__ == "__main__":
    import sys
    image_path = sys.argv[1] if len(sys.argv) > 1 else "./download/snes-map-cleaned.png"
    extract_provinces(image_path)
