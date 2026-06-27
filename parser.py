import json
import os
import sys

from scene import *

def location_to_tuple(location):
    return (location["X"], location["Y"], location["Z"])

def load_scene(filename, target, nearby_distance) -> list[FileInstance]:

    if (not os.path.isfile(filename)):
        print("No scene was found with path", filename)
        return []
    
    with open(filename) as f:
        raw = json.load(f)

    #mesh with its path, transform, distance to the target
    mesh_instances = []
    
    target_object = FileInstance()
    
    #mesh or skeletal mesh and its count
    mesh_count = dict()
    
    #objects by name to check faster
    objects_by_name: dict[str, FileInstance] = dict()
    
    #how many components of object were processed
    objects_components_found = dict()

    for obj in raw:
        if ('Outer' not in obj):
            continue
        
        outer_name = obj['Outer']['ObjectName']
        if not outer_name in objects_by_name:
            objects_by_name[outer_name] = FileInstance()
            objects_components_found[outer_name] = 0
        
        if (obj['Type'] == 'SceneComponent'):
            obj_properties = obj['Properties']
            if 'RelativeLocation' not in obj_properties:
                continue
            
            location_tuple = location_to_tuple(obj_properties["RelativeLocation"])
            rotation_tuple = ()
            if "RelativeRotation" in obj_properties:
                rotation = obj_properties["RelativeRotation"]
                rotation_tuple = (rotation["Pitch"], rotation["Yaw"], rotation["Roll"])
            else:
                rotation_tuple = (0, 0, 0)
            transform = Transform(location=location_tuple, rotation=rotation_tuple)
            
            if target.lower() in outer_name.lower():
                target_object.transform = transform
            else:
                objects_by_name[outer_name].transform = transform
                objects_components_found[outer_name] += 1
                
        elif ('SkeletalMeshComponent' in obj['Type']):
            object_path = obj['Template']['ObjectPath']
            if target.lower() in outer_name.lower():
                target_object.file_path = object_path
            else:
                objects_by_name[outer_name].file_path = object_path
                
                if object_path not in mesh_count:
                    mesh_count[object_path] = 0
                
                mesh_count[object_path] += 1
                
                objects_components_found[outer_name] += 1
                
                
    target_location = target_object.transform.location
                
    for objname, value in objects_by_name.items():
        if objects_components_found[objname] < 2:
            continue
        
        mesh_location = value.transform.location
        
        distance = ((target_location[0] - mesh_location[0])**2 + (target_location[1] - mesh_location[1])**2 + (target_location[2] - mesh_location[2])**2)**0.5
        
        if (distance > nearby_distance and mesh_count[value.file_path] > 1):
            continue
        
        mesh_instances.append(value)
    
    mesh_instances.append(target_object)
    
    return mesh_instances

def find_mesh_path(blueprint_local_path) -> FileInstance:
    if (not os.path.isfile(blueprint_local_path)):
        print("No blueprint was found in path", blueprint_local_path)
        return FileInstance
    
    with open(blueprint_local_path) as f:
        raw = json.load(f)
        
    for obj in raw:
        if ('SkeletalMeshComponent' not in obj['Type']):
            continue
            
        mesh_path = obj['Properties']['SkeletalMesh']['ObjectPath']
        location_tuple = (0, 0, 0)
        if ('RelativeLocation' in obj['Properties']):
            location = obj['Properties']['RelativeLocation']
            location_tuple = location_to_tuple(location)
        
        return FileInstance(file_path=mesh_path, transform=Transform(location=location_tuple))
    