# helper functions to convert between different modalities
import json

def read_voxel_file(jsonPath):
    # Load the JSON file
    print("Loading the Json file")
    with open(jsonPath, 'r') as file:
        data = json.load(file)
    voxels = data['voxels']
    occ_grid = []
    for voxel in voxels:
        id = voxel['gridIndex']
        occ_grid.append([id['x'], id['y'], id['z']])
    return occ_grid