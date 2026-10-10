---
name: word-documents
description: Create, inspect and revise Word documents, tables, legacy DOC exports and PDF deliverables.
---

# Word Documents

## Workflow
1. Confirm audience, purpose, facts, desired structure and format; draft with explicit assumptions.
2. `create_word` generates real DOCX with a title and paragraph/heading/bullet/table blocks. Tables use rectangular rows. Example: blocks=[{"type":"heading","text":"Findings"},{"type":"paragraph","text":"Verified findings."}].
3. Inspect with `inspect_document`; check headings, spelling, table contents and source attribution. For existing DOCX use run_python with python-docx to edit a new copy when code is enabled. Do not overwrite original documents.
4. For requested legacy `.doc`, call `convert_office` on the DOCX with a new .doc output; LibreOffice is required. For PDF call the same conversion tool. Renaming DOCX to DOC is prohibited.
5. Render through LibreOffice or Pages to PDF and inspect every page using the host's PDF/image viewer before describing layout as verified. Check clipped text, page breaks, table wrapping, fonts and total pages. If no renderer/viewer is available, report that visual verification is pending.

## Available tools and execution
Run `capabilities` first. In LM Studio use the MCP tools directly. In Bionic, if the host has no MCP connection settings, use its built-in terminal with the absolute plugin virtual-environment Python path:
`/absolute/plugin/.venv/bin/python -m workshop.cli list`
`/absolute/plugin/.venv/bin/python -m workshop.cli TOOL_NAME '{"argument":"value"}'`
Run from the plugin directory, or use PYTHONPATH set to its absolute path. Set WORKSHOP_WORKSPACE to an absolute user-authorized project/output folder. On Windows use `.venv/Scripts/python.exe`. Arguments are JSON; quote them correctly for the shell, or put them in a script rather than interpolating untrusted text. The CLI and MCP expose the same tools. Never claim an output exists unless it was returned successfully and verified.
