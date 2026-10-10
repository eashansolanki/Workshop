---
name: 3d-printing-design
description: Design usable printable parts from requirements, compare concepts, plan interfaces and features, inspect evidence and iterate using the requested CAD tool.
---

# 3D Printing Design

## Designer working process — use before generating CAD
Treat the user brief as a design problem, not a request to stack available primitives. Produce concise design decisions and evidence; do not expose private chain-of-thought or bury the user in a long questionnaire. Scale the process to the task: a simple exact part needs one compact concept, while an ambiguous or complex product needs competing concepts and iteration.

1. Understand the use. State what the object does, who uses it, the environment and which details make it recognisable. Extract exact dimensions, references, moving/mating parts, ergonomics, loads, material/process, styling and deliverables. Keep requested Fusion/OpenSCAD selection. Do not invent undocumented measurements from a reference image; distinguish measured, user-provided, assumed and derived values.
2. Define success before geometry. Identify must-have features, measurable acceptance criteria and checks. Separate critical unknowns from reversible aesthetic choices. Ask only when a missing value changes fit, mechanism, safety or the chosen architecture; continue low-risk work with explicit assumptions. If a reference is available, inspect it and capture its silhouette, proportions and feature relationships before designing details.
3. Choose a concept deliberately. For complex/ambiguous briefs compare at least two plausible constructions on function, appearance, process, serviceability, part count and modelling robustness. Select one with a short reason. Do not pick the easiest primitive representation if it loses the requested form/function. Do not turn every object into a plate with arbitrary holes, or every rounded form into a filleted box.
4. Save the design intent with `plan_cad_design`. Record purpose, context, manufacturing, requirements, concepts, selection reason, parameters/bases, parts/roles, feature operations/dependencies, interfaces and assumptions. Every feature must serve a requirement; every requirement must be covered. A plan is a public design record, not a reasoning transcript. Save it outside the not-yet-created part folder (for example `stand-v1.design.json`).
5. Plan the CAD history as a designer would. Establish datums and named parameters, define components and local/assembly coordinates, then major profiles/volumes, functional interfaces, holes/pockets/patterns and finishing details. Choose revolve for rotational forms, loft/sweep/surface methods when the form calls for them, and native components/joints for assemblies. Drive sketch geometry with dimensions/constraints where appropriate; do not replace design intent with blanket fixed constraints or hardcoded coordinates. Define clearance/tolerance at the actual interface, not by scaling the whole object.
6. Build and inspect progressively. Use `create_cad_project(..., design_plan_file=...)`, with a separate file per planned part. It refuses backend/part-name mismatches and attaches planned automatic checks. Establish the overall silhouette/proportion first; compare it to the brief before adding small details. Inspect failures at the feature that caused them. Preserve requested features and explain any necessary geometry change. Fix the chosen CAD backend instead of substituting a mesh or switching tools.
7. Critique the real result. Execute/export using the chosen backend; inspect measured dimensions, feature health and actual previews. Fusion saves `<part>.preview.png` when available; use `inspect_cad_preview` with a vision-capable model. For OpenSCAD, render a PNG with `render_openscad`, then inspect it. A model without vision must mark visual checks unverified rather than describe an image it cannot read. One viewport does not prove hidden geometry, assembly motion, fit, strength or printability. Obtain additional views/section checks or prototype evidence where required.
8. Close the design loop with `review_cad_design`. Each requirement is pass, fail or not_checked; provide saved measurement/inspection evidence for reported passes. Automatic Fusion envelope/body-count checks override unsupported pass claims. An exported file can still fail design criteria. Revise failed requirements in a new folder/job, retain a short change rationale, rerun affected checks and record unresolved assumptions. Report links per part and exactly what remains unchecked. Do not describe a design as production-ready merely because CAD exported.

