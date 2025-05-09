# helper functions to convert between different modalities

import os
os.environ['PYOPENGL_PLATFORM'] = 'egl'
from sys import platform
import trimesh
from trimesh import Trimesh
import open3d as o3d
import numpy as np
from matplotlib import pyplot as plt
import torchvision.transforms as transforms
from PIL import Image
import torch
import numbers
from scipy.spatial import cKDTree as KDTree
import os
import scipy
import json
from skimage import measure

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

# File control

def make_dir_if_not_exist(path):
    if(not os.path.exists(path)):
        print("Folder does not exist, creating the folder: " + path)
        os.makedirs(path)

# Open3d

# Compute barycentric coordinates (u, v, w) for
# point p with respect to triangle (a, b, c)
def carthesian_to_barycentric( p,  a,  b,  c):

    v0 = b - a
    v1 = c - a
    v2 = p - a
    d00 = np.dot(v0, v0)
    d01 = np.dot(v0, v1)
    d11 = np.dot(v1, v1)
    d20 = np.dot(v2, v0)
    d21 = np.dot(v2, v1)
    denom = d00 * d11 - d01 * d01
    v = (d11 * d20 - d01 * d21) / denom
    w = (d00 * d21 - d01 * d20) / denom
    u = 1.0 - v - w
    return u,v,w

def barycentric_to_carthesian(a, b, c, u, v, w):
    p = u*a + v*b + c*w
    return p


def get_tri_pixel_value(tri: np.array, image: np.array)-> np.array:
    """Returns the pixel color value of the center of a uv triangle

    Args:
        tri (np.array()): 2x3 array of (x,y) uv coordinates
        image (np.array()): nxn array of pixel values

    Returns:
        np.array(): the pixel value
    """
    avPos = np.round(np.average(tri, axis=0))
    val = image[avPos[1].astype(int)][avPos[0].astype(int)]
    return val

def get_point_pixel_value(tri: np.array, tri3D:np.array, point: np.array, image: np.array)-> np.array:
    """Returns the pixel color of the 3D point

    Args:
        tri (np.array()):  2x3 array of (x,y) uv coordinates of the triangle
        tri3D (np.array()): 3x3 array of (x,y,z) 3D coordinates of the triangle
        point (np.array()): 3x1 array of (x,y,z) 3D coordinates
        image (np.array()): nxn array of pixel values

    Returns:
        np.array(): 2x1 array the pixel value
    """

    u,v,w = carthesian_to_barycentric(point, tri3D[0],  tri3D[1], tri3D[2])
    p2d = barycentric_to_carthesian( tri[0], tri[1], tri[2], u,v,w)

    val = image[p2d[1].astype(int)][p2d[0].astype(int)]
    return val

