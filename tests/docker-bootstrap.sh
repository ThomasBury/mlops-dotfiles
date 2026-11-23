#!/usr/bin/env bash
# =============================================================================
# End-to-end bootstrap test in Docker.
#
#   tests/docker-bootstrap.sh           # cached: mise downloads persist
#   tests/docker-bootstrap.sh --fresh   # cold: no cached tools or downloads
#
# Starts from Ubuntu 26.04 without zsh, git or mise. Toolchain changes run the
# cold install in CI.
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

printf '\033[1;34m==>\033[0m running bootstrap + tests%s\n' \
    "$([[ $FRESH == 1 ]] && printf ' (cold install, 10-20+ min first time)' || printf '')"

# Repo is mounted read-only: the container must not mutate the working tree.
# Volumes persist the mise download cache and installed tools between runs.
docker_args=(--rm -i)
[[ -t 0 ]] && docker_args+=(-t)
if ((!FRESH)); then
    docker_args+=(
        -v "$CACHE_VOL:/home/tester/.cache/mise"
        -v "$DATA_VOL:/home/tester/.local/share/mise"
    )
fi

exec docker run "${docker_args[@]}" \
    -e GITHUB_TOKEN \
    -v "$REPO_ROOT:/dotfiles:ro" \
    "$IMAGE"
