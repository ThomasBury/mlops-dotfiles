# Contributing / adopting these dotfiles

This repo started as a personal setup, and nothing in it is wired to
one person — so two paths exist: run it for yourself, or change it
here. Both are short.

## Why it's safe to copy

Your identity never enters the repo:

- Git name and email are asked once on first `chezmoi init` and live
  only in your local `~/.config/chezmoi/chezmoi.toml`. See
  [Git identity and private files](README.md#git-identity-and-private-files).
- Machine-only settings belong in `~/.zshrc.local` and
  `~/.gitconfig.local` — unversioned, sourced automatically when
  present.
- `~/.aws` and `~/.azure` are excluded from management entirely
  (`.chezmoiignore`), because that's where credentials live.

So adoption is: fork, swap the repo path, answer two prompts.

## Run it for yourself

1. Fork `ThomasBury/mlops-dotfiles` on GitHub.
2. In the README one-liner, replace `ThomasBury/mlops-dotfiles` with
   `YourName/mlops-dotfiles` and run it.
3. Trim the toolchain to what you use:

   ```bash
   cd ~/.local/share/chezmoi/private_dot_config/mise
   $EDITOR config.toml      # keep only your tools
   rm mise.lock             # stale until regenerated
   mise up && mise lock     # reinstall + rewrite the lockfile
   chezmoi apply
   git add -A && git commit -m "chore: trim toolchain to my needs"
   ```

## Make a change

Edit the source, never the rendered copy — a rendered file is
overwritten on the next `chezmoi apply`:

```bash
chezmoi edit ~/.zshrc    # opens dot_zshrc in the source dir
chezmoi diff             # what would change
chezmoi apply            # render into $HOME
git add -A && git commit -m "..."
```

## Add or bump a tool

```bash
cd ~/.local/share/chezmoi/private_dot_config/mise
$EDITOR config.toml      # add or change the tool line
mise up && mise lock     # install and refresh mise.lock
chezmoi apply            # re-installs via the onchange script
git add -A && git commit -m "feat: add some-tool"
```

## Test before you push

```bash
tests/test-zsh.sh                # fast: syntax, isolated load, bindings
tests/docker-bootstrap.sh        # slow: full fresh-machine E2E in Docker
```

CI runs the fast suite on every push and scans history with gitleaks.
Run the Docker one before touching the `dot_zshrc` startup order or
the setup scripts — a workstation and a fresh container load
differently.

## What never lands in this repo

- Secrets: API keys, tokens, private keys. gitleaks scans every push.
- Personal data: names, emails, work hostnames. Those go in your local
  `~/.config/chezmoi/chezmoi.toml` or the `.local` override files.

If you catch yourself typing your email into a template, stop — that
value is a `chezmoi init` prompt answer, not repo content.

## House style

- Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`),
  one topic per commit.
- Shell scripts use `set -Eeuo pipefail` and stay idempotent; the
  prereqs script owns the Linux/macOS judgment calls, don't add more.
