#!/usr/bin/env bash
set -euo pipefail

if command -v systemctl >/dev/null 2>&1 && [[ -d /run/systemd/system ]]; then
    systemctl daemon-reload
fi
