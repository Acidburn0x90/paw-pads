import bpy
import bmesh
import math
import os
import json
from mathutils import Vector

# Reset blender
bpy.ops.wm.read_factory_settings(use_empty=True)

out_dir = os.environ.get("PAW_OUT_DIR", ".")
with open(os.path.join(out_dir, "ordered_contours.json")) as f:
    data = json.load(f)

# Compute global bounding box across palm and all toes
all_xs = [pt[0] for pt in data["palm"]]
all_ys = [pt[1] for pt in data["palm"]]
for toe in data["toes"]:
    all_xs.extend([pt[0] for pt in toe["pts"]])
    all_ys.extend([pt[1] for pt in toe["pts"]])

min_x, max_x = min(all_xs), max(all_xs)
min_y, max_y = min(all_ys), max(all_ys)
span = max(max_x - min_x, max_y - min_y)

target_size_mm = 50.0 # 2 inches
scale = target_size_mm / span
center_x = (min_x + max_x) / 2.0
center_y = (min_y + max_y) / 2.0

def transform_pts(pts):
    return [((x - center_x) * scale, -(y - center_y) * scale) for x, y in pts]

def smooth_pts(pts, iters=4):
    curr = list(pts)
    n = len(curr)
    for _ in range(iters):
        nxt = []
        for i in range(n):
            p0 = curr[(i - 1) % n]
            p1 = curr[i]
            p2 = curr[(i + 1) % n]
            nxt.append((0.25 * p0[0] + 0.5 * p1[0] + 0.25 * p2[0],
                        0.25 * p0[1] + 0.5 * p1[1] + 0.25 * p2[1]))
        curr = nxt
    return curr

def build_smooth_pad(name, poly_2d, height=4.5):
    """
    Extrudes the exact 2D perimeter, bevels the top with smooth subdivision,
    giving a perfectly flat base and an organic domed top without center pinching.
    """
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    
    # 1. Base perimeter at Z=0
    base_verts = [bm.verts.new((x, y, 0.0)) for x, y in poly_2d]
    # Bottom face
    bm.faces.new(base_verts[::-1])
    
    # Inset & elevate rings for the dome
    cx = sum(p[0] for p in poly_2d) / len(poly_2d)
    cy = sum(p[1] for p in poly_2d) / len(poly_2d)
    
    rings = 14
    prev_ring = base_verts
    for r in range(1, rings + 1):
        frac = r / rings
        # Smooth bell/sine profile
        z = height * math.sin(frac * math.pi / 2.0)
        # Taper factor
        scale_fac = math.cos(frac * math.pi / 2.0)
        
        if r == rings:
            # Close with small top cap polygon or apex
            apex = bm.verts.new((cx, cy, height))
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
palm_2d = smooth_pts(transform_pts(data["palm"]), iters=5)
palm_obj = build_smooth_pad("palm_pad", palm_2d, height=4.6)

# 2. Toes
toe_names = ["toe_1_outer_left", "toe_2_inner_left", "toe_3_inner_right", "toe_4_outer_right"]
toe_objs = []
for i, t in enumerate(data["toes"]):
    t_2d = smooth_pts(transform_pts(t["pts"]), iters=5)
    h = 4.2 if (i == 1 or i == 2) else 3.8
    obj = build_smooth_pad(toe_names[i], t_2d, height=h)
    toe_objs.append((toe_names[i], obj))

# Export individual STLs
for name, obj in [("palm_pad", palm_obj)] + toe_objs:
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

# Render preview
cam_data = bpy.data.cameras.new("Camera")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 58.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (0, 0, 80)
cam_obj.rotation_euler = (0, 0, 0)
bpy.context.scene.camera = cam_obj

light_data = bpy.data.lights.new(name="Sun", type='SUN')
light_data.energy = 4.0
light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.rotation_euler = (0.6, 0.4, 0.2)

bpy.context.scene.render.resolution_x = 600
bpy.context.scene.render.resolution_y = 600
bpy.context.scene.render.filepath = os.path.join(out_dir, "preview.png")
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
print("Preview rendered!")
