---
name: excel-spreadsheets
description: Create and revise Excel workbooks with explicit formulas, formatting and verifiable calculations.
---

# Excel Spreadsheets

## Workflow
1. Understand the business question, units, source data and assumptions. Preserve originals and keep source provenance.
2. `create_excel` accepts sheets with name, rows and optional formulas maps. Example: [{"name":"Budget","rows":[["Item","Amount"],["Parts",20],["Total",null]],"formulas":{"B3":"=SUM(B2:B2)"}}]. Normal string data is literal; formulas must be explicit.
3. Use `inspect_document` to check workbook contents and formula strings. Use run_python/openpyxl on a new copy for charts, styling and existing-workbook edits. Preserve VBA only with the correct openpyxl flags and original extension; the basic creation tool creates XLSX only.
4. Formula cells are not calculated by openpyxl. Open in Excel/Numbers/LibreOffice to recalculate, then compare actual results against independent calculations and check missing inputs, divide by zero and broken references. Report cached values as absent until recalculated.
5. Check row/column labels, dates, number formats, totals, hidden data, charts and print areas. Render/export to PDF and inspect if a printed deliverable is requested.
6. Use `convert_iwork` for a native Numbers file and verify it opens. Do not imply that every Excel feature survives conversion.

## Available tools and execution
Run `capabilities` first. In LM Studio use the MCP tools directly. In Bionic, if the host has no MCP connection settings, use its built-in terminal with the absolute plugin virtual-environment Python path:
`/absolute/plugin/.venv/bin/python -m workshop.cli list`
`/absolute/plugin/.venv/bin/python -m workshop.cli TOOL_NAME '{"argument":"value"}'`
In Bionic, use the current project working directory, never Documents/Workshop or the plugin folder. Native MCP tools obtain the host project root per request; call capabilities and verify workspace_ready and workspace before file operations. If Bionic does not expose one project root, the tools refuse file operations instead of using a global output folder. Use the terminal fallback from the current Bionic project terminal with WORKSHOP_WORKSPACE_MODE=bionic and PYTHONPATH pointing to the plugin; do not cd to the plugin. The CLI uses that terminal process working directory. Bionic must itself restrict its terminal/native tools to the selected project; Workshop cannot impose a boundary on unrelated host tools.

For changes to an existing text file, use Workshop read_file_snapshot, then Workshop edit_file with the returned sha256. Prefer complete edited content (omit search) when snippet matching is fragile. If a native Bionic editor says no match, reread the actual file and use this workflow. Exact snippets must match once; stale/ambiguous changes are refused without writing. Do not retry guessed snippets or relax matching silently. write_file is only for new files.

Bionic code subprocesses have OS-enforced project-only writes on macOS; arbitrary code fails closed on unsupported platforms. Native Fusion Python runs inside the external app, outside this sandbox, and strict Bionic tools cannot execute it. Structured Fusion recipes and workspace-contained preparation remain available. Other hosts can use explicitly opted-in trusted native scripts. Arguments are JSON; quote them correctly rather than interpolating untrusted text. Never claim an output exists unless returned successfully and verified.
