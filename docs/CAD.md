# CAD exports

Workshop supports editable OpenSCAD source and an Autodesk Fusion script bridge. Both workflows return file paths or explicit pending/error results.

## OpenSCAD

1. Check `capabilities` to confirm OpenSCAD is installed.
2. Use `create_openscad` for custom source or `create_cad_recipe` for a supported recipe.
3. Use `render_openscad` to compile the SCAD file into STL, 3MF or PNG.
4. Inspect the mesh and slicer preview before printing. Check dimensions, wall thickness, overhangs, clearances and orientation against the selected printer and material.

Creating SCAD source does not compile it. Rendering requires the installed OpenSCAD executable. Included SCAD files execute with ordinary local permissions.

## Autodesk Fusion and F3D

Follow the [Fusion setup and export walkthrough](FUSION360.md) to locate the script folder, register it and export a generated job.

Recipes support boxes and cylinders with `new`, `join` and `cut` operations, in millimetres. Box origins are lower corners; cylinder origins are axes. Cuts remove previously created material; joins must intersect existing bodies. Use `new` for disjoint bodies. The bridge converts millimetres to the Fusion API's centimetres.

Preparing a recipe returns a pending job. It cannot create an F3D archive outside Fusion. More complex geometry needs a custom Fusion script. Live F3D export remains unverified.
