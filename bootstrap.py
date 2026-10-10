"""Set up dependencies and generate config without changing host app settings."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import venv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, help="Absolute folder the tools can access")
    parser.add_argument("--enable-code", action="store_true", help="Allow trusted unsandboxed Python/Node execution")
    parser.add_argument("--browser", action="store_true", help="Install Chromium for browser tools")
    parser.add_argument("--combined", action="store_true", help="Use the legacy single integration instead of eight separate ones")
    options = parser.parse_args()
    root = Path(__file__).resolve().parent
    workspace = Path(options.workspace).expanduser()
    if not workspace.is_absolute():
        parser.error("--workspace must be absolute")
    workspace.mkdir(parents=True, exist_ok=True)
    env_root = root / ".venv"
    venv.EnvBuilder(with_pip=True).create(env_root)
    python = env_root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run([str(python), "-m", "pip", "install", "-e", str(root)], check=True)
    browser_path = root / ".browsers"
    environment = {"WORKSHOP_WORKSPACE": str(workspace.resolve()), "WORKSHOP_ALLOW_CODE": "1" if options.enable_code else "0", "PYTHONPATH": str(root), "PLAYWRIGHT_BROWSERS_PATH": str(browser_path)}
    if options.browser:
        subprocess.run([str(python), "-m", "playwright", "install", "chromium"], env={**os.environ, **environment}, check=True)
    generator = "from workshop.integrations import mcp_configuration; import json,sys; print(json.dumps(mcp_configuration(sys.argv[1], json.loads(sys.argv[2]), combined=sys.argv[3]=='1')))"
    generated = subprocess.run([str(python), "-c", generator, str(python), json.dumps(environment), "1" if options.combined else "0"], cwd=root, capture_output=True, text=True, check=True)
    config = json.loads(generated.stdout)
    output = root / "config" / "lmstudio.mcp.json"
    output.write_text(json.dumps(config, indent=2))
    (root / "config" / "bionic.env.json").write_text(json.dumps(environment, indent=2))
    print(f"Generated LM Studio config: {output}")
    print("Merge the generated server entries into LM Studio's MCP editor. Existing host config was not modified.")
    print("Bionic: add skills/*/SKILL.md in Settings > Skills; use the included terminal CLI if MCP settings are unavailable.")


if __name__ == "__main__":
    main()
