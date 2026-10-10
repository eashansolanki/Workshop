# Workshop feature list

Workshop exposes eight domain integrations in LM Studio and the same workflows as Bionic skills. This list describes the current code, including application dependencies and verification limits. It does not describe all features of the third-party applications.

## Installation and integrations

- Self-contained `install.sh` for macOS/Linux, arm64/x86_64; private managed Python, Node and Chromium setup.
- Self-contained `installupdate.sh` for existing installations; installs the release bundled in the downloaded script.
- Eight real MCP integrations, each exposing its domain tools, `capabilities` and `get_workflow`.
- Actual MCP startup checks before changing LM Studio configuration.
- Unrelated settings preserved and original configuration backed up.
- Update retains recorded workspace/configuration paths unless explicitly overridden.
- Old managed releases cleaned after successful update; output folders, protected config paths, symlinks and unrelated folders retained.
- Stable installed Bionic skill hub with eight workflow references and configured runtime paths.
- Stable Fusion script folder across updates.
- Optional manual bootstrap and combined MCP configuration; optional local HTTP transport and CLI forwarding.
- `--check` for embedded-package verification, `--yes` for unattended confirmation and setup logs for diagnosis.

## Web research

| Tool | Feature |
| --- | --- |
| `fetch_webpage` | Public HTML/text extraction and links with bounded response size |
| `search_web` | Brave search with `BRAVE_SEARCH_API_KEY`, otherwise DuckDuckGo through Chromium |
| `browse_web` | Isolated browser open/read/click/fill/screenshot/close |

Browser sessions can persist across MCP calls. Bionic's separate CLI processes need the documented background local HTTP server for multi-step sessions. Personal browser profiles and file downloads are not exposed. Local/private URLs are blocked by the tool guards; use the host browser for local Next.js pages. Brave API search remains unverified without a key.

## Word documents

- `create_word`: genuine DOCX titles, headings, paragraphs, bullets and rectangular tables.
- `inspect_document`: bounded DOCX text and table extraction.
- `convert_office`: genuine legacy DOC or PDF through installed LibreOffice.
- Existing-file edits and advanced layout via `run_python` and python-docx, saving a new copy.
- Workflow includes content checks and rendering/visual review when an appropriate viewer is available.

## Excel spreadsheets

- `create_excel`: multiple named XLSX sheets, rows and explicitly supplied cell formulas.
- Header formatting, frozen header row and bounded column widths.
- Ordinary strings beginning with `=` remain literal unless supplied through the formulas mapping.
- `inspect_document`: bounded workbook rows and formula text.
- Further edits via `run_python` and openpyxl.
- Formula recalculation requested when opened; no calculated caches are supplied. Recalculate in a spreadsheet application before relying on displayed results.

## PowerPoint presentations

- `create_powerpoint`: editable widescreen PPTX with a title slide, content slides, bullet text and optional speaker notes.
- `inspect_document`: bounded slide-text extraction.
- Further editing through `run_python` and python-pptx.
- PDF conversion through LibreOffice; visual inspection remains an application/viewer step.

These Office tools create basic editable layouts. Advanced charts, complex templates and publication-ready visual design require additional authoring and review; they are not automatic dedicated features.

## Apple iWork

- `convert_iwork`: DOCX to Pages, XLSX to Numbers and PPTX to Keynote through the installed macOS apps.
- Export native iWork files back to the corresponding Office format or PDF.
- macOS Automation permission may be required.
- Pages and Keynote creation passed live checks. Numbers conversion remains unverified after a timeout. Feature-perfect round-tripping is not guaranteed.

## 3D-printing design and printer guidance

- Workflow for dimensions, wall thickness, fit, orientation, supports, material and printer selection.
- `printer_reference`: dated Bambu Lab and Prusa references with official product/help/slicer links.
- Selected Bambu reference models: A1 mini, A1, P1S and X1 Carbon.
- Prusa MK4S facts plus references for the XL, CORE One family and MINI+.
- Exact model/nozzle/material/profile verification and calibration guidance.
- Source generation and mesh export through OpenSCAD; Fusion jobs through the bridge below.

The references are a selected catalogue, not automatically refreshed specifications. This package has no printer connection, slicer control, G-code generation or print-start tool.

## OpenSCAD

| Tool | Feature |
| --- | --- |
| `create_openscad` | Write custom `.scad` source |
| `create_cad_recipe` | Generate millimetre SCAD from boxes/cylinders and new/join/cut operations |
| `render_openscad` | Compile SCAD into STL, 3MF or PNG through installed OpenSCAD |

Recipe-generated SCAD uses `$fn=96`. Custom SCAD can use the broader OpenSCAD language. Rendering validates that a nonempty output was produced; source creation alone does not compile it. STL, 3MF and PNG exports passed live checks.

## Autodesk Fusion / Fusion 360

- `prepare_fusion_design`: validate and save a complete job JSON with absolute output path and pending status.
- Included WorkshopDesign engine runs inside Autodesk Fusion, manually or through the startup WorkshopBridge add-in.
- `prepare_fusion_script`: native modelling source for advanced shapes, using trusted `build(design, root)` Python.
- `prepare_fusion_import`: native STEP/IGES/SAT/F3D imports of existing CAD.
- `run_fusion_design` / `fusion_design_status`: automatic queue, structured errors and verified local archive links.
- `create_cad_project`: new folder with separate source/job/output files per part, respecting Fusion/OpenSCAD selection.
- `run_fusion_project` / `fusion_project_status`: batch execution and per-part completion/links.
- `open_fusion_design`: reopen a saved local F3D through the add-in.
- 1–100 box/cylinder primitives, millimetre units and finite 3D origins.
- New bodies, intersecting joins and subtractive cuts.
- New parametric document with named sketch/extrusion history and Z-offset construction planes.
- Genuine `.f3d` export through Fusion's API, with output-existence/size checks.
- Success message and companion `.result.json` with path/status/size.
- New filenames required; existing outputs are not overwritten.

No headless F3D writer or in-place existing-model edit tool is implemented. Primitive recipes do not express fillets/threads/lofts/sweeps/assemblies; native scripts can use those Fusion APIs and named parameters. Multi-part files do not automatically create a constrained assembly. Native scripts require trusted code enabled. Live F3D export remains unverified. See the [complete Fusion guide](FUSION360.md).

## Python, JavaScript and Next.js

- `run_python`: trusted local Python execution with the installed document libraries.
- `run_javascript`: trusted JavaScript ES modules through Node.
- `run_nextjs`: npm install/build/test/lint in a workspace Next.js project.
- Subprocess timeouts and bounded returned stdout/stderr.
- Code execution controlled by `WORKSHOP_ALLOW_CODE=1`; enabled by the shell installer.

Code runs with normal user privileges. PyTorch/MLX and arbitrary third-party Python packages are not bundled. The Next.js tool does not create a production application automatically or deploy it. Its routing was tested against a synthetic Next.js-declaring project.

## Shared file and workflow tools

- `read_file`: bounded UTF-8 workspace text reads.
- `write_file`: new UTF-8 files inside the configured workspace.
- Workspace containment checks, including symlink escape prevention, for structured file operations.
- `capabilities`: current workspace, code setting, runtime and application dependency reporting.
- `get_workflow`: the selected domain's full skill instructions.
- In optional combined mode, `list_skills` and `get_skill` expose all workflows.

Local code and desktop applications have ordinary system permissions; structured path checks are not an operating-system sandbox. Numbers conversion and live Fusion archive export remain unverified.
