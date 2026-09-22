import torch
import segmentation_models_pytorch as smp
import cv2
import numpy as np
import os

class RooftopAnalyzer:
    def __init__(self, model_path):
        # 1. Recreate the empty architecture (MUST MATCH COLAB EXACTLY)
        # Note: Change resnet34 if you used a different backbone
        self.model = smp.DeepLabV3Plus(
            encoder_name="resnet34", 
            encoder_weights=None, # We are loading our own weights
            classes=1, 
            activation=None
        )

        # 1. Load the object from the file
        loaded_obj = torch.load(
            model_path, 
            map_location=torch.device('cpu'), 
            weights_only=False 
        )
        
        # 2. Check what PyTorch gave us and extract the weights
        if isinstance(loaded_obj, dict):
            # It's already a dictionary of weights
            weights = loaded_obj 
        else:
            # It's a full model object! Extract the weights from it.
            weights = loaded_obj.state_dict() 
            
        # 3. Load the pure weights into your architecture
        self.model.load_state_dict(weights)
        self.model.eval()
        
    def analyze_stitched_roof(self, image_path, altitude, sensor_w, focal_l, p_width, p_height, p_wattage):
        print(f"DEBUG: Attempting to load image from: {image_path}")
        img = cv2.imread(str(image_path))
        if img is None:
            raise FileNotFoundError(f"OpenCV could not find or read the image at: {image_path}")

        img_h, img_w = img.shape[:2]
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # --- 1. WHOLE IMAGE INFERENCE ---
        print("Starting Whole Image Inference...")
        
        # We shrink the massive map to 1024x1024 so your laptop doesn't crash
        # (You can try 2048 if your laptop has enough memory!)
        ai_size = 1024 
        img_resized = cv2.resize(img_rgb, (ai_size, ai_size), interpolation=cv2.INTER_LINEAR)

        # Format for PyTorch
        img_tensor = img_resized.astype(np.float32) / 255.0
        img_tensor = np.transpose(img_tensor, (2, 0, 1))
        img_tensor = torch.from_numpy(img_tensor).unsqueeze(0)

        # Predict the roof
        with torch.no_grad():
            logits = self.model(img_tensor)
            probs = torch.sigmoid(logits)
            mask_ai = (probs > 0.6).float().squeeze().numpy()

        # Stretch the AI's small mask back to the massive original resolution
        kernel = np.ones((5,5), np.uint8)
        final_mask = cv2.resize(mask_ai, (img_w, img_h), interpolation=cv2.INTER_NEAREST)

        print("Inference Complete! Processing Physics...")

        # --- 2. PHYSICS & GSD MATH ---
        gsd = ((altitude-13) * sensor_w) / (focal_l  * img_w)

        # --- 3. THE 1-METER SETBACK ---
        pixels_for_1m = int(1.0 / gsd) if gsd > 0 else 0
        if pixels_for_1m > 0:
            kernel_size = (pixels_for_1m * 2) + 1
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            safe_mask = cv2.erode(final_mask, kernel, iterations=1)
        else:
            safe_mask = final_mask

        """ # --- 3.5 SEPARATE THE 3 ROOFTOP TIERS (TILT-TOLERANT) ---
        print("Detecting roof tier boundaries...")
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (21, 21), 0) 
        
        sobel_y = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=5)
        abs_sobel_y = cv2.convertScaleAbs(sobel_y)
        
        # 1. Higher threshold to ignore corrugation and only grab deep shadows
        _, horizontal_dividers = cv2.threshold(abs_sobel_y, 40, 255, cv2.THRESH_BINARY)
        
        # 2. TILT FIX A: Connect the broken diagonal steps using a 30x5 closing block
        connect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
        connected_dividers = cv2.morphologyEx(horizontal_dividers, cv2.MORPH_CLOSE, connect_kernel)
        
        # 3. TILT FIX B: A thicker 150x5 line detector that allows for the building's angle
        line_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (150, 5))
        true_dividers = cv2.morphologyEx(connected_dividers, cv2.MORPH_OPEN, line_kernel)
        
        internal_dividers = cv2.bitwise_and(true_dividers, true_dividers, mask=safe_mask.astype(np.uint8))
        
        # 4. Reduced the walkway gap slightly to 1.0 meters to pack more panels in
        tier_gap_px = int(1.0 / gsd) if gsd > 0 else 10
        tier_kernel = np.ones((tier_gap_px, tier_gap_px), np.uint8)
        exclusion_zones = cv2.dilate(internal_dividers, tier_kernel, iterations=2)
        
        safe_mask[exclusion_zones > 0] = 0 """
        # =========================================================

        # --- 4. PHYSICAL PANEL GRID SIMULATION ---
        print("Drawing engineering grid...")
        
        pw_px = max(1, int(p_width / gsd))
        ph_px = max(1, int(p_height / gsd))
        gap_px = max(1, int(0.05 / gsd)) 
        
        panel_overlay = img_rgb.copy()
        physically_placed_panels = 0
        
        y_indices, x_indices = np.where(safe_mask == 1)
        if len(y_indices) > 0:
            y_min, y_max = np.min(y_indices), np.max(y_indices)
            x_min, x_max = np.min(x_indices), np.max(x_indices)

            for y in range(y_min, y_max, ph_px + gap_px):
                for x in range(x_min, x_max, pw_px + gap_px):
                    
                    if y + ph_px <= img_h and x + pw_px <= img_w:
                        panel_region = safe_mask[y:y+ph_px, x:x+pw_px]
                        
                        # COVERAGE FIX: Relaxed from 0.95 to 0.85
                        # This allows panels to get closer to the edges and ignore tiny AI mask imperfections
                        if np.mean(panel_region) > 0.85: 
                            
                            cv2.rectangle(panel_overlay, (x, y), (x + pw_px, y + ph_px), (0, 75, 150), -1) 
                            cv2.rectangle(panel_overlay, (x, y), (x + pw_px, y + ph_px), (200, 220, 255), 2) 
                            
                            physically_placed_panels += 1

        # Calculate final capacity
        safe_area_m2 = np.sum(safe_mask) * (gsd ** 2)
        pv_capacity_kwp = (physically_placed_panels * p_wattage) / 1000.0

        # --- 5. VISUALIZATION BLENDING ---
        # Draw the red AI detection boundary for context
        contours, _ = cv2.findContours(final_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(img_rgb, contours, -1, (255, 0, 0), 3)

        # Blend the blue panels onto the original image (60% opaque)
        cv2.addWeighted(panel_overlay, 0.7, img_rgb, 0.3, 0, img_rgb)
        
        output_dir = os.path.dirname(image_path)
        output_path = os.path.join(output_dir, "final_estimation_result.jpg")
        
        success = cv2.imwrite(output_path, cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR))
        if not success:
            print(f"CRITICAL ERROR: OpenCV failed to save the image to {output_path}")

        # Return the new physically simulated counts!
        return output_path, round(safe_area_m2, 2), physically_placed_panels, round(pv_capacity_kwp, 2)