#!/usr/bin/env python3
"""Offline checks: python3 tests/test-context7.py (requires Git and chezmoi)."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
TOKEN = "ctx7" + "sk-" + "synthetic-test-token-123456789"


def run(args, **kwargs):
    return subprocess.run(args, capture_output=True, text=True, **kwargs)


with tempfile.TemporaryDirectory() as directory:
    base = Path(directory)
    home = base / "home"
    key = home / ".config/context7/api-key"
    env = {**os.environ, "HOME": str(home), "PATH": "/usr/bin:/bin"}
    launcher = ["/bin/sh", str(ROOT / "dot_local/bin/executable_context7-mcp")]
    for content in (None, "", "\n"):
        if content is not None:
            key.parent.mkdir(parents=True, exist_ok=True)
            key.write_text(content)
        result = run(launcher, env=env)
        assert result.returncode != 0 and not result.stdout
        assert "context7-mcp:" in result.stderr

    # Exercise the same hidden-prompt writer without a real secret or terminal.
    spec = importlib.util.spec_from_file_location("key_setup", ROOT / "scripts/set-context7-key.py")
    setup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(setup)
    with patch.dict(os.environ, {"HOME": str(home)}), patch("sys.stdin.isatty", return_value=True):
        with patch("getpass.getpass", return_value=TOKEN):
            setup.main()
        assert key.read_text().strip() == TOKEN
        assert key.stat().st_mode & 0o777 == 0o600
        assert key.parent.stat().st_mode & 0o777 == 0o700
        for invalid in ("", "wrong", TOKEN + "\n"):
            with patch("getpass.getpass", return_value=invalid):
                try:
                    setup.main()
                except SystemExit:
                    pass
                else:
                    raise AssertionError("Invalid key accepted")
            assert key.read_text().strip() == TOKEN

    npx = home / ".local/share/mise/shims/npx"
    npx.parent.mkdir(parents=True)
    npx.write_text('''#!/bin/sh
[ "$CONTEXT7_API_KEY" = "$EXPECTED_KEY" ] || exit 2
[ "$#" = 2 ] && [ "$1" = '-y' ] && [ "$2" = '@upstash/context7-mcp@4.1.1' ] || exit 3
printf 'fake npx OK\\n'
''')
    npx.chmod(0o755)
    result = run(launcher, env={**env, "EXPECTED_KEY": TOKEN, "CONTEXT7_API_KEY": "stale"})
    assert result.returncode == 0, result.stderr
    assert TOKEN not in result.stdout + result.stderr
    assert "fake npx OK" in result.stdout

    # Render each client from existing settings and check preservation and idempotence.
    chezmoi = shutil.which("chezmoi")
    assert chezmoi, "chezmoi is required"
    config = base / "chezmoi.toml"
    config.write_text('[data]\nname = "Test"\nemail = "test@example.com"\n')
    command = [str(home / ".local/bin/context7-mcp")]
    fixtures = {
        ".codex/config.toml": ('model = "keep"\n[mcp_servers.context7]\ncommand = "old"\nargs = ["' + TOKEN + '"]\n', "mcp_servers", {"command": command[0]}),
        ".config/opencode/opencode.jsonc": ('{// keep values, accept JSONC\n"plugin":["keep"],"mcp":{"context7":{"headers":{"CONTEXT7_API_KEY":"' + TOKEN + '"}},"servers":{"other":{"type":"local","command":["keep"]}}},}', "mcp", None),
        ".config/kilo/kilo.jsonc": (json.dumps({"model": "keep", "mcp": {"context7": {"environment": {"CONTEXT7_API_KEY": TOKEN}}}}), "mcp", {"type": "local", "command": command}),
        ".config/Code/User/globalStorage/kilocode.kilo-code/settings/mcp_settings.json": (json.dumps({"keep": True, "mcpServers": {"context7": {"args": [TOKEN]}}}), "mcpServers", {"command": command[0]}),
        ".config/Code/User/mcp.json": ("{}", "servers", {"type": "stdio", "command": command[0], "gallery": True}),
    }
    env["XDG_CONFIG_HOME"] = str(home / ".config")
    for name, (original, section, expected) in fixtures.items():
        target = home / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(original)
        args = [chezmoi, "--config", str(config), "--source", str(ROOT), "--destination", str(home), "cat", str(target)]
        result = run(args, env=env)
        assert result.returncode == 0, result.stderr
        assert TOKEN not in result.stdout
        data = tomllib.loads(result.stdout) if name.endswith(".toml") else json.loads(result.stdout)
        if "opencode" in name:
            assert "context7" not in data[section]
            assert data[section]["servers"]["context7"] == {"type": "local", "command": command}
            assert data[section]["servers"]["other"]["command"] == ["keep"]
            assert data["plugin"] == ["keep"]
        else:
            assert data[section]["context7"] == expected
        if "model" in data:
            assert data["model"] == "keep"
        if "mcp_settings" in name:
            assert data["keep"] is True
        target.write_text(result.stdout)
        assert run(args, env=env).stdout == result.stdout
        # Empty targets must work on a fresh machine too.
        target.unlink()
        result = run(args, env=env)
        assert result.returncode == 0, result.stderr

    # Test hooks with real commits, including a secret removed before the push.
    repo = base / "repo"
    repo.mkdir()
    def git(*args):
        result = run(["git", *args], cwd=repo)
        assert result.returncode == 0, result.stderr
        return result.stdout.strip()

    git("init", "-q")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.com")
    shutil.copytree(ROOT / "scripts", repo / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    git("config", "core.hooksPath", str(ROOT / ".githooks"))
    secret = repo / "file with spaces.txt"
    secret.write_text("clean")
    git("add", ".")
    git("commit", "-qm", "clean")
    before = git("rev-parse", "HEAD")
    secret.write_text(TOKEN)
    git("add", ".")
    # Changing the working copy must not hide a staged token.
    secret.write_text("clean")
    result = run(["git", "commit", "-qm", "blocked"], cwd=repo)
    assert result.returncode != 0
    assert "file with spaces.txt" in result.stderr and TOKEN not in result.stdout + result.stderr
    git("-c", "core.hooksPath=/dev/null", "commit", "-qm", "synthetic secret")
    secret.unlink()
    git("add", "-u")
    git("commit", "-qm", "remove synthetic secret")
    after = git("rev-parse", "HEAD")
    hook = str(ROOT / ".githooks/pre-push")
    for remote in (before, "0" * 40, "1" * 40):
        result = run([hook], cwd=repo, input=f"refs/heads/main {after} refs/heads/main {remote}\n")
        assert result.returncode != 0
        assert "file with spaces.txt" in result.stderr and TOKEN not in result.stdout + result.stderr
    for local, remote in (("0" * 40, after), (before, "0" * 40), (after, after)):
        assert run([hook], cwd=repo, input=f"refs/heads/main {local} refs/heads/main {remote}\n").returncode == 0
    assert run([hook], cwd=repo, input="malformed\n").returncode != 0

print("PASS: launcher, private key storage, client renders, staged and outgoing token checks")
