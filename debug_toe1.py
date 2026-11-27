from PIL import Image
import numpy as np
import scipy.ndimage as ndi
import os

img = Image.open(os.environ.get("PAW_REF_IMAGE", "pawpad.webp")).convert("L")
arr = np.array(img)
mask = arr < 120
labels, num_features = ndi.label(mask)
c_mask = (labels == 7)

eroded = ndi.binary_erosion(c_mask)
edge = c_mask ^ eroded
edge_pts = np.argwhere(edge)
print(f"Toe 1 edge pts count: {len(edge_pts)}, x min/max: [{edge_pts[:,1].min()},{edge_pts[:,1].max()}]")

from build_from_clean_left_paw import extract_ordered_contour
pts = extract_ordered_contour(c_mask)
print(f"Extracted pts count: {len(pts)}")
