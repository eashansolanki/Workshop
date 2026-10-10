"""MCP entrypoint. All tools are also callable through the Bionic terminal CLI."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
from mcp.server.fastmcp import Image
from .scope import ProjectMCP
from . import core, documents, cad, web, fusion_bridge, design, files

mcp = ProjectMCP("Workshop", instructions="Local research, documents, coding and CAD. Read get_skill before domain tasks. Follow the requested CAD backend: Fusion uses native geometry/scripts, OpenSCAD only when selected. Never substitute meshes or switch CAD tools after an error. For modelling follow the designer workflow: understand the brief, plan_cad_design, linked create_cad_project, execute and inspect real previews/measurements, then review_cad_design and revise failures. Tools return real outputs or explicit missing dependencies. Code execution is opt-in and not sandboxed.", host="127.0.0.1", port=8765)
SOURCE_ROOT = Path(__file__).resolve().parent.parent
PACKAGE = SOURCE_ROOT if (SOURCE_ROOT / "plugin.json").is_file() else Path(__file__).resolve().parent / "resources"


@mcp.tool()
def capabilities() -> dict:
    """Report installed executables and capability dependencies without changing the machine."""
    return {**core.workspace_status(), "strict_project_writes": core.strict_writes(), "code_enabled": os.environ.get("WORKSHOP_ALLOW_CODE") == "1",
            "python": sys.version, "node": shutil.which("node"), "npm": shutil.which("npm"),
            "openscad": shutil.which("openscad") or ("/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD" if Path("/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD").exists() else None),
            "libreoffice": shutil.which("soffice") or ("/Applications/LibreOffice.app/Contents/MacOS/soffice" if Path("/Applications/LibreOffice.app/Contents/MacOS/soffice").exists() else None),
            "iwork_installed": {name: Path(f"/Applications/{name}.app").exists() for name in ("Pages", "Numbers", "Keynote")},
            "fusion": fusion_bridge.fusion_status(),
            "browser": "requires python -m playwright install chromium"}


@mcp.tool()
def list_skills() -> list[str]:
    """List available domain workflows; load the relevant one with get_skill."""
    return sorted(file.parent.name for file in (PACKAGE / "skills").glob("*/SKILL.md"))


@mcp.tool()
def get_skill(name: str) -> str:
    """Read a packaged skill by its exact name."""
    if name not in list_skills():
        raise ValueError("Unknown skill")
    return (PACKAGE / "skills" / name / "SKILL.md").read_text()


@mcp.tool()
def read_file(relative: str) -> str:
    """Read UTF-8 text from the configured workspace, up to 100 KB."""
    file = core.path(relative)
    if file.stat().st_size > 100000:
        raise ValueError("Text file is larger than 100 KB")
    return file.read_text(encoding="utf-8")


@mcp.tool()
def write_file(relative: str, content: str) -> dict:
    """Create a new UTF-8 workspace file; existing files are never overwritten."""
    target = core.path(relative, new=True)
    target.write_text(content, encoding="utf-8")
    return {"path": str(target)}


@mcp.tool()
def read_file_snapshot(relative: str) -> dict:
    """Read current UTF-8 content and sha256 before editing a project file."""
    return files.snapshot(relative)


@mcp.tool()
def edit_file(relative: str, expected_sha256: str, replacement: str, search: str | None = None) -> dict:
    """Edit only inside the project. Requires sha256 from read_file_snapshot. Omit search to supply complete edited content; otherwise search must match exactly once. Stale/ambiguous edits leave the file unchanged."""
    return files.edit(relative, expected_sha256, replacement, search)


@mcp.tool()
def run_python(source: str, timeout: int = 60) -> dict:
    """Run trusted Python with local user privileges; needs WORKSHOP_ALLOW_CODE=1."""
    return core.execute("python", source, timeout)


@mcp.tool()
def run_javascript(source: str, timeout: int = 60) -> dict:
    """Run trusted JavaScript/ES modules through Node.js; needs WORKSHOP_ALLOW_CODE=1."""
    return core.execute("javascript", source, timeout)


@mcp.tool()
def run_nextjs(project: str, action: str) -> dict:
    """Run npm install/build/test/lint in a workspace Next.js project; opt-in code execution required. No deployment tool."""
    if os.environ.get("WORKSHOP_ALLOW_CODE") != "1":
        raise PermissionError("Enable trusted execution with WORKSHOP_ALLOW_CODE=1")
    if action not in {"install", "build", "test", "lint"}:
        raise ValueError("Supported actions: install/build/test/lint")
    folder = core.path(project)
    manifest = json.loads((folder / "package.json").read_text())
    if "next" not in {**manifest.get("dependencies", {}), **manifest.get("devDependencies", {})}:
        raise ValueError("Project must declare Next.js")
    npm = shutil.which("npm")
    if not npm:
        raise RuntimeError("Install Node.js/npm")
    args = [npm, "--prefix", str(folder)] + (["install"] if action == "install" else ["run", action])
    return core.process(args, 300)


@mcp.tool()
async def fetch_webpage(url: str) -> dict:
    """Read a public HTML/text page and links with bounded response size."""
    return await web.fetch(url)


@mcp.tool()
async def search_web(query: str) -> dict:
    """Search Brave with BRAVE_SEARCH_API_KEY, otherwise use DuckDuckGo in isolated Chromium."""
    return await web.search(query)


@mcp.tool()
async def browse_web(action: str, url: str = "", selector: str = "", value: str = "", output: str = "") -> dict:
    """Public-web browser: open/read/click/fill/screenshot/close. Clicks may submit forms; require user authorization for external actions."""
    return await web.browser.action(action, url, selector, value, output)


@mcp.tool()
def create_word(output: str, title: str, blocks: list[dict]) -> dict:
    """Create DOCX. Blocks: paragraph/heading/bullet with text, or table with rows. Use convert_office for legacy DOC."""
    return documents.create_document(output, title, blocks)


@mcp.tool()
def create_excel(output: str, sheets: list[dict]) -> dict:
    """Create XLSX. Sheets contain name, rows, optional formulas mapping cell addresses to formulas. Formula results need recalculation in Excel."""
    return documents.create_workbook(output, sheets)


@mcp.tool()
def create_powerpoint(output: str, title: str, slides: list[dict]) -> dict:
    """Create editable PPTX. Slides contain title, bullets, optional notes."""
    return documents.create_slides(output, title, slides)


@mcp.tool()
def inspect_document(source: str) -> dict:
    """Read bounded DOCX/XLSX/PPTX text, tables, rows or slides to verify/edit artifacts."""
    return documents.inspect_office(source)


@mcp.tool()
def convert_iwork(source: str, output: str) -> dict:
    """Use installed macOS Pages/Numbers/Keynote to import Office and save native files, or export native files to Office/PDF. macOS may request Automation permission."""
    return documents.apple_convert(source, output)


@mcp.tool()
def convert_office(source: str, output: str) -> dict:
    """Convert Word to legacy DOC or Office to PDF using installed LibreOffice."""
    return documents.libreoffice_convert(source, output)


@mcp.tool()
def create_openscad(output: str, source: str) -> dict:
    """Write custom parametric .scad source; render_openscad compiles it separately."""
    return cad.write_scad(output, source)


@mcp.tool()
def create_cad_recipe(output: str, recipe: dict) -> dict:
    """Generate .scad from mm primitives. parts contain kind box/cylinder, height, origin, operation new/join/cut; boxes width/depth, cylinders diameter."""
    return cad.recipe_to_scad(output, recipe)


@mcp.tool()
def render_openscad(source: str, output: str) -> dict:
    """Compile SCAD into STL/3MF/PNG with installed OpenSCAD. Rendering arbitrary SCAD can read included local files."""
    return cad.render_scad(source, output)


@mcp.tool()
def prepare_fusion_design(recipe_file: str, output: str, recipe: dict) -> dict:
    """Prepare mm box/cylinder primitives for Fusion's included WorkshopDesign script. Genuine .f3d is produced only after running that script in Fusion."""
    return cad.prepare_fusion(recipe_file, output, recipe)


