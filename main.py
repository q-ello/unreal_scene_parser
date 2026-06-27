import os

import blender_export
import parser
import sys

from scene import FileInstance

def strip_file_path(file_path):
    file_path_without_game = ('/').join(file_path.split('/')[2:])
    file_path_without_number = file_path_without_game.split('.')[0]
    return file_path_without_number

exports_path = "assets/Exports/Hibiki/Content/"
models_path = "assets/Hibiki/Content/"

WORLD_SCALE = 0.01  

arguments = sys.argv[1:]

blueprints = parser.load_scene(arguments[0], arguments[1], int(arguments[2]) if arguments[2] else 1000)
    
meshes: list[FileInstance] = []

for bp in blueprints:
    mesh = parser.find_mesh_path(exports_path + strip_file_path(bp.file_path) + '.json')
    if mesh.file_path == '':
        continue
    
    mesh.transform.location = (bp.transform.location[0] + mesh.transform.location[0] * WORLD_SCALE, bp.transform.location[1] + mesh.transform.location[1] * WORLD_SCALE, bp.transform.location[2] + mesh.transform.location[2] * WORLD_SCALE)
    mesh.transform.rotation = bp.transform.rotation
    mesh.file_path = models_path + strip_file_path(mesh.file_path) + '.glb'
    meshes.append(mesh)
    print(bp, mesh)
    
blender_export.make_scene(meshes, arguments[0].split('/')[-1].split('.')[0])