### Plan tool schema
`plan_cad_design(output, plan)` takes a JSON object:
- `backend`: the requested `fusion` or `openscad`; `complexity`: `simple` or `complex`.
- `purpose`, `context`, `manufacturing`: concise nonempty text (state if manufacturing is unspecified/concept-only).
- `requirements`: `{id, description, acceptance, verification}`; use distinct IDs for distinct criteria.
- `concepts`: `{name, approach, tradeoffs}`; two or more for a complex brief. Include `selected_concept` and `selection_reason`.
- `parameters`: `{name, value, unit, basis, reason}`, with basis `user`, `assumption` or `derived`.
- `parts`: `{name, role, features, checks?}`. Each feature is `{name, operation, reason, requirements:[IDs], depends_on:[earlier feature names]}`.
- `interfaces`: `{name, parts:[part names], relationship, verification}` for multi-part designs. Explain explicitly if the files are independent rather than mating.
- `assumptions`: `{statement, risk, resolution}` for unresolved assumptions.

Optional per-part automatic `checks`: `{requirement, metric, expected, tolerance}`. Fusion measures `size_x_mm`, `size_y_mm`, `size_z_mm` from precise BRep-instance bounds, and `body_count`/`solid_body_count` from actual bodies. Envelope dimensions are along the root assembly axes; choose the datum accordingly. Body counts include placed instances. Count criteria need integer expectations and zero tolerance. These metrics do NOT prove hole size, fillet radius, wall thickness, material strength or interface fit; add native assertions/measurement reports and inspection for those requirements. OpenSCAD review needs separate saved rendering/measurement evidence; Fusion checks are not claimed for OpenSCAD.

`review_cad_design(plan_file, project_file, output, findings)` records findings `{requirement, status, evidence, artifacts:[workspace-relative saved measurement/inspection files]}`. Omitted requirements remain not_checked. Use an empty findings list to see measured coverage and outstanding checks. A matching, unchanged plan must be attached to the project; changed design intent needs a revised project. Review statuses are `needs_revision`, `needs_verification` or `ready_for_user_review`. The last status is evidence completeness for user review, not a safety or manufacturing certification.

### Practical design critique
Before delivery ask: does the silhouette match the brief; are functional features present and correctly located; can the user handle/assemble/service it; do datums and parameters make edits predictable; do parts fit and move as intended; can the chosen process make it; which requirement has real evidence and which is still an assumption? State concise findings, then fix them. Avoid unsupported claims about load capacity, waterproofing, temperature resistance or safety. Keep aesthetic intent and usability alongside mechanical feasibility.

The design cycle is informed by the Design Council's exploration/definition/development/testing approach:
https://www.designcouncil.org.uk/resources/framework-for-innovation/
Autodesk sketch/design-intent reference:
https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-FULLY-DEFINE-CONSTRAIN-SKETCH.htm

## Workflow
1. Ask what the object does, mating measurements, load direction, environment, exact printer, nozzle, material and desired fit. Use millimetres. Separate design dimensions from fit allowances.
2. Call `printer_reference` with bambu/prusa and use its linked official pages to verify current model specifications, compatible materials and slicer profiles. The bundled catalogue is selected reference models, not an exhaustive current lineup. Never mix family specs or send print jobs without authorization.
3. Design for layer anisotropy, orientation, supported overhangs, bridging, nozzle line width, top/bottom layers and warping. Choose wall thickness relative to extrusion width; prototype critical features. Avoid unsupported isolated islands, nonmanifold surfaces and zero-thickness edges.
4. Prefer fillets at stressed transitions, chamfers to reduce elephant-foot interference, bosses with clearance from walls, and orientation that resists expected loads. Allow access for assembly/tools and heat-set inserts.
5. Fit tolerance depends on material, calibration, geometry and orientation. Prusa suggests at least 0.3 mm as an initial moving-part allowance; this is a starting point. Print clearance coupons and adjust before making the full part. Document radial versus diametral allowances.
6. Export actual geometry through the CAD program the user requested. Keep Fusion requests in Fusion and OpenSCAD requests in OpenSCAD; do not switch backends or ask for mesh import as a workaround. Slice with the exact Bambu Studio/PrusaSlicer profile; review every relevant layer, dimensions, printable region, supports, brim, purge zones and estimated material/time. Never state a design is validated from code alone.
7. Deliver source SCAD, compiled STL/3MF when available, and genuine F3D only through Fusion. Record dimensions, assumptions, material and print orientation.
Design source: https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135

