import blender_export
import parser
import sys

from scene import FileInstance

#region config
EXPORTS_PATH = "assets/Exports/Hibiki/Content/"
MODELS_PATH = "assets/Hibiki/Content/"
WORLD_SCALE = 0.01  
VERBOSE = True
#endregion

#region helpers
def strip_file_path(file_path):
    file_path_without_game = ('/').join(file_path.split('/')[2:])
    file_path_without_number = file_path_without_game.split('.')[0]
    return file_path_without_number
#endregion

#region arguments
arguments = sys.argv[1:]

if (len(arguments) == 0):
    print("You need to specify local path to the scene file in the first argument")
    sys.exit()
scene_file = arguments[0]

if (len(arguments) == 1):
    print("You need to specify part of target name that you're aware of in the second argument")
    sys.exit()
    
target_name = arguments[1]
nearby_distance = int(arguments[2]) if len(arguments) > 2 and arguments[2] else 500
#endregion

#region main_block
blueprints = parser.load_scene(scene_file, target_name, nearby_distance, VERBOSE)

meshes: list[FileInstance] = []

for bp in blueprints:
    if not bp.file_path:
        continue
    
    mesh = bp
    bp_path = strip_file_path(bp.file_path)
    if "Blueprints" in bp.file_path:
        # Pattern B: need to look up mesh inside the BP file
        mesh = parser.find_mesh_path(EXPORTS_PATH + bp_path + ".json")
        if not mesh.file_path:
            continue
        
        bx, by, bz = bp.transform.location
        mx, my, mz = mesh.transform.location
        mesh.transform.location = (bx + mx, by + my, bz + mz)
        mesh.transform.rotation  = bp.transform.rotation
        mesh.transform.scale     = tuple(a * b for a, b in zip(bp.transform.scale, mesh.transform.scale))
    
    else:
        mesh.transform.location = bp.transform.location
        mesh.transform.rotation = bp.transform.rotation
        mesh.transform.scale    = bp.transform.scale

    
    mx, my, mz = mesh.transform.location
    s = WORLD_SCALE
    
    mesh.transform.location = (mx * s, my * s, mz * s)
    mesh.file_path = MODELS_PATH + strip_file_path(mesh.file_path) + '.glb'
    meshes.append(mesh)

target_mesh = meshes[-1] if meshes else None
target_location = target_mesh.transform.location if target_mesh else None

#move so that target is in focus right away
for mesh in meshes:
    mx, my, mz = mesh.transform.location
    tx, ty, tz = target_location
    
    mesh.transform.location = (mx - tx, my - ty, mz - tz)
    
blender_export.make_scene(meshes, arguments[0].split('/')[-1].split('.')[0], target_location)
#endregion