#!/usr/bin/env python3
"""Offline delivery checks for agent instructions and workflows (requires chezmoi)."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (".codex/AGENTS.md", ".config/opencode/AGENTS.md", ".config/kilo/AGENTS.md")
WORKFLOWS = ("oss-pr", "improve-prompt", "improve-plan", "improve-package-prompt", "review-project")
WORKFLOW_SOURCES = {
    **{f".agents/skills/{name}/SKILL.md": ROOT / f"dot_agents/skills/{name}/SKILL.md"
       for name in WORKFLOWS},
    **{f".config/opencode/commands/{name}.md": ROOT / f"private_dot_config/opencode/commands/{name}.md"
       for name in WORKFLOWS},
}
UNRELATED = (".zshrc", ".agents/skills/local-only/SKILL.md", ".config/opencode/commands/local-only.md")
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
        assert set(TARGETS) | WORKFLOW_SOURCES.keys() <= set(managed)
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

        for name in UNRELATED:
            target = home / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"Unrelated local file\n")

        workflow_targets = [home / name for name in WORKFLOW_SOURCES]
        for target in workflow_targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            if existing:
                target.write_bytes(b"Previous local workflow\n")

        workflow_args = ["--exclude", "scripts", *map(str, workflow_targets)]
        assert run("diff", *workflow_args)
        run("apply", "--force", *workflow_args)
        for target, source in zip(workflow_targets, WORKFLOW_SOURCES.values()):
            assert target.read_bytes() == source.read_bytes(), target

        assert {p.relative_to(home).as_posix() for p in home.rglob("*") if p.is_file()} == (
            set(TARGETS) | set(UNRELATED) | WORKFLOW_SOURCES.keys()
        )
        before = [target.stat().st_mtime_ns for target in workflow_targets]
        run("apply", *workflow_args)
        assert not run("diff", *workflow_args)
        assert [target.stat().st_mtime_ns for target in workflow_targets] == before
        assert all((home / name).read_bytes() == b"Unrelated local file\n" for name in UNRELATED)
        assert all(target.read_text() == shared for target in targets)

print("PASS: shared instructions and workflows, absent/existing targets, preservation and repeat apply")
