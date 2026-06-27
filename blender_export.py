import bpy
import os

from scene import FileInstance

REMOVE_NAME_PATTERNS = [".ao"]

def make_scene(meshes: list[FileInstance], scene_name="scene_name", target_location: tuple = None):
    for obj in list(bpy.data.objects):
        if obj.name == "Cube":
            bpy.data.objects.remove(obj, do_unlink=True)
    
    counter = 0
    for mesh in meshes:
        if not os.path.isfile(mesh.file_path):
            print("No mesh found in path", mesh.file_path)
            continue
        
        full_path = os.path.join(os.getcwd() + '/' + mesh.file_path)
        
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=full_path)
        after = set(bpy.data.objects)
        
        new_objects = list(after - before)
        if not new_objects:
            continue
        
        root = next((o for o in new_objects if ".ao" in o.name), new_objects[0])
        
        for obj in new_objects:
            if any(pat in obj.name for pat in REMOVE_NAME_PATTERNS):
                # Hide in viewport and render rather than deleting —
                # it's the hierarchy root so deleting would take children with it
                obj.hide_viewport = True
                obj.hide_render   = True
        
        root.location = mesh.transform.location
        root.rotation_euler = mesh.transform.rotation
        root.scale = mesh.transform.scale
        
        counter += 1
    
    print(f"Successfully imported {counter} / {len(meshes)} .glb objects")
    
    os.makedirs("blender_scenes", exist_ok=True)
    filepath = "blender_scenes/" + scene_name + '.blend'
    bpy.ops.wm.save_as_mainfile(filepath=filepath)
        