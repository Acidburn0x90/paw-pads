from PIL import Image
import numpy as np
import scipy.ndimage as ndi
import json
import os

img = Image.open(os.environ.get("PAW_REF_IMAGE", "pawpad.webp")).convert("L")
arr = np.array(img)
h, w = arr.shape
mask = arr < 120
left_mask = mask[:, :w//2]
labels, num_features = ndi.label(left_mask)
sizes = ndi.sum(left_mask, labels, range(1, num_features + 1))
palm_idx = np.argmax(sizes) + 1

def extract_ordered_contour(comp_mask):
    # Find boundary pixels
    eroded = ndi.binary_erosion(comp_mask)
    edge = comp_mask ^ eroded
    edge_pts = np.argwhere(edge) # list of [y, x]
    
    # Simple nearest-neighbor walk to sort boundary points in sequential order
    remaining = set(map(tuple, edge_pts))
    start = edge_pts[np.argmin(edge_pts[:, 0])] # top-most point
    start = tuple(start)
    ordered = [start]
    remaining.remove(start)
    
    curr = start
    while remaining:
        # Look for neighbor within distance <= 2.5
        cy, cx = curr
        best_pt = None
        best_dist = 999999
        # Check nearby candidates
        for pt in list(remaining):
            d2 = (pt[0] - cy)**2 + (pt[1] - cx)**2
            if d2 < best_dist:
                best_dist = d2
                best_pt = pt
                if d2 <= 2:
                    break
        if best_dist > 25: # Jump too large, loop finished
            break
        ordered.append(best_pt)
        remaining.remove(best_pt)
        curr = best_pt
        
    # Subsample to ~120 points
    n = len(ordered)
    step = max(1, n // 100)
    sampled = ordered[::step]
    # Return as (x, y)
    return [(float(x), float(y)) for y, x in sampled]

palm_pts = extract_ordered_contour(labels == palm_idx)
toes = []
for idx in range(1, num_features + 1):
    if idx == palm_idx:
        continue
    c_mask = (labels == idx)
    cy, cx = ndi.center_of_mass(c_mask)
    pts = extract_ordered_contour(c_mask)
    toes.append({"center": (float(cx), float(cy)), "pts": pts})

toes.sort(key=lambda t: t["center"][0])
print(f"Palm pad ordered contour has {len(palm_pts)} points")
for i, t in enumerate(toes):
    print(f"Toe {i+1} has {len(t['pts'])} points")

with open(os.path.join(os.environ.get("PAW_OUT_DIR", "."), "ordered_contours.json"), "w") as f:
    json.dump({"palm": palm_pts, "toes": toes}, f, indent=2)

print("Saved ordered contours successfully")
