#!/usr/bin/env bash
# =============================================================================
# Local end-to-end bootstrap test in Docker (not GitHub Actions).
#
#   tests/docker-bootstrap.sh           # cached: mise downloads persist
#   tests/docker-bootstrap.sh --fresh   # cold: drop caches, full re-download
#
# Simulates a fresh Ubuntu 24.04 machine: minimal image (no zsh, no git, no
# mise), then the dotfiles bootstrap installs everything and tests/test-zsh.sh
# verifies the result. The 26-tool install is heavy; that is exactly why this
# is not part of GitHub Actions CI.
#
# Requirements: docker, network. GITHUB_TOKEN (or `gh auth token`) avoids
# GitHub API rate limits during mise installs.
# =============================================================================

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="mlops-dotfiles-e2e"
CACHE_VOL="mlops-dotfiles-mise-cache"
DATA_VOL="mlops-dotfiles-mise-data"

FRESH=0
[[ "${1:-}" == "--fresh" ]] && FRESH=1

command -v docker >/dev/null 2>&1 || {
    printf 'ERROR: docker not found\n' >&2
    exit 1
}

if [[ -z "${GITHUB_TOKEN:-}" ]] && command -v gh >/dev/null 2>&1; then
    GITHUB_TOKEN="$(gh auth token 2>/dev/null || true)"
    export GITHUB_TOKEN
fi

printf '\033[1;34m==>\033[0m building image\n'
docker build -t "$IMAGE" "$REPO_ROOT/tests/docker"

if ((FRESH)); then
    printf '\033[1;34m==>\033[0m --fresh: removing cached toolchain volumes\n'
    docker volume rm -f "$CACHE_VOL" "$DATA_VOL" >/dev/null
fi

printf '\033[1;34m==>\033[0m running bootstrap + tests%s\n' \
    "$([[ $FRESH ]] && printf ' (cold install, 10-20+ min first time)' || printf '')"

# Repo is mounted read-only: the container must not mutate the working tree.
# Volumes persist the mise download cache and installed tools between runs.
tty_flag=""
[[ -t 0 ]] && tty_flag="-t"

exec docker run --rm -i $tty_flag \
    -e GITHUB_TOKEN \
    -v "$REPO_ROOT:/dotfiles:ro" \
    -v "$CACHE_VOL:/home/tester/.cache/mise" \
    -v "$DATA_VOL:/home/tester/.local/share/mise" \
    "$IMAGE"
