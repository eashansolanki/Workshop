---
name: openscad-and-fusion
description: Create parametric SCAD, export meshes, and create genuine Fusion F3D archives through the included Fusion script.
---

# Openscad And Fusion

## OpenSCAD
Use create_openscad to write custom parametric source and render_openscad to export STL/3MF/PNG with installed OpenSCAD. Use modules, named parameters, mm units, union/difference/intersection, epsilon overlaps and assertions for invalid dimensions. Avoid externally included files unless authorized. The renderer runs with normal local privileges. Check rendering diagnostics and actual output; use the host/slicer to verify watertight geometry and dimensions.
## Shared recipe
create_cad_recipe accepts {"parts":[{"kind":"box","width":40,"depth":30,"height":4,"origin":[0,0,0],"operation":"new"},{"kind":"cylinder","diameter":5,"height":6,"origin":[10,10,-1],"operation":"cut"}]}. New/join are additive and cut subtracts previous material. Fusion join needs intersecting geometry; disjoint additions use new. Cylinder origin is its axis; box origin is its lower corner. All dimensions are millimetres.
## Fusion
prepare_fusion_design writes a validated recipe JSON with the requested .f3d target. It returns pending_fusion_execution, not an F3D. In Fusion open Utilities > Scripts and Add-Ins, add fusion/WorkshopDesign, run it and select the JSON. The script creates a new parametric design with sketch/extrusion timeline features, exports using ExportManager.createFusionArchiveExportOptions and records success in a result JSON. Verify the resulting F3D by opening it in Fusion.
The recipe supports boxes/cylinders and new/join/cut operations. For sketches with constraints, lofts, sweeps, fillets or complex assemblies, use the Python tool to author a dedicated adsk script and run it in Fusion; do not claim these are supported by the recipe tool. Fusion API internal length units are centimetres; the bridge converts mm by dividing by ten. External-reference assemblies may require F3Z rather than F3D.
Autodesk API: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_ExportManager.htm

## Available tools and execution
Run `capabilities` first. In LM Studio use the MCP tools directly. In Bionic, if the host has no MCP connection settings, use its built-in terminal with the absolute plugin virtual-environment Python path:
`/absolute/plugin/.venv/bin/python -m workshop.cli list`
`/absolute/plugin/.venv/bin/python -m workshop.cli TOOL_NAME '{"argument":"value"}'`
Run from the plugin directory, or use PYTHONPATH set to its absolute path. Set WORKSHOP_WORKSPACE to an absolute user-authorized project/output folder. On Windows use `.venv/Scripts/python.exe`. Arguments are JSON; quote them correctly for the shell, or put them in a script rather than interpolating untrusted text. The CLI and MCP expose the same tools. Never claim an output exists unless it was returned successfully and verified.