def get_point_pixel_colors_open3d(mesh: o3d.geometry.TriangleMesh, points:np.array, getDistance = False) -> np.array:
    """Returns the color of all the points from a mesh

    Args:
        mesh (o3d.geometry.TriangleMesh): The source colored mesh
        points (np.array): The uncolored points

    Returns:
        np.array: The point colors
    """
    # Create a scene and add the triangle mesh
    lMesh = o3d.t.geometry.TriangleMesh.from_legacy(mesh)
    scene = o3d.t.geometry.RaycastingScene()
    _ = scene.add_triangles(lMesh)  # we do not need the geometry ID for mesh

    mesh_texture = np.asarray(mesh.textures[0])
    mesh_textures = np.asarray(mesh.textures)
    mesh_uvs = np.asarray(mesh.triangle_uvs) * np.array([mesh_texture.shape[1],mesh_texture.shape[0]]) # multiply by the size of the texture map
    mesh_tris = np.asarray(mesh.triangles)
    mesh_verts = np.asarray(mesh.vertices)

    newColors = []
    if(getDistance):
        distances = []
    query_points = o3d.core.Tensor(points, dtype=o3d.core.Dtype.Float32)
    # We compute the closest points on the surface.
    ans = scene.compute_closest_points(query_points)
    print("Closest points computed")
    for i in range(len(points)):
        # We get the triangle index of the closest point
        idx = ans['primitive_ids'][i].item()
        # We get the 3D location of the closest surface point
        surfacePoint = ans['points'][i].numpy()
        if(getDistance):
            distances.append(np.linalg.norm(points[i] - surfacePoint,axis=-1))
        #print(surfacePoint)
        # We get the 3D positions of the 3 points forming the triangle
        currentTri = mesh_tris[idx]
        a3d,b3d,c3d = mesh_verts[currentTri[0]], mesh_verts[currentTri[1]],mesh_verts[currentTri[2]]
        auv, buv, cuv = mesh_uvs[3*idx], mesh_uvs[3*idx+1], mesh_uvs[3*idx+2]
        u,v,w = carthesian_to_barycentric(surfacePoint, a3d,b3d,c3d)
        projectedPoint = barycentric_to_carthesian(auv, buv, cuv, u,v,w)
        #print("Sampled point: " + str(queryPoint) + ",with closest point: "+ str(surfacePoint)+" with triangle index: " + str(idx))
        #print(a3d,b3d,c3d)
        #print(surfacePoint)
        #print(auv, buv, cuv)
        #print(projectedPoint)
        newColors.append(mesh_texture[projectedPoint[1].astype(int)][projectedPoint[0].astype(int)])
    if(getDistance):
        return newColors, distances
    return newColors


def get_point_triangle_colors_open3d(mesh: o3d.geometry.TriangleMesh, points:np.array) -> np.array:
    """Returns the color of all the points from a mesh

    Args:
        mesh (o3d.geometry.TriangleMesh): The source colored mesh
        points (np.array): The uncolored points

    Returns:
        np.array: The point colors
    """
    # Create a scene and add the triangle mesh
    lMesh = o3d.t.geometry.TriangleMesh.from_legacy(mesh)
    scene = o3d.t.geometry.RaycastingScene()
    _ = scene.add_triangles(lMesh)  # we do not need the geometry ID for mesh

    mesh_texture = np.asarray(mesh.textures[0])
    mesh_uvs = np.asarray(mesh.triangle_uvs) * np.array([mesh_texture.shape[1],mesh_texture.shape[0]]) # multiply by the size of the texture map
    mesh_tris = np.asarray(mesh.triangles)
    mesh_tris_values = []
    for i in range(len(mesh_tris)):
        points_uv = np.array([mesh_uvs[3*i],mesh_uvs[3*i+1],mesh_uvs[3*i+2]])
        mesh_tris_values.append(get_tri_pixel_value(points_uv, mesh_texture ))
    
    newColors = []
    for queryPoint in points:
        query_point = o3d.core.Tensor([queryPoint], dtype=o3d.core.Dtype.Float32)
        # We compute the closest point on the surface for the point at position [0,0,0].
        ans = scene.compute_closest_points(query_point)
        # We get the triangle index of the closest point
        idx = ans['primitive_ids'][0].item()
        #print("Sampled point: " + str(queryPoint) + ", with triangle index: " + str(idx) + " and color: " + str(mesh_tris_values[idx]))
        newColors.append(mesh_tris_values[idx])
    return newColors

# Trimesh

def mesh_to_sdf_tensor(mesh: Trimesh, resolution:int = 64, recenter: bool = True, scaleFactor = 1):
    """Creates a normalized signed distance function from a provided mesh, using a voxel grid

    Args:
        mesh (Trimesh): The mesh to convert, can be (non) watertight
        resolution (int, optional): the voxel resolution. Defaults to 64.

    Returns:
        sdf, mesh: the (res, res, res) np.array sdf and the fixed mesh
    """

    # normalize mesh
    vertices = mesh.vertices
    bbmin = vertices.min(0)
    bbmax = vertices.max(0)
    if(recenter):
        center = (bbmin + bbmax) * 0.5
    else : center = 0
    vertices = (vertices - center) * scaleFactor

    
    if platform == "linux" or platform == "linux2":
        # linux
        from mesh_to_sdf import mesh_to_voxels
        sdf = mesh_to_voxels(mesh, resolution-2, pad=True)
        mesh.vertices = mesh.vertices / scaleFactor + center
        # Marching Cubes to extract the 0-level isosurface
        verts, faces, normals, _ = measure.marching_cubes(sdf, level=2 / resolution, spacing=(1.0/resolution, 1.0/resolution, 1.0/resolution))
        # Convert to Trimesh format
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, vertex_normals=normals, process=False)
        return sdf, mesh
    else:
        # Windows and macos
        import mesh2sdf
        sdf, mesh = mesh2sdf.compute( vertices, mesh.faces, resolution, fix=(not mesh.is_watertight), level=2 / resolution, return_mesh=True)
        return sdf, mesh

