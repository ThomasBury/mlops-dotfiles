#!/usr/bin/env python3
"""Offline bootstrap, editor and Codex checks using temporary homes and fake commands."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
chezmoi = shutil.which("chezmoi")
assert chezmoi, "chezmoi is required"

with tempfile.TemporaryDirectory() as directory:
    base = Path(directory)
    home = base / "home"
    home.mkdir()
    bins = base / "bin"
    bins.mkdir()
    for command in ("bash", "grep"):
        (bins / command).symlink_to(shutil.which(command))
    config = base / "chezmoi.toml"
    config.write_text('[data]\nname = "Test"\nemail = "test@example.com"\n')
    env = {**os.environ, "HOME": str(home), "PATH": str(bins), "CI": "",
           "CODEX_HOME": str(home / ".codex")}
    common = [chezmoi, "--config", str(config), "--destination", str(home),
              "--persistent-state", str(base / "state.db"), "--cache", str(base / "cache"),
              "--no-tty", "--refresh-externals=never"]

    def fake(command, script):
        path = bins / command
        path.write_text("#!/bin/sh\n" + script)
        path.chmod(0o755)

    def run(*args, source=ROOT):
        return subprocess.run([*common, "--source", str(source), *args],
                              env=env, capture_output=True, text=True)

    # Only the missing runtime library should be handed to apt; no real install.
    fake("dpkg", '[ "$2" != "libatomic1" ]\n')
    fake("apt-get", "exit 0\n")
    fake("sudo", 'printf "%s\\n" "$*" >> "$HOME/apt-calls"\n')
    for command in ("mkdir", "curl"):
        (bins / command).symlink_to(shutil.which(command))
    mise = home / ".local/bin/mise"
    mise.parent.mkdir(parents=True)
    mise.write_text("#!/bin/sh\nexit 0\n")
    mise.chmod(0o755)
    rendered = subprocess.run(
        [*common, "--source", str(ROOT), "execute-template"], env=env,
        input=(ROOT / "run_once_before_10-prereqs.sh.tmpl").read_text(),
        capture_output=True, text=True,
    )
    assert rendered.returncode == 0, rendered.stderr
    result = subprocess.run(["/bin/bash"], input=rendered.stdout, env=env,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (home / "apt-calls").read_text().splitlines() == [
        "apt-get update", "apt-get install -y libatomic1",
    ]

    source = base / "source"
    source.mkdir()
    installer = "run_onchange_after_30-vscode-extensions.sh.tmpl"
    (source / installer).write_text((ROOT / installer).read_text())
    result = run("apply", source=source)
    assert result.returncode == 0 and "skipping" in result.stderr, result.stderr

    fake("code", '''printf '%s\\n' "$*" >> "$HOME/code-calls"
case "$1" in
  --install-extension) [ ! -f "$HOME/fail-install" ] ;;
  --list-extensions) printf 'ms-azuretools.vscode-docker\\nms-azuretools.vscode-containers\\n' ;;
esac
''')
    # Making code available changes the rendered hash; failed installs retry.
    (home / "fail-install").touch()
    result = run("apply", source=source)
    assert result.returncode != 0 and "FAILED to install" in result.stderr
    calls = (home / "code-calls").read_text()
    assert "--install-extension" in calls and "--uninstall-extension" not in calls
    (home / "fail-install").unlink()
    result = run("apply", source=source)
    assert result.returncode == 0, result.stderr
    calls = (home / "code-calls").read_text()
    assert "--uninstall-extension ms-azuretools.vscode-docker" in calls
    assert run("apply", source=source).returncode == 0
    assert (home / "code-calls").read_text() == calls

    # Exercise Ponytail with the real config modifier and fake native Codex commands.
    installer = "run_onchange_after_26-codex-ponytail.sh.tmpl"
    source = base / "ponytail source"
    source.mkdir()
    shutil.copyfile(ROOT / installer, source / installer)
    (source / "dot_codex").mkdir()
    shutil.copyfile(ROOT / "dot_codex/modify_private_config.toml",
                    source / "dot_codex/modify_private_config.toml")
    shared_names = ("ponytail", "ponytail-audit", "ponytail-debt", "ponytail-gain",
                    "ponytail-help", "ponytail-review")
    shared_paths = [str(home / ".agents/skills" / name / "SKILL.md") for name in shared_names]
    shutil.copytree(ROOT / "dot_agents", source / "dot_agents")
    for command in ("jq", "python3"):
        (bins / command).symlink_to(shutil.which(command))
    target = home / ".codex/config.toml"
    target.parent.mkdir(exist_ok=True)
    original = '''model = "keep"
[mcp_servers.other]
command = "keep"
[plugins."other@marketplace"]
enabled = false
[features]
hooks = true
[skills]
include_instructions = false
[[skills.config]]
name = "other-skill"
enabled = false
[[skills.config]]
'''
    original += f'path = {json.dumps(shared_paths[0])}\nenabled = true\n'
    original += '[[skills.config]]\nname = "ponytail"\nenabled = true\n'
    original += '[hook_trust."local-hash"]\ntrusted = true\n'
    target.write_text(original)
    hook_state = home / ".codex/hook-state.json"
    hook_state.write_text('{"local-hash":true}')
    result = run("apply", source=source)
    assert result.returncode == 0 and "skipping" in result.stderr, result.stderr
    baseline = tomllib.loads(target.read_text())
    assert baseline["skills"]["config"][1]["enabled"] is True

    # Use a Python fake to return the CLI's JSON shape and mimic its local writes.
    (home / "fake-codex.py").write_text('''import json, os, sys
from pathlib import Path
home = Path(os.environ["HOME"])
args = sys.argv[1:]
with (home / "codex-calls").open("a") as log:
    log.write(" ".join(args) + "\\n")
if args == ["plugin", "marketplace", "list", "--json"]:
    print(json.dumps({"marketplaces": [{"name": "ponytail"}] if (home / "registered").exists() else []}))
elif args == ["plugin", "marketplace", "add", "DietrichGebert/ponytail"]:
    (home / "registered").touch()
elif args == ["plugin", "list", "--json", "--marketplace", "ponytail"]:
    installed = (home / "installed").exists()
    print(json.dumps({"installed": [{"pluginId": "ponytail@ponytail", "installed": True, "enabled": True}] if installed else [], "available": []}))
elif args == ["plugin", "add", "ponytail@ponytail"]:
    if (home / "fail-plugin").exists():
        sys.exit("plugin installation failed")
    (home / "installed").touch()
    manifest = home / ".codex/plugins/cache/ponytail/ponytail/1.0.0/.codex-plugin/plugin.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text('{"name":"ponytail"}')
    with (home / ".codex/config.toml").open("a") as config:
        config.write('\\n[plugins."ponytail@ponytail"]\\nenabled = true\\n')
else:
    sys.exit("unexpected command: " + repr(args))
''')
    fake("codex", 'exec python3 "$HOME/fake-codex.py" "$@"\n')

    # CI skips even with Codex available; execute directly to avoid recording history.
    rendered = subprocess.run(
        [*common, "--source", str(source), "execute-template"], env=env,
        input=(source / installer).read_text(), capture_output=True, text=True,
    )
    assert rendered.returncode == 0, rendered.stderr
    result = subprocess.run(["/bin/bash"], input=rendered.stdout,
                            env={**env, "CI": "true"}, capture_output=True, text=True)
    assert result.returncode == 0 and "CI detected" in result.stdout
    assert not (home / "codex-calls").exists()

    # Making Codex available changes the script hash; failure must not hide skills.
    (home / "fail-plugin").touch()
    result = run("apply", source=source)
    assert result.returncode != 0 and "plugin installation failed" in result.stderr
    assert tomllib.loads(target.read_text()) == baseline
    (home / "fail-plugin").unlink()
    result = run("apply", source=source)
    assert result.returncode == 0, result.stderr
    data = tomllib.loads(target.read_text())
    assert data["model"] == "keep"
    assert data["mcp_servers"] == baseline["mcp_servers"]
    assert data["plugins"]["other@marketplace"] == {"enabled": False}
    assert data["plugins"]["ponytail@ponytail"] == {"enabled": True}
    assert data["features"] == baseline["features"]
    assert data["hook_trust"] == baseline["hook_trust"]
    assert hook_state.read_text() == '{"local-hash":true}'
    assert data["skills"]["include_instructions"] is False
    entries = data["skills"]["config"]
    assert entries[0] == {"name": "other-skill", "enabled": False}
    assert entries[1] == {"name": "ponytail", "enabled": True}
    assert {entry["path"] for entry in entries[2:]} == set(shared_paths)
    assert len(entries) == 8 and all(entry["enabled"] is False for entry in entries[2:])
    for name in shared_names:
        assert (home / ".agents/skills" / name / "SKILL.md").read_bytes() == (ROOT / "dot_agents/skills" / name / "SKILL.md").read_bytes()
    calls = (home / "codex-calls").read_text()
    assert calls.count("plugin marketplace add DietrichGebert/ponytail\n") == 1
    assert calls.count("plugin add ponytail@ponytail\n") == 2  # failed, then retried
    before = target.read_text()
    assert run("apply", source=source).returncode == 0
    assert (home / "codex-calls").read_text() == calls
    assert target.read_text() == before

    # A changed installer reruns against an existing installation without reinstalling.
    with (source / installer).open("a") as script:
        script.write("\n# Exercise existing installation.\n")
    result = run("apply", source=source)
    assert result.returncode == 0, result.stderr
    calls = (home / "codex-calls").read_text()
    assert calls.count("plugin marketplace add DietrichGebert/ponytail\n") == 1
    assert calls.count("plugin add ponytail@ponytail\n") == 2
    assert target.read_text() == before

    # A disabled or uncached plugin must not introduce new suppression entries.
    for plugin in ('[plugins."ponytail@ponytail"]\nenabled = false\n', ""):
        target.write_text(original + plugin)
        result = run("cat", str(target), source=source)
        assert result.returncode == 0, result.stderr
        assert tomllib.loads(result.stdout)["skills"] == baseline["skills"]
    shutil.rmtree(home / ".codex/plugins")
    target.write_text(original + '[plugins."ponytail@ponytail"]\nenabled = true\n')
    result = run("cat", str(target), source=source)
    assert result.returncode == 0, result.stderr
    assert tomllib.loads(result.stdout)["skills"] == baseline["skills"]

assert "theme = Gruvbox Material Dark" in (ROOT / "private_dot_config/ghostty/config").read_text().splitlines()

print("PASS: prerequisites, editor and Ponytail installs, skips, retries, preservation and repeat apply")
