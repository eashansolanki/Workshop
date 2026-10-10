# CAD exports

Workshop supports editable OpenSCAD source and an Autodesk Fusion script bridge. Both workflows return file paths or explicit pending/error results.

## OpenSCAD

1. Check `capabilities` to confirm OpenSCAD is installed.
2. Use `write_openscad` for custom source or `create_openscad_design` for a supported recipe.
3. Use `render_openscad` to compile the SCAD file into STL, 3MF or PNG.
4. Inspect the mesh and slicer preview before printing. Check dimensions, wall thickness, overhangs, clearances and orientation against the selected printer and material.

Creating SCAD source does not compile it. Rendering requires the installed OpenSCAD executable. Included SCAD files execute with ordinary local permissions.

## Autodesk Fusion and F3D

1. Call `prepare_fusion_design` with a recipe JSON path, a new `.f3d` output path and a recipe such as [`examples/plate.json`](../examples/plate.json).
2. In Fusion, open **Utilities → Scripts and Add-Ins** and add the [`fusion/WorkshopDesign`](../fusion/WorkshopDesign) folder.
3. Run **WorkshopDesign** and select the generated recipe JSON.
4. Fusion creates a new parametric design and exports a genuine F3D archive. The script records completion in a companion `.result.json`.
5. Open the exported F3D in Fusion and inspect the resulting geometry.

Recipes support boxes and cylinders with `new`, `join` and `cut` operations, in millimetres. Box origins are lower corners; cylinder origins are axes. Cuts remove previously created material; joins must intersect existing bodies. Use `new` for disjoint bodies. The bridge converts millimetres to the Fusion API's centimetres.

Preparing a recipe returns a pending job. It cannot create an F3D archive outside Fusion. More complex geometry needs a custom Fusion script. Live F3D export remains unverified in the current [test report](../TEST-REPORT.md).
