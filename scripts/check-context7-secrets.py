#!/usr/bin/env python3
"""Reject Context7 tokens in the index or every commit being pushed."""
import json
import subprocess
import sys


PATTERN = r"ctx7sk-[A-Za-z0-9_-]{8,}"


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, check=True).stdout


def scan(*args):
    result = subprocess.run(
        ["git", "grep", "-a", "-l", "-z", "-E", "-e", PATTERN, *args, "--"],
        capture_output=True,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError("Git could not scan content; refusing to continue.")
    return result.stdout.split(b"\0")[:-1]


def main():
    if sys.argv[1] == "--staged":
        paths = set(scan("--cached"))
    elif sys.argv[1] == "--pre-push":
        commits = set()
        for line in sys.stdin:
            _, local, _, remote = line.split()
            if not local.strip("0"):  # Deleting a remote ref sends no content.
                continue
            revision = local
            if remote.strip("0") and subprocess.run(
                ["git", "cat-file", "-e", remote + "^{commit}"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            ).returncode == 0:
                revision = remote + ".." + local
            # New refs (or unknown remote tips): conservatively scan all ancestors.
            commits.update(git("rev-list", revision).decode().splitlines())
        paths = set()
        for commit in commits:
            # git grep prefixes historical filenames with their commit ID.
            paths.update(p.split(b":", 1)[1] for p in scan(commit))
    else:
        raise RuntimeError("Expected --staged or --pre-push.")
    for path in sorted(paths):
        print(json.dumps(path.decode(errors="replace")), file=sys.stderr)
    return bool(paths)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (IndexError, ValueError, RuntimeError, subprocess.CalledProcessError):
        sys.exit("Context7 token check failed; refusing to continue.")
