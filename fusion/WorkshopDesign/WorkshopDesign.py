"""Run inside Fusion manually, or through the resident WorkshopBridge add-in."""
import hashlib
import json
import math
import traceback
from pathlib import Path
import adsk.core
import adsk.fusion


def validate(data):
    """Validate before creating a document; report the exact offending part."""
    if not isinstance(data, dict) or data.get("action", "recipe") not in ("recipe", "import", "script"):
        raise ValueError("Job must be a recipe, native script or CAD import object")
    if data.get("action") == "script":
        source = Path(data["script"])
        if source.suffix.lower() != ".py" or not source.is_file():
            raise ValueError("Script job needs an existing .py source")
        if hashlib.sha256(source.read_bytes()).hexdigest() != data.get("script_sha256"):
            raise ValueError("Fusion source changed after preparation; prepare a new job")
        return
    if data.get("action") == "import":
        source = Path(data["source"])
        if source.suffix.lower() not in {".step", ".stp", ".iges", ".igs", ".sat", ".f3d"} or not source.is_file() or not source.stat().st_size:
            raise ValueError("Import needs a nonempty STEP, IGES, SAT or F3D file")
        return
    parts = data.get("parts")
    if data.get("units") != "mm" or not isinstance(parts, list) or not 1 <= len(parts) <= 100:
        raise ValueError("Recipe needs mm units and 1-100 parts")
    for index, part in enumerate(parts, 1):
        try:
            if not isinstance(part, dict) or part.get("kind") not in ("box", "cylinder") or part.get("operation", "new") not in ("new", "join", "cut"):
                raise ValueError("Supported primitives: box/cylinder; operations: new/join/cut")
            if index == 1 and part.get("operation", "new") != "new":
                raise ValueError("The first primitive must create a new body")
            dimensions = [part["height"]] + ([part["width"], part["depth"]] if part["kind"] == "box" else [part["diameter"]])
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 for v in dimensions):
                raise ValueError("Dimensions must be finite positive numbers in mm")
            origin = part.get("origin", [0, 0, 0])
            if not isinstance(origin, (list, tuple)) or len(origin) != 3 or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in origin):
                raise ValueError("Origin requires three finite numbers")
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Part {index}: {exc}") from exc


def import_document(app, source):
    """Use native import APIs; never force complex imports into recipe primitives."""
    manager = app.importManager
    methods = {".step": "createSTEPImportOptions", ".stp": "createSTEPImportOptions",
               ".iges": "createIGESImportOptions", ".igs": "createIGESImportOptions",
               ".sat": "createSATImportOptions", ".f3d": "createFusionArchiveImportOptions"}
    factory = methods.get(source.suffix.lower())
    if not factory:
        raise ValueError("Unsupported import format")
    options = getattr(manager, factory)(str(source))
    if not options:
        raise RuntimeError("Fusion could not create import options")
    document = manager.importToNewDocument(options)
    if not document:
        raise RuntimeError("Fusion import failed; inspect the source file in Fusion")
    return document


def build_parts(design, parts):
    root = design.rootComponent
    ops = {"new": adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
           "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
           "cut": adsk.fusion.FeatureOperations.CutFeatureOperation}
    warnings = []
    for index, part in enumerate(parts, 1):
        operation = part.get("operation", "new")
        try:
            x, y, z = [v / 10.0 for v in part.get("origin", [0, 0, 0])]
            plane = root.xYConstructionPlane
            if z:
                plane_input = root.constructionPlanes.createInput()
                if not plane_input.setByOffset(plane, adsk.core.ValueInput.createByReal(z)):
                    raise RuntimeError("Could not define the offset plane")
                plane = root.constructionPlanes.add(plane_input)
            sketch = root.sketches.add(plane)
            sketch.name = f"Workshop profile {index}"
            # Explicit world-to-sketch conversion preserves origins on offset planes.
            point = sketch.modelToSketchSpace(adsk.core.Point3D.create(x, y, z))
            if part["kind"] == "box":
                corner = sketch.modelToSketchSpace(adsk.core.Point3D.create(x + part["width"] / 10, y + part["depth"] / 10, z))
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point, corner)
            else:
                sketch.sketchCurves.sketchCircles.addByCenterRadius(point, part["diameter"] / 20)
            if sketch.profiles.count != 1:
                raise RuntimeError(f"Expected one closed profile, got {sketch.profiles.count}")
            if operation != "new" and root.bRepBodies.count == 0:
                raise ValueError("No existing body to join or cut")
            feature_input = root.features.extrudeFeatures.createInput(sketch.profiles.item(0), ops[operation])
            distance = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(part["height"] / 10))
            if not feature_input.setOneSideExtent(distance, adsk.fusion.ExtentDirections.PositiveExtentDirection):
                raise RuntimeError("Could not define extrusion extent")
            if operation == "cut":
                # Include hidden bodies too: visibility must not change recipe geometry.
                feature_input.participantBodies = [root.bRepBodies.item(i) for i in range(root.bRepBodies.count)]
            feature = root.features.extrudeFeatures.add(feature_input)
            feature.name = f"Workshop {part['kind']} {index}"
            if feature.healthState == adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState:
                raise RuntimeError(feature.errorOrWarningMessage)
            if feature.healthState == adsk.fusion.FeatureHealthStates.WarningFeatureHealthState:
                warnings.append({"part": index, "message": feature.errorOrWarningMessage})
            sketch.isVisible = False
        except Exception as exc:
            hint = " Check intersection with existing material; use new for disjoint additions." if operation in {"join", "cut"} else ""
            raise RuntimeError(f"Part {index} ({part['kind']}, {operation}): {exc}.{hint}") from exc
    return warnings


