import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix

# Clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)

out_dir = os.environ.get("PAW_OUT_DIR", ".")
os.makedirs(out_dir, exist_ok=True)

def create_domed_object(name, polygon_2d, max_height=4.5, rings=16):
    """
    Creates an organic, support-free domed solid mesh with a flat bottom on Z=0.
    """
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    
    # Bottom flat face (Z=0)
    verts_bottom = [bm.verts.new((p[0], p[1], 0.0)) for p in polygon_2d]
    # Invert order for bottom face normal pointing downward (-Z)
    bm.faces.new(verts_bottom[::-1])
    
    # Centroid for radial tapering
    cx = sum(p[0] for p in polygon_2d) / len(polygon_2d)
    cy = sum(p[1] for p in polygon_2d) / len(polygon_2d)
    
    prev_ring = verts_bottom
    for r in range(1, rings + 1):
        frac = r / rings
        # Smooth cosine / quarter-sine dome profile
        z = max_height * math.sin(frac * math.pi / 2.0)
        # Smooth organic shrinkage towards center
        scale = math.cos(frac * math.pi / 2.0)
        
        if r == rings:
            # Apex vertex at center top
            apex = bm.verts.new((cx, cy, max_height))
            for i in range(len(prev_ring)):
                i_next = (i + 1) % len(prev_ring)
                bm.faces.new([prev_ring[i], prev_ring[i_next], apex])
        else:
            curr_ring = []
            for p in polygon_2d:
                x = cx + (p[0] - cx) * scale
                y = cy + (p[1] - cy) * scale
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
    
    # Smooth shading
    for poly in mesh.polygons:
        poly.use_smooth = True
        
    return obj

def make_ellipse_polygon(cx, cy, rx, ry, angle_deg, num_pts=48):
    rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    pts = []
    for i in range(num_pts):
        th = 2.0 * math.pi * i / num_pts
        # Base ellipse
        ex = rx * math.cos(th)
        ey = ry * math.sin(th)
        # Slight organic egg shape (narrower at tip)
        ey += (ey / ry) * 0.15 * ry
        # Rotate & translate
        rx_rot = ex * cos_a - ey * sin_a + cx
        ry_rot = ex * sin_a + ey * cos_a + cy
        pts.append((rx_rot, ry_rot))
    return pts

def make_palm_polygon(cx, cy, width, height, num_pts=64):
    """
    Classic feline/canine 3-lobed palm pad
    """
    pts = []
    for i in range(num_pts):
        th = 2.0 * math.pi * i / num_pts
        # Polar harmonic profile for classic 3-lobed bean
        r = 1.0 - 0.22 * math.cos(th) + 0.18 * math.cos(2 * th) - 0.25 * math.cos(3 * th) + 0.08 * math.sin(th)
        px = r * math.sin(th) * (width / 2.0)
        py = r * math.cos(th) * (height / 2.0)
        pts.append((px + cx, py + cy))
    return pts

# --- Overall Layout for ~2-inch (50mm) cluster ---
# 1 Main palm pad at bottom center
palm_poly = make_palm_polygon(cx=0.0, cy=-6.0, width=32.0, height=24.0, num_pts=72)
palm_obj = create_domed_object("palm_pad", palm_poly, max_height=4.5)

# 4 Toes radiating in an arch across top
# Toe 1 (Far Left / Outer)
t1_poly = make_ellipse_polygon(cx=-17.0, cy=10.0, rx=5.0, ry=7.0, angle_deg=28.0)
t1_obj = create_domed_object("toe_1_outer_left", t1_poly, max_height=3.8)

# Toe 2 (Inner Left)
t2_poly = make_ellipse_polygon(cx=-6.0, cy=15.0, rx=5.5, ry=7.5, angle_deg=10.0)
t2_obj = create_domed_object("toe_2_inner_left", t2_poly, max_height=4.2)

# Toe 3 (Inner Right)
t3_poly = make_ellipse_polygon(cx=6.0, cy=15.0, rx=5.5, ry=7.5, angle_deg=-10.0)
t3_obj = create_domed_object("toe_3_inner_right", t3_poly, max_height=4.2)

# Toe 4 (Far Right / Outer)
t4_poly = make_ellipse_polygon(cx=17.0, cy=10.0, rx=5.0, ry=7.0, angle_deg=-28.0)
t4_obj = create_domed_object("toe_4_outer_right", t4_poly, max_height=3.8)

objects = [
    ("palm_pad", palm_obj),
    ("toe_1_outer_left", t1_obj),
    ("toe_2_inner_left", t2_obj),
    ("toe_3_inner_right", t3_obj),
    ("toe_4_outer_right", t4_obj),
]

# Export individual STLs
for name, obj in objects:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    stl_path = os.path.join(out_dir, f"{name}.stl")
    bpy.ops.wm.stl_export(filepath=stl_path, export_selected_objects=True)
    print(f"Exported: {stl_path}")

# Export full 5-object combined set as complete plate
bpy.ops.object.select_all(action='SELECT')
plate_path = os.path.join(out_dir, "paw_pad_complete_plate.stl")
bpy.ops.wm.stl_export(filepath=plate_path, export_selected_objects=True)
print(f"Exported: {plate_path}")

print("All paw pad models generated successfully!")
