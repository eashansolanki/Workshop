# CAD exports

Workshop supports editable OpenSCAD source and an Autodesk Fusion script bridge. Both workflows return file paths or explicit pending/error results. Use the program the user requested: native Fusion for Fusion designs, OpenSCAD for OpenSCAD designs. Never switch programs or ask for mesh import as an error workaround.

## OpenSCAD

1. Check `capabilities` to confirm OpenSCAD is installed.
2. Use `create_openscad` for custom source or `create_cad_recipe` for a supported recipe.
3. Use `render_openscad` to compile the SCAD file into STL, 3MF or PNG.
4. Inspect the mesh and slicer preview before printing. Check dimensions, wall thickness, overhangs, clearances and orientation against the selected printer and material.

Creating SCAD source does not compile it. Rendering requires the installed OpenSCAD executable. Included SCAD files execute with ordinary local permissions.

## Autodesk Fusion and F3D

Follow the [Fusion setup and export walkthrough](FUSION360.md) to locate the script folder, register it and export a generated job.

Recipes support boxes and cylinders with `new`, `join` and `cut` operations, in millimetres. Box origins are lower corners; cylinder origins are axes. Cuts remove previously created material; joins must intersect existing bodies. Use `new` for disjoint bodies. The bridge converts millimetres to the Fusion API's centimetres.

Preparing a recipe returns a pending job. It cannot create an F3D archive outside Fusion. More complex geometry uses `prepare_fusion_script` with native `build(design, root)` source. Queue it with `run_fusion_design`; WorkshopBridge runs it inside Fusion automatically after one-time add-in registration. Use `create_cad_project` for a new folder with separate part files, `run_fusion_project` to execute all parts and `fusion_project_status` for per-part saved links. Live F3D export remains unverified.

## Design intent and verification

Before building, use `plan_cad_design` to capture the brief, acceptance criteria, concepts, parameters, feature dependencies and part interfaces. For a complex brief, compare at least two concepts. Attach the saved plan through `create_cad_project(..., design_plan_file=...)`. Backend and part names must match the plan; each part gets its own files.

After execution, inspect actual geometry and previews, then call `review_cad_design`. Measured Fusion envelope/body-count failures override reported passes. Missing checks stay unverified; exported files can still require revision. Record saved evidence for visual, interface and manufacturing checks that these metrics cannot establish.

The native example in `examples/fusion_native_part.py` drives the footprint, extrusion and fillets with named user parameters. Its rectangle uses the sketch origin and two driving dimensions; underconstrained sketches stop before extrusion. Coordinate values seed geometry and position dimension labels. Verify regeneration after changing parameters in real Fusion before claiming editability.
