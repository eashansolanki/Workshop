"""Local Fusion job queue and honest capability/completion reporting."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from . import core


def bridge_root():
    return Path(os.environ.get("WORKSHOP_FUSION_BRIDGE", str(Path.home() / ".workshop" / "fusion-bridge"))).expanduser().resolve()


def find_fusion_application(folders):
    """Match actual CAD bundle names, excluding Autodesk's service and removal apps."""
    names = ("Autodesk Fusion.app", "Autodesk Fusion 360.app")
    for folder in folders:
        for name in names:
            direct = folder / name
            if direct.is_dir():
                return str(direct)
        for name in names:
            for candidate in sorted(folder.glob("*/" + name)):
                if candidate.is_dir():
                    return str(candidate)
    return None


def fusion_status():
    """Separate available Workshop tools from Fusion installation and live readiness."""
    root = bridge_root()
    online = False
    try:
        heartbeat = json.loads((root / "heartbeat.json").read_text())
        online = 0 <= time.time() - heartbeat["time"] < 15
    except (OSError, ValueError, KeyError, TypeError):
        pass
    installed = None
    configured = os.environ.get("WORKSHOP_FUSION_APP")
    if configured and Path(configured).exists():
        installed = configured
    elif sys.platform == "darwin":
        installed = find_fusion_application((Path("/Applications"), Path.home() / "Applications", Path.home() / "Library/Application Support/Autodesk/webdeploy/production"))
    return {"integration_available": True, "recipe_preparation": True, "native_script_preparation": os.environ.get("WORKSHOP_ALLOW_CODE") == "1", "native_script_execution": os.environ.get("WORKSHOP_ALLOW_CODE") == "1" and not core.strict_writes(), "project_folders": True,
            "supported_imports": [".step", ".stp", ".iges", ".igs", ".sat", ".f3d"],
            "application_path": installed, "bridge_online": online,
            "automatic_execution": online, "bridge_directory": str(root),
            "setup": "Register fusion/WorkshopBridge as an add-in, run it once and enable Run on Startup. Manual WorkshopDesign remains available.",
            "limitation": "Fusion must execute CAD operations; preparing a job does not create an F3D."}


