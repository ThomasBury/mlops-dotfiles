# Everyday terminal recipes

These recipes assume you have [installed the dotfiles](README.md#install) and
run `exec zsh`. Try the file and Git examples from the dotfiles checkout.
The project and infrastructure recipes name any additional setup they need.

```zsh
cd "$(chezmoi source-path)"
```

## Navigate and inspect

**Return to a project.** Open it once with `cd`. After visiting other
directories, type `z` followed by part of the project directory name. zoxide
learns the directories you visit. Use `zi` to pick from the matches and
`pwd` to confirm where you landed.

**Pick a directory you haven't visited yet.** Run `fcd .`, type `tests`,
and press <kbd>Enter</kbd> on the `tests` directory. `pwd` should end in
`/tests`. Press <kbd>Esc</kbd> to cancel. The argument sets the search root,
so `fcd ~/projects` looks under that directory if it exists. `fcd` uses fzf
to select from results found by `fd`.

**See what is here.** From the checkout root, run `ll` for a detailed listing
with hidden files and Git status, `la` for a compact listing with hidden
files, or `lt` for a two-level tree. These shortcuts use eza. Starship shows
your working directory and, inside a Git checkout, the branch in the prompt.

**Read a file.** Run `b README.md` to view it with bat's syntax highlighting
and line numbers. Press <kbd>q</kbd> if it opens in a pager.

## Find, edit, and get help

**Find a filename or search inside files.** With `fd`, search by filename.
With `rg` (ripgrep), search by content. `-n` shows line numbers alongside
the matches.

```zsh
fd --glob 'README.md'
rg -n 'chezmoi apply' README.md
```

**Pick a file to open or copy its path.** Run `fv .`, type `README.md`, and
press <kbd>Enter</kbd> to open it in `$EDITOR`, which defaults to Neovim.
Press <kbd>Esc</kbd> to cancel the picker. In Neovim, press <kbd>Esc</kbd>,
type `:q`, and press <kbd>Enter</kbd> to quit if you made no edits. Use
`v README.md` if you already know the path.

Run `tv files` to browse files with previews. Type `README.md` and press
<kbd>Enter</kbd> to print the selected path. Press <kbd>Esc</kbd> to cancel.
`tv list-channels` shows the other data sources Television can browse.

**Complete a path.** At the checkout root, type `cd` followed by a space
and press <kbd>Tab</kbd>. Type `tests` in the fuzzy menu, select the
directory, and press <kbd>Enter</kbd> to fill in the path. Check the
completed command before running it. If the preview shows an `--icons`
error, you can still select the directory.

**Recall a command.** Run `rg -n 'chezmoi apply' README.md` once, then
press <kbd>Ctrl</kbd>+<kbd>R</kbd> and type `rg -n` to find it in Atuin.
Press <kbd>Esc</kbd> to return to the prompt. `hs` also opens the history
picker. When a gray history suggestion appears as you type at the prompt,
press <kbd>Right Arrow</kbd> at the end of the line to accept it. Standard
editing keys still work, including <kbd>Ctrl</kbd>+<kbd>A</kbd> for the start
of the line and <kbd>Ctrl</kbd>+<kbd>E</kbd> for the end.

**Get a quick example for a command.** Run `tldr tar` to see common `tar`
invocations. If the page cache is missing or stale, run `tldr --update` with
network access and try again. Use `man tar` when you need the full options.

## Work in a Git repository

**Review your changes.** Run `git status --short --branch` to see the current
branch and changed files. Run `git diff` for unstaged changes and
`git diff --cached` for staged changes. Press <kbd>q</kbd> to exit a pager.

**Browse the repository in one screen.** Run `lazygit` from the checkout.
Select a changed file in the Files panel to see its diff. The interface also
shows branches and commits. Press <kbd>q</kbd> to quit.

**Find open pull requests.** From a checkout with a GitHub remote, run
`gh auth status` to check your login, then `gh pr list`. You will see open
pull requests for that repository, if any. Run `gh auth login` first if you
need to sign in.

## Run a project

**Check which runtime is active.** From the project root, run
`mise current python` or `mise current node` to see the selected version.
`mise which python` and `mise which node` show the executable paths. A
project's mise configuration can override the workstation defaults. Review
an unfamiliar configuration before trusting it.

**Run a command in a locked Python project.** From a project with
`pyproject.toml` and `uv.lock`, run `uv run --locked python --version`. It
uses uv's project environment and reports its Python version. If the lock
is out of date, `--locked` stops and reports that it needs updating. Use the
same prefix for a command the project declares, such as
`uv run --locked pytest` in a project that includes pytest. For an interactive
shell in an existing `.venv`, `va` activates it and `deactivate` leaves it.

**Install a Node project's locked dependencies.** From a project with
`package.json` and `package-lock.json`, run `npm ci`. It recreates
`node_modules` using the lockfile. Run `npm test` if the project defines a
test script. Use the project's required Node version and only install
dependencies for a project you trust.

**Load variables for one project.** In a scratch directory, create a file
named `.envrc` with the following line. In an existing project, review the
whole file before approving it because direnv executes its contents.

```bash
export APP_ENV=development
```

```zsh
direnv allow
```

At the next prompt, run this check. It should print `development`.

```zsh
print -r -- "$APP_ENV"
```

Run `cd ..` to leave the project and restore the previous environment.
Keep credentials out of committed `.envrc` files.

**Preview local files in a browser.** From a directory of files you want to
preview, run the following command and open `http://127.0.0.1:8000`.
Stop the server with <kbd>Ctrl</kbd>+<kbd>C</kbd>.

```zsh
python3 -m http.server --bind 127.0.0.1 8000
```

The `serve 8000` shortcut starts the same server with Python's default
binding, which listens on all interfaces. Use it when you intend to make the
directory available to other devices on your network.

## Read structured files

**Extract one value from JSON or YAML.** Use `jq` for JSON and `yq` for YAML.
Both examples print `8080`. To work with a file, pass its path after the
expression, as in `jq '.service.port' config.json`.

```zsh
printf '%s\n' '{"service":{"port":8080}}' | jq '.service.port'
printf '%s\n' 'service:' '  port: 8080' | yq '.service.port'
```

## Inspect containers and infrastructure

**Check local services and logs.** Use a directory with a Compose project
and active services. Install Docker and its Compose plugin separately and
make sure you can reach the Docker daemon. The dotfiles install Lazydocker
and add Compose shortcuts in Zsh when `docker` is available.

```zsh
docker compose ps
dcl --tail 50
```

`ps` shows running services and their status. `dcl` runs
`docker compose logs`, and `dclf` follows live logs until you press
<kbd>Ctrl</kbd>+<kbd>C</kbd>. Run `lazydocker` to browse local containers and
logs in a terminal interface and press <kbd>q</kbd> to quit.

**Confirm your Kubernetes target before looking at pods.** You need a
kubeconfig with a current context and permission to list pods. Run `kwhere`
and check the context and namespace. If both are the ones you intend to
inspect, run `kubectl get pods` to see pod names, status, and restarts.
`kctx` prints just the context. For more detail, use `k9s --readonly` to
browse resources, `helm list` to see Helm releases in the current namespace,
or Stern to follow logs across pods by name.

**Check your cloud identity.** Run `awswho` with the intended AWS profile
active to see the account and caller ARN. Run `azwho` after signing in to
see the active Azure subscription, tenant, and user. These shortcuts wrap
`aws sts get-caller-identity` and `az account show`. See
[Git identity and private files](README.md#git-identity-and-private-files)
for where these tools keep machine-specific configuration.

**Check infrastructure file formatting.** From a Terraform project, run
`terraform fmt -check`. For an OpenTofu project, run `tofu fmt -check`.
The command lists files that need formatting and exits with a nonzero
status if it finds any. The check leaves the files as they are.

## Manage the setup or use an assistant

- [Manage your dotfiles](README.md#manage-your-dotfiles) to preview and apply
  shared changes with chezmoi. `reload` starts a fresh Zsh session after a
  change.
- [Set up Context7](README.md#context7-setup) to look up library documentation
  from a configured assistant.
- [Use shared agent workflows](README.md#shared-agent-workflows) to improve
  prompts and plans, review a project, or deliver a pull request.
- See the [mise configuration](private_dot_config/mise/config.toml) for the
  tool inventory and [Updating tools](README.md#updating-tools) for upgrades.
