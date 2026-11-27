from PIL import Image
import numpy as np
import os

img = Image.open(os.environ.get("PAW_REF_IMAGE", "pawpad.webp")).convert("L")
arr = np.array(img)
h, w = arr.shape
print(f"Loaded image size: {w}x{h}")

# The background is white (~220-255), pads are black (~20-60)
mask = arr < 120
print(f"Total foreground pixels: {np.sum(mask)}")

# Let's crop to the left paw (roughly left half: x from 0 to w//2)
left_mask = mask[:, :w//2]
# Find bounding boxes of connected components
import scipy.ndimage as ndi

labels, num_features = ndi.label(left_mask)
print(f"Found {num_features} components in left paw")

# Find sizes and centroids
sizes = ndi.sum(left_mask, labels, range(1, num_features + 1))
print("Sizes:", sizes)
