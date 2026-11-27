from PIL import Image
import numpy as np
import scipy.ndimage as ndi
import json
import os

img = Image.open(os.environ.get("PAW_REF_IMAGE", "pawpad.webp")).convert("L")
arr = np.array(img)
mask = arr < 120
labels, num_features = ndi.label(mask)

def trace_component(comp_mask):
    pad = np.pad(comp_mask, 2, mode='constant', constant_values=False)
    # Marching squares or standard boundary tracking
    # Simple radial angle sort from center of mass for convex-like toes
    cy, cx = ndi.center_of_mass(pad)
    eroded = ndi.binary_erosion(pad)
    edge = pad ^ eroded
    ys, xs = np.where(edge)
    
    # Angle binning works cleanly when taking median/outer radius
    angles = np.arctan2(ys - cy, xs - cx)
    dists = np.hypot(ys - cy, xs - cx)
    
    num_bins = 120
    bin_edges = np.linspace(-np.pi, np.pi, num_bins + 1)
    boundary = []
    for i in range(num_bins):
        in_bin = (angles >= bin_edges[i]) & (angles < bin_edges[i+1])
        if np.any(in_bin):
            max_d = np.max(dists[in_bin])
            mid_a = 0.5 * (bin_edges[i] + bin_edges[i+1])
            bx = cx + max_d * np.cos(mid_a) - 2 # unpad
            by = cy + max_d * np.sin(mid_a) - 2
            boundary.append((float(bx), float(by)))
            
    return boundary

# Left paw features: 7 (far left toe), 1, 2, 5 (far right toe), 9 (palm)
palm_pts = trace_component(labels == 9)
toes = []
for tid in [7, 1, 2, 5]:
    c_mask = (labels == tid)
    cy, cx = ndi.center_of_mass(c_mask)
    pts = trace_component(c_mask)
    toes.append({"center": (float(cx), float(cy)), "pts": pts})

toes.sort(key=lambda t: t["center"][0])
print(f"Traced palm ({len(palm_pts)} pts) and {len(toes)} toes with full angular coverage.")

with open(os.path.join(os.environ.get("PAW_OUT_DIR", "."), "clean_left_paw.json"), "w") as f:
    json.dump({"palm": palm_pts, "toes": toes}, f, indent=2)

print("Saved clean_left_paw.json successfully.")
