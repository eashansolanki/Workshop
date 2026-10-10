"""Resident local job bridge. Only custom-event handlers call the CAD API."""
import importlib.util
import json
import os
from pathlib import Path
import threading
import time
import traceback
import adsk.core

EVENT = "workshop.fusion.jobs.v1"
_handlers = []
_stop = None
_thread = None
_app = None
_event = None
_pending = threading.Event()


def bridge_root():
    config = Path(__file__).with_name("bridge-config.json")
    setting = json.loads(config.read_text()).get("directory") if config.exists() else None
    return Path(setting or os.environ.get("WORKSHOP_FUSION_BRIDGE", str(Path.home() / ".workshop/fusion-bridge"))).expanduser().resolve()


def write_json(file, value):
    temp = file.with_suffix(".tmp")
    temp.write_text(json.dumps(value), encoding="utf-8")
    temp.replace(file)


def engine():
    source = Path(__file__).resolve().parents[1] / "WorkshopDesign/WorkshopDesign.py"
    spec = importlib.util.spec_from_file_location("workshop_fusion_engine", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def process_queue(root, worker):
    """Persistent receipts ensure Fusion restarts cannot silently replay jobs."""
    for ticket in sorted((root / "queue").glob("*.json")):
        receipt = ticket.with_suffix(".receipt")
        if receipt.exists():
            continue
        request = None
        try:
            request = json.loads(ticket.read_text())
            workspace = Path(request["workspace"]).resolve()
            source = Path(request.get("job") or request.get("source", "")).resolve()
            if not source.is_relative_to(workspace) or not source.is_file():
                raise ValueError("Request file is outside its workspace or missing")
            # Never interrupt an in-progress user command; wait for Fusion to be idle.
            if _app.userInterface.activeCommand != "SelectCommand":
                return
            try:
                with receipt.open("x", encoding="utf-8") as stream:
                    json.dump({"status": "running", "time": time.time()}, stream)
            except FileExistsError:
                continue
            if request.get("action") == "open":
                if source.suffix.lower() != ".f3d":
                    raise ValueError("Open requests require F3D")
                worker.import_document(_app, source)
                result = {"status": "opened", "source": str(source)}
            else:
                result = worker.execute_job(source, workspace, allow_code=request.get("allow_code") is True)
            write_json(receipt, result)
        except Exception as exc:
            result = {"status": "error", "error": str(exc), "traceback": traceback.format_exc()}
            write_json(receipt, result)
            if request and request.get("job"):
                job = Path(request["job"]).resolve()
                workspace = Path(request.get("workspace", "")).resolve()
                if job.is_relative_to(workspace) and job.is_file():
                    worker.write_result(job, result)


class JobEventHandler(adsk.core.CustomEventHandler):
    def __init__(self, root, worker):
        super().__init__()
        self.root, self.worker = root, worker

    def notify(self, args):
        try:
            write_json(self.root / "heartbeat.json", {"time": time.time()})
            process_queue(self.root, self.worker)
        except Exception:
            _app.log(traceback.format_exc())
        finally:
            _pending.clear()


def poll(stop_flag, app):
    while not stop_flag.wait(1):
        if not _pending.is_set():
            _pending.set()
            if not app.fireCustomEvent(EVENT):
                _pending.clear()


def run(context):
    global _stop, _thread, _app, _event
    if _thread and _thread.is_alive():
        return
    _app = adsk.core.Application.get()
    root = bridge_root()
    (root / "queue").mkdir(parents=True, exist_ok=True)
    _event = _app.registerCustomEvent(EVENT)
    handler = JobEventHandler(root, engine())
    _event.add(handler)
    _handlers.append(handler)
    _pending.clear()
    _stop = threading.Event()
    _thread = threading.Thread(target=poll, args=(_stop, _app), daemon=True)
    _thread.start()


def stop(context):
    global _thread
    if _stop:
        _stop.set()
    if _thread:
        _thread.join(timeout=2)
    if _event:
        for handler in _handlers:
            _event.remove(handler)
        _app.unregisterCustomEvent(EVENT)
    _handlers.clear()
    _thread = None
    (bridge_root() / "heartbeat.json").unlink(missing_ok=True)
