"""Shell installer engine: private runtimes, verified tools, backed-up LM Studio settings."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import uuid


def atomic_text(target: Path, text: str):
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".workshop-", dir=target.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(text)
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)


def progress(title: str, message: str):
    """Report progress in the terminal without opening apps or creating GUI artifacts."""
    print(f"\n{title}\n{message}", flush=True)


def merge_config(target: Path, additions: dict) -> Path | None:
    """Validate before changing anything, preserve unrelated servers, back up exact bytes."""
    if target.is_symlink():
        raise ValueError("LM Studio settings are a symbolic link; automatic setup will not replace them")
    original = target.read_bytes() if target.exists() else None
    existing = json.loads(original) if original is not None else {}
    if not isinstance(existing, dict) or not isinstance(existing.get("mcpServers", {}), dict):
        raise ValueError("LM Studio settings have an unsupported format; they were left unchanged")
    updated = dict(existing)
    updated["mcpServers"] = {**existing.get("mcpServers", {}), **additions["mcpServers"]}
    backup = None
    if original is not None:
        backup = target.with_name(target.name + ".workshop-" + uuid.uuid4().hex[:10] + ".backup")
        backup.write_bytes(original)
        backup.chmod(0o600)
    atomic_text(target, json.dumps(updated, indent=2) + "\n")
    target.chmod(0o600)
    return backup


def bionic_environment(environment: dict) -> dict:
    """Bionic owns the working directory; no installed output folder is inherited."""
    return {**{k: v for k, v in environment.items() if k != "WORKSHOP_WORKSPACE"},
            "WORKSHOP_WORKSPACE_MODE": "bionic", "WORKSHOP_STRICT_WRITES": "1"}


def bionic_configuration(additions: dict) -> dict:
    """Bionic stores native MCP connections separately from LM Studio's mcp.json."""
    return {"servers": [
        {"id": str(uuid.uuid5(uuid.NAMESPACE_URL, "workshop/mcp/" + name)),
         "name": name, "enabled": True, "connection": {"type": "stdio", **entry,
          "env": bionic_environment(entry.get("env", {}))}}
        for name, entry in additions["mcpServers"].items()
    ]}


def merge_bionic_config(target: Path, additions: dict, *, validate_only=False) -> Path | None:
    """Preserve other connections and existing IDs; reject ambiguous or unknown formats."""
    if target.is_symlink():
        raise ValueError("Bionic settings are a symbolic link; they were left unchanged")
    original = target.read_bytes() if target.exists() else None
    existing = json.loads(original) if original is not None else {"servers": []}
    if not isinstance(existing, dict) or not isinstance(existing.get("servers"), list):
        raise ValueError("Bionic settings have an unsupported format; they were left unchanged")
    servers = existing["servers"]
    if any(not isinstance(item, dict) or not isinstance(item.get("name"), str) or not isinstance(item.get("id"), str) for item in servers):
        raise ValueError("Bionic contains invalid server entries; settings were left unchanged")
    new = {item["name"]: item for item in additions["servers"]}
    names = [item["name"] for item in servers if item["name"] in new]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate Workshop connections in Bionic; settings were left unchanged")
    updated = []
    for item in servers:
        if item["name"] in new:
            entry = new.pop(item["name"])
            updated.append({**item, **entry, "id": item["id"], "enabled": item.get("enabled", True)})
        else:
            updated.append(item)
    updated.extend(new.values())
    if validate_only:
        return None
    backup = None
    if original is not None:
        backup = target.with_name(target.name + ".workshop-" + uuid.uuid4().hex[:10] + ".backup")
        backup.write_bytes(original)
        backup.chmod(0o600)
    atomic_text(target, json.dumps({**existing, "servers": updated}, indent=2) + "\n")
    target.chmod(0o600)
    return backup


def download(url: str, target: Path, *, limit: int = 150_000_000):
    if not url.startswith("https://nodejs.org/dist/"):
        raise ValueError("Node downloads must use the official HTTPS distribution site")
    with urllib.request.urlopen(url, timeout=90) as response, target.open("wb") as stream:
        if not response.geturl().startswith("https://nodejs.org/dist/"):
            raise ValueError("Unexpected download redirect")
        size = 0
        while block := response.read(1024 * 1024):
            size += len(block)
            if size > limit:
                raise ValueError("Download exceeds expected size")
            stream.write(block)


