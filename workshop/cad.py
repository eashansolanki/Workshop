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
    if not isinstance(recipe, dict) or not isinstance(recipe.get("parts"), list) or not recipe["parts"] or len(recipe["parts"]) > 100:
        raise ValueError("A recipe needs 1–100 parts")
    if recipe.get("units", "mm") != "mm":
        raise ValueError("Recipe units must be mm")
    cleaned = {"units": "mm", "parts": []}
    for index, part in enumerate(recipe["parts"], 1):
        if not isinstance(part, dict):
            raise ValueError(f"Part {index} must be an object")
        kind, operation = part.get("kind"), part.get("operation", "new")
        if not isinstance(kind, str) or not isinstance(operation, str):
            raise ValueError(f"Part {index}: kind and operation must be strings")
        required = {"box": ("height", "width", "depth"), "cylinder": ("height", "diameter")}.get(kind, ())
        if any(key not in part for key in required):
            raise ValueError(f"Part {index}: missing required dimension ({required})")
        if kind not in ("box", "cylinder") or operation not in ("new", "join", "cut"):
            raise ValueError("Supported primitives: box/cylinder; operations: new/join/cut")
        origin = part.get("origin", [0, 0, 0])
        if not isinstance(origin, (list, tuple)) or len(origin) != 3 or any(isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n) for n in origin):
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
    if job == target or job.with_name(job.stem + ".result.json").exists():
        raise FileExistsError("Job result already exists; use a new recipe filename")
    data["output"] = str(target)
    job.write_text(json.dumps(data, indent=2, allow_nan=False), encoding="utf-8")
    return {"recipe_path": str(job), "requested_output": str(target), "requested_output_url": target.as_uri(), "status": "pending_fusion_execution", "instructions": "Call run_fusion_design to queue execution via WorkshopBridge, or run WorkshopDesign manually and select this JSON. Check fusion_design_status for the saved-design link. No F3D exists until export succeeds."}


def prepare_fusion_import(recipe_file: str, source: str, output: str) -> dict:
    """Prepare native CAD import into a new Fusion document, then export F3D."""
    src, target, job = path(source), path(output, new=True), path(recipe_file, new=True)
    if src.suffix.lower() not in {".step", ".stp", ".iges", ".igs", ".sat", ".f3d"} or not src.is_file() or src.stat().st_size == 0:
        raise ValueError("Import requires a nonempty STEP, IGES, SAT or F3D file; meshes are not supported")
    if target.suffix.lower() != ".f3d" or job.suffix.lower() != ".json":
        raise ValueError("Use .json job and .f3d output")
    if job.with_name(job.stem + ".result.json").exists():
        raise FileExistsError("Job result already exists; use a new recipe filename")
    job.write_text(json.dumps({"action": "import", "source": str(src), "output": str(target)}, indent=2))
    return {"recipe_path": str(job), "requested_output": str(target), "requested_output_url": target.as_uri(), "status": "pending_fusion_execution", "instructions": "Call run_fusion_design, then fusion_design_status. Import/export are performed inside Fusion."}


def validate_fusion_source(source: str):
    """Check generated native Fusion code before saving it; execution is trusted/opt-in."""
    import ast
    import os
    if os.environ.get("WORKSHOP_ALLOW_CODE") != "1":
        raise PermissionError("Native Fusion scripts require WORKSHOP_ALLOW_CODE=1, like the existing Python tools")
    if not isinstance(source, str) or not source.strip() or len(source.encode()) > 1000000:
        raise ValueError("Provide 1-1000000 bytes of Fusion Python source")
    tree = ast.parse(source, filename="fusion-design.py")
    if not any(isinstance(node, ast.FunctionDef) and node.name == "build" and len(node.args.args) == 2 for node in tree.body):
        raise ValueError("Fusion source must define build(design, root); Workshop creates the new document and exports it")


