"""Verify actual installations from the Ubuntu Docker bootstrap."""

from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import subprocess
import tomllib


def output(*args):
    return subprocess.check_output(args, text=True).strip()


def check_version(name, installed, expected):
    if installed != expected:
        raise SystemExit(f"{name}: expected {expected}, got {installed}")
    print(f"{name}: {installed}", flush=True)


home = Path.home()
mise_dir = home / ".config/mise"
tools = tomllib.loads((mise_dir / "mise.lock").read_text())["tools"]
check_version("Python", platform.python_version(), tools["python"][0]["version"])
check_version("Node", output("node", "--version").removeprefix("v"), tools["node"][0]["version"])
print(f"npm: {output('npm', '--version')}", flush=True)
check_version("uv", output("uv", "--version").split()[1], tools["uv"][0]["version"])

context7_dir = home / ".local/share/context7-mcp"
context7_package = "node_modules/@upstash/context7-mcp"
npm_lock = json.loads((context7_dir / "package-lock.json").read_text())
installed_context7 = json.loads((context7_dir / context7_package / "package.json").read_text())
check_version("Context7", installed_context7["version"], npm_lock["packages"][context7_package]["version"])

azure = tools["azure"][0]
check_version("Azure CLI", json.loads(output("az", "version", "--output", "json"))["azure-cli"], azure["version"])
graph = mise_dir / azure["uv"]["path"]
digest = sha256((graph / "uv.lock").read_bytes()).hexdigest()
if f"sha256:{digest}" != azure["uv"]["digest"]:
    raise SystemExit("Azure CLI dependency lock does not match mise.lock")

azure_env = Path(output("mise", "which", "az")).resolve().parent.parent
subprocess.run(
    ["uv", "sync", "--check", "--frozen", "--offline", "--no-install-project", "--project", str(graph)],
    env={**os.environ, "UV_PROJECT_ENVIRONMENT": str(azure_env)},
    check=True,
)