def install_node(runtime: Path) -> Path:
    """Get prebuilt Node LTS from its official site and check SHA-256 before extraction."""
    node_root = runtime / "node"
    executable = node_root / "bin" / "node"
    if executable.is_file():
        subprocess.run([str(executable), "--version"], check=True, capture_output=True)
        return node_root / "bin"
    arch = {"arm64": "arm64", "x86_64": "x64"}.get(platform.machine())
    if not arch:
        raise ValueError("This installer supports arm64 and x86_64 machines")
    system = platform.system()
    if system not in {"Darwin", "Linux"}:
        raise ValueError("This shell installer supports macOS and Linux")
    target = ("darwin-" if system == "Darwin" else "linux-") + arch
    catalogue_target = f"osx-{arch}-tar" if system == "Darwin" else f"linux-{arch}"
    runtime.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="node-", dir=runtime) as temporary:
        temp = Path(temporary)
        index = temp / "index.json"
        download("https://nodejs.org/dist/index.json", index, limit=5_000_000)
        entries = json.loads(index.read_text())
        release = next(entry for entry in entries if entry.get("lts") and catalogue_target in entry.get("files", []))
        version = release["version"]
        if not re.fullmatch(r"v\d+\.\d+\.\d+", version):
            raise ValueError("Invalid Node version in download catalogue")
        name = f"node-{version}-{target}"
        archive = temp / (name + ".tar.gz")
        sums = temp / "SHASUMS256.txt"
        base = f"https://nodejs.org/dist/{version}/"
        download(base + archive.name, archive)
        download(base + sums.name, sums, limit=100000)
        records = [line.split() for line in sums.read_text().splitlines()]
        expected = next(record[0] for record in records if len(record) == 2 and record[1].lstrip('*') == archive.name)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
            raise ValueError("Node download checksum did not match; nothing was installed")
        with tarfile.open(archive) as packaged:
            for member in packaged.getmembers():
                if not member.name.startswith(name + "/") and member.name != name:
                    raise ValueError("Unexpected file in Node archive")
            packaged.extractall(temp, filter="data")
        shutil.move(str(temp / name), str(node_root))
    return node_root / "bin"


def make_bionic_hub(root: Path, environment: dict[str, str]):
    """One native Bionic skill routes to all eight workflows with concrete runtime paths."""
    references = root / "Bionic" / "references"
    references.mkdir(parents=True, exist_ok=True)
    names = []
    for skill in sorted((root / "skills").glob("*/SKILL.md")):
        names.append(skill.parent.name)
        shutil.copyfile(skill, references / (skill.parent.name + ".md"))
    project_environment = bionic_environment(environment)
    setup = json.dumps({"python": str(root / (".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python")), "plugin": str(root), "environment": project_environment}, indent=2)
    text = '''---
name: workshop
description: Browse and research the web, create Word/Excel/PowerPoint and Pages/Numbers/Keynote files, run Python or JavaScript/Next.js, and design printable objects with OpenSCAD/Fusion and Bambu Lab/Prusa guidance.
---

# Workshop

Use the connected workshop-* MCP tools first. Call get_workflow on the relevant connection to load the full workflow and capabilities to check the actual runtime. These tools do not require terminal commands or enabling coding in a Bionic project. If the connections are unavailable, use the terminal fallback below; terminal access requires a project with Allow coding enabled. Never claim a connection works without a successful tool response.

For CAD, follow the designer process: save design intent with plan_cad_design, build parts with the linked plan, inspect actual results, record requirement evidence with review_cad_design, and revise failures. The user does not need to run setup commands.

'''
    text += '\n'.join(f'- [{name}](references/{name}.md)' for name in names)
    text += '\n\n## Installed tools\n\nThe installer configured these exact paths. Use them without asking the user to find Python, edit settings, or install packages.\n\n```json\n' + setup + '\n```\n'
    text += '''\nUse the configured Python with `-m workshop.cli TOOL_NAME JSON_ARGUMENTS`, from the current Bionic project working directory (never cd to the plugin or Documents/Workshop folder), and pass the environment shown above to the terminal process. Call capabilities first and confirm workspace matches the current project. Native MCP uses the host-provided project root and fails closed if it is missing; use the CLI from the project terminal when roots are unavailable. For edits use read_file_snapshot then edit_file with its sha256. If search is stale or not unique, read again or supply complete edited content without search; never loosen matching silently. For multiple browser steps, keep `workshop.server --transport streamable-http` running in a Bionic-managed terminal with that environment and send CLI calls with `--url http://127.0.0.1:8765/mcp`; close the browser and stop that server when done. Do not run the server in a terminal call that waits forever for completion. Use the host's managed/background session support.

Code subprocess writes are restricted to the current project on macOS; unsupported platforms fail closed. Native Fusion Python executes outside this sandbox and is disabled in strict Bionic mode; structured native recipes remain available. Follow the user's task scope, preserve original files and obtain authorization before consequential external actions. Native iWork requires the installed macOS apps. Real F3D export must run through the included Fusion script. Report missing applications or failed operations plainly.
'''
    atomic_text(root / "Bionic/SKILL.md", text)


