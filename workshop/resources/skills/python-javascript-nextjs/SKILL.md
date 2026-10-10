---
name: python-javascript-nextjs
description: Run trusted Python and JavaScript, build/test Next.js projects, and document code changes without deployment.
---

# Python Javascript Nextjs

## Workflow
1. Inspect existing files and use the existing stack. Ask the preferred stack for a new app; do not silently change technologies. Never deploy to ChatGPT Sites. For Flutter use ForUI unless the user explicitly requests something else.
2. Keep knowledge.txt updated with functions, components, loops, locations and changes. Understand the project before editing.
3. run_python uses the plugin's Python interpreter with document libraries installed; add PyTorch/MLX only if needed by the project. run_javascript uses Node.js with ES modules. Both require WORKSHOP_ALLOW_CODE=1 and run with the user's permissions; they are not sandboxes and can reach files/network beyond the tool workspace. Execute only trusted, task-authorized code.
4. Use file tools for new text files. For edits use trusted execution on a new copy or the host's project tools. For Next.js keep package.json scripts, tests and dependency choices aligned with the existing project. New Next.js scaffolding may be generated through trusted code with npm/create-next-app after confirming stack.
5. run_nextjs handles install/build/test/lint for a project declaring next. npm scripts and installs execute code; inspect the project before running. Persistent dev servers are managed through Bionic's terminal, not a background MCP job. Use the host browser for local dev URLs; public web tools intentionally reject private addresses.
6. Thoroughly test the implemented behavior, errors, boundaries and regressions, run the project checks/build and review the final diff. Report what was actually verified and any dependency/environment blockers.

## Available tools and execution
Run `capabilities` first. In LM Studio use the MCP tools directly. In Bionic, if the host has no MCP connection settings, use its built-in terminal with the absolute plugin virtual-environment Python path:
`/absolute/plugin/.venv/bin/python -m workshop.cli list`
`/absolute/plugin/.venv/bin/python -m workshop.cli TOOL_NAME '{"argument":"value"}'`
Run from the plugin directory, or use PYTHONPATH set to its absolute path. Set WORKSHOP_WORKSPACE to an absolute user-authorized project/output folder. On Windows use `.venv/Scripts/python.exe`. Arguments are JSON; quote them correctly for the shell, or put them in a script rather than interpolating untrusted text. The CLI and MCP expose the same tools. Never claim an output exists unless it was returned successfully and verified.
