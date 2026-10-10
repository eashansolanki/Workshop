---
name: apple-iwork
description: Produce native Pages, Numbers and Keynote files using installed macOS apps and Office import/export.
---

# Apple Iwork

## Workflow
1. Run capabilities and check installed apps. Native Apple formats require macOS and the respective application; macOS may ask for Automation permission the first time.
2. Generate DOCX/XLSX/PPTX with Word/Excel/PowerPoint tools. Then call `convert_iwork` with matching .pages/.numbers/.key output. This is actual application import/save, not extension renaming.
3. Existing native files can be exported with `convert_iwork` to matching Office formats or PDF for inspection and revision. Review the converted copy, then import back under a new name if needed.
4. Inspect tables, formulas, speaker notes and layouts after conversion. Some features do not round-trip; preserve the original and call out limitations.
5. If iWork apps are unavailable, deliver genuine Office intermediates and clearly mark native delivery pending. For macOS automation errors, inspect the script dictionary/Automation permissions and report the exact error.
Official conversion guidance: https://support.apple.com/en-gb/105050

## Available tools and execution
Run `capabilities` first. In LM Studio use the MCP tools directly. In Bionic, if the host has no MCP connection settings, use its built-in terminal with the absolute plugin virtual-environment Python path:
`/absolute/plugin/.venv/bin/python -m workshop.cli list`
`/absolute/plugin/.venv/bin/python -m workshop.cli TOOL_NAME '{"argument":"value"}'`
Run from the plugin directory, or use PYTHONPATH set to its absolute path. Set WORKSHOP_WORKSPACE to an absolute user-authorized project/output folder. On Windows use `.venv/Scripts/python.exe`. Arguments are JSON; quote them correctly for the shell, or put them in a script rather than interpolating untrusted text. The CLI and MCP expose the same tools. Never claim an output exists unless it was returned successfully and verified.
