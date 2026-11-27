import bpy
import bmesh
import math
import os
import json
from mathutils import Vector

# Reset blender
bpy.ops.wm.read_factory_settings(use_empty=True)

out_dir = os.environ.get("PAW_OUT_DIR", ".")
json_path = os.path.join(out_dir, "extracted_polygons.json")

with open(json_path) as f:
    data = json.load(f)

# Find global bounding box of all parts in pixel space to scale to 50.8mm (2 inches)
all_xs = []
all_ys = []
for pt in data["palm"]["pts"]:
    all_xs.append(pt[0])
    all_ys.append(pt[1])
for toe in data["toes"]:
    for pt in toe["pts"]:
        all_xs.append(pt[0])
        all_ys.append(pt[1])

min_x, max_x = min(all_xs), max(all_xs)
min_y, max_y = min(all_ys), max(all_ys)
pixel_width = max_x - min_x
pixel_height = max_y - min_y
pixel_span = max(pixel_width, pixel_height)

# Desired total span = 50.0 mm
target_size_mm = 50.0
scale = target_size_mm / pixel_span

# Centering offset (in Blender, Y is up, in image Y is down)
center_x = (min_x + max_x) / 2.0
center_y = (min_y + max_y) / 2.0

def transform_pts(pts):
    res = []
    for x, y in pts:
        nx = (x - center_x) * scale
        ny = -(y - center_y) * scale  # flip Y so top is positive Y
        res.append((nx, ny))
    return res

def smooth_polygon(pts, iterations=3):
    """Laplacian smoothing on closed polygon"""
    curr = list(pts)
    n = len(curr)
    for _ in range(iterations):
        smoothed = []
        for i in range(n):
            p_prev = curr[(i - 1) % n]
            p_curr = curr[i]
            p_next = curr[(i + 1) % n]
            sx = 0.25 * p_prev[0] + 0.5 * p_curr[0] + 0.25 * p_next[0]
            sy = 0.25 * p_prev[1] + 0.5 * p_curr[1] + 0.25 * p_next[1]
            smoothed.append((sx, sy))
        curr = smoothed
    return curr

def build_domed_mesh(name, poly_2d, max_height=4.5, rings=20):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    
    # Bottom flat face
    verts_bottom = [bm.verts.new((p[0], p[1], 0.0)) for p in poly_2d]
    # Winding for bottom face pointing down (-Z)
    bm.faces.new(verts_bottom[::-1])
    
    cx = sum(p[0] for p in poly_2d) / len(poly_2d)
    cy = sum(p[1] for p in poly_2d) / len(poly_2d)
    
    prev_ring = verts_bottom
    for r in range(1, rings + 1):
        frac = r / rings
        # Smooth quarter-sine elevation
        z = max_height * math.sin(frac * math.pi / 2.0)
        # Organic cosine taper
        scale_fac = math.cos(frac * math.pi / 2.0)
        
        if r == rings:
            apex = bm.verts.new((cx, cy, max_height))
            for i in range(len(prev_ring)):
                i_next = (i + 1) % len(prev_ring)
                bm.faces.new([prev_ring[i], prev_ring[i_next], apex])
        else:
            curr_ring = []
            for p in poly_2d:
                x = cx + (p[0] - cx) * scale_fac
                y = cy + (p[1] - cy) * scale_fac
                curr_ring.append(bm.verts.new((x, y, z)))
            for i in range(len(prev_ring)):
                i_next = (i + 1) % len(prev_ring)
                bm.faces.new([
                    prev_ring[i],
                    prev_ring[i_next],
                    curr_ring[i_next],
                    curr_ring[i]
                ])
            prev_ring = curr_ring
            
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    
    for poly in mesh.polygons:
        poly.use_smooth = True
        
    return obj

# 1. Palm Pad
palm_pts = transform_pts(data["palm"]["pts"])
palm_pts = smooth_polygon(palm_pts, iterations=4)
palm_obj = build_domed_mesh("palm_pad", palm_pts, max_height=4.8)

# 2. Toes
toe_objs = []
toe_names = [
    "toe_1_outer_left",
    "toe_2_inner_left",
    "toe_3_inner_right",
    "toe_4_outer_right"
]
for i, toe_data in enumerate(data["toes"]):
    t_pts = transform_pts(toe_data["pts"])
    t_pts = smooth_polygon(t_pts, iterations=4)
    # Heights: middle toes slightly taller, outer toes slightly lower
    h = 4.2 if (i == 1 or i == 2) else 3.8
    obj = build_domed_mesh(toe_names[i], t_pts, max_height=h)
    toe_objs.append((toe_names[i], obj))

# Export individual STLs
all_items = [("palm_pad", palm_obj)] + toe_objs
for name, obj in all_items:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    path = os.path.join(out_dir, f"{name}.stl")
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)
    print(f"Exported: {path}")

# Export combined plate
bpy.ops.object.select_all(action='SELECT')
plate_path = os.path.join(out_dir, "paw_pad_complete_plate.stl")
bpy.ops.wm.stl_export(filepath=plate_path, export_selected_objects=True)
print(f"Exported complete plate: {plate_path}")

print("Paw pad generation matched to reference image completed!")
