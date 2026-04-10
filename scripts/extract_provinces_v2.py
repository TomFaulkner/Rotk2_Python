#!/usr/bin/env python3
"""
Extract province boundaries from SNES map image - Version 2.
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
    
    # Step 1: Find province borders (thick black lines)
    print("\nStep 1: Detecting province borders...")
    
    # Threshold for black lines
    _, border_mask = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY_INV)
    
    # Dilate to connect border segments
    kernel = np.ones((3, 3), np.uint8)
    border_mask = cv2.dilate(border_mask, kernel, iterations=1)
    
    # Find province contours
    contours, _ = cv2.findContours(border_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"Found {len(contours)} contours")
    
    # Filter for province-sized contours
    provinces = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 500:  # Skip small noise
            continue
            
        x, y, w, h = cv2.boundingRect(cnt)
        
        # Skip if too small or too large
        if w < 30 or h < 30 or w > 300 or h > 300:
            continue
        
        # Calculate centroid
        M = cv2.moments(cnt)
        if M['m00'] > 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
        else:
            cx, cy = x + w//2, y + h//2
        
        provinces.append({
            'contour': cnt,
            'bbox': (x, y, w, h),
            'center': (cx, cy),
            'area': area
        })
    
    print(f"Found {len(provinces)} potential provinces")
    
    # Step 2: Detect number boxes to identify provinces
    print("\nStep 2: Detecting province number boxes...")
    
    # Look for black rectangles (number boxes)
    _, num_mask = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)
    
    # Find number box contours
    num_contours, _ = cv2.findContours(num_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    number_boxes = []
    for cnt in num_contours:
        area = cv2.contourArea(cnt)
        x, y, w, h = cv2.boundingRect(cnt)
        aspect = w/h if h > 0 else 0
        
        # Number boxes: small, solid, roughly square
        if 100 < area < 800 and 0.6 < aspect < 1.5 and w > 12 and h > 12:
            # Check solidity
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            solidity = area / hull_area if hull_area > 0 else 0
            
            if solidity > 0.7:  # Solid filled box
                number_boxes.append({
                    'bbox': (x, y, w, h),
                    'center': (x + w//2, y + h//2),
                    'area': area
                })
    
    print(f"Found {len(number_boxes)} number boxes")
    
    # Step 3: Match number boxes to provinces
    print("\nStep 3: Matching number boxes to provinces...")
    
    province_data = {}
    
    for nb in number_boxes:
        nb_center = nb['center']
        
        # Find which province contains this number box
        for prov in provinces:
            # Check if number box center is inside province
            if cv2.pointPolygonTest(prov['contour'], nb_center, False) >= 0:
                # Simplify contour
                epsilon = 0.01 * cv2.arcLength(prov['contour'], True)
                approx = cv2.approxPolyDP(prov['contour'], epsilon, True)
                
                points = [[int(p[0][0]), int(p[0][1])] for p in approx]
                
                # Extract number using OCR (simplified - just use position for now)
                # We'll manually map later
                province_data[len(province_data) + 1] = {
                    'points': points,
                    'center': list(prov['center']),
                    'number_pos': list(nb_center),
                    'bbox': prov['bbox']
                }
                break
    
    print(f"Matched {len(province_data)} provinces with number boxes")
    
    # Step 4: Create debug visualization
    print("\nStep 4: Creating debug visualization...")
    debug_img = img.copy()
    
    for pid, pdata in province_data.items():
        # Draw province contour
        pts = np.array(pdata['points'], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(debug_img, [pts], True, (0, 255, 0), 2)
        
        # Draw number
        cx, cy = pdata['number_pos']
        cv2.putText(debug_img, str(pid), (cx-10, cy+5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    debug_path = Path(image_path).parent / "debug_provinces.png"
    cv2.imwrite(str(debug_path), debug_img)
    print(f"Saved: {debug_path}")
    
    return province_data


if __name__ == "__main__":
    import sys
    image_path = sys.argv[1] if len(sys.argv) > 1 else "./download/snes-map.png"
    extract_provinces(image_path)
