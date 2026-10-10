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
In Bionic, use the current project working directory, never Documents/Workshop or the plugin folder. Native MCP tools obtain the host project root per request; call capabilities and verify workspace_ready and workspace before file operations. If Bionic does not expose one project root, the tools refuse file operations instead of using a global output folder. Use the terminal fallback from the current Bionic project terminal with WORKSHOP_WORKSPACE_MODE=bionic and PYTHONPATH pointing to the plugin; do not cd to the plugin. The CLI uses that terminal process working directory. Bionic must itself restrict its terminal/native tools to the selected project; Workshop cannot impose a boundary on unrelated host tools.

For changes to an existing text file, use Workshop read_file_snapshot, then Workshop edit_file with the returned sha256. Prefer complete edited content (omit search) when snippet matching is fragile. If a native Bionic editor says no match, reread the actual file and use this workflow. Exact snippets must match once; stale/ambiguous changes are refused without writing. Do not retry guessed snippets or relax matching silently. write_file is only for new files.

Bionic code subprocesses have OS-enforced project-only writes on macOS; arbitrary code fails closed on unsupported platforms. Native Fusion Python runs inside the external app, outside this sandbox, and strict Bionic tools cannot execute it. Structured Fusion recipes and workspace-contained preparation remain available. Other hosts can use explicitly opted-in trusted native scripts. Arguments are JSON; quote them correctly rather than interpolating untrusted text. Never claim an output exists unless returned successfully and verified.
