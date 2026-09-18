# =============================================================================
# E2E harness base image: a fresh laptop, nothing more.
#
# Only ca-certificates/curl/sudo are provided. zsh, git, mise and the whole
# 26-tool toolchain must come from the dotfiles bootstrap scripts themselves.
# =============================================================================

FROM ubuntu:24.04

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        sudo \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/bash tester \
    && echo 'tester ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/tester \
    && chmod 0440 /etc/sudoers.d/tester \
    # Pre-create named-volume mountpoints owned by tester, or docker mounts
    # them root-owned and the bootstrap cannot write to $HOME.
    && mkdir -p /home/tester/.local/bin /home/tester/.local/share/mise /home/tester/.cache/mise \
    && chown -R tester:tester /home/tester/.local /home/tester/.cache

USER tester
WORKDIR /home/tester

COPY --chmod=755 entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
