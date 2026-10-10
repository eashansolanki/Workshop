"""Run INSIDE Autodesk Fusion. Build recipe primitives and export an actual F3D."""
import json
import math
import traceback
from pathlib import Path
import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    document = None
    try:
        picker = ui.createFileDialog()
        picker.title = "Select Workshop recipe"
        picker.filter = "JSON recipes (*.json)"
        if picker.showOpen() != adsk.core.DialogResults.DialogOK:
            return
        job = Path(picker.filename).resolve()
        data = json.loads(job.read_text(encoding="utf-8"))
        output = Path(data["output"]).resolve()
        if output.suffix.lower() != ".f3d" or output.exists():
            raise ValueError("Output must be a new .f3d filename")
        parts = data["parts"]
        if data.get("units") != "mm" or not parts or len(parts) > 100 or parts[0].get("operation", "new") != "new":
            raise ValueError("Invalid millimetre recipe")
        for part in parts:
            if part["kind"] not in {"box", "cylinder"} or part.get("operation", "new") not in {"new", "join", "cut"}:
                raise ValueError("Unsupported primitive/operation")
            dimensions = [part["height"]] + ([part["width"], part["depth"]] if part["kind"] == "box" else [part["diameter"]])
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 for v in dimensions):
                raise ValueError("Invalid dimensions")
            origin = part.get("origin", [0, 0, 0])
            if len(origin) != 3 or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in origin):
                raise ValueError("Invalid origin")
        output.parent.mkdir(parents=True, exist_ok=True)
        document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        ops = {"new": adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
               "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
               "cut": adsk.fusion.FeatureOperations.CutFeatureOperation}
        for index, part in enumerate(parts):
            x, y, z = [v / 10.0 for v in part.get("origin", [0, 0, 0])]
            plane = root.xYConstructionPlane
            if z:
                plane_input = root.constructionPlanes.createInput()
                plane_input.setByOffset(plane, adsk.core.ValueInput.createByReal(z))
                plane = root.constructionPlanes.add(plane_input)
            sketch = root.sketches.add(plane)
            sketch.name = f"Workshop profile {index + 1}"
            point = adsk.core.Point3D.create(x, y, 0)
            if part["kind"] == "box":
                corner = adsk.core.Point3D.create(x + part["width"] / 10, y + part["depth"] / 10, 0)
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point, corner)
            else:
                sketch.sketchCurves.sketchCircles.addByCenterRadius(point, part["diameter"] / 20)
            operation = ops[part.get("operation", "new")]
            feature_input = root.features.extrudeFeatures.createInput(sketch.profiles.item(0), operation)
            distance = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(part["height"] / 10))
            feature_input.setOneSideExtent(distance, adsk.fusion.ExtentDirections.PositiveExtentDirection)
            feature = root.features.extrudeFeatures.add(feature_input)
            feature.name = f"Workshop {part['kind']} {index + 1}"
        options = design.exportManager.createFusionArchiveExportOptions(str(output), root)
        if not design.exportManager.execute(options) or not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError("Fusion archive export failed")
        (job.parent / (job.stem + ".result.json")).write_text(json.dumps({"status": "exported", "output": str(output), "bytes": output.stat().st_size}, indent=2))
        ui.messageBox(f"Exported genuine Fusion archive:\n{output}")
    except Exception:
        ui.messageBox(traceback.format_exc())
