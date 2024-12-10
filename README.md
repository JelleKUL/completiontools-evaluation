# completiontools-evaluation
The evaluation code for the completion tools

## Getting Started
This document is meant to keep track of all your work, use it to track sources, progress and problems.

## Workflow

### Pre processing
Use the [`pre-processing.ipynb`](pre-processing.ipynb) file to convert meshes to SDF's. The SDF's will be saved to a folder of your choice as a `.pt` tensor file.

### Voxel Selection
The voxel selection is performed in Unity using [GeoSharpi](https://github.com/JelleKUL/GeoSharpi). The user interface allows you to import a mesh, select a number of voxels and export them as json files.

### Object completion
Object completion is performed in the [`AutoSDF.ipynb`](AutoSDF.ipynb) file using the voxel selection from GeoSharpi and the SDF from Pre-processing.

### Texture Completion
Texture completion is performed using a command line tool explained in [`TEXTure.ipynb`](TEXTure.ipynb)

