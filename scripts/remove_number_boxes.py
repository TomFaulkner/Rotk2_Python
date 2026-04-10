#!/usr/bin/env python3
"""
Aggressively remove all number boxes from SNES map image.
This cleans up the image so province extraction can follow actual borders.
"""

import cv2
import numpy as np
from pathlib import Path


def remove_number_boxes(image_path: str, output_path: str = None):
    """Remove all number boxes from map image."""
    
    print(f"Loading image: {image_path}")
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")
    
    height, width = img.shape[:2]
    print(f"Image size: {width}x{height}")
    
    # Create a copy to work with
    cleaned = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Step 1: Find all black regions
    print("\nStep 1: Finding black regions...")
    _, black_mask = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)
    
    # Step 2: Find connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(black_mask, connectivity=8)
    
    print(f"Found {num_labels - 1} black regions")
    
    # Step 3: Filter for number box characteristics
    # Number boxes are:
    # - Rectangular (aspect ratio close to 1)
    # - Size between 100-2000 pixels area
    # - Width and height between 10-50 pixels
    # - Solid fill (not just lines)
    
    number_boxes = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        
        # Calculate aspect ratio
        aspect = w / h if h > 0 else 0
        
        # Number box criteria (be inclusive to catch all)
        if 80 < area < 2500 and 0.4 < aspect < 2.5 and 8 < w < 60 and 8 < h < 60:
            # Additional check: should be somewhat solid
            # Calculate solidity
            component_mask = (labels == i).astype(np.uint8) * 255
            contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                hull = cv2.convexHull(contours[0])
                hull_area = cv2.contourArea(hull)
                solidity = area / hull_area if hull_area > 0 else 0
                
                if solidity > 0.5:  # At least 50% solid
                    number_boxes.append({
                        'id': i,
                        'bbox': (x, y, w, h),
                        'center': (int(centroids[i][0]), int(centroids[i][1])),
                        'area': area,
                        'aspect': aspect
                    })
    
    print(f"Found {len(number_boxes)} potential number boxes")
    
    # Step 4: Remove number boxes by filling with white
    print("\nStep 2: Removing number boxes...")
    
    # Expand boxes slightly to ensure complete removal
    expand = 4
    
    removed_count = 0
    for box in number_boxes:
        x, y, w, h = box['bbox']
        
        # Expand the rectangle
        x1 = max(0, x - expand)
        y1 = max(0, y - expand)
        x2 = min(width, x + w + expand)
        y2 = min(height, y + h + expand)
        
        # Fill with white
        cv2.rectangle(cleaned, (x1, y1), (x2, y2), (255, 255, 255), -1)
        removed_count += 1
    
    print(f"Removed {removed_count} number boxes")
    
    # Step 5: Clean up small black artifacts (noise)
    print("\nStep 3: Cleaning up small artifacts...")
    
    gray_cleaned = cv2.cvtColor(cleaned, cv2.COLOR_BGR2GRAY)
    _, small_black = cv2.threshold(gray_cleaned, 60, 255, cv2.THRESH_BINARY_INV)
    
    # Find small black regions
    num_labels_small, labels_small, stats_small, _ = cv2.connectedComponentsWithStats(small_black, connectivity=8)
    
    small_removed = 0
    for i in range(1, num_labels_small):
        area = stats_small[i, cv2.CC_STAT_AREA]
        if area < 150:  # Remove very small artifacts
            x = stats_small[i, cv2.CC_STAT_LEFT]
            y = stats_small[i, cv2.CC_STAT_TOP]
            w = stats_small[i, cv2.CC_STAT_WIDTH]
            h = stats_small[i, cv2.CC_STAT_HEIGHT]
            cv2.rectangle(cleaned, (x, y), (x+w, y+h), (255, 255, 255), -1)
            small_removed += 1
    
    print(f"Removed {small_removed} small artifacts")
    
    # Step 6: Optional - morphological cleanup to smooth borders
    print("\nStep 4: Smoothing borders...")
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    # Step 7: Save cleaned image
    if output_path is None:
        output_path = str(Path(image_path).parent / "snes-map-cleaned.png")
    
    cv2.imwrite(output_path, cleaned)
    print(f"\n✓ Saved cleaned image: {output_path}")
    
    # Step 8: Create comparison
    print("\nStep 5: Creating comparison image...")
    comparison = np.hstack((img, cleaned))
    
    # Add labels
    cv2.putText(comparison, "Original", (20, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    cv2.putText(comparison, "Cleaned", (width + 20, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
    comparison_path = str(Path(image_path).parent / "comparison_cleaned.png")
    cv2.imwrite(comparison_path, comparison)
    print(f"✓ Saved comparison: {comparison_path}")
    
    # Step 9: Create debug showing detected boxes
    debug_img = img.copy()
    for box in number_boxes:
        x, y, w, h = box['bbox']
        cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(debug_img, str(box['id']), (x, y-5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    
    debug_path = str(Path(image_path).parent / "debug_detected_boxes.png")
    cv2.imwrite(debug_path, debug_img)
    print(f"✓ Saved detection debug: {debug_path}")
    
    print(f"\n{'='*60}")
    print(f"Cleaning complete!")
    print(f"  - Removed: {removed_count} number boxes")
    print(f"  - Removed: {small_removed} small artifacts")
    print(f"  - Output: {output_path}")
    print(f"{'='*60}")
    
    return output_path


if __name__ == "__main__":
    import sys
    
    image_path = sys.argv[1] if len(sys.argv) > 1 else "./download/snes-map.png"
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    remove_number_boxes(image_path, output_path)