## Available tools and execution
Run `capabilities` first. In LM Studio use the MCP tools directly. In Bionic, if the host has no MCP connection settings, use its built-in terminal with the absolute plugin virtual-environment Python path:
`/absolute/plugin/.venv/bin/python -m workshop.cli list`
`/absolute/plugin/.venv/bin/python -m workshop.cli TOOL_NAME '{"argument":"value"}'`
In Bionic, use the current project working directory, never Documents/Workshop or the plugin folder. Native MCP tools obtain the host project root per request; call capabilities and verify workspace_ready and workspace before file operations. If Bionic does not expose one project root, the tools refuse file operations instead of using a global output folder. Use the terminal fallback from the current Bionic project terminal with WORKSHOP_WORKSPACE_MODE=bionic and PYTHONPATH pointing to the plugin; do not cd to the plugin. The CLI uses that terminal process working directory. Bionic must itself restrict its terminal/native tools to the selected project; Workshop cannot impose a boundary on unrelated host tools.

For changes to an existing text file, use Workshop read_file_snapshot, then Workshop edit_file with the returned sha256. Prefer complete edited content (omit search) when snippet matching is fragile. If a native Bionic editor says no match, reread the actual file and use this workflow. Exact snippets must match once; stale/ambiguous changes are refused without writing. Do not retry guessed snippets or relax matching silently. write_file is only for new files.

Bionic code subprocesses have OS-enforced project-only writes on macOS; arbitrary code fails closed on unsupported platforms. Native Fusion Python runs inside the external app, outside this sandbox, and strict Bionic tools cannot execute it. Structured Fusion recipes and workspace-contained preparation remain available. Other hosts can use explicitly opted-in trusted native scripts. Arguments are JSON; quote them correctly rather than interpolating untrusted text. Never claim an output exists unless returned successfully and verified.

## Fusion execution
Workshop includes Fusion recipe and native STEP/IGES/SAT/F3D import tools even when Fusion is offline. Prepare with `prepare_fusion_design` or `prepare_fusion_import`, queue with `run_fusion_design`, then verify using `fusion_design_status`. Show the verified saved-design link. Automatic execution requires the WorkshopBridge add-in registered once and running in Fusion; use the OpenSCAD and Fusion workflow for full setup.


## CAD choice: follow the user's request
If the user asks for Fusion, create native Fusion geometry and F3D files using the Fusion tools. Do not route the design through OpenSCAD, export an STL as a workaround, or tell the user to import a mesh. Use native Fusion scripts for advanced geometry. If the user asks for OpenSCAD, create SCAD source and render it with OpenSCAD. Never silently switch programs after an error. Diagnose the chosen backend and repair the design. If neither backend was specified, ask which one they want before choosing it. Missing Fusion/add-in setup is a setup issue, not permission to change the CAD program.

