"""Bionic terminal adapter. Optional HTTP forwarding preserves browser state."""
import argparse
import asyncio
import json
import os
import sys
from .server import mcp


def emit(result):
    content = result[0] if isinstance(result, tuple) else result
    print(json.dumps([item.model_dump(mode="json") for item in content], indent=2, default=str))


async def invoke(options):
    if options.url:
        from urllib.parse import urlparse
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client
        parsed = urlparse(options.url)
        if parsed.scheme != "http" or parsed.hostname != "127.0.0.1":
            raise ValueError("CLI forwarding only supports the local 127.0.0.1 HTTP server")
        async with streamable_http_client(options.url) as (reader, writer, _):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                if options.tool == "list":
                    found = await session.list_tools()
                    print(json.dumps([tool.model_dump(mode="json") for tool in found.tools], indent=2))
                else:
                    result = await session.call_tool(options.tool, json.loads(options.arguments))
                    emit(result.content)
                    if result.isError:
                        raise RuntimeError("Remote tool returned an error; see output")
        return
    if options.tool == "list":
        print(json.dumps([tool.model_dump(mode="json") for tool in await mcp.list_tools()], indent=2))
    else:
        emit(await mcp.call_tool(options.tool, json.loads(options.arguments)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("WORKSHOP_MCP_URL", ""))
    parser.add_argument("tool", nargs="?", default="list")
    parser.add_argument("arguments", nargs="?", default="{}")
    options = parser.parse_args()
    try:
        asyncio.run(invoke(options))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
