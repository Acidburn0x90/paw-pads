from PIL import Image
import numpy as np
import scipy.ndimage as ndi
import json
import os

img = Image.open(os.environ.get("PAW_REF_IMAGE", "pawpad.webp")).convert("L")
arr = np.array(img)
h, w = arr.shape

# Threshold foreground
mask = arr < 120
left_mask = mask[:, :w//2]
labels, num_features = ndi.label(left_mask)
sizes = ndi.sum(left_mask, labels, range(1, num_features + 1))

# Find the components: 4 toes and 1 palm pad (the largest, size ~7032)
palm_idx = np.argmax(sizes) + 1

# Extract contours using marching squares or simple boundary tracing
def get_contour(component_mask):
    # Dilate minus erode to get edge pixels
    eroded = ndi.binary_erosion(component_mask)
    edge = component_mask ^ eroded
    ys, xs = np.where(edge)
    
    # Sort points radially around centroid
    cy, cx = np.mean(ys), np.mean(xs)
    angles = np.arctan2(ys - cy, xs - cx)
    
    # Bin by angle to get a clean ordered closed polygon
    num_bins = 100
    bin_angles = np.linspace(-np.pi, np.pi, num_bins, endpoint=False)
    pts = []
    for i in range(num_bins):
        a_min = bin_angles[i]
        a_max = bin_angles[(i+1)%num_bins] if i < num_bins-1 else np.pi
        in_bin = (angles >= a_min) & (angles < a_max)
        if np.any(in_bin):
            # take outermost point in this angle bin
            b_xs = xs[in_bin]
            b_ys = ys[in_bin]
            dists = (b_xs - cx)**2 + (b_ys - cy)**2
            max_i = np.argmax(dists)
            pts.append((float(b_xs[max_i]), float(b_ys[max_i])))
        else:
            # interpolate
            pass
    return pts, (float(cx), float(cy))

palm_contour, palm_center = get_contour(labels == palm_idx)
print(f"Extracted {len(palm_contour)} contour points for palm pad, center={palm_center}")

# Toe components
toes = []
for idx in range(1, num_features + 1):
    if idx == palm_idx:
        continue
    c_pts, center = get_contour(labels == idx)
    toes.append({"center": center, "pts": c_pts})

# Sort toes from left to right by center X
toes.sort(key=lambda t: t["center"][0])
print(f"Extracted {len(toes)} toes")

# Save to JSON
data = {
    "palm": {"center": palm_center, "pts": palm_contour},
    "toes": toes,
    "image_w": w//2,
    "image_h": h
}
with open(os.path.join(os.environ.get("PAW_OUT_DIR", "."), "extracted_polygons.json"), "w") as f:
    json.dump(data, f, indent=2)

print("Saved polygon data successfully")
