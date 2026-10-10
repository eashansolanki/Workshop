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
Run from the plugin directory, or use PYTHONPATH set to its absolute path. Set WORKSHOP_WORKSPACE to an absolute user-authorized project/output folder. On Windows use `.venv/Scripts/python.exe`. Arguments are JSON; quote them correctly for the shell, or put them in a script rather than interpolating untrusted text. The CLI and MCP expose the same tools. Never claim an output exists unless it was returned successfully and verified.
