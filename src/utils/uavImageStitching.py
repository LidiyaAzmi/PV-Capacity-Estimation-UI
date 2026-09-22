# -*- coding: utf-8 -*-
"""
Improved Image Stitching for Drone Panoramas
Key improvements:
1. Better feature detection with SIFT (more robust than ORB)
2. Improved homography estimation with stricter RANSAC
3. Multi-band blending for seamless transitions
4. Automatic black border cropping
5. Better overlap handling
"""

import sys
import os
import cv2
import numpy as np
import glob

def create_low_res_preview(image_path, scale_percent=20):
    img = cv2.imread(image_path)

    # Safety Check: Ensure the image was actually loaded
    if img is None:
        print(f"Error: Could not load image at {image_path}")
        return None # Avoid crashing the app
    
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)
    
    # Use INTER_AREA for best quality when shrinking
    resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
    
    preview_path = image_path.replace(".jpg", "_preview.jpg")
    cv2.imwrite(preview_path, resized)
    return preview_path

def crop_black_borders(img):
    """Remove black borders from stitched panorama"""
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Threshold to find non-black pixels
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) > 0:
        # Get the largest contour (the actual image content)
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Crop to bounding rectangle
        cropped = img[y:y+h, x:x+w]
        return cropped
    
    return img

def create_blend_mask(img1, img2, overlap_region):
    """Create smooth gradient mask for blending"""
    rows, cols = img1.shape[:2]
    mask = np.zeros((rows, cols), dtype=np.float32)
    
    # Create gradient in overlap region
    if overlap_region[1] > overlap_region[0]:
        width = overlap_region[1] - overlap_region[0]
        for i in range(overlap_region[0], overlap_region[1]):
            alpha = (i - overlap_region[0]) / width
            mask[:, i] = alpha
    
    return mask

def warpImages(img1, img2, H):
    """
    Warp and blend two images using homography
    img1: accumulating panorama (left/previous)
    img2: new image to add (right/current)
    H: homography matrix from img2 to img1
    """
    rows1, cols1 = img1.shape[:2]
    rows2, cols2 = img2.shape[:2]

    # Get corners of both images
    list_of_points_1 = np.float32([[0,0], [0, rows1], [cols1, rows1], [cols1, 0]]).reshape(-1, 1, 2)
    temp_points = np.float32([[0,0], [0,rows2], [cols2,rows2], [cols2,0]]).reshape(-1,1,2)

    # Transform corners of img2 to img1 coordinate system
    list_of_points_2 = cv2.perspectiveTransform(temp_points, H)
    list_of_points = np.concatenate((list_of_points_1, list_of_points_2), axis=0)

    # Calculate canvas size
    [x_min, y_min] = np.int32(list_of_points.min(axis=0).ravel() - 0.5)
    [x_max, y_max] = np.int32(list_of_points.max(axis=0).ravel() + 0.5)
    
    translation_dist = [-x_min, -y_min]
    
    # Create translation matrix
    H_translation = np.array([[1, 0, translation_dist[0]], [0, 1, translation_dist[1]], [0, 0, 1]])

    # Warp img2 onto canvas
    output_img = cv2.warpPerspective(img2, H_translation.dot(H), (x_max-x_min, y_max-y_min))
    
    # Create mask for img2 (warped)
    mask2 = cv2.warpPerspective(
        np.ones((rows2, cols2), dtype=np.float32) * 255,
        H_translation.dot(H),
        (x_max-x_min, y_max-y_min)
    )
    
    # Define ROI for img1
    y_start = translation_dist[1]
    y_end = rows1 + translation_dist[1]
    x_start = translation_dist[0]
    x_end = cols1 + translation_dist[0]

    # Create mask for img1
    mask1 = np.zeros((y_max-y_min, x_max-x_min), dtype=np.float32)
    mask1[y_start:y_end, x_start:x_end] = 255

    # Find overlap region
    overlap = cv2.bitwise_and(
        (mask1 > 0).astype(np.uint8),
        (mask2 > 0).astype(np.uint8)
    )
    
    # Create blending weights
    # In overlap: use distance transform for smooth blending
    # Outside overlap: use original images
    
    # Distance transform from edges
    dist1 = cv2.distanceTransform((mask1 > 0).astype(np.uint8), cv2.DIST_L2, 5)
    dist2 = cv2.distanceTransform((mask2 > 0).astype(np.uint8), cv2.DIST_L2, 5)
    
    # Normalize distances
    dist1_norm = dist1 / (dist1 + dist2 + 1e-10)
    dist2_norm = dist2 / (dist1 + dist2 + 1e-10)
    
    # Expand dimensions for broadcasting
    dist1_norm = np.expand_dims(dist1_norm, axis=2)
    dist2_norm = np.expand_dims(dist2_norm, axis=2)
    
    # Blend images
    result = np.zeros_like(output_img, dtype=np.float32)
    
    # Add warped img2
    result += output_img.astype(np.float32) * dist2_norm
    
    # Add img1 in its region
    temp_img1 = np.zeros_like(output_img, dtype=np.uint8)
    temp_img1[y_start:y_end, x_start:x_end] = img1
    result += temp_img1.astype(np.float32) * dist1_norm
    
    # Convert back to uint8
    result = np.clip(result, 0, 255).astype(np.uint8)
    
    return result

