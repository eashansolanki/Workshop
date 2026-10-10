"""Workspace paths and local execution. Code execution is not an OS sandbox."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(os.environ.get("WORKSHOP_WORKSPACE", str(Path.cwd() / "workspace"))).expanduser().resolve()


def path(relative: str, *, new: bool = False) -> Path:
    """Resolve a workspace-relative path, including symlink containment checks."""
    value = Path(relative)
    if value.is_absolute() or not relative or relative == ".":
        raise ValueError("Provide a nonempty workspace-relative file path")
    result = (ROOT / value).resolve()
    if result == ROOT or not result.is_relative_to(ROOT):
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
    ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        proc = subprocess.Popen(args, cwd=ROOT, stdout=out, stderr=err,
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
    ROOT.mkdir(parents=True, exist_ok=True)
    suffix = ".py" if language == "python" else ".mjs"
    interpreter = sys.executable if language == "python" else shutil.which("node")
    if not interpreter:
        raise RuntimeError("Node.js is not installed")
    fd, filename = tempfile.mkstemp(prefix="workshop-", suffix=suffix, dir=ROOT)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(source)
        return process([interpreter, filename], timeout)
    finally:
        Path(filename).unlink(missing_ok=True)
