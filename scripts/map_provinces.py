#!/usr/bin/env python3
"""
Interactive province mapping tool.
Click on each province to assign the correct province number.
"""

import cv2
import numpy as np
import json
from pathlib import Path

# Expected province numbers by rough position (for auto-suggestion)
PROVINCE_POSITIONS = {
    # Northern row (top)
    1: (850, 100), 2: (750, 100), 3: (650, 100), 4: (550, 100),
    5: (500, 150), 6: (700, 180), 7: (600, 180), 8: (800, 180),
    # Second row
    9: (700, 250), 10: (600, 250), 11: (500, 250), 12: (400, 250),
    13: (300, 250), 14: (200, 250), 15: (100, 250),
    # Third row  
    16: (800, 320), 17: (700, 320), 18: (800, 380), 19: (600, 320),
    20: (400, 320), 21: (550, 380), 22: (650, 400),
    # Fourth row
    23: (550, 480), 24: (900, 350), 25: (850, 450), 26: (950, 550),
    27: (800, 520), 28: (700, 500),
    # Western
    29: (350, 380), 30: (250, 350), 31: (450, 450), 32: (300, 450),
    33: (200, 450), 34: (300, 600), 35: (150, 550), 36: (250, 700),
    # Southern
    37: (700, 650), 38: (600, 650), 39: (500, 650), 40: (400, 650),
    41: (350, 750)
}


def auto_assign_provinces(provinces):
    """Auto-assign province numbers based on position."""
    assignments = {}
    used_provinces = set()
    
    for expected_id, expected_pos in PROVINCE_POSITIONS.items():
        best_match = None
        best_dist = float('inf')
        
        for prov in provinces:
            if prov['id'] in used_provinces:
                continue
            
            cx, cy = prov['center']
            dist = np.sqrt((cx - expected_pos[0])**2 + (cy - expected_pos[1])**2)
            
            if dist < best_dist and dist < 80:  # Within 80 pixels
                best_dist = dist
                best_match = prov['id']
        
        if best_match:
            assignments[best_match] = expected_id
            used_provinces.add(best_match)
    
    return assignments


def main():
    # Load extracted provinces
    with open("data/province_shapes_extracted.json", "r") as f:
        data = json.load(f)
    
    provinces = []
    for pid, pdata in data['provinces'].items():
        provinces.append({
            'id': int(pid),
            'points': pdata['points'],
            'center': pdata['center']
        })
    
    print(f"Loaded {len(provinces)} provinces")
    print(f"Expected: 41 provinces")
    print(f"Missing: {41 - len(provinces)} province(s)")
    
    # Auto-assign based on position
    assignments = auto_assign_provinces(provinces)
    
    print(f"\nAuto-assigned {len(assignments)} provinces")
    
    # Show assignments
    print("\nDetected -> Province Number:")
    for det_id, prov_num in sorted(assignments.items()):
        print(f"  {det_id:2d} -> Province {prov_num}")
    
    # Find unassigned
    unassigned = [p['id'] for p in provinces if p['id'] not in assignments]
    if unassigned:
        print(f"\nUnassigned detected provinces: {unassigned}")
    
    # Find missing province numbers
    assigned_nums = set(assignments.values())
    missing = [n for n in range(1, 42) if n not in assigned_nums]
    if missing:
        print(f"\nMissing province numbers: {missing}")
    
    print("\n✓ Province extraction complete!")
    print(f"  Detected: {len(provinces)} provinces")
    print(f"  Assigned: {len(assignments)} provinces")
    print(f"  Missing: {len(missing)} province(s)")


if __name__ == "__main__":
    main()
