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
# Left paw
left_mask = mask[:, :w//2]
labels, num_features = ndi.label(left_mask)
sizes = ndi.sum(left_mask, labels, range(1, num_features + 1))
palm_idx = np.argmax(sizes) + 1

# Standard contour following (Moore-Neighbor tracing / sorted edge tracking)
def trace_boundary(comp_mask):
    # Pad to prevent out of bounds
    padded = np.pad(comp_mask, 1, mode='constant', constant_values=False)
    # Find start point (highest row, leftmost col)
    ys, xs = np.where(padded)
    start_y, start_x = ys[0], xs[0]
    
    # Directions: 8-neighborhood clockwise starting from up-left
    # 0: (-1,0), 1: (-1,1), 2: (0,1), 3: (1,1), 4: (1,0), 5: (1,-1), 6: (0,-1), 7: (-1,-1)
    dirs = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
    
    boundary = []
    curr = (start_y, start_x)
    b_dir = 7
    
    for _ in range(2000):
        boundary.append((curr[1] - 1, curr[0] - 1)) # back to unpadded (x, y)
        found = False
        start_search = (b_dir + 5) % 8
        for i in range(8):
            d = (start_search + i) % 8
            dy, dx = dirs[d]
            ny, nx = curr[0] + dy, curr[1] + dx
            if padded[ny, nx]:
                curr = (ny, nx)
                b_dir = d
                found = True
                break
        if not found or (curr == (start_y, start_x) and len(boundary) > 2):
            break
            
    # Subsample to ~120 evenly spaced points
    n = len(boundary)
    step = max(1, n // 120)
    sampled = boundary[::step]
    return [(float(x), float(y)) for x, y in sampled]

palm_pts = trace_boundary(labels == palm_idx)
toes = []
for idx in range(1, num_features + 1):
    if idx == palm_idx:
        continue
    c_mask = (labels == idx)
    cy, cx = ndi.center_of_mass(c_mask)
    pts = trace_boundary(c_mask)
    toes.append({"center": (float(cx), float(cy)), "pts": pts})

toes.sort(key=lambda t: t["center"][0])

with open(os.path.join(os.environ.get("PAW_OUT_DIR", "."), "precise_traced_polygons.json"), "w") as f:
    json.dump({"palm": palm_pts, "toes": toes}, f, indent=2)

print(f"Traced palm ({len(palm_pts)} pts) and {len(toes)} toes successfully.")
