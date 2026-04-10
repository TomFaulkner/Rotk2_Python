#!/usr/bin/env python3
"""
Final province extraction - Two-stage approach:
1. Detect all province regions
2. Identify by reading numbers or manual mapping
"""

import cv2
import numpy as np
import json
from pathlib import Path


def extract_all_provinces(image_path: str):
    """Extract all province regions from SNES map."""
    
    print(f"Loading image: {image_path}")
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")
    
    height, width = img.shape[:2]
    print(f"Image size: {width}x{height}")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Step 1: Create mask from edges
    print("\nStep 1: Detecting province boundaries...")
    
    # Canny edge detection for black borders
    edges = cv2.Canny(gray, 20, 80)
    
    # Dilate to connect border segments
    kernel = np.ones((4, 4), np.uint8)
    edges_dilated = cv2.dilate(edges, kernel, iterations=3)
    
    # Fill holes to get province regions
    province_mask = cv2.bitwise_not(edges_dilated)
    
    # Clean up
    province_mask = cv2.morphologyEx(province_mask, cv2.MORPH_CLOSE, kernel, iterations=4)
    
    # Step 2: Find all connected components
    print("\nStep 2: Finding province regions...")
    
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(province_mask, connectivity=8)
    
    print(f"Found {num_labels - 1} total regions")
    
    # Filter for province-sized regions
    provinces = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        
        # Filter by size - be more inclusive
        if area < 400:  # Skip very small
            continue
        if w < 25 or h < 25:  # Skip thin regions
            continue
        if w > 280 or h > 280:  # Skip overly large (background)
            continue
        
        # Get contour
        component_mask = (labels == i).astype(np.uint8) * 255
        contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Simplify contour
            epsilon = 0.008 * cv2.arcLength(contours[0], True)
            approx = cv2.approxPolyDP(contours[0], epsilon, True)
            
            # Ensure minimum points
            if len(approx) < 6:
                epsilon = 0.004 * cv2.arcLength(contours[0], True)
                approx = cv2.approxPolyDP(contours[0], epsilon, True)
            
            points = [[int(p[0][0]), int(p[0][1])] for p in approx]
            
            provinces.append({
                'id': len(provinces) + 1,
                'points': points,
                'center': [int(centroids[i][0]), int(centroids[i][1])],
                'bbox': (x, y, w, h),
                'area': int(area),
                'num_points': len(points)
            })
    
    print(f"Filtered to {len(provinces)} province candidates")
    
    # Step 3: Visualize all detected provinces
    print("\nStep 3: Creating visualization...")
    debug_img = img.copy()
    
    for prov in provinces:
        pid = prov['id']
        pts = np.array(prov['points'], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(debug_img, [pts], True, (0, 255, 0), 2)
        
        # Draw ID at center
        cx, cy = prov['center']
        cv2.putText(debug_img, str(pid), (cx-10, cy+5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    debug_path = Path(image_path).parent / "debug_all_provinces.png"
    cv2.imwrite(str(debug_path), debug_img)
    print(f"Saved: {debug_path}")
    
    # Step 4: Calculate neighbors
    print("\nStep 4: Calculating neighbor relationships...")
    
    for i, prov in enumerate(provinces):
        neighbors = []
        x1, y1, w1, h1 = prov['bbox']
        
        for j, other in enumerate(provinces):
            if i == j:
                continue
            
            x2, y2, w2, h2 = other['bbox']
            
            # Check bbox proximity
            margin = 30
            if (x1 - margin < x2 + w2 + margin and 
                x1 + w1 + margin > x2 - margin and
                y1 - margin < y2 + h2 + margin and 
                y1 + h1 + margin > y2 - margin):
                neighbors.append(other['id'])
        
        prov['neighbors'] = neighbors[:10]
    
    # Step 5: Save results
    print(f"\nStep 5: Saving {len(provinces)} provinces...")
    
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
    
    for prov in provinces:
        output['provinces'][str(prov['id'])] = {
            'id': prov['id'],
            'name': f'Province-{prov["id"]}',
            'points': prov['points'],
            'center': prov['center'],
            'number_position': prov['center'],  # Use center for now
            'neighbors': prov['neighbors'],
            'terrain_features': [],
            'area': prov['area']
        }
    
    output_path = Path("data/province_shapes_extracted.json")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Saved to {output_path}")
    
    # Statistics
    point_counts = [p['num_points'] for p in provinces]
    print(f"\nStatistics:")
    print(f"  Total provinces: {len(provinces)}")
    print(f"  Points per province: min={min(point_counts)}, max={max(point_counts)}, avg={sum(point_counts)/len(point_counts):.1f}")
    
    return provinces


if __name__ == "__main__":
    import sys
    image_path = sys.argv[1] if len(sys.argv) > 1 else "./download/snes-map.png"
    extract_all_provinces(image_path)
