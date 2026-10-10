"""Design briefs, traceable modelling decisions and evidence-based reviews."""
import copy
import hashlib
import json
import math
import re
from pathlib import Path
from . import core

METRICS = {"size_x_mm", "size_y_mm", "size_z_mm", "body_count", "solid_body_count"}


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + " must be nonempty text")
    return value


def records(value, label, *, minimum=1, maximum=100):
    if not isinstance(value, list) or not minimum <= len(value) <= maximum or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{label} needs {minimum}-{maximum} objects")
    return value


def validate_checks(checks):
    records(checks, "Checks", minimum=0, maximum=100)
    ids = set()
    for check in checks:
        identity = text(check.get("requirement"), "Check requirement")
        if identity in ids:
            raise ValueError("Only one automatic metric per requirement; use distinct requirement IDs for distinct criteria")
        ids.add(identity)
        if not isinstance(check.get("metric"), str) or check["metric"] not in METRICS:
            raise ValueError("Automatic checks support envelope size in mm and body/solid-body counts")
        for field in ("expected", "tolerance"):
            value = check.get(field, 0 if field == "tolerance" else None)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError("Check expected/tolerance must be finite nonnegative numbers")
        if check["metric"].endswith("count") and (check["expected"] % 1 or check.get("tolerance", 0) != 0):
            raise ValueError("Body-count checks need an integer expected count and zero tolerance")
    return copy.deepcopy(checks)


def validate_plan(plan):
    """Require design intent, concept selection and verification, not private chain of thought."""
    if not isinstance(plan, dict) or plan.get("backend") not in ("fusion", "openscad"):
        raise ValueError("Design plan must explicitly choose fusion or openscad as requested by the user")
    text(plan.get("purpose"), "Purpose")
    text(plan.get("context"), "Use context")
    text(plan.get("manufacturing"), "Manufacturing/process/material assumptions")
    if plan.get("complexity", "simple") not in ("simple", "complex"):
        raise ValueError("Complexity must be simple or complex")
    requirements = records(plan.get("requirements"), "Requirements")
    ids = set()
    for requirement in requirements:
        identity = text(requirement.get("id"), "Requirement ID")
        if identity in ids:
            raise ValueError("Requirement IDs must be unique")
        ids.add(identity)
        for field in ("description", "acceptance", "verification"):
            text(requirement.get(field), "Requirement " + identity + " " + field)
    concepts = records(plan.get("concepts"), "Concepts", minimum=2 if plan.get("complexity") == "complex" else 1, maximum=10)
    concept_names = set()
    for concept in concepts:
        name = text(concept.get("name"), "Concept name")
        if name in concept_names:
            raise ValueError("Concept names must be unique")
        concept_names.add(name)
        for field in ("approach", "tradeoffs"):
            text(concept.get(field), "Concept " + name + " " + field)
    if not isinstance(plan.get("selected_concept"), str) or plan["selected_concept"] not in concept_names:
        raise ValueError("Select one of the described concepts")
    text(plan.get("selection_reason"), "Concept selection reason")
    parameters = records(plan.get("parameters", []), "Parameters", minimum=0)
    parameter_names = set()
    for parameter in parameters:
        name = text(parameter.get("name"), "Parameter name")
        if name in parameter_names:
            raise ValueError("Parameter names must be unique")
        parameter_names.add(name)
        text(parameter.get("unit"), "Parameter units")
        text(parameter.get("reason"), "Parameter reason")
        if parameter.get("basis") not in ("user", "assumption", "derived"):
            raise ValueError("Parameter basis must be user, assumption or derived")
        value = parameter.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float, str)) or isinstance(value, (int, float)) and not math.isfinite(value):
            raise ValueError("Parameter value must be a finite number or an expression")
        if isinstance(value, str):
            text(value, "Parameter expression")
    parts = records(plan.get("parts"), "Parts")
    part_names, covered = set(), set()
    for part in parts:
        name = text(part.get("name"), "Part name")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", name) or name.lower() in part_names:
            raise ValueError("Use unique filesystem-safe part names")
        part_names.add(name.lower())
        text(part.get("role"), "Part role")
        features = records(part.get("features"), "Part features")
        previous = set()
        for feature in features:
            identity = text(feature.get("name"), "Feature name")
            if identity in previous:
                raise ValueError("Feature names must be unique within their part")
            for field in ("operation", "reason"):
                text(feature.get(field), "Feature " + field)
            linked = feature.get("requirements")
            if not isinstance(linked, list) or not linked or any(not isinstance(item, str) or item not in ids for item in linked):
                raise ValueError("Every planned feature must reference known requirements")
            dependencies = feature.get("depends_on", [])
            if not isinstance(dependencies, list) or any(not isinstance(item, str) or item not in previous for item in dependencies):
                raise ValueError("Feature dependencies must refer to earlier features in the same part")
            previous.add(identity)
            covered.update(linked)
        validate_checks(part.get("checks", []))
        if any(check["requirement"] not in ids for check in part.get("checks", [])):
            raise ValueError("Automatic checks must reference known requirements")
    if covered != ids:
        raise ValueError("Every requirement must be covered by at least one planned feature; missing " + ", ".join(sorted(ids - covered)))
    interfaces = records(plan.get("interfaces", []), "Interfaces", minimum=1 if len(parts) > 1 else 0)
    for interface in interfaces:
        for field in ("name", "relationship", "verification"):
            text(interface.get(field), "Interface " + field)
        members = interface.get("parts")
        if not isinstance(members, list) or len(members) < 2 or any(not isinstance(item, str) or item.lower() not in part_names for item in members) or len({item.lower() for item in members}) < 2:
            raise ValueError("Interfaces must name at least two known parts; describe independent parts explicitly if they do not mate")
    assumptions = records(plan.get("assumptions", []), "Assumptions", minimum=0)
    for assumption in assumptions:
        for field in ("statement", "risk", "resolution"):
            text(assumption.get(field), "Assumption " + field)
    return copy.deepcopy(plan)


