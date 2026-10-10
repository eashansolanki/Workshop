---
name: 3d-printing-design
description: Design printable functional parts with model-specific Bambu Lab and Prusa guidance, calibrated tolerances and slicer checks.
---

# 3D Printing Design

## Workflow
1. Ask what the object does, mating measurements, load direction, environment, exact printer, nozzle, material and desired fit. Use millimetres. Separate design dimensions from fit allowances.
2. Call `printer_reference` with bambu/prusa and use its linked official pages to verify current model specifications, compatible materials and slicer profiles. The bundled catalogue is selected reference models, not an exhaustive current lineup. Never mix family specs or send print jobs without authorization.
3. Design for layer anisotropy, orientation, supported overhangs, bridging, nozzle line width, top/bottom layers and warping. Choose wall thickness relative to extrusion width; prototype critical features. Avoid unsupported isolated islands, nonmanifold surfaces and zero-thickness edges.
4. Prefer fillets at stressed transitions, chamfers to reduce elephant-foot interference, bosses with clearance from walls, and orientation that resists expected loads. Allow access for assembly/tools and heat-set inserts.
5. Fit tolerance depends on material, calibration, geometry and orientation. Prusa suggests at least 0.3 mm as an initial moving-part allowance; this is a starting point. Print clearance coupons and adjust before making the full part. Document radial versus diametral allowances.
6. Export actual geometry through OpenSCAD or Fusion. Slice with the exact Bambu Studio/PrusaSlicer profile; review every relevant layer, dimensions, printable region, supports, brim, purge zones and estimated material/time. Never state a design is validated from code alone.
7. Deliver source SCAD, compiled STL/3MF when available, and genuine F3D only through Fusion. Record dimensions, assumptions, material and print orientation.
Design source: https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135

## Available tools and execution
Run `capabilities` first. In LM Studio use the MCP tools directly. In Bionic, if the host has no MCP connection settings, use its built-in terminal with the absolute plugin virtual-environment Python path:
`/absolute/plugin/.venv/bin/python -m workshop.cli list`
`/absolute/plugin/.venv/bin/python -m workshop.cli TOOL_NAME '{"argument":"value"}'`
Run from the plugin directory, or use PYTHONPATH set to its absolute path. Set WORKSHOP_WORKSPACE to an absolute user-authorized project/output folder. On Windows use `.venv/Scripts/python.exe`. Arguments are JSON; quote them correctly for the shell, or put them in a script rather than interpolating untrusted text. The CLI and MCP expose the same tools. Never claim an output exists unless it was returned successfully and verified.