## Modelling principles to apply before constructing geometry
- Establish design intent: function, load cases, interacting parts, dimensions, units, coordinate system, materials, process, clearances, and required deliverables. Ask only for critical unknowns; state reasonable assumptions and keep them editable.
- Work in millimetres for user dimensions. Fusion API real length values are centimetres; convert every position, radius, distance and tolerance consistently. Angles expressed as real API values use radians. Use unit-bearing expressions for named parameters where supported. Never confuse radius with diameter or linear with angular units.
- Define a datum: stable origin, principal planes, symmetry planes and assembly axes. Locate geometry relative to those datums rather than arbitrary faces that may disappear when features change. Separate local part coordinates from assembly placement.
- Choose a representation deliberately. Sketch/extrude/revolve are appropriate for prismatic and rotational parts. Lofts join cross-sections; sweeps follow paths. Use surface construction/stitching for complex skins and validate the resulting solid. Use native CAD import only for an existing STEP/IGES/SAT/F3D source the user provided, not as a substitute for modelling a requested part.
- Make sketches planar with closed, non-self-intersecting profiles. Resolve gaps, duplicate edges, degeneracy and multiple profiles explicitly. Select the intended profile by geometry rather than assuming index zero in complicated sketches. Dimension and constrain design-driving geometry; use construction lines for references. Avoid conflicting or redundant constraints. Check degrees of freedom instead of assuming a sketch is fully constrained.
- Build meaningful features in an editable order: base volume, major additions, pockets/holes, patterns/mirrors, then finishing fillets/chamfers where practical. Apply meaningful component, sketch, feature and parameter names. Separate design parameters from derived expressions; keep units with expressions.
- Boolean joins need a real common volume or valid kernel contact; disjoint additions need separate bodies/components. Cuts must intersect intended targets. Specify cut participants where supported, including hidden bodies if intended. A through-hole tool should extend beyond both surfaces. Avoid coincident faces, tiny sliver faces and zero-thickness connections; don't increase tolerances blindly to disguise bad geometry.
- Validate loft section order, compatible profile topology, rail intersections and continuity. For sweeps, check path connectivity, profile orientation, curvature and self-intersection. For revolutions, check the axis and profile relation and angular extent. For shells, check wall thickness against curvature and small details. For fillets/chamfers, select edges by stable geometric criteria, start with physically feasible radii, and inspect feature health; do not drop a requested feature silently when the kernel rejects it.
- Avoid brittle face/edge indices after topology changes. Identify entities by stable references where available, or by geometric tests (normal, axis, radius, centre, bounds and adjacency) with a tolerance and a uniqueness check. Fail with a useful diagnostic if selection is ambiguous.
- Separate a body from a component: bodies represent solid volumes; components represent independently located parts. Use occurrences/transforms and appropriate joints for assemblies. Check contact, interference, clearances and degrees of freedom. Separate part files are deliverables, not proof of a correctly constrained assembly.
- Design tolerances as a system. Account for process capability, mating dimensions, tolerance stacks and expected motion. State whether a clearance is radial or diametral and whether a nominal size includes that clearance. Fasteners, bearings, inserts, seals and threads require specification-matched dimensions, not invented approximations.
- For additive manufacture, account for layer strength direction, overhangs, bridging, nozzle/line width, wall count, small holes, elephant foot, shrinkage, warping and support removal. Make orientation and material choices match actual loads and temperature. Verify fit with a calibration coupon where needed. Do not claim a universal tolerance works for every printer/material.
- For machining, consider tool access, internal corner radii, stock, setup/clamping, reachable pockets and drill/tap depths. For moulded parts consider draft, uniform walls, ribs, shrinkage and undercuts. Don't apply printing assumptions to every manufacturing process.
- Check validity after each major feature. Inspect Fusion timeline health and kernel diagnostics. Check body count, dimensions/bounding boxes, minimum walls, holes, symmetry, volume, interference and manifold/solid status as appropriate. A syntactically valid script is not a validated model; a nonempty exported file is not proof of dimensional accuracy. Report checks actually performed and remaining live checks.

## Multi-part deliverables
Use `create_cad_project(folder, backend, parts, notes)` to create a new workspace folder. Each part has a unique filesystem-safe `name` and exactly one `recipe` or `source`. Fusion recipe parts get separate `<name>.job.json` and eventual `<name>.f3d`; native scripts also get `<name>.py`. OpenSCAD parts get separate `<name>.scad`, with per-part meshes rendered only when requested. `project.json` records files, backend and design notes. Use new revision folders instead of overwriting existing work. Include dimension/tolerance/placement assumptions in notes.

For Fusion, use `run_fusion_project(project_file, launch=True)` and `fusion_project_status(project_file)` to run/check every part. Return each part's verified archive link, name and status. One part failing must not hide another part's success. Repair failed parts with new filenames. Do not claim an assembly merely because independent part archives exist; create a dedicated native assembly script/component design if the user requests an assembly.

## Native Fusion scripts for advanced modelling
Use `prepare_fusion_script(recipe_file, script_file, output, source)` or put Python `source` in a Fusion project part. The source MUST define `build(design, root)` with two arguments. Workshop creates a new parametric design and supplies its root component; `build` constructs native geometry with `adsk` APIs. Do not create your own document, modify unrelated open documents, export files or prompt for file selection inside build; the bridge handles document creation, archive export and result reporting. Top-level imports/helpers are allowed. Use native sketches, constraints, named parameters, extrusions, revolves, lofts, sweeps, shells, fillets/chamfers, patterns, components and joints as required by the actual design.

Generated Python is trusted code with local user permissions, exactly like the existing Python tool. `WORKSHOP_ALLOW_CODE=1` enables preparation/execution (the standard installer already enables it). Syntax and a build entry point are checked before saving. A source hash detects changes after preparation; regenerate a job after editing. Execution checks that a body/component was created and inspects timeline feature errors/warnings before export. These checks cannot establish that every design is geometrically correct.

