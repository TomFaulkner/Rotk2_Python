#!/usr/bin/env python3
"""
Extract province boundaries from SNES map image - Version 5.
Better number box detection on colored backgrounds.
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
    
    # Step 1: Create province mask using edge detection
    print("\nStep 1: Creating province mask from edges...")
    
    # Detect edges (black borders)
    edges = cv2.Canny(gray, 30, 100)
    
    # Dilate to close gaps in borders
    kernel = np.ones((3, 3), np.uint8)
    edges_dilated = cv2.dilate(edges, kernel, iterations=3)
    
    # Fill provinces (areas not on edges)
    province_mask = cv2.bitwise_not(edges_dilated)
    
    # Clean up
    province_mask = cv2.morphologyEx(province_mask, cv2.MORPH_CLOSE, kernel, iterations=3)
    
    # Step 2: Find connected components
    print("\nStep 2: Finding connected components...")
    
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(province_mask, connectivity=8)
    
    print(f"Found {num_labels - 1} components")
    
    # Filter provinces by size
    provinces = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        
        # Province size filter
        if area < 600 or area > 25000:
            continue
        if w < 30 or h < 30 or w > 250 or h > 250:
            continue
        
        # Get contour
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
    
    # Step 3: Find ALL dark regions (potential number boxes)
    print("\nStep 3: Finding number boxes...")
    
    # Use adaptive threshold to find dark regions on any background
    dark_mask = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY_INV, 11, 2)
    
    # Also use simple threshold for solid black regions
    _, black_mask = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)
    
    # Combine both
    combined_mask = cv2.bitwise_or(dark_mask, black_mask)
    
    # Find connected components in dark regions
    num_labels_dark, labels_dark, stats_dark, centroids_dark = cv2.connectedComponentsWithStats(
        combined_mask, connectivity=8)
    
    number_boxes = []
    for i in range(1, num_labels_dark):
        area = stats_dark[i, cv2.CC_STAT_AREA]
        x = stats_dark[i, cv2.CC_STAT_LEFT]
        y = stats_dark[i, cv2.CC_STAT_TOP]
        w = stats_dark[i, cv2.CC_STAT_WIDTH]
        h = stats_dark[i, cv2.CC_STAT_HEIGHT]
        
        # Number box characteristics
        if 100 < area < 1500 and 0.5 < w/h < 2.0 and 10 < w < 50 and 10 < h < 50:
            number_boxes.append({
                'center': (int(centroids_dark[i][0]), int(centroids_dark[i][1])),
                'bbox': (x, y, w, h),
                'area': area
            })
    
    print(f"Found {len(number_boxes)} potential number boxes")
    
    # Step 4: Match provinces to number boxes
    print("\nStep 4: Matching provinces to number boxes...")
    
    province_data = {}
    matched_provinces = set()
    
    for nb in number_boxes:
        nb_center = nb['center']
        
        # Find the smallest province that contains this number box
        best_province = None
        best_area = float('inf')
        
        for idx, prov in enumerate(provinces):
            if idx in matched_provinces:
                continue
            
            if cv2.pointPolygonTest(prov['contour'], nb_center, False) >= 0:
                if prov['area'] < best_area:
                    best_area = prov['area']
                    best_province = (idx, prov)
        
        if best_province:
            idx, prov = best_province
            
            # Simplify contour
            epsilon = 0.01 * cv2.arcLength(prov['contour'], True)
            approx = cv2.approxPolyDP(prov['contour'], epsilon, True)
            
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
    
    print(f"Matched {len(province_data)} provinces")
    
    # Step 5: Visualize
    print("\nStep 5: Creating visualization...")
    debug_img = img.copy()
    
    for pid, pdata in province_data.items():
        pts = np.array(pdata['points'], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(debug_img, [pts], True, (0, 255, 0), 2)
        
        nx, ny = pdata['number_pos']
        cv2.putText(debug_img, str(pid), (nx-8, ny+5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    debug_path = Path(image_path).parent / "debug_provinces_v5.png"
    cv2.imwrite(str(debug_path), debug_img)
    print(f"Saved: {debug_path}")
    
    # Step 6: Save to JSON
    if province_data:
        output = {
            "version": "3.0",
            "description": "SNES map province shapes extracted via image processing",
            "source_image": str(Path(image_path).name),
            "map_dimensions": {
                "width": width,
                "height": height,
                "offset_x": 0,
                "offset_y": 0
            },
            "provinces": {}
        }
        
        for pid, pdata in province_data.items():
            output['provinces'][str(pid)] = {
                'id': pdata['id'],
                'name': f'Province-{pid}',
                'points': pdata['points'],
                'center': pdata['center'],
                'number_position': pdata['number_pos'],
                'neighbors': [],
                'terrain_features': []
            }
        
        output_path = Path("data/province_shapes_extracted.json")
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✓ Saved {len(province_data)} provinces to {output_path}")
        
        point_counts = [len(p['points']) for p in province_data.values()]
        print(f"\nStatistics:")
        print(f"  Points per province: min={min(point_counts)}, max={max(point_counts)}, avg={sum(point_counts)/len(point_counts):.1f}")
    
    return province_data


if __name__ == "__main__":
    import sys
    image_path = sys.argv[1] if len(sys.argv) > 1 else "./download/snes-map.png"
    extract_provinces(image_path)
