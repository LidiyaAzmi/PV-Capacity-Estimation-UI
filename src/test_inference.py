import torch
import cv2
import numpy as np
import matplotlib.pyplot as plt
import segmentation_models_pytorch as smp
import time

# --- 1. CONFIGURATION ---
MODEL_WEIGHTS = "assets/best_model.pth"  # Your downloaded weights
TEST_IMAGE = "assets/stitched_panorama.jpg" 
OUTPUT_FILE = "fyp_model_test_result.png"

print("Loading model architecture...")
# Must match your training setup exactly
model = smp.DeepLabV3Plus(
    encoder_name="resnet34", 
    encoder_weights=None, 
    classes=1, 
    activation=None
)

print("Loading weights to CPU...")
state_dict = torch.load(MODEL_WEIGHTS, map_location=torch.device('cpu'), weights_only=True)
model.load_state_dict(state_dict)
model.eval()

# --- 2. LOAD AND PREPROCESS IMAGE ---
print(f"Reading image: {TEST_IMAGE}")
image = cv2.imread(TEST_IMAGE)
if image is None:
    raise FileNotFoundError(f"Could not find {TEST_IMAGE}. Make sure you zoomed in on Flet first to generate it!")

image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# Pad the image so dimensions are divisible by 32 (PyTorch requirement)
h, w, _ = image_rgb.shape
pad_h = (32 - h % 32) % 32
pad_w = (32 - w % 32) % 32
padded_image = np.pad(image_rgb, ((0, pad_h), (0, pad_w), (0, 0)), mode='reflect')

# Preprocess (Scale 0-1 and convert to Tensor)
img_tensor = padded_image.astype(np.float32) / 255.0
img_tensor = np.transpose(img_tensor, (2, 0, 1)) # HWC to CHW
img_tensor = torch.from_numpy(img_tensor).unsqueeze(0) # Add batch dimension

# --- 3. RUN INFERENCE ---
print("Running prediction (this might take a few seconds on CPU)...")
with torch.no_grad():
    logits = model(img_tensor)
    probs = torch.sigmoid(logits)
    
    # Threshold at 50% probability
    mask = (probs > 0.5).float().squeeze().numpy()

# Remove the padding from the mask so it matches the original image
mask = mask[:h, :w]

# --- 4. VISUALIZATION FOR FYP REPORT ---
print("Generating overlay...")
# Create a red overlay for the detected roofs
colored_mask = np.zeros_like(image_rgb)
colored_mask[mask == 1] = [255, 0, 0] # Red

# Blend the original image and the red mask
overlay = cv2.addWeighted(image_rgb, 0.7, colored_mask, 0.5, 0)

# Plotting
fig, axs = plt.subplots(1, 3, figsize=(18, 6))
axs[0].imshow(image_rgb)
axs[0].set_title("Original ROI")
axs[0].axis("off")

axs[1].imshow(mask, cmap="gray")
axs[1].set_title("Predicted Mask")
axs[1].axis("off")

axs[2].imshow(overlay)
axs[2].set_title("Rooftop Overlay")
axs[2].axis("off")

plt.tight_layout()
plt.savefig(OUTPUT_FILE, dpi=300)
print(f"✅ Success! Open '{OUTPUT_FILE}' to see your results.")