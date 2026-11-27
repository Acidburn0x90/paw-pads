import bpy
import bmesh
import math
from mathutils import Vector, Matrix

# Clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)

def create_dome_mesh(points_2d, height=4.5, bevel_res=8):
    """
    Given a list of 2D polygon vertices (XY), creates a 3D solid with:
    - Flat bottom at Z=0
    - Smoothly domed/beveled top up to Z=height
    """
    bm = bmesh.new()
    
    # Bottom face
    verts_bottom = [bm.verts.new((p[0], p[1], 0.0)) for p in points_2d]
    bm.faces.new(verts_bottom)
    
    # Calculate centroid
    cx = sum(p[0] for p in points_2d) / len(points_2d)
    cy = sum(p[1] for p in points_2d) / len(points_2d)
    
    # We can create concentric rings to make a nice organic dome
    rings = 6
    prev_verts = verts_bottom
    for r in range(1, rings + 1):
        frac = r / rings
        z = height * math.sin(frac * math.pi / 2.0)
        scale = 1.0 - frac * 0.75  # taper inward
        
        if r == rings:
            # Apex vertex
            apex = bm.verts.new((cx, cy, height))
            for i in range(len(prev_verts)):
                bm.faces.new([prev_verts[i], prev_verts[(i + 1) % len(prev_verts)], apex])
        else:
            curr_verts = []
            for p in points_2d:
                x = cx + (p[0] - cx) * scale
                y = cy + (p[1] - cy) * scale
                curr_verts.append(bm.verts.new((x, y, z)))
            
            for i in range(len(prev_verts)):
                bm.faces.new([
                    prev_verts[i],
                    prev_verts[(i + 1) % len(prev_verts)],
                    curr_verts[(i + 1) % len(prev_verts)],
                    curr_verts[i]
                ])
            prev_verts = curr_verts

    bm.normal_update()
    return bm

def create_toe_polygon(rx, ry, num_pts=32):
    pts = []
    for i in range(num_pts):
        th = 2.0 * math.pi * i / num_pts
        pts.append((rx * math.cos(th), ry * math.sin(th)))
    return pts

def create_palm_polygon(scale=1.0, num_pts=64):
    """
    Parametric 3-lobed palm pad outline centered around (0,0)
    """
    pts = []
    for i in range(num_pts):
        th = 2.0 * math.pi * i / num_pts
        # Base heart/kidney formula
        # r(theta) = 1 + 0.3*cos(theta) - 0.2*cos(2*theta) + 0.15*cos(3*theta)
        r = 1.0 - 0.25 * math.sin(th) + 0.2 * math.cos(2 * th) - 0.15 * math.cos(4 * th)
        x = scale * r * math.cos(th) * 1.35
        y = scale * r * math.sin(th) * 1.05
        pts.append((x, y))
    return pts

print("Geometry helper defined")
