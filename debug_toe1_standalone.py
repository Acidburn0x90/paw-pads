from PIL import Image
import numpy as np
import scipy.ndimage as ndi
import json
import os

with open(os.path.join(os.environ.get("PAW_OUT_DIR", "."), "clean_left_paw.json")) as f:
    d = json.load(f)

t1 = d["toes"][0]["pts"]
print(f"Toe 1 pts in JSON: {len(t1)}")
xs = [p[0] for p in t1]
ys = [p[1] for p in t1]
print(f"X range: [{min(xs)}, {max(xs)}], Y range: [{min(ys)}, {max(ys)}]")
print("First 10 pts:", t1[:10])
print("Last 10 pts:", t1[-10:])
