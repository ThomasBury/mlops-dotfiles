# mlops-dotfiles

This repository reproduces one Debian/Ubuntu development environment across
machines. It sets up the shell, command-line tools, editors, terminal, font,
and assistant integrations so you do not have to rebuild them by hand or let
tool versions drift between machines.

[chezmoi](https://www.chezmoi.io/) manages the files,
[mise](https://mise.jdx.dev/) installs the pinned toolchain, and Zsh provides
the shell.

## Contents

- [Install](#install)
- [What you get](#what-you-get)
- [Daily use](#daily-use)
  - [Make a shared change](#make-a-shared-change)
  - [Refresh another machine](#refresh-another-machine)
- [Details](#details)
  - [Git identity and private files](#git-identity-and-private-files)
  - [Context7 setup](#context7-setup)
  - [Optional VS Code MCP servers](#optional-vs-code-mcp-servers)
  - [Ghostty theme](#ghostty-theme)
  - [Shared agent instructions](#shared-agent-instructions)
  - [Shared agent workflows](#shared-agent-workflows)
  - [How installation works](#how-installation-works)
  - [How managed files work](#how-managed-files-work)
  - [Updating tools](#updating-tools)
- [Testing](#testing)
  - [Full bootstrap test](#full-bootstrap-test)
- [Troubleshooting](#troubleshooting)
- [Remove chezmoi](#remove-chezmoi)
- [Repository layout](#repository-layout)
- [License](#license)

## Install

The supported path is Debian or Ubuntu with `apt` and sudo. macOS is not
supported. On Linux without `apt-get`, install your distribution's equivalents
of these base packages first: `ca-certificates`, `curl`, `fontconfig`, `git`,
`libatomic1`, `unzip`, `xz-utils`, and `zsh`. This list comes from the
[prerequisite script](run_once_before_10-prereqs.sh.tmpl).

Back up any existing managed files, especially `~/.zshrc` and
`~/.gitconfig`, before installing. `chezmoi init --apply` can replace them
without creating backups.

Run this on a fresh machine:

```bash
mkdir -p -m 700 ~/.local/bin && \
sh -c "$(curl -fsLS https://get.chezmoi.io)" -- -b "$HOME/.local/bin" \
    init --apply ThomasBury/mlops-dotfiles
```

The installer asks for your Git user name and email. Sudo may also ask for
your password while `apt` installs base packages. A cold install takes
10–20 minutes or longer because mise downloads the full toolchain.

VS Code extensions are skipped when `code` is absent, and the font install
is skipped when `fc-cache` is absent. Install
[Ghostty](https://ghostty.org/docs/install/binary) and
[Codex CLI](https://developers.openai.com/codex/cli/) separately; both are
prerequisites for their integrations.

If you install VS Code later, run `chezmoi apply` once `code` is on your
`PATH`. Failed extension installs stop the apply; run it again to retry.

When installation finishes, start the configured shell:

```bash
exec zsh
```

Forking this for your own machine? See [CONTRIBUTING.md](CONTRIBUTING.md) for
what to change.

## What you get

| Layer | Managed by | Contents |
|---|---|---|
| Shell | chezmoi | Zsh, Git, Oh My Zsh, and three Zsh plugins |
| Prompt | Starship | Default prompt with optional local configuration |
| Toolchain | mise | Locked command-line tool versions |
| Editor | chezmoi and `code` | VS Code settings, MCP definitions, flags, and extensions |
| Terminal | chezmoi | Ghostty font and Gruvbox Material Dark theme |
| Font | install script | Checksum-verified JetBrainsMono Nerd Font |
| Assistants | chezmoi | Context7, shared instructions and skills, and VS Code native MCP |
| Identity | chezmoi prompt | Local Git name and email |

## Daily use

Chezmoi reads managed files from your local checkout, including uncommitted edits.
Commit and push the source changes when you want to share them with another
machine.

### Make a shared change

For a Zsh change, open the source and check the edit before applying it.

```bash
cd "$(chezmoi source-path)"
chezmoi edit ~/.zshrc
zsh -n dot_zshrc
git diff -- dot_zshrc
chezmoi diff ~/.zshrc
```

`git diff` shows your source edits. `chezmoi diff` shows what would change in
your home directory. If the preview looks right, apply just the file you edited.

```bash
chezmoi apply ~/.zshrc
```

Open a fresh Zsh session and check the behavior. Stage the source file with
`git add -- dot_zshrc` and commit the change.

### Refresh another machine

On a machine with a clean checkout, pull the latest commits and preview the
update.

```bash
chezmoi update --apply=false
chezmoi status
chezmoi diff
```

In `chezmoi status`, `R` marks a setup script that a full apply would run. After
reviewing the output, run `chezmoi apply`. Plain `chezmoi update` pulls and
applies in one step.

## Details

### Git identity and private files

Chezmoi asks for your Git name and email once, during `chezmoi init`. It
saves them in `~/.config/chezmoi/chezmoi.toml` with `0600` permissions.
`dot_gitconfig.tmpl` reads that local file when it creates
`~/.gitconfig`; your answers are not stored in this repository.

To change your name or email later:

```bash
chezmoi edit-config    # opens ~/.config/chezmoi/chezmoi.toml in $EDITOR
chezmoi apply          # re-renders ~/.gitconfig with the new values
```

For a non-interactive machine, create the config file first and run
`chezmoi init --source <repo> --apply`. The
[Docker test](tests/docker/entrypoint.sh) and
[CI workflow](.github/workflows/test.yml) use this approach. Chezmoi only asks
when a saved answer is missing, so `chezmoi update --init` reuses your
answers.

Put machine-specific shell and Git settings in `~/.zshrc.local` and
`~/.gitconfig.local`. Zsh and Git load these unversioned files after the shared
settings when present, and `chezmoi apply` leaves them alone.

`~/.aws` and `~/.azure` are never managed. Their contents are
machine-specific, may include credentials, and belong to interactive setup
such as `aws configure` and `az login`. `.chezmoiignore` excludes both
directories.

GitHub Actions runs
[gitleaks](https://github.com/gitleaks/gitleaks) over the full history on
every push.

### Context7 setup

Codex, OpenCode V2, Kilo CLI, the Kilo extension, and VS Code native MCP use
`~/.local/bin/context7-mcp`. The launcher reads
`~/.config/context7/api-key` and passes the key through
`CONTEXT7_API_KEY`. It adds mise's shims to `PATH`, so desktop clients can
find Node without an interactive shell, and runs from your home directory
so workspace settings do not select its runtime. The MCP package is pinned
to `4.1.1`; its dependency tree is recorded in a committed npm lockfile.
The setup installs it with `npm ci` under `~/.local/share/context7-mcp`.
Only the package manifest and lockfile are managed; `node_modules` stays local.

After applying the dotfiles, run this from the repository in your own
terminal:

```bash
python3 scripts/set-context7-key.py
```

The prompt hides your input. It stores the key with `0600` permissions
inside an owner-only (`0700`) directory. Never paste the key into an
assistant or a shell command. The file and the old Context7 CLI credential
store are excluded from chezmoi and Git.

To rotate the key, run the same command, then restart Context7 in each client
(`opencode reload` reloads OpenCode V2). Revoke exposed keys in the
[Context7 dashboard](https://context7.com/dashboard); deleting a local copy
does not revoke it.

The OpenCode, Kilo and Codex `modify_` templates update their Context7 entries.
They preserve unrelated settings. Rendering accepts JSONC where supported,
normalizes formatting and drops comments.
The Kilo CLI and VS Code extension share `~/.config/kilo/kilo.jsonc`.
Any legacy Kilo `mcp_settings.json` in VS Code's `globalStorage` is local
editor state.
Chezmoi manages the full VS Code user MCP file, which declares GitHub and
Context7.

Enable this repository's local checks after cloning:

```bash
git config --local core.hooksPath .githooks
python3 tests/test-context7.py
```

If you already use a custom hooks directory, integrate these checks there
instead of replacing it. The pre-commit hook checks indexed content; pre-push
checks every outgoing commit, including secrets deleted by a later commit.
New refs or unknown remote tips conservatively scan all reachable history.
Matches report filenames only. These checks detect literal Context7 tokens;
they are local and can be bypassed. CI runs the same scanner against the full
checked-out history, alongside Gitleaks for other secret formats. CI runs
after upload.

If the installed Context7 dependencies are removed, reset just its installer
and apply again:

```bash
chezmoi state delete --bucket=entryState --key="$HOME/25-context7-install.sh"
chezmoi apply
```

For a live check, restart each client's Context7 connection and ask it to
resolve the Python library, then query its documentation for reading a UTF-8
file. Repeat in VS Code launched from the desktop, for both native MCP and
Kilo. The offline test uses a dummy key and fake npm/server commands. It does
not validate account access or the editor UI.

### Optional VS Code MCP servers

Add MarkItDown, DuckDB, or Firecrawl to `.vscode/mcp.json` in a project that
uses them. Copy the server entries you need and the matching inputs.

```json
{
  "servers": {
    "markitdown": {
      "type": "stdio",
      "command": "uvx",
      "args": ["markitdown-mcp"],
      "gallery": true
    },
    "duckdb": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-server-duckdb", "--db-path", "${input:duckdb_db_path}"],
      "gallery": true
    },
    "firecrawl": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "firecrawl-mcp@latest"],
      "env": {
        "FIRECRAWL_API_KEY": "${input:firecrawl_api_key}"
      },
      "gallery": true
    }
  },
  "inputs": [
    {
      "id": "duckdb_db_path",
      "type": "promptString",
      "description": "Path to the DuckDB database file (e.g., /path/to/database.duckdb)",
      "password": false
    },
    {
      "id": "firecrawl_api_key",
      "type": "promptString",
      "description": "Firecrawl API Key (get from https://www.firecrawl.dev/app/api-keys)",
      "password": true
    }
  ]
}
```

### Ghostty theme

The managed config selects `Gruvbox Material Dark` and the installed
JetBrainsMono Nerd Font. After installing Ghostty separately, check that the
theme is available:

```bash
ghostty +list-themes
```

Find `Gruvbox Material Dark`, then reload Ghostty's configuration or reopen
the terminal after `chezmoi apply`. Ghostty
[bundles its themes](https://ghostty.org/docs/features/theme), so Gogh is
unnecessary.

### Shared agent instructions

Edit [.chezmoitemplates/AGENTS.md](.chezmoitemplates/AGENTS.md) to change the
engineering defaults for all three agents. Chezmoi's
[shared templates](https://www.chezmoi.io/user-guide/templating/) render the
same text into these native instruction files:

| Agent | Global destination |
|---|---|
| [Codex CLI/editor](https://developers.openai.com/codex/guides/agents-md/) | `~/.codex/AGENTS.md` |
| [OpenCode V2 CLI/editor](https://opencode.ai/v2/docs/instructions) | `~/.config/opencode/AGENTS.md` |
| [Kilo CLI/editor](https://kilo.ai/docs/customize/custom-instructions) | `~/.config/kilo/AGENTS.md` |

The three `AGENTS.md.tmpl` files only include that shared template; edit the
shared text rather than the wrappers or installed copies. The template
directory itself does not deploy into your home.

Global instructions describe reusable preferences. Keep repository commands,
architecture, and exceptions in that project's `AGENTS.md`. The shared text
explicitly defers to project conventions because agents load instructions in
different orders. Stack defaults are conditional; they do not request tool
installation or migration. CodeRabbit and unmanaged agents are outside this setup.

To activate only these instructions, run the following from this repository.
First, back up existing destinations locally and preview the changes:

```bash
agent_source="$PWD"
agent_backup="$(mktemp -d "$HOME/agent-instructions-backup.XXXXXX")"
for relative in .codex/AGENTS.md .config/opencode/AGENTS.md .config/kilo/AGENTS.md; do
    if [ -f "$HOME/$relative" ]; then
        mkdir -p "$agent_backup/$(dirname "$relative")"
        cp -p "$HOME/$relative" "$agent_backup/$relative"
    fi
done
echo "Instruction backups: $agent_backup"
chezmoi --source "$agent_source" --refresh-externals=never --no-pager diff \
    --exclude scripts ~/.codex/AGENTS.md \
    ~/.config/opencode/AGENTS.md ~/.config/kilo/AGENTS.md
```

After reviewing the diff, apply those same three files and check for an empty
diff. These commands exclude scripts and disable external refresh:

```bash
mkdir -p ~/.codex ~/.config/opencode ~/.config/kilo
chezmoi --source "$agent_source" --refresh-externals=never apply \
    --exclude scripts ~/.codex/AGENTS.md \
    ~/.config/opencode/AGENTS.md ~/.config/kilo/AGENTS.md
chezmoi --source "$agent_source" --refresh-externals=never --no-pager diff \
    --exclude scripts ~/.codex/AGENTS.md \
    ~/.config/opencode/AGENTS.md ~/.config/kilo/AGENTS.md
```

Start a fresh session in each CLI and editor integration to load the files.
For a smoke check, ask each agent to summarize its global engineering defaults
and name the source file. Then use a scratch project whose `AGENTS.md` says
"For this project, explain changes in French." Start another fresh session
there and ask which language it should use and why. It should retain the
global defaults while following the project's language instruction. Codex's
`AGENTS.override.md`, if present, takes precedence over its global `AGENTS.md`.

The offline check verifies delivery and repeatable applies; this manual smoke
check verifies that each installed client loads the instructions and respects
project exceptions. This setup uses the standard configuration locations.

### Shared agent workflows

Edit the [shared skills](dot_agents/skills/) in one place. Codex and Kilo
discover them in `~/.agents/skills/`. The [OpenCode wrappers](private_dot_config/opencode/commands/)
load the same skills from the current conversation and pass along any arguments.

| Workflow | Codex example | OpenCode and Kilo example |
| --- | --- | --- |
| Deliver an OSS PR | `$oss-pr` | `/oss-pr` |
| Release after maintainer merge | `$oss-pr release 42` | `/oss-pr release 42` |
| Improve a task prompt | `$improve-prompt Review the import errors` | `/improve-prompt Review the import errors` |
| Improve the plan in this conversation | `$improve-plan` | `/improve-plan` |
| Improve a package request | `$improve-package-prompt Clarify the export API` | `/improve-package-prompt Clarify the export API` |
| Review a project | `$review-project Focus on installation` | `/review-project Focus on installation` |

To activate only these workflows, run the following in Bash from this repository.
Back up any existing copies and preview the ten targets.

```bash
workflow_source="$PWD"
workflow_backup="$(mktemp -d "$HOME/agent-workflows-backup.XXXXXX")"
workflow_targets=()
for name in oss-pr improve-prompt improve-plan improve-package-prompt review-project; do
    workflow_targets+=("$HOME/.agents/skills/$name/SKILL.md")
    workflow_targets+=("$HOME/.config/opencode/commands/$name.md")
done
for target in "${workflow_targets[@]}"; do
    if [ -e "$target" ] || [ -L "$target" ]; then
        backup="$workflow_backup/${target#"$HOME/"}"
        mkdir -p "$(dirname "$backup")" && cp -pP "$target" "$backup"
    fi
done
echo "Workflow backups: $workflow_backup"
chezmoi --source "$workflow_source" --refresh-externals=never --no-pager diff \
    --exclude scripts "${workflow_targets[@]}"
```

After confirming the backups and reviewing the preview, apply the same files
in the same shell. The final diff should be empty. Start fresh agent sessions
to pick up the workflows.

```bash
for target in "${workflow_targets[@]}"; do
    mkdir -p "$(dirname "$target")"
done
chezmoi --source "$workflow_source" --refresh-externals=never apply \
    --exclude scripts "${workflow_targets[@]}"
chezmoi --source "$workflow_source" --refresh-externals=never --no-pager diff \
    --exclude scripts "${workflow_targets[@]}"
```

### How installation works

The install command performs these steps in order:

1. Downloads chezmoi into `~/.local/bin`.
2. Clones this repository to `~/.local/share/chezmoi`.
3. Asks for your Git user name and email.
4. Renders and runs `run_once_before_10-prereqs.sh.tmpl`, which installs the
   base `apt` packages and mise.
5. Writes the managed files into `$HOME`, including the shell and Git
   configuration, mise configuration, VS Code settings, Ghostty font and theme,
   Oh My Zsh, and three Zsh plugins.
6. Runs four numbered `run_onchange_after` scripts. They install the locked
   toolchain, locked Context7 dependencies, VS Code extensions when `code` is
   available, and JetBrainsMono Nerd Font when `fc-cache` is available.
7. Leaves the files ready for `exec zsh`. To make Zsh your login shell, run
   `chsh -s "$(command -v zsh)"`, then sign out and back in.

The bootstrap configures VS Code, Ghostty and Codex but does not install them.

### How managed files work

The full model is documented in the
[chezmoi docs](https://www.chezmoi.io/). This repository uses no symlinks.
The source directory (by default `~/.local/share/chezmoi`) is the master
copy. `chezmoi apply` renders it into `$HOME` as real files:

```text
source dir (default ~/.local/share/chezmoi)      $HOME (rendered copy)
  dot_zshrc                    ── chezmoi apply ──▸  ~/.zshrc
  dot_gitconfig.tmpl           ── chezmoi apply ──▸  ~/.gitconfig
                                                     + name/email read from
                                                     ~/.config/chezmoi/chezmoi.toml
  dot_vscode/argv.json.tmpl    ── chezmoi apply ──▸  ~/.vscode/argv.json
  private_dot_config/…         ── chezmoi apply ──▸  ~/.config/…
```

A clone plus `chezmoi init` and `chezmoi apply` can rebuild every managed file.
For a file managed in full, such as `~/.zshrc`, edit the source. Applying it
can overwrite edits made to the installed file.

A `modify_` template reads the installed file and updates selected settings.
The Codex configuration template defaults to **Approve for me** with the
`workspace-write` sandbox. It fills in missing approval and sandbox settings,
respects existing selections including named permission profiles, and removes
the obsolete `personality = "pragmatic"` setting. Project trust stays local.

Starship uses its defaults until you add `~/.config/starship.toml`, which it
reads automatically.

The filename prefixes connect source files to their targets:

| Prefix or suffix | Meaning | Example |
|---|---|---|
| `dot_` | Becomes a dotfile | `dot_zshrc` → `~/.zshrc` |
| `.tmpl` | Renders a template before writing or running it | `dot_gitconfig.tmpl` reads your Git identity |
| `private_` | Gives the target restrictive permissions | `private_dot_config/` |
| `run_once_*` / `run_onchange_*` | Runs once, or again when content changes, including the hashed mise config | `run_once_before_10-prereqs.sh.tmpl` |

Where to make each change:

| Change | Edit | Then |
|---|---|---|
| Global agent instructions | `.chezmoitemplates/AGENTS.md` | [Targeted apply](#shared-agent-instructions), fresh sessions |
| Shell aliases, plugins, bindings | `dot_zshrc` | `chezmoi apply`, commit |
| Git identity and machine values | `chezmoi edit-config` | `chezmoi apply` |
| Machine-only settings | `~/.zshrc.local` / `~/.gitconfig.local` | Reload the shell |
| Tool versions | `private_dot_config/mise/config.toml` (see [Updating tools](#updating-tools)) | `mise upgrade --local`, `chezmoi apply`, commit |
| VS Code settings and MCP | `private_dot_config/Code/User/` | `chezmoi apply`, commit |
| VS Code extensions | `EXTENSIONS` in `run_onchange_after_30-vscode-extensions.sh.tmpl` | `chezmoi apply` |
| Ghostty config | `private_dot_config/ghostty/config` | `chezmoi apply`, commit |
| Nerd Font version | `VERSION` and `SHA256` in `run_onchange_after_40-nerd-font.sh.tmpl` | `chezmoi apply` |

### Updating tools

CLI versions live in `mise.lock` and install with
`mise install --locked`. Azure CLI also has a Python dependency lock under
`private_dot_config/mise/dot_mise/locks/azure/`. Keep the generated dependency
files with `mise.lock` when updating Azure CLI. Run
`mise lock --global --bump azure` against the applied mise config, then copy
the updated `mise.lock` and the referenced `.mise/locks/azure/` directory back
to the managed source paths. Oh My Zsh and its three plugins come from
commit-specific archives with checksums in `.chezmoiexternal.toml`.

Python development tools such as ruff, ty, pytest, and IPython are not pinned
globally. Their versions belong to each project, where `uv` reads
`pyproject.toml`. Run a tool on demand with `uvx ruff check`, or install a
stable user-level shim with `uv tool install ruff`.

The shell keeps standard Emacs/readline key bindings. Ctrl-R belongs to
[Atuin](https://atuin.sh/).

```bash
# CLI tools (mise upgrade also updates the existing mise.lock)
cd "$(chezmoi source-path)/private_dot_config/mise"
mise upgrade --local
chezmoi apply
# commit the changed config.toml / mise.lock

# Oh My Zsh and Zsh plugins (review new commits and update URLs and checksums)
$EDITOR "$(chezmoi source-path)/.chezmoiexternal.toml"
chezmoi apply

# Context7 (edit the exact package version, then refresh its dependency lock)
cd "$(chezmoi source-path)/dot_local/share/context7-mcp"
$EDITOR package.json
npm install --package-lock-only --ignore-scripts --no-audit --no-fund
chezmoi apply
# commit package.json and package-lock.json together

# VS Code extensions
$EDITOR "$(chezmoi source-path)/run_onchange_after_30-vscode-extensions.sh.tmpl"
chezmoi apply

# Nerd Font (bump VERSION and SHA256 together)
$EDITOR "$(chezmoi source-path)/run_onchange_after_40-nerd-font.sh.tmpl"
chezmoi apply
```

## Testing

Run the offline setup checks (Python 3.11+, Git, and chezmoi required):

```bash
python3 tests/test-context7.py
python3 tests/test-agent-instructions.py
python3 tests/test-installers.py
```

CI runs all three checks. The agent delivery check covers fresh and existing
instruction and workflow files, unrelated file preservation, template
exclusion, and an empty diff after a second targeted apply.
The installer check covers prerequisites, optional editor detection,
installation failure and retry, and repeated applies.

For shell checks:

```bash
tests/test-zsh.sh
```

This checks Zsh syntax, loads the configuration in an isolated `ZDOTDIR`,
verifies key bindings, checks tool paths through mise, and runs Node and npm
to catch missing runtime libraries. The fast CI workflow applies the dotfiles,
checks Zsh syntax, and loads an interactive shell on each push and pull
request.

For a hands-on check in a clean Ubuntu container, follow the
[manual verification guide](tests/manual-verification.md).

### Full bootstrap test

The [bootstrap workflow](.github/workflows/bootstrap.yml) runs the cold
install in an Ubuntu 26.04 container when toolchain inputs change. It installs
the `apt` prerequisites, mise tools, Context7, the shell archives, and the Nerd
Font. It applies the same dotfiles again, checks that chezmoi has no pending
changes, and verifies the installed runtime versions and Azure dependency
lock.

```bash
tests/docker-bootstrap.sh          # cached: mise downloads persist between runs
tests/docker-bootstrap.sh --fresh  # cold: run without the cache or tool volumes
```

You need Docker and network access. `GITHUB_TOKEN` avoids GitHub API rate
limits while the toolchain installs. If `gh` is authenticated, the script
can read the token from `gh auth token`. A cold run takes 10–20 minutes or
longer.

## Troubleshooting

- **The toolchain install hits GitHub rate limits.** Export a token first:
  `export GITHUB_TOKEN="$(gh auth token)"`.
- **mise refuses to read the config.** It distrusts config files it has not
  seen before. The setup script runs
  `mise trust ~/.config/mise/config.toml`; run it again if you reset
  `~/.local/share/mise`.
- **Wrong answer to a prompt.** Fix it with
  `chezmoi edit-config && chezmoi apply`. See
  [Git identity and private files](#git-identity-and-private-files).
- **Rerun unchanged prerequisites.** `chezmoi apply --force` suppresses
  prompts but does not reset script history. Run
  `chezmoi state delete-bucket --bucket=scriptState`, then `chezmoi apply`.
  This resets all `run_once` scripts.

## Remove chezmoi

Chezmoi leaves no daemons behind. To detach it, delete the source directory,
config directory, and binary:

```bash
rm -rf ~/.local/share/chezmoi ~/.config/chezmoi ~/.local/bin/chezmoi
```

Everything chezmoi wrote remains as plain files, including `~/.zshrc`,
`~/.gitconfig`, `~/.config/mise`, `~/.config/Code`,
`~/.config/ghostty`, `~/.vscode/argv.json`, `~/.oh-my-zsh`, and the Nerd
Font. Delete those by hand only if you want a clean slate.

## Repository layout

```text
.chezmoi.toml.tmpl                    # prompts for git name/email on init
.chezmoitemplates/AGENTS.md           # shared engineering instructions
.chezmoiexternal.toml                 # pinned Oh My Zsh and plugin archives
.chezmoiignore                        # repo docs + ~/.aws, ~/.azure excluded
dot_agents/skills/                    # shared agent workflows
dot_zshrc                             # → ~/.zshrc
dot_gitconfig.tmpl                    # → ~/.gitconfig (identity from .data)
dot_vscode/argv.json.tmpl             # → ~/.vscode/argv.json
private_dot_config/
├── mise/{config.toml,mise.lock}      # → ~/.config/mise/
├── {opencode,kilo}/AGENTS.md.tmpl    # global instruction wrappers
├── opencode/commands/               # wrappers for the shared workflows
├── ghostty/config                    # → ~/.config/ghostty/config
└── Code/User/                        # settings.json and mcp.json.tmpl
run_once_before_10-prereqs.sh.tmpl    # apt base packages (incl. fontconfig) + mise
run_onchange_after_20-mise-install.sh.tmpl  # re-installs tools on config change
run_onchange_after_25-context7-install.sh.tmpl  # installs the locked npm dependency tree
run_onchange_after_30-vscode-extensions.sh.tmpl  # installs the extension list
run_onchange_after_40-nerd-font.sh.tmpl  # JetBrainsMono Nerd Font, checksummed
dot_local/bin/executable_context7-mcp # → ~/.local/bin/context7-mcp
dot_local/share/context7-mcp/         # managed package.json and package-lock.json
dot_codex/AGENTS.md.tmpl              # → ~/.codex/AGENTS.md
dot_codex/modify_private_config.toml  # Codex approval defaults and Context7
scripts/set-context7-key.py           # hidden prompt; writes only outside the repo
scripts/check-context7-secrets.py     # local Git hook check
.githooks/{pre-commit,pre-push}       # enabled with core.hooksPath
tests/test-agent-instructions.py      # offline instruction and workflow delivery checks
tests/test-context7.py                # offline launcher/config/hook checks
tests/test-installers.py              # offline prerequisite and editor installer checks
tests/test-zsh.sh                     # local shell/toolchain test suite
tests/docker-bootstrap.sh             # Docker bootstrap test for local use and CI
```

## License

[MIT](LICENSE)
