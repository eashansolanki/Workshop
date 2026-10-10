"""MCP entrypoint. All tools are also callable through the Bionic terminal CLI."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
from mcp.server.fastmcp import FastMCP
from . import core, documents, cad, web

mcp = FastMCP("Workshop", instructions="Local research, documents, coding and CAD. Read get_skill before domain tasks. Tools return real outputs or explicit missing dependencies. Code execution is opt-in and not sandboxed.", host="127.0.0.1", port=8765)
SOURCE_ROOT = Path(__file__).resolve().parent.parent
PACKAGE = SOURCE_ROOT if (SOURCE_ROOT / "plugin.json").is_file() else Path(__file__).resolve().parent / "resources"


@mcp.tool()
def capabilities() -> dict:
    """Report installed executables and capability dependencies without changing the machine."""
    return {"workspace": str(core.ROOT), "code_enabled": os.environ.get("WORKSHOP_ALLOW_CODE") == "1",
            "python": sys.version, "node": shutil.which("node"), "npm": shutil.which("npm"),
            "openscad": shutil.which("openscad") or ("/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD" if Path("/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD").exists() else None),
            "libreoffice": shutil.which("soffice") or ("/Applications/LibreOffice.app/Contents/MacOS/soffice" if Path("/Applications/LibreOffice.app/Contents/MacOS/soffice").exists() else None),
            "iwork_installed": {name: Path(f"/Applications/{name}.app").exists() for name in ("Pages", "Numbers", "Keynote")},
            "fusion": "requires Autodesk Fusion and the included script; no headless F3D writer",
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
