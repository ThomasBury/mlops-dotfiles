# mlops-dotfiles

Reproducible Linux workstation setup for Python, ML/MLOps, Kubernetes,
Terraform and cloud tooling — managed with
[chezmoi](https://www.chezmoi.io/), [mise](https://mise.jdx.dev/) and Zsh.

One command installs everything, then asks for your git name and email.
Your personal data never lands in this repository.

## Quick start

On a fresh Debian/Ubuntu machine:

```bash
mkdir -p -m 700 ~/.local/bin && \
sh -c "$(curl -fsLS get.chezmoi.io)" -- -b "$HOME/.local/bin" \
    init --apply ThomasBury/mlops-dotfiles
```

What happens, in order:

1. The script downloads chezmoi into `~/.local/bin`.
2. chezmoi clones this repository to `~/.local/share/chezmoi`.
3. It asks you twice: "Git user name" and "Git email". Type your answers.
4. It runs the setup scripts: base packages via `apt` (sudo), then mise,
   then all 26 pinned CLI tools, then Oh My Zsh and three Zsh plugins.
5. It renders `~/.zshrc` and `~/.gitconfig` (your answers go into the
   gitconfig). Start a new shell and you're done.

First run takes a few minutes — the toolchain is the slow part.

## Personal info: what gets asked, where it goes, how to change it

**When:** only once, during `chezmoi init`, at step 3 above.

**Where it lives:** in `~/.config/chezmoi/chezmoi.toml`, a file
chezmoi creates and keeps at `0600` permissions. Nothing in this
repository contains your name or email; `dot_gitconfig.tmpl` reads them
from that local file when it renders `~/.gitconfig`, so there is nowhere
else the values could come from — and nowhere in the repo to commit
them. CI additionally runs
[gitleaks](https://github.com/gitleaks/gitleaks) over the full history
on every push to guard against committed secrets.

**To change it later**, edit the local config and re-render:

```bash
chezmoi edit-config    # opens ~/.config/chezmoi/chezmoi.toml in $EDITOR
chezmoi apply          # re-renders ~/.gitconfig with the new values
```

Setup on a machine without a prompt (CI, Docker) works the same way —
pre-seed the config file, then run `chezmoi apply` instead of `init --apply`.
Because chezmoi only asks for a value when it's missing
(`promptStringOnce`), it will never re-ask you on later
`chezmoi update --init` runs; it reuses your saved answers.

## What you get

| Layer | Managed by | Contents |
|-------|------------|----------|
| Shell | chezmoi | `.zshrc` (Oh My Zsh + fzf-tab, autosuggestions, syntax-highlighting), `.gitconfig` |
| Prompt | Starship | defaults until you drop a config at `~/.config/starship.toml` — Starship picks it up automatically, nothing in the shell is involved |
| Toolchain | mise | 26 pinned CLIs: python, uv, nvim, fzf, ripgrep, kubectl, helm, k9s, terraform, opentofu, aws-cli, azure-cli, lazygit, atuin, zoxide, … |
| Plugins | chezmoi externals | cloned once, floating until you run `chezmoi apply --refresh-externals` |
| Identity | `chezmoi init` prompt | stored in `~/.config/chezmoi/chezmoi.toml`, never committed |

CLI tool versions live in `mise.lock` and install with
`mise install --locked`, so two machines run the same tools. Oh My Zsh
and the Zsh plugins are not pinned: fresh machines get their latest
state, and you pick when to refresh. The shell keeps standard
Emacs/readline key bindings (Ctrl-R belongs to
[Atuin](https://atuin.sh/)).

Python development tools (ruff, ty, pytest, ipython, …) are
deliberately not pinned globally: their versions belong to each
project, where `uv` picks them up from `pyproject.toml`. Run a tool on
demand with `uvx ruff check`, or install a stable user-level shim with
`uv tool install ruff`.

## Requirements

Debian/Ubuntu Linux. The bootstrap installs base packages via `apt`
with sudo; everything after that is user-level and touches no system
files.

## Daily use

```bash
chezmoi edit ~/.zshrc        # edit the source of a managed file
chezmoi apply                # render source state into $HOME
chezmoi diff                 # preview what would change
chezmoi update               # pull the repo and apply
```

Machine-specific extras go in `~/.zshrc.local` (unversioned, sourced
automatically if present).

`~/.aws` and `~/.azure` are never managed: their contents are
machine-specific and interactive (`aws configure`, `az login`) and may
include credentials. These paths are excluded via `.chezmoiignore`, so
no future change to this repo can accidentally pull them into the
managed set.

## How it works

Full details live in the
[chezmoi docs](https://www.chezmoi.io/); here is the model that
matters for this repo. There are no symlinks. `~/mlops-dotfiles`
is the master copy, and `chezmoi apply` renders it into `$HOME`
by writing real files:

```text
~/mlops-dotfiles (source, in git)          $HOME (rendered copy)
  dot_zshrc           ── chezmoi apply ──▸  ~/.zshrc
  dot_gitconfig.tmpl  ── chezmoi apply ──▸  ~/.gitconfig
                                            + name/email read from
                                            ~/.config/chezmoi/chezmoi.toml
```

`$HOME` is disposable: from a clone of this repo, `chezmoi init`
and `apply` rebuild every managed file. Editing a rendered file
directly works for a moment, and the next `apply` overwrites it.
Edit the source instead.

The filenames are the wiring:

| Prefix/suffix | Meaning | Example |
|---|---|---|
| `dot_` | becomes a dotfile | `dot_zshrc` → `~/.zshrc` |
| `.tmpl` | run the template engine first; `.name`/`.email` come from your `chezmoi init` answers | `dot_gitconfig.tmpl` |
| `private_` | restrictive permissions on the target | `private_dot_config/` |
| `run_once_*` / `run_onchange_*` | scripts: first runs once per machine; second re-runs only when its content (including the hashed `mise` config) changes | `run_once_before_10-prereqs.sh.tmpl` |

Where to edit what:

| Change | Edit | Then |
|---|---|---|
| Shell (aliases, plugins, bindings) | `dot_zshrc` | `chezmoi apply`, commit |
| Git identity, machine values | `chezmoi edit-config` | `chezmoi apply` |
| Machine-only settings | `~/.zshrc.local` / `~/.gitconfig.local` (unversioned) | reload shell / nothing to apply |
| Tool versions | `mise` `config.toml` (see Updating tools) | `mise up && mise lock`, commit |

## Updating tools

```bash
# CLI tools (pinned in mise.lock)
cd "$(chezmoi source-path)/private_dot_config/mise"
mise up && mise lock
chezmoi apply
# commit the changed config.toml / mise.lock

# Oh My Zsh + Zsh plugins (externals, manual refresh)
chezmoi apply --refresh-externals
```

## Testing

```bash
tests/test-zsh.sh
```

This runs a syntax check, loads the config in an isolated `ZDOTDIR`,
verifies key bindings, and checks that every tool resolves through
mise. CI runs a chezmoi apply, a zsh syntax check and an interactive
load test on every push; it skips the 26-tool install. Secrets are
scanned by gitleaks over the full commit history.

### Full end-to-end bootstrap test (local Docker, not CI)

Simulates a fresh Ubuntu 24.04 machine inside a container and runs the
real bootstrap (apt packages, mise, all 26 pinned tools, Oh My Zsh +
plugins), then the full test suite. Kept out of GitHub Actions because
the toolchain install would blow the runners' network/API limits on
every push.

```bash
tests/docker-bootstrap.sh          # cached: mise downloads persist between runs
tests/docker-bootstrap.sh --fresh  # cold: wipe caches, full re-download
```

You need Docker and network access. Set `GITHUB_TOKEN` (or run
`gh auth token`) to avoid GitHub API rate limits while the toolchain
installs. The first cold run takes a few minutes.

## Troubleshooting

- **The toolchain install hits GitHub rate limits.** Export a token
  first: `export GITHUB_TOKEN="$(gh auth token)"`.
- **mise refuses to read the config.** It distrusts config files it
  hasn't seen before; the setup script already runs
  `mise trust ~/.config/mise/config.toml` — re-run it if you reset
  `~/.local/share/mise`.
- **I answered the prompts wrong.** Fix it with
  `chezmoi edit-config && chezmoi apply` (see the personal info
  section above).

## Repository layout

```text
.chezmoi.toml.tmpl                    # prompts for git name/email on init
.chezmoiexternal.toml                 # Oh My Zsh + plugins (refreshPeriod = 0)
dot_zshrc                             # → ~/.zshrc
dot_gitconfig.tmpl                    # → ~/.gitconfig (identity from .data)
private_dot_config/
└── mise/{config.toml,mise.lock}      # → ~/.config/mise/
run_once_before_10-prereqs.sh.tmpl    # apt base packages + mise binary
run_onchange_after_20-mise-install.sh.tmpl  # re-installs tools on config change
tests/test-zsh.sh                     # full local test suite
tests/docker-bootstrap.sh             # local Docker fresh-machine E2E (not CI)
```

## License

[MIT](LICENSE)
