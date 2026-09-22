#!/usr/bin/env python3
"""Store or rotate the local Context7 key without echoing it."""
import getpass
import os
from pathlib import Path
import sys
import tempfile
import warnings


def main():
    if not sys.stdin.isatty():
        sys.exit("Run this command in your own terminal for a hidden key prompt.")
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        key = getpass.getpass("New Context7 API key (hidden): ")
    if not key.startswith("ctx7sk-") or len(key) <= 7 or any(c.isspace() for c in key):
        sys.exit("Expected a Context7 API key without whitespace; nothing changed.")
    directory = Path.home() / ".config/context7"
    if directory.is_symlink():
        sys.exit("Refusing a symlinked credential directory; nothing changed.")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory.chmod(0o700)
    fd, name = tempfile.mkstemp(dir=directory)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(key + "\n")
        os.replace(name, directory / "api-key")
    finally:
        Path(name).unlink(missing_ok=True)
    print("Key saved with owner-only access. Restart each client's MCP connection.")


if __name__ == "__main__":
    main()