def launch_fusion():
    """Launch a known app without shell commands or guessed executable paths."""
    installed = fusion_status()["application_path"]
    if sys.platform == "darwin":
        args = ["/usr/bin/open", "-a", installed or "Autodesk Fusion"]
    elif sys.platform == "win32" and installed:
        core.workspace().mkdir(parents=True, exist_ok=True)
        proc = subprocess.Popen([installed], cwd=core.workspace(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "launch_requested", "pid": proc.pid}
    else:
        return {"status": "manual_launch_required", "instructions": "Open Autodesk Fusion; on Windows configure WORKSHOP_FUSION_APP with its executable path."}
    result = core.process(args, 30)
    return {"status": "launch_requested" if result["exit_code"] == 0 else "launch_failed", "diagnostics": result["stderr"]}


def result_path(job):
    return job.with_name(job.stem + ".result.json")


def design_status(recipe_file):
    job = core.path(recipe_file)
    result = result_path(job)
    found = json.loads(result.read_text()) if result.exists() else None
    if found and found.get("status") == "error":
        return found
    data = json.loads(job.read_text())
    output = Path(data["output"]).resolve()
    if not output.is_relative_to(core.workspace()):
        raise ValueError("Job output escapes the configured workspace")
    if found is None:
        ticket = bridge_root() / "queue" / (hashlib.sha256(str(job).encode()).hexdigest() + ".json")
        status = "queued" if ticket.exists() else "pending_fusion_execution"
        receipt = ticket.with_suffix(".receipt")
        if receipt.exists():
            record = json.loads(receipt.read_text())
            status = record.get("status", "error")
            if status == "running" and not fusion_status()["bridge_online"]:
                status = "execution_unconfirmed"
            if status == "error":
                return record
        return {"status": status, "recipe_path": str(job), "requested_output": str(output)}
    if found.get("status") in {"exported", "validation_failed"}:
        if Path(found.get("output", "")).resolve() != output or not output.is_file() or output.stat().st_size == 0:
            return {"status": "invalid_export", "error": "Result reports success but the expected archive is missing or empty"}
        found.update(output=str(output), bytes=output.stat().st_size, design_url=output.as_uri(),
                     design_link=f"[{output.name}]({output.as_uri()})")
    return found


def run_design(recipe_file, launch=True):
    """Queue one prepared job; never rerun a completed or queued job implicitly."""
    job = core.path(recipe_file)
    if not job.is_file():
        raise FileNotFoundError("Prepare the Fusion job first")
    data = json.loads(job.read_text())
    script_job = data.get("action") == "script"
    if script_job and core.strict_writes():
        raise PermissionError("Native Fusion Python runs inside Fusion outside the project sandbox. Strict Bionic tools cannot execute it; preparing source/jobs remains available.")
    if script_job and os.environ.get("WORKSHOP_ALLOW_CODE") != "1":
        raise PermissionError("Native Fusion script execution requires WORKSHOP_ALLOW_CODE=1")
    current = design_status(recipe_file)
    if current["status"] != "pending_fusion_execution":
        return current
    launch_result = launch_fusion() if launch and not fusion_status()["bridge_online"] else None
    root = bridge_root()
    queue = root / "queue"
    queue.mkdir(parents=True, exist_ok=True)
    # An exclusive deterministic ticket also deduplicates requests across MCP processes.
    ticket = queue / (hashlib.sha256(str(job).encode()).hexdigest() + ".json")
    request = {"job": str(job), "workspace": str(core.workspace()), "id": uuid.uuid4().hex, "allow_code": script_job}
    temp = queue / (uuid.uuid4().hex + ".tmp")
    try:
        temp.write_text(json.dumps(request), encoding="utf-8")
        try:
            os.link(temp, ticket)
        except FileExistsError:
            pass
    finally:
        temp.unlink(missing_ok=True)
    return {"status": "queued", "recipe_path": str(job), "requested_output": current["requested_output"],
            "bridge_online": fusion_status()["bridge_online"], "launch": launch_result,
            "instructions": "Use fusion_design_status to check completion. If bridge is offline, register/run WorkshopBridge in Fusion. Do not submit the same job again."}


def open_design(source):
    """Open an existing local archive in Fusion through the resident add-in."""
    file = core.path(source)
    if file.suffix.lower() != ".f3d" or not file.is_file() or not file.stat().st_size:
        raise ValueError("Select an existing nonempty .f3d file")
    root = bridge_root() / "queue"
    root.mkdir(parents=True, exist_ok=True)
    request = {"action": "open", "source": str(file), "workspace": str(core.workspace())}
    ticket = root / (uuid.uuid4().hex + ".json")
    temp = ticket.with_suffix(".tmp")
    temp.write_text(json.dumps(request))
    temp.replace(ticket)
    return {"status": "queued_open", "design_url": file.as_uri(), "bridge_online": fusion_status()["bridge_online"], "launch": launch_fusion() if not fusion_status()["bridge_online"] else None}


def project_jobs(project_file):
    """Read a Fusion project manifest and contain its jobs to that project folder."""
    manifest = core.path(project_file)
    data = json.loads(manifest.read_text())
    if data.get("backend") != "fusion" or not isinstance(data.get("parts"), list) or not 1 <= len(data["parts"]) <= 100:
        raise ValueError("Select a Fusion project manifest with 1-100 parts")
    jobs = []
    for part in data["parts"]:
        job = Path(part["recipe_path"]).resolve()
        if not job.is_relative_to(manifest.parent) or not job.is_relative_to(core.workspace()) or not job.is_file():
            raise ValueError("Part job escapes the project folder or is missing")
        jobs.append((part["name"], str(job.relative_to(core.workspace()))))
    return jobs


def run_project(project_file, launch=True):
    jobs = project_jobs(project_file)
    # Validate all parts before queuing any of them.
    for name, job in jobs:
        data = json.loads(core.path(job).read_text())
        if data.get("action") == "script" and core.strict_writes():
            raise PermissionError("Strict project-only mode cannot run unsandboxed native Fusion scripts")
        if data.get("action") == "script" and os.environ.get("WORKSHOP_ALLOW_CODE") != "1":
            raise PermissionError("Native Fusion scripts require WORKSHOP_ALLOW_CODE=1")
        design_status(job)
    launch_result = launch_fusion() if launch and not fusion_status()["bridge_online"] else None
    parts = [{"name": name, **run_design(job, False)} for name, job in jobs]
    return {"status": "submitted", "parts": parts, "launch": launch_result,
            "instructions": "Check fusion_project_status for every part's verified export and link."}


def project_status(project_file):
    parts = [{"name": name, **design_status(job)} for name, job in project_jobs(project_file)]
    states = {part["status"] for part in parts}
    status = "exported" if states == {"exported"} else "error" if states & {"error", "invalid_export", "validation_failed"} else "in_progress"
    return {"status": status, "parts": parts}
