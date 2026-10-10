# Workshop

Local tools for **LM Studio** and **Bionic**: research the web, create documents, write code and design objects for 3D printing.

Workshop provides eight independently selectable MCP integrations in LM Studio. Bionic has its own MCP settings; the installer registers the same eight native connections there. Every connection supplies its workflow through `get_workflow`.

## Quick start

Download `install.sh` from this repository or a release, close LM Studio, then run:

```sh
bash install.sh
```

The self-contained installer sets up private Python and Node runtimes, downloads Chromium, checks all eight integrations, and adds them to LM Studio. It preserves unrelated integrations and backs up your settings. **No compiler or manual Python/Node setup is required.** An internet connection is required for the initial installation.

1. Restart LM Studio and enable the Workshop integrations you need.
2. Restart Bionic and check **Settings → Connected Apps / MCP** for the eight `workshop-*` connections. Call `capabilities` on a connection to verify it. You can also add the optional `SKILL.md` printed by the installer in **Settings → Skills**.
3. Ask your model to check capabilities, load the relevant workflow and create an output.

For example: “Use Workshop's Excel integration to create a monthly budget spreadsheet in my workspace.”

For the complete walkthrough, including where to find and register the Fusion script, see [Set up Workshop](docs/GETTING-STARTED.md).

## Update an existing installation

Download the latest `installupdate.sh` from this repository or its release, close LM Studio, Bionic and Fusion, then run:

```sh
bash installupdate.sh
```

The script installs the version bundled in that download, checks all eight integrations and refreshes LM Studio settings before removing old managed release folders. It keeps your generated documents/CAD files, custom workspace/configuration paths, unrelated integrations, settings backups and runtime downloads. Download a new updater for each release; it does not fetch unpublished changes from GitHub.

Bionic and Fusion now have stable registration paths. For an installation made before this update, replace the old Bionic skill with `~/Library/Application Support/Workshop/Bionic/SKILL.md` and register `~/Library/Application Support/Workshop/fusion/WorkshopDesign` in Fusion once. Use the paths printed by the updater on Linux or custom installations. Later updates keep these registration paths.

## Included integrations

| Integration | Tools and outputs |
| --- | --- |
| Advanced web browsing | Search, page extraction, browser navigation, forms and screenshots |
| Word documents | DOCX documents and tables; DOC/PDF conversion through LibreOffice |
| Excel spreadsheets | XLSX sheets, formulas and workbook inspection |
| PowerPoint presentations | Editable PPTX slides and speaker notes |
| Apple iWork | Pages, Numbers and Keynote import/export through installed macOS apps |
| 3D-printing design | Design workflow, print orientation, tolerances and Bambu Lab/Prusa references |
| OpenSCAD and Fusion | SCAD source, STL/3MF/PNG rendering and native Fusion recipes/scripts/imports, automatic execution, per-part project folders and saved-file links |
| Python, JavaScript and Next.js | Local code execution and npm install/build/test/lint tasks |

## Requirements and current limits

The shell installer supports **macOS and Linux**, on **arm64 and x86_64**. Windows source setup is described in the developer guide; this shell installer does not support Windows.

Install additional applications only for the formats you need:

- **LibreOffice** for legacy DOC and PDF conversion.
- **Pages, Numbers and Keynote on macOS** for native iWork files. macOS may request Automation permission.
- **OpenSCAD** for compiled meshes and previews.
- **Autodesk Fusion** for genuine F3D export. Register WorkshopBridge once for automatic queued execution, or run WorkshopDesign manually; preparation alone is not an F3D export.

Numbers conversion and live Fusion archive export remain unverified. Document tools produce editable base layouts; visual review and spreadsheet formula recalculation require the appropriate application. Printer references provide guidance, not printer control. Numbers conversion and live Fusion archive export remain unverified.

Python and JavaScript run with your user permissions. Structured file tools stay within the selected workspace and refuse to overwrite files. Code execution is not an operating-system sandbox.

## Installation options

```sh
bash install.sh --check  # Verify the embedded package without installing
bash install.sh --yes    # Skip the installation prompt
bash install.sh --help   # Show usage
```

| Setting | Default |
| --- | --- |
| Created files | `~/Documents/Workshop` |
| macOS installation | `~/Library/Application Support/Workshop` |
| Linux installation | `${XDG_DATA_HOME:-~/.local/share}/workshop` |
| LM Studio configuration | `~/.lmstudio/mcp.json` |

Override these paths with `WORKSHOP_WORKSPACE`, `WORKSHOP_HOME` and `WORKSHOP_LMSTUDIO_CONFIG`. For example:

```sh
WORKSHOP_WORKSPACE="$HOME/Projects/workshop-output" bash install.sh
```

The installer prints the Bionic skill path and keeps a setup log in the installation folder. If setup fails, inspect that log before retrying. Keep the installation directory: the generated integrations refer to its runtime and source files.

## Development and documentation

- [Installation, Bionic and Fusion walkthrough](docs/GETTING-STARTED.md)
- [Source setup and host configuration](DEVELOPER-SETUP.md)
- [Build and release guide](docs/BUILDING.md)
- [Complete Fusion setup and export guide](docs/FUSION360.md)
- [Full feature list](docs/FEATURES.md)
- [CAD export guide](docs/CAD.md)
- [Contributing](CONTRIBUTING.md)

## Help

If you can help develop this project more please do by submitting a PR as some of the refinements and some features have been vibe coded. 

Bionic keeps native MCP connections in its own `~/.lmstudio/apps/bionic/.internal/ng-mcp.json`; adding entries to LM Studio’s `mcp.json` alone does not connect Bionic. The updater preserves unrelated connections and existing Workshop IDs/toggles, backs up the original file, and rejects unsupported settings. Set `WORKSHOP_BIONIC_CONFIG` for a custom Bionic location. Restart Bionic after updating.

### Bionic project boundaries and edits

Bionic connections no longer inherit `~/Documents/Workshop`. Native MCP calls use one project root supplied by Bionic on each request. If the host supplies no root or several unrelated roots, file tools refuse operations. Check `capabilities.workspace_ready` and `capabilities.workspace` before working. The terminal fallback runs from the current Bionic project directory using the installed Python and `WORKSHOP_WORKSPACE_MODE=bionic`; keep `PYTHONPATH` pointing to the plugin and do not change into its folder. Bionic's own terminal/native editor permissions are controlled by Bionic, separately from Workshop.

For an existing text file, call `read_file_snapshot`, then `edit_file` with its `sha256`. Omit `search` to supply the complete edited content, or provide one exact unique snippet. Stale reads and zero/multiple matches return recovery instructions without changing the file. CRLF-only files accept equivalent LF snippets while preserving CRLF. No fuzzy matching silently rewrites code.

Strict Bionic mode uses macOS sandbox-exec for code subprocesses, allowing writes only in that project. The restricted profile also denies network/IPC operations that could delegate writes to another process. Unsupported platforms refuse arbitrary code. Native Python running inside Fusion is outside this sandbox, so strict Bionic tools cannot execute native scripts; they can prepare them and run structured recipes. This restriction is necessary to enforce the requested write boundary.