Queue native scripts with `run_fusion_design` or the project run tool. WorkshopBridge executes them on Fusion's main thread automatically after one-time registration. Do not tell the user to run Python in a terminal to build Fusion geometry: the adsk API runs inside Fusion. If the bridge is unavailable, explain its one-time setup and retain the Fusion files. A manually selected script job asks Fusion's user for confirmation before executing trusted code.

Official API references for current signatures and samples:
- https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Sketch_UM.htm
- https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Component.htm
- https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Features.htm
- https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Units_UM.htm
- https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CustomEventSample_Sample.htm

## Native Fusion source example
This is a starting example for a simple filleted part, not a substitute for the requested dimensions/features. Pass its Python as `source` to the native script/project tool, then queue/check the job. The bridge exports the document. Live geometry still requires verification.

```python
"""Native Fusion example for prepare_fusion_script's source argument.

Build a 40 x 30 x 4 mm plate with 1 mm edge fillets. Workshop supplies a new
design/root, validates feature health and performs the archive export.
This example requires live Fusion verification; it is not a mesh workaround.
"""
import adsk.core
import adsk.fusion


def build(design, root):
    # User parameters drive the CAD history; coordinates only seed the sketch.
    for name, expression, reason in (
        ("width", "40 mm", "Requested footprint width"),
        ("depth", "30 mm", "Requested footprint depth"),
        ("thickness", "4 mm", "Requested spacer thickness"),
        ("edge_radius", "1 mm", "Assumed handling-edge rounding; confirm preference"),
    ):
        if not design.userParameters.add(
                name, adsk.core.ValueInput.createByString(expression), "mm", reason):
            raise RuntimeError("Could not create parameter " + name)
    if design.userParameters.itemByName("edge_radius").value * 2 >= design.userParameters.itemByName("thickness").value:
        raise ValueError("Edge radius must leave a positive straight section through the thickness")
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.name = "Plate footprint (40 x 30 mm)"
    rectangle = sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        sketch.originPoint, adsk.core.Point3D.create(4, 3, 0))
    if not rectangle or rectangle.count != 4:
        raise RuntimeError("Plate rectangle creation failed")
    # Find the opposing corner without depending on the returned edge order.
    opposite = None
    for index in range(rectangle.count):
        line = rectangle.item(index)
        for point in (line.startSketchPoint, line.endSketchPoint):
            if point.geometry.x > 0 and point.geometry.y > 0:
                opposite = point
    if opposite is None:
        raise RuntimeError("Plate rectangle is missing its opposite corner")
    dimensions = sketch.sketchDimensions
    horizontal = dimensions.addDistanceDimension(
        sketch.originPoint, opposite,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        adsk.core.Point3D.create(2, -0.5, 0))
    vertical = dimensions.addDistanceDimension(
        sketch.originPoint, opposite,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        adsk.core.Point3D.create(-0.5, 1.5, 0))
    if not horizontal or not vertical:
        raise RuntimeError("Could not dimension the plate footprint")
    horizontal.parameter.expression = "width"
    vertical.parameter.expression = "depth"
    if not sketch.isFullyConstrained:
        raise RuntimeError("Footprint is underconstrained; repair its datum or dimensions before exporting")
    if sketch.profiles.count != 1:
        raise RuntimeError("Plate footprint must have one closed profile")
    extrudes = root.features.extrudeFeatures
    extrusion = extrudes.createInput(
        sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extent = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString("thickness"))
    if not extrusion.setOneSideExtent(extent, adsk.fusion.ExtentDirections.PositiveExtentDirection):
        raise RuntimeError("Plate thickness extent failed")
    plate = extrudes.add(extrusion)
    plate.name = "Plate thickness (4 mm)"
    body = plate.bodies.item(0)
    body.name = "Filleted plate"
    edges = adsk.core.ObjectCollection.create()
    for index in range(body.edges.count):
        edges.add(body.edges.item(index))
    fillets = root.features.filletFeatures
    fillet = fillets.createInput()
    fillet.edgeSetInputs.addConstantRadiusEdgeSet(
        edges, adsk.core.ValueInput.createByString("edge_radius"), True)
    finishing = fillets.add(fillet)
    finishing.name = "Edge fillets (1 mm)"
    sketch.isVisible = False
```