async def verify_integrations(python: Path, environment: dict[str, str]):
    """Check every server over the actual transport before touching host settings."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from workshop.integrations import INTEGRATIONS
    for name in INTEGRATIONS:
        parameters = StdioServerParameters(command=str(python), args=["-m", "workshop.server", "--integration", name], env={**os.environ, **environment})
        async with asyncio.timeout(30):
            async with stdio_client(parameters) as (reader, writer):
                async with ClientSession(reader, writer) as session:
                    await session.initialize()
                    found = await session.list_tools()
                    expected = {"get_workflow", "capabilities", *INTEGRATIONS[name]}
                    if {tool.name for tool in found.tools} != expected:
                        raise RuntimeError(f"Integration did not start correctly: {name}")
                    call = await session.call_tool("capabilities", {})
                    if call.isError:
                        raise RuntimeError(f"Integration check failed: {name}")


def run_logged(command: list[str], *, env: dict, log: Path, cwd: Path | None = None):
    """Keep dependency/protocol diagnostics in the setup log while showing plain progress."""
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a") as stream:
        subprocess.run(command, env=env, cwd=cwd, stdout=stream, stderr=stream, check=True)


def previous_installation(base: Path) -> dict:
    """Validate stored installation paths before an update, without changing them."""
    state = base / "installed.json"
    if state.is_symlink():
        raise ValueError("Installation metadata must not be a symbolic link")
    data = json.loads(state.read_text())
    if not isinstance(data, dict):
        raise ValueError("Invalid installation metadata")
    for key in ("release", "workspace", "config"):
        if not isinstance(data.get(key), str) or not Path(data[key]).is_absolute():
            raise ValueError("Invalid installation path: " + key)
    release = Path(data["release"])
    if release.is_symlink() or release.resolve().parent != (base / "releases").resolve():
        raise ValueError("Previous release is outside the managed releases folder")
    return data


def publish_shared_files(root: Path, base: Path, environment: dict[str, str]):
    """Publish skills and Fusion scripts at stable paths that survive release cleanup."""
    for name, source in (("Bionic", root / "Bionic"), ("fusion", root / "fusion")):
        target = base / name
        if target.is_symlink() or any(parent.is_symlink() for parent in target.parents if parent != base.parent):
            raise ValueError("Shared installation path must not contain symbolic links")
        target.mkdir(parents=True, exist_ok=True)
        for file in source.rglob("*"):
            if file.is_file() and file.suffix != ".pyc" and "__pycache__" not in file.parts:
                destination = target / file.relative_to(source)
                if destination.is_symlink():
                    raise ValueError("Shared installation file is a symbolic link")
                atomic_text(destination, file.read_text())

    bridge_directory = environment.get("WORKSHOP_FUSION_BRIDGE", str(Path.home() / ".workshop/fusion-bridge"))
    atomic_text(base / "fusion/WorkshopBridge/bridge-config.json", json.dumps({"directory": bridge_directory}))


def clean_old_releases(base: Path, current: Path, workspace: Path, protected: tuple[Path, ...] = ()) -> list[str]:
    """Remove identifiable managed releases, never symlinks, output folders or unrelated files."""
    releases = base / "releases"
    if releases.is_symlink() or current.resolve().parent != releases.resolve():
        raise ValueError("Invalid managed releases directory")
    removed = []
    for candidate in releases.iterdir():
        if candidate.is_symlink() or not candidate.is_dir() or candidate.resolve() == current.resolve():
            continue
        # A user may have selected an output folder inside a release; retain that release.
        if any(path.resolve().is_relative_to(candidate.resolve()) for path in (workspace, *protected)):
            continue
        manifest = candidate / "plugin.json"
        if manifest.is_symlink():
            continue
        try:
            data = json.loads(manifest.read_text())
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict) or data.get("name") != "workshop":
            continue
        shutil.rmtree(candidate)
        removed.append(candidate.name)
    return removed


def install(options):
    root = options.release.resolve()
    runtime = options.runtime.resolve()
    updating = getattr(options, "update", False)
    previous = previous_installation(runtime.parent) if updating else None
    # Updates retain the existing destinations unless explicit environment overrides were provided.
    workspace = (Path(previous["workspace"]) if previous and "WORKSHOP_WORKSPACE" not in os.environ else options.workspace).resolve()
    config_target = Path(previous["config"]) if previous and "WORKSHOP_LMSTUDIO_CONFIG" not in os.environ else options.config
    workspace.mkdir(parents=True, exist_ok=True)
    uv = runtime / "bin/uv"
    log = options.log or runtime.parent / "setup.log"
    private_environment = {**os.environ, "UV_CACHE_DIR": str(runtime / "cache"), "UV_PYTHON_INSTALL_DIR": str(runtime / "python")}
    progress("Getting your tools ready", "This may take a few minutes the first time. Keep this window open.")
    run_logged([str(uv), "venv", "--python", "3.12", "--managed-python", str(root / ".venv")], env=private_environment, log=log)
    python = root / ".venv/bin/python"
    run_logged([str(uv), "pip", "install", "--python", str(python), "--only-binary", ":all:", "-r", str(root / "requirements-tested.txt"), "-e", str(root)], env=private_environment, log=log)
    node_bin = install_node(runtime)
    environment = {"WORKSHOP_WORKSPACE": str(workspace), "WORKSHOP_ALLOW_CODE": "1", "PYTHONPATH": str(root), "PLAYWRIGHT_BROWSERS_PATH": str(runtime / "browsers"), "PATH": str(node_bin) + os.pathsep + "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"}
    run_logged([str(python), "-m", "playwright", "install", "chromium"], env={**os.environ, **environment}, log=log)
    progress("Checking your integrations", "Checking that all eight tools can connect before changing LM Studio settings.")
    # Run the verification using the newly installed interpreter, not the bootstrap interpreter.
    checker = "import asyncio,json,sys; from pathlib import Path; from installer.install import verify_integrations; asyncio.run(verify_integrations(Path(sys.argv[1]),json.loads(sys.argv[2])))"
    run_logged([str(python), "-c", checker, str(python), json.dumps(environment)], cwd=root, env={**os.environ, **environment}, log=log)
    generator = "import json,sys; from workshop.integrations import mcp_configuration; print(json.dumps(mcp_configuration(sys.argv[1],json.loads(sys.argv[2]))))"
    generated = subprocess.run([str(python), "-c", generator, str(python), json.dumps(environment)], cwd=root, env={**os.environ, **environment}, capture_output=True, text=True, check=True)
    config = json.loads(generated.stdout)
    atomic_text(root / "config/lmstudio.mcp.json", json.dumps(config, indent=2))
    bionic_config = bionic_configuration(config)
    atomic_text(root / "config/bionic.mcp.json", json.dumps(bionic_config, indent=2))
    atomic_text(root / "config/bionic.env.json", json.dumps(bionic_environment(environment), indent=2))
    make_bionic_hub(root, environment)
    bionic_target = options.bionic_config
    if bionic_target.parent.parent.is_dir():
        merge_bionic_config(bionic_target, bionic_config, validate_only=True)
    progress("Connecting LM Studio", "Adding your integrations and saving a backup of your existing settings.")
    publish_shared_files(root, runtime.parent, environment)
    backup = merge_config(config_target, config)
    bionic_backup = None
    if bionic_target.parent.parent.is_dir():
        progress("Connecting Bionic", "Registering native tools in Bionic's separate settings and preserving existing connections.")
        bionic_backup = merge_bionic_config(bionic_target, bionic_config)
    else:
        progress("Bionic not installed", "Generated config/bionic.mcp.json for later setup. LM Studio settings are independent.")
    atomic_text(options.runtime.parent / "installed.json", json.dumps({"release": str(root), "workspace": str(workspace), "config": str(config_target.resolve()), "backup": str(backup) if backup else None, "bionic_config": str(bionic_target), "bionic_backup": str(bionic_backup) if bionic_backup else None}, indent=2))
    if updating:
        try:
            removed = clean_old_releases(runtime.parent, root, workspace, (config_target, *((backup,) if backup else ())))
            progress("Old releases cleaned", f"Removed {len(removed)} old managed release(s). Runtime downloads and generated files were kept.")
        except (OSError, ValueError) as error:
            progress("Cleanup incomplete", f"The update succeeded, but some old files could not be removed: {error}")
    progress("Installation complete", "Restart LM Studio and Bionic to load the connections. In Bionic's Connected Apps/MCP settings, check the workshop-* entries. Each connection supplies its workflow directly; the skill below is optional guidance.")
    print(str(runtime.parent / "Bionic/SKILL.md"))
    print("Fusion script folder: " + str(runtime.parent / "fusion/WorkshopDesign"))
    print("Fusion automatic add-in folder: " + str(runtime.parent / "fusion/WorkshopBridge"))
    if updating:
        print("If Bionic or Fusion references an old release folder, replace it once with the stable paths above. Future updates keep these paths.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--bionic-config", type=Path, default=Path(os.environ.get("WORKSHOP_BIONIC_CONFIG", str(Path.home() / ".lmstudio/apps/bionic/.internal/ng-mcp.json"))))
    parser.add_argument("--log", type=Path)
    parser.add_argument("--update", action="store_true")
    options = parser.parse_args()
    try:
        install(options)
    except Exception:
        progress("Installation failed", "Your previous installation remains available. See the error above for details. Unsupported LM Studio settings are left unchanged.")
        raise


if __name__ == "__main__":
    main()
