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
    server = home / ".local/share/context7-mcp/node_modules/.bin/context7-mcp"
    server.parent.mkdir(parents=True)
    server.write_text('''#!/bin/sh
[ "$CONTEXT7_API_KEY" = "$EXPECTED_KEY" ] || exit 2
[ "$PWD" = "$HOME" ] && [ "$#" = 0 ] || exit 3
printf 'fake server OK\\n'
''')
    server.chmod(0o755)
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

    project = base / "project"
    project.mkdir()
    (project / "mise.toml").write_text('[tools]\nnode = "0.0.0"\n')
    result = run(launcher, cwd=project,
                 env={**env, "EXPECTED_KEY": TOKEN, "CONTEXT7_API_KEY": "stale"})
    assert result.returncode == 0, result.stderr
    assert TOKEN not in result.stdout + result.stderr
    assert "fake server OK" in result.stdout
    server.unlink()
    result = run(launcher, env=env)
    assert result.returncode != 0 and "dependencies missing" in result.stderr

    # Render each client from existing settings and check preservation and idempotence.
    chezmoi = shutil.which("chezmoi")
    assert chezmoi, "chezmoi is required"
    config = base / "chezmoi.toml"
    config.write_text('[data]\nname = "Test"\nemail = "test@example.com"\n')
    install_source = base / "install-source"
    packages = install_source / "dot_local/share/context7-mcp"
    packages.mkdir(parents=True)
    for name in ("package.json", "package-lock.json"):
        shutil.copyfile(ROOT / "dot_local/share/context7-mcp" / name, packages / name)
    installer = "run_onchange_after_25-context7-install.sh.tmpl"
    shutil.copyfile(ROOT / installer, install_source / installer)
    npm = home / ".local/share/mise/shims/npm"
    npm.parent.mkdir(parents=True)
    npm.write_text('''#!/bin/sh
[ "$PWD" = "$HOME" ] || exit 2
[ "$*" = "ci --prefix $HOME/.local/share/context7-mcp --ignore-scripts --no-audit --no-fund" ] || exit 3
printf 'installed\\n' >> "$HOME/npm-calls"
''')
    npm.chmod(0o755)
    install_env = {**env, "CI": ""}
    install = [chezmoi, "--config", str(config), "--source", str(install_source),
               "--destination", str(home), "--persistent-state", str(base / "install.db")]
    assert run([*install, "apply"], cwd=project, env=install_env).returncode == 0
    assert run([*install, "apply"], cwd=project, env=install_env).returncode == 0
    assert (home / "npm-calls").read_text() == "installed\n"
    # Verify the documented targeted reinstall also works after a successful apply.
    result = run([*install, "state", "delete", "--bucket=entryState",
                  "--key=" + str(home / "25-context7-install.sh")], env=install_env)
    assert result.returncode == 0, result.stderr
    result = run([*install, "apply"], env=install_env)
    assert result.returncode == 0, result.stderr
    assert (home / "npm-calls").read_text() == "installed\ninstalled\n"
    command = [str(home / ".local/bin/context7-mcp")]
    codex_defaults = {
        "approval_policy": "on-request",
        "approvals_reviewer": "auto_review",
        "sandbox_mode": "workspace-write",
    }
    fixtures = {
        ".codex/config.toml": ('model = "keep"\npersonality = "pragmatic"\n[mcp_servers.context7]\ncommand = "old"\nargs = ["' + TOKEN + '"]\n', "mcp_servers", {"command": command[0]}),
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
        if name == ".codex/config.toml":
            assert {key: data[key] for key in codex_defaults} == codex_defaults
            assert "personality" not in data
        target.write_text(result.stdout)
        assert run(args, env=env).stdout == result.stdout
        # Empty targets must work on a fresh machine too.
        target.unlink()
        result = run(args, env=env)
        assert result.returncode == 0, result.stderr
        if name == ".codex/config.toml":
            data = tomllib.loads(result.stdout)
            assert {key: data[key] for key in codex_defaults} == codex_defaults

    # Keep explicitly chosen approval settings and either kind of sandbox selector.
    target = home / ".codex/config.toml"
    args = [chezmoi, "--config", str(config), "--source", str(ROOT), "--destination", str(home), "cat", str(target)]
    for selector, value in (("sandbox_mode", "read-only"), ("default_permissions", ":read-only")):
        target.write_text(
            'approval_policy = "never"\napprovals_reviewer = "user"\npersonality = "none"\n'
            f'{selector} = "{value}"\n'
        )
        result = run(args, env=env)
        assert result.returncode == 0, result.stderr
        data = tomllib.loads(result.stdout)
        assert data["approval_policy"] == "never"
        assert data["approvals_reviewer"] == "user"
        assert data["personality"] == "none"
        assert data[selector] == value
        assert "sandbox_mode" not in data or selector == "sandbox_mode"

    # Deliver the real launcher and manifests without running workstation installers.
    launcher_target = home / ".local/bin/context7-mcp"
    launcher_target.parent.mkdir(parents=True, exist_ok=True)
    manifest_targets = [home / ".local/share/context7-mcp" / name
                        for name in ("package.json", "package-lock.json")]
    result = run([chezmoi, "--config", str(config), "--source", str(ROOT),
                  "--destination", str(home), "--refresh-externals=never", "apply",
                  "--exclude", "scripts", str(launcher_target),
                  *map(str, manifest_targets)], env=env)
    assert result.returncode == 0, result.stderr
    assert launcher_target.stat().st_mode & 0o111
    assert launcher_target.read_bytes() == (ROOT / "dot_local/bin/executable_context7-mcp").read_bytes()
    for target in manifest_targets:
        assert target.read_bytes() == (ROOT / "dot_local/share/context7-mcp" / target.name).read_bytes()

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
    scanner = ["python3", str(repo / "scripts/check-context7-secrets.py"), "--history"]
    assert run(scanner, cwd=repo).returncode == 0
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
    result = run(scanner, cwd=repo)
    assert result.returncode != 0
    assert "file with spaces.txt" in result.stderr and TOKEN not in result.stdout + result.stderr
    hook = str(ROOT / ".githooks/pre-push")
    for remote in (before, "0" * 40, "1" * 40):
        result = run([hook], cwd=repo, input=f"refs/heads/main {after} refs/heads/main {remote}\n")
        assert result.returncode != 0
        assert "file with spaces.txt" in result.stderr and TOKEN not in result.stdout + result.stderr
    for local, remote in (("0" * 40, after), (before, "0" * 40), (after, after)):
        assert run([hook], cwd=repo, input=f"refs/heads/main {local} refs/heads/main {remote}\n").returncode == 0
    assert run([hook], cwd=repo, input="malformed\n").returncode != 0

print("PASS: launcher, private key storage, client renders, staged and outgoing token checks")