def prepare_fusion_script(recipe_file: str, script_file: str, output: str, source: str) -> dict:
    """Prepare native sketches/lofts/sweeps/fillets/etc, without a mesh intermediary."""
    import hashlib
    validate_fusion_source(source)
    job, script, target = path(recipe_file, new=True), path(script_file, new=True), path(output, new=True)
    if job.suffix.lower() != ".json" or script.suffix.lower() != ".py" or target.suffix.lower() != ".f3d":
        raise ValueError("Use .json job, .py Fusion source and .f3d archive filenames")
    if job.with_name(job.stem + ".result.json").exists():
        raise FileExistsError("Job result already exists; use a new recipe filename")
    script.write_text(source, encoding="utf-8")
    data = {"action": "script", "script": str(script), "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(), "output": str(target)}
    job.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return {"recipe_path": str(job), "script_path": str(script), "requested_output": str(target), "status": "pending_fusion_execution", "instructions": "Call run_fusion_design then fusion_design_status. This uses native Fusion geometry; no OpenSCAD or mesh import is needed."}


def create_cad_project(folder: str, backend: str, parts: list[dict], notes: str = "", design_plan_file: str = "") -> dict:
    """Create a fresh project folder with separate source/job/output files for every part."""
    import re
    if backend not in {"fusion", "openscad"}:
        raise ValueError("Choose fusion or openscad explicitly, following the user's requested tool")
    if not isinstance(parts, list) or not 1 <= len(parts) <= 100:
        raise ValueError("Provide 1-100 separately named parts")
    names = set()
    for part in parts:
        if not isinstance(part, dict) or not isinstance(part.get("name"), str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", part["name"]):
            raise ValueError("Part names must be 1-80 letters/digits/hyphens/underscores; no paths")
        reserved = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
        if part["name"].lower() in reserved:
            raise ValueError("Part name is reserved by Windows; choose a portable filename")
        if part["name"].lower() in names:
            raise ValueError("Part names must be unique, ignoring case")
        names.add(part["name"].lower())
        if ("source" in part) == ("recipe" in part):
            raise ValueError("Each part needs exactly one source or recipe")
        if "recipe" in part:
            validate_recipe(part["recipe"])
        elif backend == "fusion":
            validate_fusion_source(part["source"])
        elif not isinstance(part["source"], str) or not part["source"].strip():
            raise ValueError("OpenSCAD source must be nonempty text")
    from . import design
    plan = design.read_plan(design_plan_file) if design_plan_file else None
    if plan and (plan["backend"] != backend or {part["name"] for part in plan["parts"]} != {part["name"] for part in parts}):
        raise ValueError("Project backend and exact part names must match the selected design plan")
    plan_parts = {part["name"]: part for part in plan["parts"]} if plan else {}
    target = path(folder, new=True)
    target.mkdir()
    created = []
    for part in parts:
        base = f"{folder}/{part['name']}"
        if backend == "fusion":
            if "source" in part:
                result = prepare_fusion_script(base + ".job.json", base + ".py", base + ".f3d", part["source"])
            else:
                result = prepare_fusion(base + ".job.json", base + ".f3d", part["recipe"])
        else:
            result = write_scad(base + ".scad", part["source"]) if "source" in part else recipe_to_scad(base + ".scad", part["recipe"])
        if plan:
            intent = plan_parts[part["name"]]
            result["planned_features"] = intent["features"]
            if backend == "fusion":
                job = Path(result["recipe_path"])
                job_data = json.loads(job.read_text())
                job_data["checks"] = design.validate_checks(intent.get("checks", []))
                job_data["design_plan_path"] = str(path(design_plan_file))
                job.write_text(json.dumps(job_data, indent=2, allow_nan=False), encoding="utf-8")
        created.append({"name": part["name"], **result})
    manifest = target / "project.json"
    project = {"backend": backend, "notes": notes, "parts": created}
    if plan:
        import hashlib
        plan_path = path(design_plan_file)
        project.update(design_plan_path=str(plan_path), design_plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest())
        (target / "design-plan.json").write_text(json.dumps(plan, indent=2, allow_nan=False), encoding="utf-8")
    manifest.write_text(json.dumps(project, indent=2), encoding="utf-8")
    return {"folder": str(target), "project_path": str(manifest), "backend": backend, "parts": created,
            "design_plan_path": project.get("design_plan_path"), "design_review_required": True, "status": "prepared", "instructions": "Fusion: run_fusion_project, then fusion_project_status. OpenSCAD: render each source with render_openscad. Separate part files do not constitute a constrained assembly."}