def get_point_colors_trimesh(mesh, points):
    
    # get the indexes of the closest triangle for each point triangles [n,1]
    _,_,triangleIds = trimesh.proximity.closest_point(mesh, points)
    # get the 3 vertex indices of each triangle [n,3]
    vertices = mesh.faces[triangleIds]
    # get the uv coordinate of each vertex [n,3,2]
    uvCoordinates = mesh.visual.uv[vertices]
    # get the average coordinate of each uv triangle [n,2]
    uvCenters = np.average(uvCoordinates, axis = 1)
    # get uv color of each uv center [n,4]
    pointColors = mesh.visual.material.to_color(uvCenters)
    return pointColors

def mesh_to_voxelgrid_trimesh(mesh: Trimesh, resolution: int = 64, hollow =True):
    
    # Normalize the mesh
    scale = 1 / np.max(mesh.extents)
    center = mesh.centroid
    transformMtx =  np.vstack((np.hstack((np.identity(3) * scale, center.reshape((3,1)) )), [0,0,0,1]))
    mesh.apply_transform(transformMtx)

    # Voxelize the mesh
    voxelSize = 1/(resolution-1) # the mesh was scaled to one
    voxelScale = voxelSize / scale
    voxelMesh = mesh.voxelized(voxelSize)
    if(hollow): voxelMesh = voxelMesh.hollow() # hollow to add colors to the grid
    
    # Get voxel colors
    voxelPoints = voxelMesh.points
    voxelColors = get_point_colors_trimesh(mesh, voxelPoints)
    ids = voxelMesh.points_to_indices(voxelPoints)
    colorGrid=np.zeros([voxelMesh.shape[0],voxelMesh.shape[1],voxelMesh.shape[2],4])
    for i in range(len(voxelPoints)):
        colorGrid[ids[i][0],ids[i][1], ids[i][2],:] = voxelColors[i]
    

    return voxelMesh, colorGrid, voxelScale

def show_mask_annotations(anns):
    if len(anns) == 0:
        return
    sorted_anns = sorted(anns, key=(lambda x: x['area']), reverse=True)
    ax = plt.gca()
    ax.set_autoscale_on(False)

    img = np.ones((sorted_anns[0]['segmentation'].shape[0], sorted_anns[0]['segmentation'].shape[1], 4))
    img[:,:,3] = 0
    nr = len(sorted_anns)
    i = 0
    for ann in sorted_anns:
        m = ann['segmentation']
        color_mask = np.concatenate([np.ones(3) / nr * i, [1]])
        img[m] = color_mask
        i+=1
    ax.imshow(img)
    print("Detected " + str(i) + " patches")

def isolate_mask(image, mask):
    img = image.copy()
    img[~mask,:] = [0,0,0]
    return img

def load_jpeg_from_file(image, image_size, cuda=True):
    img_transforms = transforms.Compose(
        [
            transforms.Resize(image_size + 32),
            transforms.CenterCrop(image_size),
            transforms.ToTensor(),
        ]
    )

    img = img_transforms(image)
    with torch.no_grad():
        # mean and std are not multiplied by 255 as they are in training script
        # torch dataloader reads data into bytes whereas loading directly
        # through PIL creates a tensor with floats in [0,1] range
        mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)

        if cuda:
            mean = mean.cuda()
            std = std.cuda()
            img = img.cuda()
        img = img.float()

        input = img.unsqueeze(0).sub_(mean).div_(std)

    return input

