#!/usr/bin/env bash

# =============================================================================
# Dotfiles test suite (local, full)
#
#   tests/test-zsh.sh [path-to-zshrc]
#
# Defaults to the rendered ~/.zshrc. Tests it in an isolated ZDOTDIR (the
# live interactive session is never touched) and verifies the mise-managed
# toolchain. CI runs only a syntax + load check; run this locally after
# `chezmoi apply`.
# =============================================================================

set -Eeuo pipefail

ZSHRC="${1:-$HOME/.zshrc}"

[[ -r "$ZSHRC" ]] || {
    printf 'ERROR: %s not readable\n' "$ZSHRC" >&2
    exit 1
}


pass() {
    printf '\033[1;32mPASS\033[0m  %s\n' "$1"
}


fail() {
    printf '\033[1;31mFAIL\033[0m  %s\n' "$1" >&2
    exit 1
}


# =============================================================================
# 1. Syntax
# =============================================================================

printf '\nZsh syntax\n'
printf '%s\n' '----------'

if zsh -n "$ZSHRC"; then
    pass "zsh -n"
else
    fail "Invalid .zshrc syntax"
fi


# =============================================================================
# 2. Load configuration in an isolated ZDOTDIR
#
# HOME stays unchanged, so ~/.oh-my-zsh and mise remain available.
# Only the Zsh configuration file location is isolated.
# =============================================================================

printf '\nInteractive load\n'
printf '%s\n' '----------------'

TMPDIR_ZSH="$(mktemp -d)"

cleanup() {
    rm -rf "$TMPDIR_ZSH"
}

trap cleanup EXIT

ln -s "$(readlink -f "$ZSHRC")" "$TMPDIR_ZSH/.zshrc"


if ZDOTDIR="$TMPDIR_ZSH" zsh -i -c '
    print "shell loaded successfully"
' >/dev/null; then
    pass "interactive .zshrc load"
else
    fail "interactive .zshrc load"
fi


# =============================================================================
# 3. Key bindings
#
# Standard Emacs/readline bindings must be preserved, with one deliberate
# exception: Atuin owns Ctrl-R (and Up) by design.
# =============================================================================

printf '\nKey bindings\n'
printf '%s\n' '------------'

ZDOTDIR="$TMPDIR_ZSH" zsh -i -c '

check_binding() {
    local key="$1"
    local expected="$2"

    local binding
    binding="$(bindkey -M emacs "$key")"

    if [[ "$binding" != *"$expected"* ]]; then
        print -u2 "Unexpected binding:"
        print -u2 "  $key -> $binding"
        print -u2 "Expected widget containing:"
        print -u2 "  $expected"
        exit 1
    fi
}

check_binding "^A" "beginning-of-line"
check_binding "^E" "end-of-line"
check_binding "^W" "backward-kill-word"
check_binding "^K" "kill-line"
check_binding "^P" "up-line-or-history"
check_binding "^N" "down-line-or-history"

# Deliberately owned by Atuin (see .zshrc).
if command -v atuin >/dev/null 2>&1; then
    check_binding "^R" "atuin"
else
    check_binding "^R" "history-incremental-search-backward"
fi

' >/dev/null || fail "key bindings"

pass "standard Emacs/Zsh bindings preserved (Ctrl-R owned by Atuin)"


# =============================================================================
# 4. Tool availability
#
# All tools below are expected to be provided by mise. A single interactive
# shell is used for the whole loop to keep startup cost down.
# =============================================================================

printf '\nToolchain\n'
printf '%s\n' '---------'

TOOLS=(
    python
    uv

    starship
    atuin
    zoxide
    direnv

    fzf
    fd
    rg
    eza
    bat

    jq
    yq

    nvim

    chezmoi
    gh
    lazygit
    lazydocker

    kubectl
    helm
    k9s
    stern

    terraform
    tofu

    aws
    az
)

# One interactive shell checks both executable presence and mise resolution.
# It is invoked as a direct command so a failure inside the checking shell
# propagates as the shell's exit status (a process substitution or
# command substitution would silently discard it).
#
# whence -p resolves the underlying binary, ignoring aliases such as
# Oh My Zsh's uv plugin alias (uv='noglob uv').

ZDOTDIR="$TMPDIR_ZSH" zsh -i -c '
    tools_missing=0
    not_mise=0

    for tool in "$@"; do
        command -v "$tool" >/dev/null 2>&1 || {
            print -u2 "missing: $tool"
            tools_missing=1
            continue
        }

        resolved="$(whence -p "$tool" 2>/dev/null)" || continue

        if [[ "$resolved" != *mise* ]]; then
            print -u2 "not resolved via mise: $tool -> $resolved"
            not_mise=1
        fi
    done

    if ((tools_missing)) || ((not_mise)); then
        exit 1
    fi
    exit 0
' test-tools "${TOOLS[@]}" || fail "toolchain incomplete or shadowed (run: mise install)"

pass "all ${#TOOLS[@]} tools available and resolving through mise"


# =============================================================================
# 6. mise health
# =============================================================================

printf '\nmise\n'
printf '%s\n' '----'

if ZDOTDIR="$TMPDIR_ZSH" zsh -i -c '"$HOME/.local/bin/mise" doctor' >/dev/null; then
    pass "mise doctor"
else
    fail "mise doctor"
fi


printf '\nAll tests passed.\n'
