# Workshop for LM Studio and Bionic

Eight independently selectable LM Studio MCP integrations and eight standard Bionic Agent Skills for research, documents, iWork, Python/JavaScript, Next.js, OpenSCAD and 3D-printing design. This guide covers manual source setup. For automatic installation, follow the [README](README.md). The manual bootstrap generates configuration without changing host settings.

## Set up a source checkout

Requires Python 3.11+; Node.js/npm for JavaScript and Next.js. Extract the ZIP and keep the plugin folder in a permanent location. From that folder:

```sh
python3 bootstrap.py --workspace "/absolute/path/to/your/work" --browser --enable-code
```

On Windows use `python` and a Windows absolute workspace path. `--browser` installs isolated Chromium. `--enable-code` enables Python/JavaScript and npm tasks with your normal user permissions. Omit it if you only want structured tools. The code tools are not operating-system sandboxes. The file tools enforce workspace containment and refuse to overwrite files.

Bootstrap creates `.venv`, installs this source folder in editable mode, downloads dependencies when needed, and writes `config/lmstudio.mcp.json` with absolute paths. It does not edit existing host settings. Keep this entire folder: skills and printer references are loaded from the source checkout. `requirements-tested.txt` records the dependency versions tested during development; bootstrap installs compatible declared ranges.

## LM Studio

Open Program > Install > Edit mcp.json. Merge the eight `workshop-*` entries from generated `config/lmstudio.mcp.json` into your existing `mcpServers`. Preserve other entries. Reload the server if needed and use a model capable of tool calling.

Each skill is a separate integration: advanced-web-browsing, word-documents, excel-spreadsheets, powerpoint-presentations, apple-iwork, 3d-printing-design, openscad-and-fusion, and python-javascript-nextjs. Enable the integrations you need in LM Studio. Each one exposes its actual domain tools, a `capabilities` check, and a `get_workflow` tool that returns exactly the same SKILL.md used by Bionic. Its MCP initialization instructions also include that workflow.

Ask: “Use the Excel Spreadsheets integration, load its workflow, and create a budget in my workspace.” Skill guidance instructs the model; it is not a guarantee that every model will follow every step.

To retain the original single integration instead, run bootstrap with `--combined`. That mode continues to expose all 22 tools, including `list_skills` and `get_skill`. Do not enable both configurations together unless you want duplicate tool collections.

The root `mcp.json` is a portable package template with `${PLUGIN_ROOT}`. For LM Studio use bootstrap's generated absolute-path configuration rather than assuming host substitution support.

