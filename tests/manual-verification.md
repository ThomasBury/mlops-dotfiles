# Manual verification on fresh Ubuntu

This guide is for developers who want to inspect the dotfiles on a clean Ubuntu
machine. Do not call it from CI or another script. [`test-zsh.sh`](test-zsh.sh)
and [`docker-bootstrap.sh`](docker-bootstrap.sh) are the maintained automated
tests.

The steps below prepare `libatomic1` before mise installs Node. This keeps the
manual check focused on the applied files, tools, and shell experience. The
automated Docker test covers the full package bootstrap.

## Prerequisites

- Docker with network access
- A GitHub token to avoid API rate limits during the full tool installation

Set the token without printing it:

```bash
export GITHUB_TOKEN="$(gh auth token)"
```

If `gh` is unavailable, export a suitable token by another secure method.

## 1. Build and enter a clean Ubuntu container

Run these commands from the repository root:

```bash
docker build -t mlops-dotfiles-manual tests/docker

docker run --rm -it \
  --name mlops-dotfiles-manual \
  --entrypoint /bin/bash \
  -e GITHUB_TOKEN \
  -v "$PWD:/dotfiles:ro" \
  mlops-dotfiles-manual
```

The repository is mounted read-only. Docker removes the container when you
exit. No mise cache or data volume is mounted, so each run gets a new home and
tool installation.

Inside the container, confirm the starting point:

```bash
grep '^PRETTY_NAME=' /etc/os-release
command -v git zsh mise chezmoi || true
```

The image should report Ubuntu 24.04, and the four commands should initially be
absent.

## 2. Refresh APT and install the Node runtime library

Refresh the package index, install the library required by Node, and update the
dynamic linker cache before applying the dotfiles:

```bash
sudo apt-get update
sudo env DEBIAN_FRONTEND=noninteractive \
  apt-get install -y --no-install-recommends libatomic1
sudo ldconfig

dpkg -s libatomic1 | grep -F "Status: install ok installed"
ldconfig -p | grep -F "libatomic.so.1"
```

The checks should report `install ok installed` and a path for
`libatomic.so.1`. You do not need to run `apt-get upgrade`.

## 3. Seed the non-interactive chezmoi answers

```bash
mkdir -p "$HOME/.config/chezmoi"
cat > "$HOME/.config/chezmoi/chezmoi.toml" <<'EOF'
[data]
    name = "Manual Verification"
    email = "manual-verification@example.com"
EOF
chmod 600 "$HOME/.config/chezmoi/chezmoi.toml"
```

These placeholder values keep the test repeatable and avoid interactive
prompts. They exist only inside the disposable container.

## 4. Install chezmoi and apply the repository

```bash
mkdir -p "$HOME/.local/bin"
curl -fsLS https://get.chezmoi.io | sh -s -- -b "$HOME/.local/bin"
export PATH="$HOME/.local/bin:$PATH"

chezmoi init --source /dotfiles --apply
```

Read the output before moving on. Chezmoi should install the remaining Ubuntu
packages, shell configuration, mise toolchain, and Nerd Font. It will skip the
VS Code extensions because the container has no `code` command.

If the apply still fails, preserve its output. Do not make further manual
repairs and call the run successful; fix the repository, exit, and restart from
step 1.

## 5. Confirm chezmoi has nothing left to change

Both commands should produce no output:

```bash
chezmoi --source /dotfiles status
chezmoi --source /dotfiles diff
```

Apply once more, then repeat the checks:

```bash
chezmoi --source /dotfiles apply
chezmoi --source /dotfiles status
chezmoi --source /dotfiles diff
```

## 6. Check the applied files and toolchain

```bash
ls -l \
  "$HOME/.zshrc" \
  "$HOME/.config/mise/config.toml" \
  "$HOME/.config/mise/mise.lock" \
  "$HOME/.config/ghostty/config" \
  "$HOME/.config/Code/User/settings.json" \
  "$HOME/.config/Code/User/mcp.json" \
  "$HOME/.vscode/argv.json"

git config --global user.name
git config --global user.email
"$HOME/.local/bin/mise" ls --current
```

The Git values should match the placeholders from step 3. Mise should list
every configured tool as installed.

## 7. Try the shell as a user

Start a login shell as you would on a new machine:

```bash
zsh -l
```

The prompt should load without warnings or missing-command errors. From that
shell, check mise and the two tools that exposed bootstrap problems:

```zsh
mise ls --current
mise doctor
mise which node
mise which nvim
node --version
nvim --version | head -n 1
```

Try the shell features that depend on interactive setup:

1. Press <kbd>Ctrl</kbd>+<kbd>R</kbd>. Atuin should open its history search.
   Press <kbd>Esc</kbd> to close it.
2. Run `fcd /dotfiles`. The directory picker should open. Press <kbd>Esc</kbd>
   to cancel without changing directory.
3. Run `fv /dotfiles`. The file picker should open. Press <kbd>Esc</kbd> to
   cancel without opening a file.

Open Neovim and run `:checkhealth`. Review any warnings that relate to this
configuration, then exit with `:qa`.

You can also run `cd /dotfiles && lazygit`, then press `q` to exit. Skip tools
that need services or credentials that this container does not have, such as
lazydocker, k9s, AWS, Azure, and Terraform. The automated test checks that
their commands exist and resolve through mise.

Exit the login shell to return to Bash:

```zsh
exit
```

## 8. Run the maintained test suite

Finish with the automated checks:

```bash
/dotfiles/tests/test-zsh.sh "$HOME/.zshrc"
```

The final line should be `All tests passed.`

Exit when finished. Docker removes the container automatically:

```bash
exit
```

## Diagnosing a failure

Keep the original error output. These checks are safe to run while you
investigate:

```bash
chezmoi --source /dotfiles status
chezmoi --source /dotfiles diff
dpkg -s libatomic1 | grep -F "Status: install ok installed"
ldconfig -p | grep -F "libatomic.so.1"
"$HOME/.local/bin/mise" install --yes --locked --verbose
"$HOME/.local/bin/mise" doctor
```

If a manual experiment confirms the cause, make the smallest repository fix
and repeat the process in a new container. Do not promote the commands in this
guide into another test script; extend the existing test suite instead.