def geometry_summary(design):
    """Measure actual BRep instances in root assembly coordinates, excluding sketches."""
    root = design.rootComponent
    instances = [root.bRepBodies.item(i) for i in range(root.bRepBodies.count)]
    for index in range(root.allOccurrences.count):
        occurrence = root.allOccurrences.item(index)
        instances.extend(occurrence.bRepBodies.item(i) for i in range(occurrence.bRepBodies.count))
    if not instances:
        raise RuntimeError("Design created no BRep bodies; empty components and meshes are not a completed native design")
    minimum = [math.inf, math.inf, math.inf]
    maximum = [-math.inf, -math.inf, -math.inf]
    solids = 0
    for body in instances:
        if not body.isValid:
            raise RuntimeError("Design created an invalid BRep body")
        solids += int(body.isSolid)
        box = body.preciseBoundingBox
        for axis, name in enumerate(("x", "y", "z")):
            low, high = getattr(box.minPoint, name), getattr(box.maxPoint, name)
            if not math.isfinite(low) or not math.isfinite(high):
                raise RuntimeError("Body bounds are not finite")
            minimum[axis] = min(minimum[axis], low)
            maximum[axis] = max(maximum[axis], high)
    return {"body_count": len(instances), "solid_body_count": solids, "component_count": design.allComponents.count,
            **{f"size_{name}_mm": (maximum[axis] - minimum[axis]) * 10 for axis, name in enumerate(("x", "y", "z"))}}


def validate_checks(checks):
    if not isinstance(checks, list) or len(checks) > 100:
        raise ValueError("Checks must be a list of up to 100 criteria")
    metrics = ("size_x_mm", "size_y_mm", "size_z_mm", "body_count", "solid_body_count")
    identities = set()
    for check in checks:
        if not isinstance(check, dict) or not isinstance(check.get("requirement"), str) or not check["requirement"].strip() or check.get("metric") not in metrics:
            raise ValueError("Each check needs a requirement ID and supported geometry metric")
        if check["requirement"] in identities:
            raise ValueError("Automatic check requirement IDs must be unique per part")
        identities.add(check["requirement"])
        for name in ("expected", "tolerance"):
            value = check.get(name, 0 if name == "tolerance" else None)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError("Check expected/tolerance must be finite nonnegative numbers")
        if check["metric"].endswith("count") and (check["expected"] % 1 or check.get("tolerance", 0) != 0):
            raise ValueError("Body-count criteria must be exact integer counts")


def evaluate_checks(geometry, checks):
    validate_checks(checks)
    measured = []
    for check in checks:
        actual = geometry[check["metric"]]
        expected, tolerance = check["expected"], check.get("tolerance", 0)
        passed = abs(actual - expected) <= tolerance + 1e-9
        measured.append({**check, "actual": actual, "tolerance": tolerance, "status": "pass" if passed else "fail"})
    return measured


def save_preview(app, output, warnings):
    preview = output.with_suffix(".preview.png")
    try:
        if preview.exists():
            raise FileExistsError("Preview already exists; it was not overwritten")
        options = adsk.core.SaveImageFileOptions.create(str(preview))
        options.width, options.height = 1200, 900
        if not app.activeViewport.saveAsImageFileWithOptions(options) or not preview.is_file() or not preview.stat().st_size:
            raise RuntimeError("Fusion did not save a nonempty viewport image")
        return str(preview)
    except Exception as exc:
        warnings.append({"message": f"Archive exported, but preview is unavailable: {exc}"})
        return None


