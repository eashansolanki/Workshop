---
name: python-javascript-nextjs
description: Run trusted Python and JavaScript, build/test Next.js projects, and document code changes without deployment.
---

# Python Javascript Nextjs

## Workflow
1. Inspect existing files and use the existing stack. Ask the preferred stack for a new app; do not silently change technologies. Never deploy to ChatGPT Sites. For Flutter use ForUI unless the user explicitly requests something else.
3. run_python uses the plugin's Python interpreter with document libraries installed; add PyTorch/MLX only if needed by the project. run_javascript uses Node.js with ES modules. Both require WORKSHOP_ALLOW_CODE=1 and run with the user's permissions; they are not sandboxes and can reach files/network beyond the tool workspace. Execute only trusted, task-authorized code.
4. Use file tools for new text files. For edits use trusted execution on a new copy or the host's project tools. For Next.js keep package.json scripts, tests and dependency choices aligned with the existing project. New Next.js scaffolding may be generated through trusted code with npm/create-next-app after confirming stack.
5. run_nextjs handles install/build/test/lint for a project declaring next. npm scripts and installs execute code; inspect the project before running. Persistent dev servers are managed through Bionic's terminal, not a background MCP job. Use the host browser for local dev URLs; public web tools intentionally reject private addresses.
6. Thoroughly test the implemented behavior, errors, boundaries and regressions, run the project checks/build and review the final diff. Report what was actually verified and any dependency/environment blockers.

## Available tools and execution
Run `capabilities` first. In LM Studio use the MCP tools directly. In Bionic, if the host has no MCP connection settings, use its built-in terminal with the absolute plugin virtual-environment Python path:
`/absolute/plugin/.venv/bin/python -m workshop.cli list`
`/absolute/plugin/.venv/bin/python -m workshop.cli TOOL_NAME '{"argument":"value"}'`
In Bionic, use the current project working directory, never Documents/Workshop or the plugin folder. Native MCP tools obtain the host project root per request; call capabilities and verify workspace_ready and workspace before file operations. If Bionic does not expose one project root, the tools refuse file operations instead of using a global output folder. Use the terminal fallback from the current Bionic project terminal with WORKSHOP_WORKSPACE_MODE=bionic and PYTHONPATH pointing to the plugin; do not cd to the plugin. The CLI uses that terminal process working directory. Bionic must itself restrict its terminal/native tools to the selected project; Workshop cannot impose a boundary on unrelated host tools.

For changes to an existing text file, use Workshop read_file_snapshot, then Workshop edit_file with the returned sha256. Prefer complete edited content (omit search) when snippet matching is fragile. If a native Bionic editor says no match, reread the actual file and use this workflow. Exact snippets must match once; stale/ambiguous changes are refused without writing. Do not retry guessed snippets or relax matching silently. write_file is only for new files.

Bionic code subprocesses have OS-enforced project-only writes on macOS; arbitrary code fails closed on unsupported platforms. Native Fusion Python runs inside the external app, outside this sandbox, and strict Bionic tools cannot execute it. Structured Fusion recipes and workspace-contained preparation remain available. Other hosts can use explicitly opted-in trusted native scripts. Arguments are JSON; quote them correctly rather than interpolating untrusted text. Never claim an output exists unless returned successfully and verified.
