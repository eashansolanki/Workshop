"""Request-scoped workspaces and project-only subprocess writes in strict Bionic mode."""
import os
import json
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(os.environ.get("WORKSHOP_WORKSPACE", str(Path.cwd() / "workspace"))).expanduser().resolve()

_ACTIVE_ROOT = ContextVar("workshop_project_root", default=None)
_SCOPE_ERROR = ContextVar("workshop_project_error", default=None)


def bionic_mode():
    return os.environ.get("WORKSHOP_WORKSPACE_MODE") == "bionic"


@contextmanager
def workspace_scope(folder, error=None):
    token = _ACTIVE_ROOT.set(Path(folder).resolve() if folder is not None else None)
    error_token = _SCOPE_ERROR.set(error)
    try:
        yield
    finally:
        _SCOPE_ERROR.reset(error_token)
        _ACTIVE_ROOT.reset(token)


def workspace():
    active = _ACTIVE_ROOT.get()
    if active is not None:
        return active
    if bionic_mode():
        raise PermissionError(_SCOPE_ERROR.get() or "Bionic working directory unavailable; Documents/Workshop fallback is disabled")
    return ROOT


def workspace_status():
    try:
        return {"workspace": str(workspace()), "workspace_ready": True, "workspace_mode": "bionic" if bionic_mode() else "configured"}
    except PermissionError as exc:
        return {"workspace": None, "workspace_ready": False, "workspace_mode": "bionic", "workspace_error": str(exc)}


def strict_writes():
    return bionic_mode() or os.environ.get("WORKSHOP_STRICT_WRITES") == "1"


def sandbox_command(args):
    """Code subprocesses may write only inside the selected project; fail closed elsewhere."""
    if not strict_writes():
        return args
    if sys.platform != "darwin" or not Path("/usr/bin/sandbox-exec").is_file():
        raise PermissionError("Strict project-only code execution requires macOS sandbox-exec; arbitrary code is disabled on this platform")
    folder = json.dumps(str(workspace()))
    profile = f'(version 1)(deny default)(allow file-read*)(allow file-write* (subpath {folder}))(allow process-exec process-fork process-info* signal sysctl-read)'
    return ["/usr/bin/sandbox-exec", "-p", profile, *args]


def path(relative: str, *, new: bool = False) -> Path:
    """Resolve a workspace-relative path, including symlink containment checks."""
    value = Path(relative)
    if value.is_absolute() or not relative or relative == ".":
        raise ValueError("Provide a nonempty workspace-relative file path")
    result = (workspace() / value).resolve()
    if result == workspace() or not result.is_relative_to(workspace()):
        raise ValueError("Path escapes the configured workspace")
    if new:
        if result.exists():
            raise FileExistsError("Output already exists; use a new filename")
        result.parent.mkdir(parents=True, exist_ok=True)
    return result


def process(args: list[str], timeout: int = 60) -> dict:
    """Execute without a shell; kill the process group after timeout on POSIX."""
    if not 1 <= timeout <= 300:
        raise ValueError("Timeout must be 1–300 seconds")
    workspace().mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        proc = subprocess.Popen(sandbox_command(args), cwd=workspace(), stdout=out, stderr=err,
                                start_new_session=os.name == "posix")
        try:
            code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                import signal
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                proc.kill()
            proc.wait()
            raise TimeoutError(f"Process exceeded {timeout} seconds")
        out.seek(0)
        err.seek(0)
        return {"exit_code": code, "stdout": out.read(64000).decode(errors="replace"),
                "stderr": err.read(64000).decode(errors="replace")}


def execute(language: str, source: str, timeout: int = 60) -> dict:
    """Run trusted Python or JavaScript only when explicitly enabled by the owner."""
    if os.environ.get("WORKSHOP_ALLOW_CODE") != "1":
        raise PermissionError("Set WORKSHOP_ALLOW_CODE=1 to enable trusted local code execution")
    if language not in {"python", "javascript"}:
        raise ValueError("Language must be python or javascript")
    workspace().mkdir(parents=True, exist_ok=True)
    suffix = ".py" if language == "python" else ".mjs"
    interpreter = sys.executable if language == "python" else shutil.which("node")
    if not interpreter:
        raise RuntimeError("Node.js is not installed")
    fd, filename = tempfile.mkstemp(prefix="workshop-", suffix=suffix, dir=workspace())
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(source)
        return process([interpreter, "-B", filename] if language == "python" else [interpreter, filename], timeout)
    finally:
        Path(filename).unlink(missing_ok=True)
