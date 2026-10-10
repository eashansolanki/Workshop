# Workshop

WARNING: MACOS ONLY FOR NOW 
Local tools for **LM Studio** and **Bionic**: research the web, create documents, write code and design objects in Fusion and OpenScad.

Workshop provides eight independently selectable MCP integrations in LM Studio. Bionic uses the same workflows as skills, backed by the same local tools.

## Quick start

Download `install.sh` from this repository or a release, close LM Studio, then run:

```sh
bash install.sh
```

The self-contained installer sets up private Python and Node runtimes, downloads Chromium, checks all eight integrations, and adds them to LM Studio. It preserves unrelated integrations and backs up your settings. **No compiler or manual Python/Node setup is required.** An internet connection is required for the initial installation.

1. Restart LM Studio and enable the Workshop integrations you need.
2. In Bionic, open **Settings → Skills → Add file** and select the `SKILL.md` path printed by the installer. This hub contains all eight workflows.
3. Ask your model to check capabilities, load the relevant workflow and create an output.

For example: “Use Workshop's Excel integration to create a monthly budget spreadsheet in my workspace.”

## Included integrations

| Integration | Tools and outputs |
| --- | --- |
| Advanced web browsing | Search, page extraction, browser navigation, forms and screenshots |
| Word documents | DOCX documents and tables; DOC/PDF conversion through LibreOffice |
| Excel spreadsheets | XLSX sheets, formulas and workbook inspection |
| PowerPoint presentations | Editable PPTX slides and speaker notes |
| Apple iWork | Pages, Numbers and Keynote import/export through installed macOS apps |
| 3D-printing design | Design workflow, print orientation, tolerances and Bambu Lab/Prusa references |
| OpenSCAD and Fusion | SCAD source, STL/3MF/PNG rendering and a Fusion recipe/script bridge |
| Python, JavaScript and Next.js | Local code execution and npm install/build/test/lint tasks |

## Requirements and current limits

The shell installer supports **macOS and Linux**, on **arm64 and x86_64**. Windows source setup is described in the developer guide; this shell installer does not support Windows.

Install additional applications only for the formats you need:

- **LibreOffice** for legacy DOC and PDF conversion.
- **Pages, Numbers and Keynote on macOS** for native iWork files. macOS may request Automation permission.
- **OpenSCAD** for compiled meshes and previews.
- **Autodesk Fusion** for genuine F3D export. Run the included script inside Fusion; a prepared recipe is not yet an F3D file.

Numbers conversion and live Fusion archive export remain unverified. Document tools produce editable base layouts; visual review and spreadsheet formula recalculation require the appropriate application. Printer references provide guidance, not printer control. See the [test report](TEST-REPORT.md) for verified behavior and remaining limits.

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

- [Source setup and host configuration](DEVELOPER-SETUP.md)
- [Build and release guide](docs/BUILDING.md)
- [CAD export guide](docs/CAD.md)
- [Contributing](CONTRIBUTING.md)
- [Verification report](TEST-REPORT.md)

Source code is in `workshop/`, workflows in `skills/`, the Fusion bridge in `fusion/`, and installation code in `installer/`. `knowledge.txt` indexes Python functions, components and loops.

