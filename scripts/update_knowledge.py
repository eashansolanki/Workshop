"""Refresh the requested project map after source changes."""
import ast
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
lines = ["Workshop 0.6.0 project knowledge - updated 2026-10-10", "",
         "Stack: Python >=3.11, FastMCP, local CLI, Autodesk Fusion adsk API, shell installers.",
         "No web deployment. Existing Python architecture is preserved.", "",
         "Changes: structured Fusion capability detection; strict recipe validation; native CAD import jobs;",
         "atomic deduplicated local queue; main-thread Fusion custom-event add-in; saved archive links;",
         "error/warning results; launcher and installer support; synchronized skills and regression tests.", "",
         "Bionic request roots are isolated with ContextVar; no Documents/Workshop fallback. CLI uses current project cwd.",
         "Version-checked atomic edit_file/read_file_snapshot: stale and ambiguous edits do not write; CRLF matching is preserved.",
         "Strict Bionic code uses macOS sandbox-exec with project-only writes; uncontained native Fusion scripts are refused.",
         "Designer flow: plan_cad_design -> linked part project -> native execution/preview -> review_cad_design -> revision.",
         "Evidence: automatic Fusion BRep envelope/count checks override self-reports; missing checks remain unverified.",
         "Native example uses named parameters, origin-anchored driven sketch dimensions and a fully constrained sketch gate.",
         "Bionic uses separate ng-mcp.json servers/connection settings; installer preserves other entries and backs up changes.",
         "Flow: MCP/CLI -> cad.prepare_fusion/import -> fusion_bridge.run_design -> local queue ->",
         "WorkshopBridge custom event -> WorkshopDesign.execute_job -> .f3d + .result.json -> status/link.",
         "Manual WorkshopDesign JSON-picker execution remains supported.",
         "Automatic execution requires one-time add-in registration. Native build(design, root) scripts are supported with trusted code enabled.",
         "Respect CAD intent: Fusion stays native Fusion; OpenSCAD only when requested. No mesh workaround for Fusion designs.",
         "create_cad_project creates a new folder and per-part source/job/output files plus project.json; batch run/status returns every part.",
         "Windows launches without waiting on or killing Fusion. macOS uses open -a.",
         "Default queue: ~/.workshop/fusion-bridge; override WORKSHOP_FUSION_BRIDGE with matching add-in config.",
         "Receipts stop replay after restart; finish active Fusion commands before queued CAD executes.",
         "docs/DESIGN-VALIDATION.md records acceptance tasks and Qwen Coder Next/GPT-OSS/Gemma 4 targets; live behaviour and image input remain untested.",
         "Tests: python3 -m unittest discover -s tests -v; compileall; all eight MCP integration checks.",
         "Release: python3 scripts/build_release.py; bash install.sh --check; bash installupdate.sh --check.",
         "Live Fusion geometry/export and the user's unspecified complex error remain unverified.", "",
         "Source inventory (line numbers refreshed automatically; includes functions, classes and loops):"]
excluded = {".git", ".venv", "dist", "build", "__pycache__"}
for file in sorted(root.rglob("*.py")):
    if any(part in excluded for part in file.relative_to(root).parts):
        continue
    relative = str(file.relative_to(root))
    tree = ast.parse(file.read_text())
    lines.append("\n" + relative)
    entries = []
    def visit(node, scope=""):
        next_scope = scope
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            name = scope + getattr(node, "name", "lambda")
            entries.append((node.lineno, f"  {node.lineno}-{node.end_lineno}: {type(node).__name__} {name}"))
            next_scope = name + "."
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.While, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            entries.append((node.lineno, f"  {node.lineno}-{node.end_lineno}: {type(node).__name__} in {scope.rstrip('.') or 'module'}"))
        for child in ast.iter_child_nodes(node):
            visit(child, next_scope)
    visit(tree)
    lines.extend(value for _, value in sorted(entries))
for relative in ("installer/install.template.sh", "install.sh", "installupdate.sh"):
    lines.append("\n" + relative)
    for number, value in enumerate((root / relative).read_text().splitlines(), 1):
        if re.match(r"\s*(for |while |until |[A-Za-z_][A-Za-z_0-9]*\s*\(\)\s*\{)", value):
            lines.append(f"  {number}: shell function/loop {value.strip()}")

lines += ["", "Other components:", "mcp.json: eight selectable MCP server entries.",
          "plugin.json and pyproject.toml: plugin identity and Python packaging/dependencies.",
          "fusion/*/*.manifest: manual script and startup add-in registration metadata.",
          "skills/*/SKILL.md + workshop/resources/skills/*/SKILL.md: source and wheel workflow copies.",
          "installer/install.template.sh: shell runtime/bootstrap/payload installer; generated install.sh/installupdate.sh embed the source bundle.",
          "docs/FUSION360.md: automatic setup, formats, local links, receipts, manual fallback and troubleshooting.",
          "README.md, DEVELOPER-SETUP.md, docs/*.md: user and developer workflow documentation.",
          "config/printers.json + workshop/resources/config/printers.json: printer reference data.",
          "examples/plate.json: raw example recipe (prepare a job before running).", ""]
(root / "knowledge.txt").write_text("\n".join(lines), encoding="utf-8")
