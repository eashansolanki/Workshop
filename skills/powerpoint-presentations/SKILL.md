---
name: powerpoint-presentations
description: Create and revise editable PowerPoint decks with coherent narrative, notes and checked layouts.
---

# Powerpoint Presentations

## Workflow
1. Confirm audience, purpose and intended decision. Plan a short narrative with one clear takeaway per slide.
2. `create_powerpoint` accepts title and slides of {title,bullets,notes}; it generates editable widescreen PPTX with a cover slide.
3. For richer layouts, charts and pictures or editing existing decks, use run_python with python-pptx and new output filenames. Use accurate data and licensed assets. Avoid overflowing text and tiny fonts.
4. Inspect with `inspect_document`, export to PDF using LibreOffice or Keynote, and review every rendered slide using the host's viewer. Verify alignment, contrast, clipping, hierarchy, source notes and speaker notes. Do not claim visual QA based on text extraction alone.
5. Native Keynote delivery uses `convert_iwork` and requires installed macOS Keynote. Check the converted file in Keynote for font/substitution and animation differences.

## Available tools and execution
Run `capabilities` first. In LM Studio use the MCP tools directly. In Bionic, if the host has no MCP connection settings, use its built-in terminal with the absolute plugin virtual-environment Python path:
`/absolute/plugin/.venv/bin/python -m workshop.cli list`
`/absolute/plugin/.venv/bin/python -m workshop.cli TOOL_NAME '{"argument":"value"}'`
In Bionic, use the current project working directory, never Documents/Workshop or the plugin folder. Native MCP tools obtain the host project root per request; call capabilities and verify workspace_ready and workspace before file operations. If Bionic does not expose one project root, the tools refuse file operations instead of using a global output folder. Use the terminal fallback from the current Bionic project terminal with WORKSHOP_WORKSPACE_MODE=bionic and PYTHONPATH pointing to the plugin; do not cd to the plugin. The CLI uses that terminal process working directory. Bionic must itself restrict its terminal/native tools to the selected project; Workshop cannot impose a boundary on unrelated host tools.

For changes to an existing text file, use Workshop read_file_snapshot, then Workshop edit_file with the returned sha256. Prefer complete edited content (omit search) when snippet matching is fragile. If a native Bionic editor says no match, reread the actual file and use this workflow. Exact snippets must match once; stale/ambiguous changes are refused without writing. Do not retry guessed snippets or relax matching silently. write_file is only for new files.

Bionic code subprocesses have OS-enforced project-only writes on macOS; arbitrary code fails closed on unsupported platforms. Native Fusion Python runs inside the external app, outside this sandbox, and strict Bionic tools cannot execute it. Structured Fusion recipes and workspace-contained preparation remain available. Other hosts can use explicitly opted-in trusted native scripts. Arguments are JSON; quote them correctly rather than interpolating untrusted text. Never claim an output exists unless returned successfully and verified.
