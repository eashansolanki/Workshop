# Contributing to Workshop

Use the existing Python/MCP tools and JavaScript/Node integration. Start with the [build guide](docs/BUILDING.md) and verify affected tools before submitting a change. This release folder excludes the private development test suite.

## Where changes belong

| Location | Responsibility |
| --- | --- |
| `workshop/server.py` | MCP tool definitions and capability reporting |
| `workshop/integrations.py` | Per-skill tool collections and configuration |
| `workshop/core.py` | Workspace paths, execution controls and timeouts |
| `workshop/documents.py` | Office and iWork tools |
| `workshop/web.py` | Web extraction, search and browser sessions |
| `workshop/cad.py`, `fusion/` | CAD recipes, rendering and Fusion export |
| `skills/` | Bionic workflows and MCP instructions |
| `workshop/resources/` | Packaged copies of workflows and printer references |
| `installer/` | Installer engine and shell template |
| `scripts/build_release.py` | Installer/source release packaging |

Keep each `skills/*/SKILL.md` synchronized with its copy in `workshop/resources/skills/`. Keep `config/printers.json` synchronized with its packaged resource. Check that both copies match when updating a workflow.

## Before submitting

- Check changed behavior through the runtime tools and inspect the generated outputs.
- Describe what changed, how it was tested and any application-level verification still pending.
- Preserve unrelated host configuration and avoid overwriting user documents.
- Return real outputs or explicit dependency/pending results; do not claim an export completed when only a recipe was prepared.
- Exclude local environments, browser profiles, generated host configuration, credentials and user files from commits.

For a bug report, include the operation, operating system, relevant dependency versions and the error or setup-log excerpt. Remove credentials and personal paths before sharing logs.
