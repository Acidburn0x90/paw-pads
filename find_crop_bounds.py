from PIL import Image
import numpy as np
import scipy.ndimage as ndi
import os

img = Image.open(os.environ.get("PAW_REF_IMAGE", "pawpad.webp")).convert("L")
arr = np.array(img)
h, w = arr.shape
mask = arr < 120
print(f"Total image: {w}x{h}")

labels, num_features = ndi.label(mask)
sizes = ndi.sum(mask, labels, range(1, num_features + 1))

# Find the components and their bounding boxes
for idx in range(1, num_features + 1):
    c_mask = (labels == idx)
    ys, xs = np.where(c_mask)
    print(f"Feature {idx}: size={len(ys)}, x=[{xs.min()},{xs.max()}], y=[{ys.min()},{ys.max()}]")
