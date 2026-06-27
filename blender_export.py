import bpy
import os

from scene import FileInstance

def make_scene(meshes: list[FileInstance], scene_name="scene_name"):
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
        
        root = None
        
        for obj in new_objects:
            if ".ao" in obj.name:
                root = obj
            
        if root is None:
            root = new_objects[0]
        
        root.location = mesh.transform.location
        root.rotation_euler = mesh.transform.rotation
        
        counter += 1
    
    print(f"Successfully imported {counter} .glb objects")
    
    filepath = "blender_scenes/" + scene_name + '.blend'
    bpy.ops.wm.save_as_mainfile(filepath=filepath)
        