def as_mesh(scene_or_mesh):
    if isinstance(scene_or_mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate([
            trimesh.Trimesh(vertices=m.vertices, faces=m.faces)
            for m in scene_or_mesh.geometry.values()])
    else:
        mesh = scene_or_mesh
    return mesh

def normalize_mesh(mesh):
    # Get the bounding box of the mesh
    min_bound, max_bound = mesh.bounds

    # Calculate the center of the bounding box
    center = (max_bound + min_bound) / 2.0

    # Calculate the scale factor to normalize the mesh to fit within [-1, 1]
    max_extent = max(max_bound - center)
    scale_factor = 1.0 / max_extent

    # Translate and scale the vertices
    mesh.vertices -= center
    mesh.vertices *= scale_factor

    return mesh


def scale_mesh_to_unity_cube(mesh):
    # Get the bounding box of the mesh
    min_bound, max_bound = mesh.bounds

    # Calculate the scaling factors for each axis
    scale_factors = 1.0 / (max_bound - min_bound)

    # Translate the mesh to the origin
    mesh.vertices -= min_bound

    # Scale the mesh
    mesh.vertices *= scale_factors

    return mesh

def create_grid_points_from_xyz_bounds(min_x, max_x, min_y, max_y ,min_z, max_z, res):
    x = np.linspace(min_x, max_x, res)
    y = np.linspace(min_y, max_y, res)
    z = np.linspace(min_z, max_z, res)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij', sparse=False)
    X = X.reshape((np.prod(X.shape),))
    Y = Y.reshape((np.prod(Y.shape),))
    Z = Z.reshape((np.prod(Z.shape),))

    points_list = np.column_stack((X, Y, Z))
    del X, Y, Z, x
    return points_list

def shoot_holes(vertices, n_holes, dropout, mask_faces=None, faces=None,
                rng=None):
    """Generate a partial shape by cutting holes of random location and size.

    Each hole is created by selecting a random point as the center and removing
    the k nearest-neighboring points around it.

    Args:
        vertices: The array of vertices of the mesh.
        n_holes (int or (int, int)): Number of holes to create, or bounds from
            which to randomly draw the number of holes.
        dropout (float or (float, float)): Proportion of points (with respect
            to the total number of points) in each hole, or bounds from which
            to randomly draw the proportions (a different proportion is drawn
            for each hole).
        mask_faces: A boolean mask on the faces. 1 to keep, 0 to ignore. If
                    set, the centers of the holes are sampled only on the
                    non-masked regions.
        faces: The array of faces of the mesh. Required only when `mask_faces`
               is set.
        rng: (optional) An initialised np.random.Generator object. If None, a
             default Generator is created.

    Returns:
        array: Indices of the points defining the holes.
    """
    if rng is None:
        rng = np.random.default_rng()

    if not isinstance(n_holes, numbers.Integral):
        n_holes_min, n_holes_max = n_holes
        n_holes = rng.integers(n_holes_min, n_holes_max)

    if mask_faces is not None:
        valid_vertex_indices = np.unique(faces[mask_faces > 0])
        valid_vertices = vertices[valid_vertex_indices]
    else:
        valid_vertices = vertices

    # Select random hole centers.
    center_indices = rng.choice(len(valid_vertices), size=n_holes)
    centers = valid_vertices[center_indices]

    n_vertices = len(valid_vertices)
    if isinstance(dropout, numbers.Number):
        hole_size = n_vertices * dropout
        hole_sizes = [hole_size] * n_holes
    else:
        hole_size_bounds = n_vertices * np.asarray(dropout)
        hole_sizes = rng.integers(*hole_size_bounds, size=n_holes)

    # Identify the points indices making up the holes.
    kdtree = KDTree(vertices, leafsize=200)
    to_crop = []
    for center, size in zip(centers, hole_sizes):
        _, indices = kdtree.query(center, k=size)
        to_crop.append(indices)
    to_crop = np.unique(np.concatenate(to_crop))
    return to_crop