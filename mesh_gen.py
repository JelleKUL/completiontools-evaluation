# Import packages and Setup everything
import os
import json
import torch
import pytorch3d.io
import sys
# some utility function for visualization from AutoSDF
sys.path.insert(0, '../')
import AutoSDF.utils as utils
from AutoSDF.utils.util_3d import init_mesh_renderer, sdf_to_mesh
from AutoSDF.utils.demo_util import get_shape_comp_opt
from AutoSDF.utils.demo_util import get_shape_comp_model
from AutoSDF.utils.qual_util import save_mesh_as_gif, get_partial_shape_by_voxels, get_partial_shape_by_range, get_shape_comp_input_mesh

def complete_mesh(partialShape, voxelSelection, nrOfShapes, device):
    
    shape_comp_input = get_partial_shape_by_voxels(partialShape, voxelSelection, device=device)

    # Define the incomplete mesh
    input_mesh = get_shape_comp_input_mesh(shape_comp_input['sdf'], shape_comp_input['sdf_missing'])
    print("perform shape completion")
    input_mesh, comp_sdf = model.shape_comp(shape_comp_input, bs=3, topk=30)
    gen_mesh = sdf_to_mesh(comp_sdf)          # completed shape