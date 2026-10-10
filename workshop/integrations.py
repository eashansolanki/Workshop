"""Expose the same Bionic skills as separately selectable LM Studio MCP servers."""
from .scope import ProjectMCP

# Every integration loads its original SKILL.md and exposes actual domain tools.
INTEGRATIONS = {
    "advanced-web-browsing": ("fetch_webpage", "search_web", "browse_web"),
    "word-documents": ("create_word", "inspect_document", "convert_office", "convert_iwork", "read_file", "write_file", "read_file_snapshot", "edit_file", "run_python"),
    "excel-spreadsheets": ("create_excel", "inspect_document", "convert_office", "convert_iwork", "read_file", "write_file", "read_file_snapshot", "edit_file", "run_python"),
    "powerpoint-presentations": ("create_powerpoint", "inspect_document", "convert_office", "convert_iwork", "read_file", "write_file", "read_file_snapshot", "edit_file", "run_python"),
    "apple-iwork": ("create_word", "create_excel", "create_powerpoint", "inspect_document", "convert_iwork", "convert_office", "read_file", "write_file", "read_file_snapshot", "edit_file", "run_python"),
    "3d-printing-design": ("printer_reference", "fetch_webpage", "search_web", "create_openscad", "create_cad_recipe", "render_openscad", "prepare_fusion_design", "prepare_fusion_import", "run_fusion_design", "fusion_design_status", "open_fusion_design", "prepare_fusion_script", "create_cad_project", "plan_cad_design", "review_cad_design", "inspect_cad_preview", "run_fusion_project", "fusion_project_status", "read_file", "write_file", "read_file_snapshot", "edit_file", "run_python"),
    "openscad-and-fusion": ("create_openscad", "create_cad_recipe", "render_openscad", "prepare_fusion_design", "prepare_fusion_import", "run_fusion_design", "fusion_design_status", "open_fusion_design", "prepare_fusion_script", "create_cad_project", "plan_cad_design", "review_cad_design", "inspect_cad_preview", "run_fusion_project", "fusion_project_status", "printer_reference", "read_file", "write_file", "read_file_snapshot", "edit_file", "run_python"),
    "python-javascript-nextjs": ("run_python", "run_javascript", "run_nextjs", "read_file", "write_file", "read_file_snapshot", "edit_file", "fetch_webpage"),
}


def create_integration(name: str, *, port: int = 8765) -> ProjectMCP:
    """Build a domain server whose instructions and workflow tool use the Bionic skill."""
    from . import server
    if name not in INTEGRATIONS:
        raise ValueError(f"Unknown integration: {name}")
    workflow = server.get_skill(name)
    integration = ProjectMCP(
        "Workshop: " + name.replace("-", " ").title(),
        instructions=f"Use get_workflow before this integration's domain tools.\n\n{workflow}",
        host="127.0.0.1", port=port,
    )

    def get_workflow() -> str:
        """Load this integration's complete skill instructions before performing domain work."""
        return server.get_skill(name)

    integration.add_tool(get_workflow, description=f"Load the {name} workflow before using its tools. Returns the same SKILL.md used by Bionic.")
    integration.add_tool(server.capabilities)
    for tool_name in INTEGRATIONS[name]:
        integration.add_tool(getattr(server, tool_name))
    return integration


def mcp_configuration(python: str, environment: dict[str, str], *, combined: bool = False) -> dict:
    """Generate LM Studio's supported command/args/env server configuration."""
    if combined:
        entries = {"workshop": {"command": python, "args": ["-m", "workshop.server"], "env": dict(environment)}}
    else:
        entries = {
            "workshop-" + name: {
                "command": python,
                "args": ["-m", "workshop.server", "--integration", name],
                "env": dict(environment),
            }
            for name in INTEGRATIONS
        }
    return {"mcpServers": entries}
