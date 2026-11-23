#!/usr/bin/env bash
# =============================================================================
# E2E entrypoint: run the real bootstrap inside the container, then test it.
#
# The repo is mounted read-only at /dotfiles. HOME is /home/tester.
# =============================================================================

set -Eeuo pipefail

# CI must be unset: run_onchange_after_20-mise-install.sh skips the whole
# toolchain install when CI is set (GitHub Actions always sets it).
unset CI GITHUB_ACTIONS GITHUB_WORKFLOW GITHUB_REF

log() {
    printf '\n\033[1;34m==>\033[0m %s\n' "$*"
}

check_apply_status() {
    local status
    status="$("$HOME/.local/bin/chezmoi" --source /dotfiles status)"
    if [[ -n "$status" ]]; then
        printf 'Changes pending %s the second apply:\n%s\n' "$1" "$status" >&2
        exit 1
    fi
}

log "identity: seeding non-interactive chezmoi config"
mkdir -p "$HOME/.config/chezmoi"
cat > "$HOME/.config/chezmoi/chezmoi.toml" <<'EOF'
[data]
    name = "E2E"
    email = "e2e@example.com"
EOF

log "installing chezmoi (same path as the README one-liner)"
# A fresh home has no ~/.local/bin; the chezmoi installer requires it to exist.
mkdir -p "$HOME/.local/bin"
curl -fsLS https://get.chezmoi.io | sh -s -- -b "$HOME/.local/bin"
export PATH="$HOME/.local/bin:$PATH"

log "applying dotfiles from /dotfiles (full bootstrap: apt, mise, tools)"
# GITHUB_TOKEN avoids unauthenticated GitHub API rate limits (60 req/h).
"$HOME/.local/bin/chezmoi" init --source /dotfiles --apply

log "applying the same dotfiles again"
check_apply_status before
"$HOME/.local/bin/chezmoi" --source /dotfiles apply --verbose
check_apply_status after

export PATH="$HOME/.local/share/mise/shims:$PATH"
log "verifying installed versions and the Azure dependency lock"
python3 /dotfiles/tests/docker/verify-toolchain.py

log "running full local test suite"
python3 /dotfiles/tests/test-installers.py
python3 /dotfiles/tests/test-context7.py
python3 /dotfiles/tests/test-agent-instructions.py
exec /dotfiles/tests/test-zsh.sh
