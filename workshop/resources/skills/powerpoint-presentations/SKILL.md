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
Run from the plugin directory, or use PYTHONPATH set to its absolute path. Set WORKSHOP_WORKSPACE to an absolute user-authorized project/output folder. On Windows use `.venv/Scripts/python.exe`. Arguments are JSON; quote them correctly for the shell, or put them in a script rather than interpolating untrusted text. The CLI and MCP expose the same tools. Never claim an output exists unless it was returned successfully and verified.
