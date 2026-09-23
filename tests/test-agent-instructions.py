#!/usr/bin/env python3
"""Offline checks: python3 tests/test-agent-instructions.py (requires chezmoi)."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (".codex/AGENTS.md", ".config/opencode/AGENTS.md", ".config/kilo/AGENTS.md")
shared = (ROOT / ".chezmoitemplates/AGENTS.md").read_text()
chezmoi = shutil.which("chezmoi")
assert chezmoi, "chezmoi is required"

for existing in (False, True):
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        home = base / "home"
        home.mkdir()
        config = base / "chezmoi.toml"
        config.write_text('[data]\nname = "Test"\nemail = "test@example.com"\n')
        env = {
            **os.environ,
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "XDG_CACHE_HOME": str(base / "cache"),
            "XDG_DATA_HOME": str(base / "data"),
            "XDG_STATE_HOME": str(base / "state"),
        }
        command = [
            chezmoi, "--config", str(config), "--source", str(ROOT),
            "--destination", str(home), "--persistent-state", str(base / "chezmoi.db"),
            "--cache", str(base / "cache"), "--refresh-externals=never",
            "--no-tty", "--no-pager", "--use-builtin-diff",
        ]

        def run(*args):
            result = subprocess.run(
                [*command, *args], env=env, capture_output=True, text=True,
            )
            assert result.returncode == 0, result.stderr
            return result.stdout

        targets = [home / name for name in TARGETS]
        for target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            if existing:
                target.write_text("Previous local instructions\n")
        for target in targets:
            assert run("cat", str(target)) == shared

        managed = run("managed", "--path-style", "relative").splitlines()
        assert set(TARGETS) <= set(managed)
        assert "AGENTS.md" not in managed
        assert not any("chezmoitemplates" in name for name in managed)

        paths = [str(target) for target in targets]
        run("apply", "--exclude", "scripts", "--force", *paths)
        for target in targets:
            assert target.read_text() == shared
            assert target.read_text().count(shared) == 1
        assert {p.relative_to(home).as_posix() for p in home.rglob("*") if p.is_file()} == set(TARGETS)
        before = [target.stat().st_mtime_ns for target in targets]
        run("apply", "--exclude", "scripts", *paths)
        assert [target.stat().st_mtime_ns for target in targets] == before
        assert not run("diff", "--exclude", "scripts", *paths)

print("PASS: shared instructions, absent/existing targets, partial exclusion, targeted apply idempotence")