[Official LM Studio MCP configuration](https://lmstudio.ai/docs/app/mcp).

## Bionic by LM Studio

In Settings > Skills, add each `skills/*/SKILL.md`. The eight skills are:

- Advanced web browsing
- Word documents
- Excel spreadsheets
- PowerPoint presentations
- Apple iWork
- 3D-printing design
- OpenSCAD and Fusion
- Python, JavaScript and Next.js

The `skills/` files are preserved and remain directly installable in Bionic. Bionic explicitly documents standard Agent Skills installation. Its documented skills support does not establish that it imports this package manifest or shares LM Studio's MCP configuration. If your Bionic version exposes MCP settings, connect the generated server configuration there. Otherwise the included skills instruct Bionic to use its built-in terminal to call the same tools through the CLI:

```sh
cd "/absolute/path/to/workshop"
export WORKSHOP_WORKSPACE="/absolute/path/to/your/work"
export WORKSHOP_ALLOW_CODE=1
export PLAYWRIGHT_BROWSERS_PATH="$PWD/.browsers"
.venv/bin/python -m workshop.cli list
.venv/bin/python -m workshop.cli capabilities
.venv/bin/python -m workshop.cli create_word '{"output":"report.docx","title":"Report","blocks":[{"type":"paragraph","text":"Hello."}]}'
```

For multiple browser interactions in Bionic, keep the local server running in a Bionic-managed terminal so page state survives between CLI calls:

```sh
.venv/bin/python -m workshop.server --transport streamable-http
```

In a second terminal, use `.venv/bin/python -m workshop.cli --url http://127.0.0.1:8765/mcp browse_web '{"action":"open","url":"https://example.com"}'`, then further read/click/fill calls with the same `--url`. The HTTP adapter preserves the isolated browser across separate CLI processes. Ordinary standalone CLI calls are stateless. Stop the managed server after the task.

Use `.venv/Scripts/python.exe` and the corresponding PowerShell environment assignments on Windows. `config/bionic.env.json` records the needed values. Give Bionic the absolute plugin and workspace paths once; the skill uses these for subsequent terminal calls. No separate compiled “Bionic plugin API” is assumed.

[Official Bionic skills instructions](https://lmstudio.ai/docs/bionic/agent/skills).

## Capabilities and dependencies

| Capability | Implemented behavior | Additional requirements |
|---|---|---|
| Web research | Static extraction, links, isolated browser navigation, forms, screenshots | Chromium; optional `BRAVE_SEARCH_API_KEY` for API search, otherwise DuckDuckGo |
| Word | DOCX headings, text, bullets, tables; inspect/edit via Python | LibreOffice for genuine legacy DOC and PDF exports |
| Excel | XLSX rows, explicit formulas, header formatting; inspect/edit via Python | Excel/Numbers/LibreOffice for formula recalculation |
| PowerPoint | Editable widescreen PPTX, bullets and notes; inspect/edit via Python | Renderer/app for visual QA |
| Pages/Numbers/Keynote | Office import/save as real .pages/.numbers/.key; native export to Office/PDF | Installed apps on macOS and Automation permission |
| OpenSCAD | Custom .scad source; recipe generation; STL/3MF/PNG export | Installed OpenSCAD |
| Fusion | Prepare recipe; included in-app script builds a parametric design and exports genuine .f3d | Installed/licensed Autodesk Fusion; run script inside Fusion |
| Printer guidance | Selected Bambu Lab/Prusa reference models, dated facts, official source URLs | Verify exact model/revision using current official sources |
| Python | Execute trusted code with bundled document libraries | `WORKSHOP_ALLOW_CODE=1` |
| JavaScript/Next.js | Node ES modules; npm install/build/test/lint for Next.js projects | Node/npm and `WORKSHOP_ALLOW_CODE=1` |

The document tools provide simple reliable base layouts. Advanced charts, layouts and existing-file editing use the exposed Python tools with python-docx, openpyxl and python-pptx. Native iWork files are generated by the actual apps; feature-perfect round-tripping is not guaranteed. Browser tools do not reuse personal profiles, accept file downloads or reach local/private URLs; use the host browser for local Next.js development. Web content is untrusted source material. Browser actions can submit forms, so the browsing skill requires user authorization for consequential external actions.

Structured file operations stay inside the workspace. Python, Node, npm, OpenSCAD includes and desktop applications run with ordinary local permissions. The public-URL checks are useful guards, not an OS/network isolation boundary. HTTP transport is optional and defaults to 127.0.0.1:8765; when running several domain integrations over HTTP use distinct `--port` values; it has no remote deployment/authentication setup.

## Genuine Fusion files

1. Call `prepare_fusion_design` with a recipe JSON path, a new `.f3d` output path and a recipe like `examples/plate.json`.
2. In Autodesk Fusion open Utilities > Scripts and Add-Ins; add the `fusion/WorkshopDesign` script folder.
3. Run WorkshopDesign and choose the generated recipe JSON.
4. Fusion creates sketches/extrusions in a new parametric design and exports the archive. The script records success in a companion `.result.json`. Open the resulting F3D in Fusion to validate it.

The recipe supports boxes/cylinders and new/join/cut operations, in millimetres. Box origins are lower corners, cylinder origins are axes. Cuts remove earlier material; joins must intersect existing bodies. Disjoint bodies use new. The bridge converts millimetres to Fusion API centimetres. Complex designs require custom Fusion scripts written using the Python tool and run in Fusion. Preparing a job is explicitly **pending**, never a claim that an F3D already exists. Assemblies with external references may need F3Z.

[Autodesk export API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_ExportManager.htm).

## Verification

Run `python -m pip install -e '.[test]'` and `python -m pytest tests -q` in the plugin environment. See [the test report](TEST-REPORT.md) for the actual development checks and limits. `knowledge.txt` indexes every Python function and loop location. The host-app UI connection and Fusion archive export require final verification in their respective applications.

For release packaging and Python wheel builds, see the [build guide](docs/BUILDING.md).
