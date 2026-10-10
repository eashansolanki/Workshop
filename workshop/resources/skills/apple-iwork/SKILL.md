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
In Bionic, use the current project working directory, never Documents/Workshop or the plugin folder. Native MCP tools obtain the host project root per request; call capabilities and verify workspace_ready and workspace before file operations. If Bionic does not expose one project root, the tools refuse file operations instead of using a global output folder. Use the terminal fallback from the current Bionic project terminal with WORKSHOP_WORKSPACE_MODE=bionic and PYTHONPATH pointing to the plugin; do not cd to the plugin. The CLI uses that terminal process working directory. Bionic must itself restrict its terminal/native tools to the selected project; Workshop cannot impose a boundary on unrelated host tools.

For changes to an existing text file, use Workshop read_file_snapshot, then Workshop edit_file with the returned sha256. Prefer complete edited content (omit search) when snippet matching is fragile. If a native Bionic editor says no match, reread the actual file and use this workflow. Exact snippets must match once; stale/ambiguous changes are refused without writing. Do not retry guessed snippets or relax matching silently. write_file is only for new files.

Bionic code subprocesses have OS-enforced project-only writes on macOS; arbitrary code fails closed on unsupported platforms. Native Fusion Python runs inside the external app, outside this sandbox, and strict Bionic tools cannot execute it. Structured Fusion recipes and workspace-contained preparation remain available. Other hosts can use explicitly opted-in trusted native scripts. Arguments are JSON; quote them correctly rather than interpolating untrusted text. Never claim an output exists unless returned successfully and verified.
