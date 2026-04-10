#!/usr/bin/env python3
"""
Finalize province extraction by adding missing provinces 8, 38, 39.
"""

import cv2
import numpy as np
import json
from pathlib import Path


def add_missing_provinces(image_path: str):
    """Extract provinces and add missing ones."""
    
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    height, width = img.shape[:2]
    
    print(f"Image: {width}x{height}")
    
    # Step 1: Extract provinces using edge method (from previous script)
    edges = cv2.Canny(gray, 30, 100)
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=2)
    province_mask = cv2.bitwise_not(edges)
    province_mask = cv2.morphologyEx(province_mask, cv2.MORPH_CLOSE, kernel, iterations=3)
    
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(province_mask, connectivity=8)
    
    provinces = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        
        if area < 400 or w < 30 or h < 30 or w > 300 or h > 300:
            continue
        
        component_mask = (labels == i).astype(np.uint8) * 255
        contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            epsilon = 0.005 * cv2.arcLength(contours[0], True)
            approx = cv2.approxPolyDP(contours[0], epsilon, True)
            points = [[int(p[0][0]), int(p[0][1])] for p in approx]
            
            provinces.append({
                'points': points,
                'center': [int(centroids[i][0]), int(centroids[i][1])],
                'bbox': (x, y, w, h),
                'area': area
            })
    
    print(f"Auto-detected: {len(provinces)} provinces")
    
    # Step 2: Add missing provinces manually
    # Based on visual analysis of the map:
    
    # Province 8: Qingzhou - eastern coastal province
    # Position: roughly x:750-850, y:200-280
    prov_8 = {
        'points': [
            [745, 195], [780, 188], [820, 192], [855, 210],
            [868, 245], [860, 280], [825, 295], [785, 290],
            [755, 270], [740, 235], [745, 195]
        ],
        'center': [805, 240],
        'bbox': (740, 188, 128, 107),
        'area': 8000,
        'manual': True
    }
    
    # Province 38: Yangzhou-4 - southern coastal
    # Position: roughly x:540-620, y:580-650
    prov_38 = {
        'points': [
            [535, 575], [575, 570], [615, 580], [635, 615],
            [630, 655], [595, 675], [550, 670], [530, 635],
            [535, 575]
        ],
        'center': [582, 620],
        'bbox': (530, 570, 105, 105),
        'area': 8500,
        'manual': True
    }
    
    # Province 39: Yangzhou-5 - southern coastal, west of 38
    # Position: roughly x:460-540, y:600-680
    prov_39 = {
        'points': [
            [455, 595], [495, 590], [535, 600], [555, 635],
            [550, 675], [515, 695], [470, 690], [450, 655],
            [455, 595]
        ],
        'center': [502, 640],
        'bbox': (450, 590, 105, 105),
        'area': 9000,
        'manual': True
    }
    
    # Add to provinces list
    all_provinces = provinces + [prov_8, prov_38, prov_39]
    
    print(f"Total with manual additions: {len(all_provinces)} provinces")
    
    # Step 3: Create province data with IDs
    province_data = {}
    # Map based on position
    # This is approximate - we'd need to verify each one
    
    for i, prov in enumerate(all_provinces, 1):
        province_data[i] = {
            'id': i,
            'name': f'Province-{i}',
            'points': prov['points'],
            'center': prov['center'],
            'number_position': prov['center'],  # Use center for now
            'bbox': prov['bbox'],
            'area': prov.get('area', 0),
            'manual': prov.get('manual', False)
        }
    
    # Step 4: Calculate neighbors
    print("Calculating neighbors...")
    for pid, pdata in province_data.items():
        neighbors = []
        x1, y1, w1, h1 = pdata['bbox']
        
        for other_id, other_data in province_data.items():
            if pid == other_id:
                continue
            
            x2, y2, w2, h2 = other_data['bbox']
            margin = 25
            if (x1 - margin < x2 + w2 + margin and 
                x1 + w1 + margin > x2 - margin and
                y1 - margin < y2 + h2 + margin and 
                y1 + h1 + margin > y2 - margin):
                neighbors.append(other_id)
        
        pdata['neighbors'] = neighbors[:10]
    
    # Step 5: Save
    output = {
        "version": "4.0",
        "description": "SNES map provinces - 38 auto-extracted + 3 manual",
        "source_image": "snes-map.png",
        "map_dimensions": {"width": width, "height": height, "offset_x": 0, "offset_y": 0},
        "provinces": {}
    }
    
    for pid, pdata in province_data.items():
        output['provinces'][str(pid)] = {
            'id': pdata['id'],
            'name': pdata['name'],
            'points': pdata['points'],
            'center': pdata['center'],
            'number_position': pdata['number_position'],
            'neighbors': pdata['neighbors'],
            'terrain_features': []
        }
    
    # Save
    output_path = Path("data/province_shapes.json")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✓ Saved {len(province_data)} provinces to {output_path}")
    
    # Step 6: Visualize
    debug_img = img.copy()
    for pid, pdata in province_data.items():
        pts = np.array(pdata['points'], np.int32)
        pts = pts.reshape((-1, 1, 2))
        color = (0, 255, 0) if not pdata.get('manual') else (255, 0, 0)  # Green=auto, Blue=manual
        cv2.polylines(debug_img, [pts], True, color, 2)
        cv2.putText(debug_img, str(pid), (pdata['center'][0]-10, pdata['center'][1]),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    debug_path = Path(image_path).parent / "debug_final.png"
    cv2.imwrite(str(debug_path), debug_img)
    print(f"✓ Saved visualization: {debug_path}")
    
    return province_data


if __name__ == "__main__":
    import sys
    image_path = sys.argv[1] if len(sys.argv) > 1 else "./download/snes-map.png"
    add_missing_provinces(image_path)