def stitch_images(image_paths):
    """Main stitching function with improved feature matching"""
    
    # Load images
    img_list = []
    for img_path in sorted(image_paths):
        img = cv2.imread(img_path)
        if img is not None:
            img_list.append(img)
            print(f"Loaded: {img_path}")
    
    if len(img_list) == 0:
        print("Error: No images found!")
        return None
    
    print(f"Total images to stitch: {len(img_list)}")
    
    # Start with first image
    result = img_list[0]
    
    # Use SIFT for better feature detection (more robust than ORB for aerial images)
    try:
        sift = cv2.SIFT_create(nfeatures=5000)
        print("Using SIFT detector")
    except:
        # Fallback to ORB if SIFT not available
        sift = cv2.ORB_create(nfeatures=5000)
        print("Using ORB detector (SIFT not available)")
    
    # Process remaining images
    for idx, img2 in enumerate(img_list[1:], start=1):
        print(f"\n{'='*60}")
        print(f"Stitching image {idx+1}/{len(img_list)}")
        print(f"{'='*60}")
        
        img1 = result  # Accumulating panorama
        
        # Detect keypoints and compute descriptors
        print("Detecting features...")
        keypoints1, descriptors1 = sift.detectAndCompute(img1, None)
        keypoints2, descriptors2 = sift.detectAndCompute(img2, None)
        
        print(f"Features in panorama: {len(keypoints1)}")
        print(f"Features in new image: {len(keypoints2)}")
        
        if descriptors1 is None or descriptors2 is None:
            print("Warning: No descriptors found. Skipping this image.")
            continue
        
        # Match features using FLANN or BFMatcher
        if descriptors1.dtype == np.uint8:  # ORB descriptors
            matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        else:  # SIFT descriptors
            FLANN_INDEX_KDTREE = 1
            index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
            search_params = dict(checks=50)
            matcher = cv2.FlannBasedMatcher(index_params, search_params)
        
        # Find matches
        matches = matcher.knnMatch(descriptors1, descriptors2, k=2)
        
        # Apply ratio test (Lowe's ratio test)
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < 0.7 * n.distance:  # Stricter threshold
                    good_matches.append(m)
        
        print(f"Good matches found: {len(good_matches)}")
        
        # Minimum match requirement
        MIN_MATCH_COUNT = 10
        
        if len(good_matches) >= MIN_MATCH_COUNT:
            # Extract matched keypoint coordinates
            src_pts = np.float32([keypoints2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([keypoints1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            
            # Find homography with RANSAC
            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            
            if M is not None:
                matches_mask = mask.ravel().tolist()
                inliers = sum(matches_mask)
                print(f"Inliers: {inliers}/{len(good_matches)}")
                
                if inliers >= MIN_MATCH_COUNT:
                    # Warp and blend images
                    print("Warping and blending...")
                    result = warpImages(img1, img2, M)
                    print(f"Panorama size: {result.shape[1]} x {result.shape[0]}")
                else:
                    print(f"Warning: Not enough inliers ({inliers}). Skipping this image.")
            else:
                print("Warning: Homography estimation failed. Skipping this image.")
        else:
            print(f"Warning: Not enough matches ({len(good_matches)}). Skipping this image.")
    
    # Crop black borders
    print("\nCropping black borders...")
    result = crop_black_borders(result)
    
    return result

# Main execution
if __name__ == "__main__":
    # Get all drone images
    path_pattern = "*.jpg"
    image_paths = sorted(glob.glob(path_pattern))
    
    print(f"Found {len(image_paths)} images")
    
    if len(image_paths) == 0:
        print("Error: No images found!")
        sys.exit(1)
    
    # Stitch images
    result = stitch_images(image_paths)
    
    if result is not None:
        # Save result
        output_path = "stitched_panorama.jpg"
        cv2.imwrite(output_path, result, [cv2.IMWRITE_JPEG_QUALITY, 95])
        print(f"\n{'='*60}")
        print(f"✔ Saved panorama: {output_path}")
        print(f"Final size: {result.shape[1]} x {result.shape[0]} pixels")
        print(f"{'='*60}")
    else:
        print("Error: Stitching failed!")
