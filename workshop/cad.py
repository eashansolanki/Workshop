"""OpenSCAD exports and recipe preparation for genuine Fusion archives."""
import json
import math
import shutil
from pathlib import Path
from .core import path, process


def positive(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError("Dimensions must be finite positive numbers in millimetres")
    return float(value)


def validate_recipe(recipe: dict) -> dict:
    """Validate additive/cut primitive recipe, keeping it portable across CAD tools."""
    if not isinstance(recipe, dict) or not recipe.get("parts") or len(recipe["parts"]) > 100:
        raise ValueError("A recipe needs 1–100 parts")
    cleaned = {"units": "mm", "parts": []}
    for part in recipe["parts"]:
        kind, operation = part["kind"], part.get("operation", "new")
        if kind not in {"box", "cylinder"} or operation not in {"new", "join", "cut"}:
            raise ValueError("Supported primitives: box/cylinder; operations: new/join/cut")
        origin = part.get("origin", [0, 0, 0])
        if len(origin) != 3 or any(isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n) for n in origin):
            raise ValueError("Origin requires three finite numbers")
        item = {"kind": kind, "operation": operation, "origin": origin, "height": positive(part["height"])}
        if kind == "box":
            item.update(width=positive(part["width"]), depth=positive(part["depth"]))
        else:
            item["diameter"] = positive(part["diameter"])
        cleaned["parts"].append(item)
    if cleaned["parts"][0]["operation"] != "new":
        raise ValueError("The first primitive must create a new body")
    return cleaned


def recipe_to_scad(output: str, recipe: dict) -> dict:
    """Generate mm-based SCAD; new/join add material and cut subtracts existing material."""
    data = validate_recipe(recipe)
    lines = ""
    for part in data["parts"]:
        primitive = (f'cube([{part["width"]},{part["depth"]},{part["height"]}]);' if part["kind"] == "box" else f'cylinder(h={part["height"]},d={part["diameter"]});')
        geometry = f'translate({json.dumps(part["origin"])}) {primitive}\n'
        if part["operation"] == "cut":
            lines = "difference(){\n" + lines + geometry + "}\n"
        else:
            lines = "union(){\n" + lines + geometry + "}\n"
    return write_scad(output, "$fn=96;\n" + lines)


def write_scad(output: str, source: str) -> dict:
    """Save custom OpenSCAD source; compilation is a separate explicit tool."""
    target = path(output, new=True)
    if target.suffix.lower() != ".scad":
        raise ValueError("OpenSCAD source needs .scad")
    target.write_text(source, encoding="utf-8")
    return {"path": str(target), "compiled": False}


def render_scad(source: str, output: str) -> dict:
    """Compile OpenSCAD to STL/3MF/PNG with installed OpenSCAD executable."""
    src, target = path(source), path(output, new=True)
    if src.suffix.lower() != ".scad" or target.suffix.lower() not in {".stl", ".3mf", ".png"}:
        raise ValueError("Use SCAD input and STL, 3MF or PNG output")
    binary = shutil.which("openscad")
    fallback = Path("/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD")
    if not binary and fallback.exists():
        binary = str(fallback)
    if not binary:
        raise RuntimeError("Install OpenSCAD and add it to PATH")
    result = process([binary, "-o", str(target), str(src)], 120)
    if result["exit_code"] or not target.is_file() or not target.stat().st_size:
        target.unlink(missing_ok=True)
        raise RuntimeError(result["stderr"] or "OpenSCAD export failed")
    return {"path": str(target), "diagnostics": result["stderr"]}


def prepare_fusion(recipe_file: str, output: str, recipe: dict) -> dict:
    """Write a validated job; Fusion's WorkshopDesign script must perform the F3D export."""
    data = validate_recipe(recipe)
    target = path(output, new=True)
    if target.suffix.lower() != ".f3d":
        raise ValueError("Fusion archive output must end in .f3d")
    job = path(recipe_file, new=True)
    if job.suffix.lower() != ".json":
        raise ValueError("Recipe file must end in .json")
    data["output"] = str(target)
    job.write_text(json.dumps(data, indent=2, allow_nan=False), encoding="utf-8")
    return {"recipe_path": str(job), "requested_output": str(target), "status": "pending_fusion_execution", "instructions": "Run fusion/WorkshopDesign in Autodesk Fusion and select this recipe JSON. No F3D exists until Fusion exports successfully."}
