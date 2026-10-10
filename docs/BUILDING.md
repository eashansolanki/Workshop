# Building Workshop

Workshop is a Python project with a shell installer. Most users only need `bash install.sh`; the commands below are for contributors and release maintainers. Run them from the repository root, alongside `pyproject.toml`.

## Set up development dependencies

Use Python 3.11 or newer. The current verified environment uses Python 3.12. Node.js/npm are required for JavaScript and Next.js tools.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-tested.txt
.venv/bin/python -m pip install -e .
```

On Windows, use `python` to create the environment and `.venv\Scripts\python.exe` for subsequent commands. The shell installer itself requires macOS or Linux.

For interactive browser development, install Chromium into the repository's private browser folder:

```sh
PLAYWRIGHT_BROWSERS_PATH="$PWD/.browsers" .venv/bin/python -m playwright install chromium
```

For generated LM Studio configuration and manual Bionic connections, follow [source setup](../DEVELOPER-SETUP.md). That bootstrap uses declared compatible dependency ranges; the commands above install the recorded development versions first.

## Package the self-contained installer

No native compilation is needed. The release builder uses the Python standard library:

```sh
python3 scripts/build_release.py
bash -n dist/install.sh
bash -n dist/installupdate.sh
bash dist/install.sh --check
bash dist/installupdate.sh --check
```


| Artifact | Purpose |
| --- | --- |
| `dist/install.sh` | Standalone installer; no source archive required |
| `dist/installupdate.sh` | Standalone updater for existing installations |
| `dist/workshop.zip` | Source package with documentation and installer |
| `dist/SETUP.md` | Copy of the user-facing README |

It also refreshes the root `install.sh` and `installupdate.sh`. The generated installer must be rebuilt after changing source, skills, dependencies or installer code. Edit `installer/install.template.sh`, not the generated payload. `dist/`, virtual environments, browser downloads and Python build outputs are excluded from the release payload.

## Build a Python distribution

For developers using Python packaging rather than the bundled installer:

```sh
.venv/bin/python -m pip install build
.venv/bin/python -m build
```

This creates a wheel and source distribution in `dist/`. The wheel includes Python tools, packaged skill resources and printer references. It does not include the repository's shell installer or Fusion script; use `workshop.zip` for the complete bundle. Building a wheel does not connect LM Studio or Bionic.

## Prepare a GitHub release

1. Verify the affected tools through an MCP client and inspect generated outputs. This upload bundle excludes the private development test suite and verification report.
2. Rebuild and verify the installer using the commands above.
3. Test installation with a temporary workspace and temporary LM Studio configuration before using real settings. `WORKSHOP_HOME`, `WORKSHOP_WORKSPACE` and `WORKSHOP_LMSTUDIO_CONFIG` support isolated installation paths.
4. Attach `dist/install.sh`, `dist/installupdate.sh` and `dist/workshop.zip` to the release.
5. Include any application-level checks still pending in the release notes.

The repository does not assume a GitHub owner, release URL or hosted installer endpoint. Replace download links with your real release URLs when publishing.
