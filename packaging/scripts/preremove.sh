#!/usr/bin/env bash
set -euo pipefail

if command -v systemctl >/dev/null 2>&1 && [[ -d /run/systemd/system ]]; then
    systemctl stop jasmin-web.service jasmin-celery.service 2>/dev/null || true
    systemctl disable jasmin-web.service jasmin-celery.service 2>/dev/null || true
fi
