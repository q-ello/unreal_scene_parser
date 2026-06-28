import json
import os
import sys

from scene import *

#region config
#probably you need to tweak this for other UE games or map formats
#the order of components where relative location can live
LOCATION_COMPONENT_PRIORITY = ["SceneComponent", "CapsuleComponent", "BoxComponent", "HbkSkeletalMeshComponent", "SkeletalMeshComponent", "StaticMeshComponent"]
#maps component type names
MESH_COMPONENT_TYPES = {
    "SkeletalMeshComponent": "SkeletalMesh",
    "HbkSkeletalMeshComponent": "SkeletalMesh",
    "HbkStaticMeshComponent": "StaticMesh",
    "StaticMeshComponent": "StaticMesh"
}
#preferred names for multiple scene components
ROOT_COMPONENT_NAMES = {"RootComp", "DefaultSceneRoot"}

#some meshes are inlined some baked in external bp
INLINE_MESH_KEYS = ["SkeletalMesh", "StaticMesh", "Mesh"]

#endregion

#region helpers
def location_to_tuple(location: dict):
    return (location.get("X", 0), location.get("Y", 0), location.get("Z", 0))

def rotation_to_tuple(rot: dict) -> tuple:
    return (rot.get("Pitch", 0), rot.get("Yaw", 0), rot.get("Roll", 0))

def scale_to_tuple(scale: dict) -> tuple:
    return (scale.get("X", 1), scale.get("Y", 1), scale.get("Z", 1))

#return the asset-path property for this component type or None
def mesh_property_key(component_type: str) -> str | None:
    for type_key, prop_key in MESH_COMPONENT_TYPES.items():
        if type_key in component_type:
            return prop_key
    return None

#check what component exactly has location
def pick_location(candidates: list[dict]) -> dict | None:
    by_type: dict[str, list[dict]] = {}
    
    for comp in candidates:
        by_type.setdefault(comp.get("Type", ""), []).append(comp)
    
    for priority_type in LOCATION_COMPONENT_PRIORITY:
        comps = by_type.get(priority_type, [])
        #prefer known root names first
        for comp in comps:
            if comp.get("Name", "") in ROOT_COMPONENT_NAMES and "RelativeLocation" in comp.get("Priorities", {}):
                return comp
        for comp in comps:
            if "RelativeLocation" in comp.get("Properties", {}):
                return comp
     
    #fallback: any component with a location        
    for comp in candidates:
        if "RelativeLocation" in comp.get("Priorities", {}):
            return comp
    return None

#best mesh file for the actor. tries inline first, then falls back to template
def resolve_mesh(actor_obj: dict, comps: list[dict]) -> str:
    actor_props = actor_obj.get("Properties", {})
    for key in INLINE_MESH_KEYS:
        ref = actor_props.get(key)
        if isinstance(ref, dict):
            path = ref.get("ObjectPath", "")
            #reject internal level references that contain the map name
            if path and "/Maps/" not in path:
                return path
    
    #bp file
    for comp in comps:
        comp_type = comp.get("Type", "")
        matched_key = next((prop for type_key, prop in MESH_COMPONENT_TYPES.items() if type_key in comp_type), None)
        
        if matched_key is None:
            continue
        
        template = comp.get("Template", {})
        path = template.get("ObjectPath", "")
        if path:
            return path #then will find a path with find_mesh_path
    
    return ""

#endregion

#region api
def load_scene(filename: str, target: str, nearby_distance: float, verbose: bool = False) -> list[FileInstance]:

    if (not os.path.isfile(filename)):
        print("No scene was found with path", filename)
        return []
    
    with open(filename) as f:
        raw = json.load(f)
        
    #group all objects by their outer name
    actor_components: dict[str, list[dict]] = {}
    for obj in raw:
        if "Outer" not in obj:
            continue
        outer_name = obj.get("Outer", {}).get("ObjectName", "")
        actor_components.setdefault(outer_name, []).append(obj)
    
    #resolve each actor to file instance
    instances: dict[str, FileInstance] = {}
    
    for outer_name, comps in actor_components.items():
        #split: actor-level object vs child components
        actor_obj = next((c for c in comps if "PersistentLevel" in c.get("Outer", {}).get("ObjectName", "") and c.get("Name", "") in outer_name), None)
        children = [c for c in comps if c is not actor_obj]
        
        #location
        loc_comp = pick_location(children or comps)
        if loc_comp is None:
            continue
        props = loc_comp["Properties"]
        location = location_to_tuple(props.get("RelativeLocation", {}))
        rotation = rotation_to_tuple(props.get("RelativeRotation", {}))
        scale = scale_to_tuple(props.get("RelativeScale3D", {}))
        transform = Transform(location, rotation, scale)
        
        #mesh path
        file_path = resolve_mesh(actor_obj or {}, children)
        
        instances[outer_name] = FileInstance(file_path, transform)
    
    #find target
    target_lower = target.lower()
    target_instance = FileInstance()
    actor_file_paths: dict[str, str] = {} #outer name -> file path
    
    for outer_name, inst in instances.items():
        if target_lower in outer_name.lower():
            target_instance = inst
        if inst.file_path:
            actor_file_paths[outer_name] = inst.file_path
            print(outer_name)
        
    if not target_instance.file_path:
        print("There is no", target, "in a scene", filename)
        sys.exit()
    
    target_loc = target_instance.transform.location
    
    #detect unique bps
    path_count: dict[str, int] = {}
    for fp in actor_file_paths.values():
        path_count[fp] = path_count.get(fp, 0) + 1
    
    #filter
    result: list[FileInstance] = []
    for outer_name, inst in instances.items():
        if target_lower in outer_name.lower():
            continue  # target added separately below
        
        loc = inst.transform.location
        distance = ((target_loc[0] - loc[0])**2 + (target_loc[1] - loc[1])**2 + (target_loc[2] - loc[2])**2)**0.5
        
        fp = inst.file_path
        is_nearby = distance <= nearby_distance
        is_unique = fp and path_count.get(fp, 0) == 1
        
        if not (is_nearby or is_unique):
            continue
        
        if verbose:
            print(f"{'UNIQUE' if is_unique else 'nearby':8s} dist={distance:8.0f} {outer_name}")
        
        result.append(inst)
    
    result.append(target_instance)
    return result

def find_mesh_path(blueprint_local_path: str) -> FileInstance:
    if (not os.path.isfile(blueprint_local_path)):
        print("No blueprint was found in path", blueprint_local_path)
        return FileInstance()
    
    with open(blueprint_local_path) as f:
        raw = json.load(f)
        
    for obj in raw:
        prop_key = mesh_property_key(obj.get("Type", ""))
        if prop_key is None:
            continue
    
        props = obj.get("Properties", {})
        mesh_ref = props.get(prop_key)
        if not mesh_ref or "ObjectPath" not in mesh_ref:
            continue
        
        location = location_to_tuple(props["RelativeLocation"]) if "RelativeLocation" in props else (0, 0, 0)
        rotation = rotation_to_tuple(props["RelativeRotation"]) if "RelativeRotation" in props else (0, 0, 0)
        scale = scale_to_tuple(props.get("RelativeScale3D", {}))
        
        return FileInstance(file_path=mesh_ref.get("ObjectPath", ""), transform=Transform(location, rotation, scale))
    
    return FileInstance()
    
#endregion