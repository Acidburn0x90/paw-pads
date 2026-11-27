import bpy
import bmesh
import math
import os
import json

bpy.ops.wm.read_factory_settings(use_empty=True)

out_dir = os.environ.get("PAW_OUT_DIR", ".")
with open(os.path.join(out_dir, "clean_left_paw.json")) as f:
    data = json.load(f)

# Global bounding box across all parts to get clean 50mm scale
all_xs = [pt[0] for pt in data["palm"]]
all_ys = [pt[1] for pt in data["palm"]]
for toe in data["toes"]:
    all_xs.extend([pt[0] for pt in toe["pts"]])
    all_ys.extend([pt[1] for toe in data["toes"] for pt in toe["pts"]])

min_x, max_x = min(all_xs), max(all_xs)
min_y, max_y = min(all_ys), max(all_ys)
span = max(max_x - min_x, max_y - min_y)

target_size_mm = 50.0  # 2 inches total
scale = target_size_mm / span
center_x = (min_x + max_x) / 2.0
center_y = (min_y + max_y) / 2.0

def transform_pts(pts, mirror_x=False):
    res = []
    for x, y in pts:
        nx = (x - center_x) * scale
        ny = -(y - center_y) * scale
        if mirror_x:
            nx = -nx
        res.append((nx, ny))
    return res

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
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    
    base_verts = [bm.verts.new((x, y, 0.0)) for x, y in poly_2d]
    # Check polygon winding so bottom face normal points strictly down (-Z)
    bm.faces.new(base_verts[::-1])
    
    cx = sum(p[0] for p in poly_2d) / len(poly_2d)
    cy = sum(p[1] for p in poly_2d) / len(poly_2d)
    
    rings = 16
    prev_ring = base_verts
    for r in range(1, rings + 1):
        frac = r / rings
        z = height * math.sin(frac * math.pi / 2.0)
        scale_fac = math.cos(frac * math.pi / 2.0)
        
        if r == rings:
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
    # Ensure normals are oriented consistently outwards
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    
    for poly in mesh.polygons:
        poly.use_smooth = True
        
    return obj

def generate_paw_set(prefix, mirror_x=False):
    palm_2d = smooth_pts(transform_pts(data["palm"], mirror_x=mirror_x), iters=5)
    # If mirrored, reverse points so winding order remains counter-clockwise
    if mirror_x:
        palm_2d = palm_2d[::-1]
    palm_obj = build_smooth_pad(f"{prefix}_palm_pad", palm_2d, height=4.6)
    
    toe_names = [
        f"{prefix}_toe_1_outer_left" if not mirror_x else f"{prefix}_toe_1_outer_right",
        f"{prefix}_toe_2_inner_left" if not mirror_x else f"{prefix}_toe_2_inner_right",
        f"{prefix}_toe_3_inner_right" if not mirror_x else f"{prefix}_toe_3_inner_left",
        f"{prefix}_toe_4_outer_right" if not mirror_x else f"{prefix}_toe_4_outer_left"
    ]
    
    toe_objs = []
    for i, t in enumerate(data["toes"]):
        t_2d = smooth_pts(transform_pts(t["pts"], mirror_x=mirror_x), iters=5)
        if mirror_x:
            t_2d = t_2d[::-1]
        h = 4.2 if (i == 1 or i == 2) else 3.8
        obj = build_smooth_pad(toe_names[i], t_2d, height=h)
        toe_objs.append((toe_names[i], obj))
        
    return [palm_obj] + [obj for _, obj in toe_objs], [(f"{prefix}_palm_pad", palm_obj)] + toe_objs

# Build Left Paw
left_objs, left_named = generate_paw_set("left", mirror_x=False)
# Build Right Paw
right_objs, right_named = generate_paw_set("right", mirror_x=True)

# Export individual left STLs
for name, obj in left_named:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    path = os.path.join(out_dir, f"{name}.stl")
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)

# Export individual right STLs
for name, obj in right_named:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    path = os.path.join(out_dir, f"{name}.stl")
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)

# Export complete left plate
bpy.ops.object.select_all(action='DESELECT')
for obj in left_objs:
    obj.select_set(True)
bpy.context.view_layer.objects.active = left_objs[0]
bpy.ops.wm.stl_export(filepath=os.path.join(out_dir, "paw_pad_left_plate.stl"), export_selected_objects=True)

# Export complete right plate
bpy.ops.object.select_all(action='DESELECT')
for obj in right_objs:
    obj.select_set(True)
bpy.context.view_layer.objects.active = right_objs[0]
bpy.ops.wm.stl_export(filepath=os.path.join(out_dir, "paw_pad_right_plate.stl"), export_selected_objects=True)

# Offset right paw by +65mm along X for dual plate layout and preview
for obj in right_objs:
    obj.location.x += 65.0
for obj in left_objs:
    obj.location.x -= 32.5
for obj in right_objs:
    obj.location.x -= 32.5

# Export combined dual pair plate (Both Left and Right together)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.wm.stl_export(filepath=os.path.join(out_dir, "paw_pad_pair_both_shoes_plate.stl"), export_selected_objects=True)

# Render side-by-side preview of Left and Right
cam_data = bpy.data.cameras.new("Camera")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 130.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (0, 0, 100)
cam_obj.rotation_euler = (0, 0, 0)
bpy.context.scene.camera = cam_obj

light_data = bpy.data.lights.new(name="Sun", type='SUN')
light_data.energy = 4.0
light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.rotation_euler = (0.6, 0.4, 0.2)

bpy.context.scene.render.resolution_x = 900
bpy.context.scene.render.resolution_y = 500
bpy.context.scene.render.filepath = os.path.join(out_dir, "preview_pair.png")
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)

print("Generated both Left and Right paw sets and rendered pair preview successfully!")