def plan_design(output, plan):
    data = validate_plan(plan)
    target = core.path(output, new=True)
    if target.suffix.lower() != ".json":
        raise ValueError("Design plan output needs .json")
    target.write_text(json.dumps(data, indent=2, allow_nan=False), encoding="utf-8")
    return {"path": str(target), "status": "planned", "backend": data["backend"],
            "requirements": len(data["requirements"]), "parts": [part["name"] for part in data["parts"]],
            "next": "Create the selected design with create_cad_project(..., design_plan_file=...). Execute, inspect and call review_cad_design. A plan is not tested geometry."}


def read_plan(source):
    return validate_plan(json.loads(core.path(source).read_text(encoding="utf-8")))


def check_artifact(relative):
    artifact = core.path(relative)
    if not artifact.is_file() or not artifact.stat().st_size:
        raise ValueError("Evidence must reference an existing nonempty workspace file: " + relative)
    return {"path": str(artifact), "bytes": artifact.stat().st_size}


def review_design(plan_file, project_file, output, findings):
    """Keep failed/untested criteria visible; measured Fusion checks override self-reports."""
    from . import fusion_bridge
    plan = read_plan(plan_file)
    manifest = core.path(project_file)
    project = json.loads(manifest.read_text(encoding="utf-8"))
    if project.get("design_plan_path") != str(core.path(plan_file)) or project.get("backend") != plan["backend"]:
        raise ValueError("Project must be linked to this design plan and backend")
    if project.get("design_plan_sha256") != hashlib.sha256(core.path(plan_file).read_bytes()).hexdigest():
        raise ValueError("Design plan changed after project creation; create a revised project")
    actual_parts = {part["name"] for part in project["parts"]}
    if actual_parts != {part["name"] for part in plan["parts"]}:
        raise ValueError("Project parts differ from the plan")
    records(findings, "Review findings", minimum=0)
    by_id = {}
    known = {item["id"] for item in plan["requirements"]}
    for finding in findings:
        identity = finding.get("requirement")
        if not isinstance(identity, str) or identity not in known or identity in by_id:
            raise ValueError("Findings must uniquely reference known requirements")
        if finding.get("status") not in ("pass", "fail", "not_checked"):
            raise ValueError("Finding status must be pass, fail or not_checked")
        text(finding.get("evidence"), "Finding evidence or unresolved-check explanation")
        artifacts = finding.get("artifacts", [])
        if not isinstance(artifacts, list):
            raise ValueError("Finding artifacts must be workspace-relative filenames")
        checked_files = [check_artifact(item) for item in artifacts]
        if finding["status"] == "pass" and not checked_files:
            raise ValueError("Reported passes need saved measurement/inspection evidence, not just a claim")
        by_id[identity] = {**finding, "artifacts": checked_files, "authority": "caller_reported"}
    part_results = []
    automatic = {}
    for part in project["parts"]:
        if plan["backend"] == "fusion":
            job = Path(part["recipe_path"]).resolve()
            if not job.is_relative_to(manifest.parent):
                raise ValueError("Part job escapes project folder")
            result = fusion_bridge.design_status(str(job.relative_to(core.workspace())))
            for check in result.get("checks", []):
                automatic.setdefault(check["requirement"], []).append({**check, "part": part["name"]})
        else:
            source = Path(part["path"]).resolve()
            if not source.is_relative_to(manifest.parent):
                raise ValueError("Part source escapes project folder")
            result = {"status": "source_only", "path": str(source)}
        part_results.append({"name": part["name"], **result})
    reviewed = []
    expected_checks = {}
    for part in plan["parts"]:
        for check in part.get("checks", []):
            expected_checks.setdefault(check["requirement"], set()).add(part["name"])
    for requirement in plan["requirements"]:
        identity = requirement["id"]
        measured_parts = {check["part"] for check in automatic.get(identity, [])}
        if identity in expected_checks and measured_parts != expected_checks[identity]:
            finding = {"requirement": identity, "status": "not_checked", "evidence": "Required automatic checks have not completed for every planned part", "authority": "none"}
        elif identity in automatic:
            checks = automatic[identity]
            finding = {"requirement": identity, "status": "pass" if all(item["status"] == "pass" for item in checks) else "fail", "authority": "fusion_measured", "checks": checks}
        else:
            finding = by_id.get(identity, {"requirement": identity, "status": "not_checked", "evidence": "No measurement or inspection evidence supplied", "authority": "none"})
        reviewed.append({"description": requirement["description"], "acceptance": requirement["acceptance"], **finding})
    failures = [item["requirement"] for item in reviewed if item["status"] == "fail"]
    outstanding = [item["requirement"] for item in reviewed if item["status"] == "not_checked"]
    execution_pending = plan["backend"] == "fusion" and any(item["status"] not in ("exported", "validation_failed") for item in part_results)
    status = "needs_revision" if failures else "needs_verification" if outstanding or execution_pending else "ready_for_user_review"
    report = {"status": status, "plan_path": str(core.path(plan_file)), "project_path": str(manifest), "requirements": reviewed, "parts": part_results,
              "failed_requirements": failures, "unchecked_requirements": outstanding,
              "limitations": "Caller-supplied inspection reports are not independently verified. Export/metric checks do not establish strength, fit or safety. Physical checks remain necessary where the brief requires them."}
    target = core.path(output, new=True)
    if target.suffix.lower() != ".json":
        raise ValueError("Review output needs .json")
    target.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    return {"review_path": str(target), **report}
