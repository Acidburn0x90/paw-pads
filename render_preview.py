import bpy
import os

out_path = os.path.join(os.environ.get("PAW_OUT_DIR", "."), "preview.png")

# Setup camera
cam_data = bpy.data.cameras.new("Camera")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 65.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (0, 0, 80)
cam_obj.rotation_euler = (0, 0, 0)
bpy.context.scene.camera = cam_obj

# Setup light
light_data = bpy.data.lights.new(name="Sun", type='SUN')
light_data.energy = 3.5
light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.rotation_euler = (0.6, 0.4, 0.2)

# Render settings
bpy.context.scene.render.resolution_x = 600
bpy.context.scene.render.resolution_y = 600
bpy.context.scene.render.filepath = out_path
bpy.context.scene.render.image_settings.file_format = 'PNG'

bpy.ops.render.render(write_still=True)
print("Preview rendered to:", out_path)
