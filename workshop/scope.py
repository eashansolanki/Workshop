"""Per-request host project roots, never a model-selected global workspace."""
import asyncio
from pathlib import Path
from urllib.parse import unquote, urlparse
from mcp import types
from mcp.server.fastmcp import FastMCP
from . import core


def root_path(uri):
    parsed = urlparse(str(uri))
    if parsed.scheme != 'file' or parsed.netloc not in ('', 'localhost') or parsed.query or parsed.fragment:
        raise ValueError('Working directory must be a local file URI')
    candidate = Path(unquote(parsed.path))
    if not candidate.is_absolute() or not candidate.is_dir():
        raise ValueError('Working directory must be an existing absolute folder')
    resolved = candidate.resolve()
    if resolved == Path(resolved.anchor) or resolved == Path.home().resolve():
        raise ValueError('Select a project folder, not the filesystem or home root')
    return resolved


class ProjectMCP(FastMCP):
    async def call_tool(self, name, arguments):
        if not core.bionic_mode():
            return await super().call_tool(name, arguments)
        project, error = None, 'Bionic did not supply its working directory. Use the CLI from the current Bionic project terminal; never fall back to Documents/Workshop.'
        try:
            try:
                session = self.get_context().request_context.session
            except ValueError:
                if core.workspace_status()["workspace_ready"]:
                    return await super().call_tool(name, arguments)
                raise
            if session.check_client_capability(types.ClientCapabilities(roots=types.RootsCapability())):
                async with asyncio.timeout(5):
                    roots = (await session.list_roots()).roots
                if len(roots) != 1:
                    raise ValueError('Bionic must expose exactly one current project root; selecting among unrelated projects is unsafe')
                project = root_path(roots[0].uri)
                error = None
        except Exception as exc:
            error = f'Cannot determine the Bionic working directory: {exc}'
        # Tokens isolate simultaneous requests and projects, including thread-pool tools.
        with core.workspace_scope(project, error):
            return await super().call_tool(name, arguments)
