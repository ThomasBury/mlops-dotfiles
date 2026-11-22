#!/usr/bin/env python3
"""Offline bootstrap and editor checks using temporary homes and fake commands."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

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

assert "theme = Gruvbox Material Dark" in (ROOT / "private_dot_config/ghostty/config").read_text().splitlines()

print("PASS: prerequisites, editor installation, skips, retries, and repeat apply")