def write_result(job, result):
    file = job.with_name(job.stem + ".result.json")
    temp = file.with_suffix(".tmp")
    temp.write_text(json.dumps(result, indent=2), encoding="utf-8")
    temp.replace(file)


def execute_job(job, workspace=None, allow_code=False):
    """Export a new document and always record errors for the calling model."""
    job = Path(job).resolve()
    output = None
    try:
        app = adsk.core.Application.get()
        data = json.loads(job.read_text(encoding="utf-8"))
        output = Path(data["output"])
        if not output.is_absolute():
            raise ValueError("Output path must be absolute")
        output = output.resolve()
        if workspace:
            root = Path(workspace).resolve()
            if not job.is_relative_to(root) or not output.is_relative_to(root):
                raise ValueError("Job or output escapes the requested workspace")
            if data.get("action") == "import" and not Path(data["source"]).resolve().is_relative_to(root):
                raise ValueError("Import source escapes the requested workspace")
            if data.get("action") == "script" and not Path(data["script"]).resolve().is_relative_to(root):
                raise ValueError("Script source escapes the requested workspace")
        if data.get("action") == "script" and not allow_code:
            raise PermissionError("Native Fusion script execution was not enabled by the calling tool")
        if output.suffix.lower() != ".f3d" or output.exists():
            raise ValueError("Output must be a new .f3d filename")
        validate(data)
        validate_checks(data.get("checks", []))
        output.parent.mkdir(parents=True, exist_ok=True)
        if data.get("action") == "import":
            document = import_document(app, Path(data["source"]).resolve())
        else:
            document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
        if not design:
            raise RuntimeError("The new document does not contain a Fusion design")
        warnings = []
        geometry = None
        if data.get("action") != "import":
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            if data.get("action") == "script":
                source = Path(data["script"])
                namespace = {"adsk": adsk, "__name__": "workshop_generated_design", "__file__": str(source)}
                exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"), namespace)
                build = namespace.get("build")
                if not callable(build):
                    raise ValueError("Native script must define build(design, root)")
                build(design, design.rootComponent)
                for index in range(design.timeline.count):
                    entity = design.timeline.item(index).entity
                    health = getattr(entity, "healthState", None)
                    if health == adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState:
                        raise RuntimeError(f"Timeline feature {index + 1}: {entity.errorOrWarningMessage}")
                    if health == adsk.fusion.FeatureHealthStates.WarningFeatureHealthState:
                        warnings.append({"feature": index + 1, "message": entity.errorOrWarningMessage})
            else:
                warnings = build_parts(design, data["parts"])
        geometry = geometry_summary(design)
        checks = evaluate_checks(geometry, data.get("checks", []))
        if not document.isSaved:
            document.name = output.stem
        options = design.exportManager.createFusionArchiveExportOptions(str(output), design.rootComponent)
        if not options or not design.exportManager.execute(options) or not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError("Fusion archive export failed")
        try:
            app.activeViewport.fit()
        except Exception as exc:
            warnings.append({"message": f"Archive exported, but viewport fit failed: {exc}"})
        preview = save_preview(app, output, warnings)
        result = {"status": "validation_failed" if any(check["status"] == "fail" for check in checks) else "exported", "output": str(output), "bytes": output.stat().st_size,
                  "design_url": output.as_uri(), "design_link": f"[{output.name}]({output.as_uri()})", "warnings": warnings, "geometry": geometry, "checks": checks, "preview_path": preview}
    except Exception as exc:
        result = {"status": "error", "error": str(exc), "traceback": traceback.format_exc(), "requested_output": str(output) if output else None}
    write_result(job, result)
    return result


def run(context):
    ui = adsk.core.Application.get().userInterface
    picker = ui.createFileDialog()
    picker.title = "Select Workshop recipe or import job"
    picker.filter = "JSON jobs (*.json)"
    if picker.showOpen() != adsk.core.DialogResults.DialogOK:
        return
    try:
        data = json.loads(Path(picker.filename).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        result = execute_job(picker.filename)
        ui.messageBox(result["traceback"])
        return
    allow_code = False
    if data.get("action") == "script":
        answer = ui.messageBox("This job executes trusted Python inside Fusion with your user permissions. Run it?", "Workshop native script", adsk.core.MessageBoxButtonTypes.YesNoButtonType)
        if answer != adsk.core.DialogResults.DialogYes:
            return
        allow_code = True
    result = execute_job(picker.filename, allow_code=allow_code)
    ui.messageBox(f"Exported genuine Fusion archive:\n{result['output']}" if result["status"] == "exported" else f"Archive exported but design checks failed:\n{result['output']}\n{result['checks']}" if result["status"] == "validation_failed" else result["traceback"])