@mcp.tool()
def prepare_fusion_import(recipe_file: str, source: str, output: str) -> dict:
    """Prepare STEP/IGES/SAT/F3D import into a new document and genuine F3D export."""
    return cad.prepare_fusion_import(recipe_file, source, output)


@mcp.tool()
def run_fusion_design(recipe_file: str, launch: bool = True) -> dict:
    """Queue a prepared Fusion job and optionally open Fusion. Requires WorkshopBridge registered/running; check fusion_design_status for success."""
    return fusion_bridge.run_design(recipe_file, launch)


@mcp.tool()
def fusion_design_status(recipe_file: str) -> dict:
    """Read structured Fusion errors or verified export with a clickable saved-design link."""
    return fusion_bridge.design_status(recipe_file)


@mcp.tool()
def open_fusion_design(source: str) -> dict:
    """Queue opening an existing workspace F3D in Fusion via WorkshopBridge."""
    return fusion_bridge.open_design(source)


@mcp.tool()
def prepare_fusion_script(recipe_file: str, script_file: str, output: str, source: str) -> dict:
    """Save native Fusion Python defining build(design, root). Supports arbitrary native modelling APIs, requires trusted code enabled. Queue with run_fusion_design; no mesh conversion."""
    return cad.prepare_fusion_script(recipe_file, script_file, output, source)


