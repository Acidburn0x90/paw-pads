from PIL import Image
import numpy as np
import scipy.ndimage as ndi
import json
import os

img = Image.open(os.environ.get("PAW_REF_IMAGE", "pawpad.webp")).convert("L")
arr = np.array(img)
mask = arr < 120

labels, num_features = ndi.label(mask)

# Left paw components from our analysis:
# Feature 7: Toe 1 (outer left, x=[16,60])
# Feature 1: Toe 2 (mid left, x=[51,92])
# Feature 2: Toe 3 (mid right, x=[98,140])
# Feature 5: Toe 4 (outer right, x=[135,177])
# Feature 9: Palm (x=[43,159])

left_toes_ids = [7, 1, 2, 5]
palm_id = 9

def extract_ordered_contour(comp_mask):
    eroded = ndi.binary_erosion(comp_mask)
    edge = comp_mask ^ eroded
    edge_pts = np.argwhere(edge)
    
    # Start at top-most point
    start = edge_pts[np.argmin(edge_pts[:, 0])]
    remaining = set(map(tuple, edge_pts))
    start = tuple(start)
    ordered = [start]
    remaining.remove(start)
    
    curr = start
    while remaining:
        cy, cx = curr
        best_pt = None
        best_dist = 999999
        for pt in list(remaining):
            d2 = (pt[0] - cy)**2 + (pt[1] - cx)**2
            if d2 < best_dist:
                best_dist = d2
                best_pt = pt
                if d2 <= 2:
                    break
        if best_dist > 25:
            break
        ordered.append(best_pt)
        remaining.remove(best_pt)
        curr = best_pt
        
    n = len(ordered)
    step = max(1, n // 100)
    sampled = ordered[::step]
    return [(float(x), float(y)) for y, x in sampled]

palm_pts = extract_ordered_contour(labels == palm_id)
toes = []
for tid in left_toes_ids:
    c_mask = (labels == tid)
    cy, cx = ndi.center_of_mass(c_mask)
    pts = extract_ordered_contour(c_mask)
    toes.append({"center": (float(cx), float(cy)), "pts": pts})

with open(os.path.join(os.environ.get("PAW_OUT_DIR", "."), "clean_left_paw.json"), "w") as f:
    json.dump({"palm": palm_pts, "toes": toes}, f, indent=2)

print("Saved clean left paw successfully.")