@mcp.tool()
def create_cad_project(folder: str, backend: str, parts: list[dict], notes: str = "", design_plan_file: str = "") -> dict:
    """Create a new folder and separate files for each named part. backend MUST match user's fusion/openscad choice. parts: name + recipe or source (Fusion build(design,root) Python / OpenSCAD source). Attach design_plan_file from plan_cad_design to preserve requirements and measured checks."""
    return cad.create_cad_project(folder, backend, parts, notes, design_plan_file)


@mcp.tool()
def run_fusion_project(project_file: str, launch: bool = True) -> dict:
    """Queue every prepared Fusion part in a project manifest, opening Fusion once."""
    return fusion_bridge.run_project(project_file, launch)


@mcp.tool()
def fusion_project_status(project_file: str) -> dict:
    """Report every part's status/error and verified saved-design links; exported only when all parts export."""
    return fusion_bridge.project_status(project_file)


@mcp.tool()
def plan_cad_design(output: str, plan: dict) -> dict:
    """Before modelling: save purpose/context/manufacturing, measurable requirements, justified concept selection, parameter bases, parts/feature dependencies, interfaces and assumptions. Complex plans need multiple concepts. Use the chosen CAD backend."""
    return design.plan_design(output, plan)


@mcp.tool()
def review_cad_design(plan_file: str, project_file: str, output: str, findings: list[dict]) -> dict:
    """After modelling: review every requirement using saved evidence; absent checks remain not_checked. findings: requirement, status pass/fail/not_checked, evidence, artifacts [workspace paths]. Fusion measurements override claims. Returns revision/verification needs."""
    return design.review_design(plan_file, project_file, output, findings)


@mcp.tool()
def inspect_cad_preview(source: str) -> Image:
    """View a real saved Fusion/OpenSCAD PNG or JPEG for visual design critique. Requires a vision-capable model. A preview does not prove dimensions or hidden geometry."""
    file = core.path(source)
    if file.suffix.lower() not in {".png", ".jpg", ".jpeg"} or not file.is_file() or not 0 < file.stat().st_size <= 10 * 1024 * 1024:
        raise ValueError("Choose a nonempty workspace PNG/JPEG up to 10 MiB")
    with file.open("rb") as stream:
        header = stream.read(8)
    if not (header == b"\x89PNG\r\n\x1a\n" or header.startswith(b"\xff\xd8\xff")):
        raise ValueError("Preview does not have a PNG/JPEG image signature")
    return Image(path=str(file))


@mcp.tool()
def printer_reference(brand: str) -> dict:
    """Return source-backed Bambu Lab/Prusa reference facts, dates, model-specific official documentation and design guidance."""
    data = json.loads((PACKAGE / "config" / "printers.json").read_text())
    key = brand.lower().strip()
    if key not in data:
        raise ValueError("Use bambu or prusa")
    return data[key]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    from .integrations import INTEGRATIONS, create_integration
    parser.add_argument("--integration", choices=sorted(INTEGRATIONS), help="Expose one skill as a separate LM Studio integration")
    parser.add_argument("--port", type=int, default=8765, help="Loopback HTTP port; choose distinct ports for separate HTTP integrations")
    options = parser.parse_args()
    if not 1 <= options.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    selected = create_integration(options.integration, port=options.port) if options.integration else mcp
    if not options.integration:
        selected.settings.port = options.port
    selected.run(transport=options.transport)


if __name__ == "__main__":
    main()
