#!/usr/bin/env bash
# Build native Debian (.deb) and RHEL/Fedora (.rpm) packages using nFPM.
#
# Usage:
#   ./packaging/build-packages.sh [amd64|arm64]
#
# Prerequisites:
#   - nfpm (https://nfpm.goreleaser.com/install/)
#   - python3 (3.11+) or uv

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PKG_ARCH="${1:-amd64}"
PKG_VERSION="$(sed -n 's/^VERSION = "\(.*\)"/\1/p' config/version.py)"
[[ -n "${PKG_VERSION}" ]] || { echo "Failed to read VERSION from config/version.py" >&2; exit 1; }

STAGE_DIR="${ROOT_DIR}/build/stage/opt/jasmin-web-panel"
DIST_DIR="${ROOT_DIR}/dist"

echo "==> Building Jasmin Web Panel v${PKG_VERSION} packages for linux/${PKG_ARCH}"
rm -rf "${ROOT_DIR}/build/stage"
mkdir -p "${STAGE_DIR}" "${DIST_DIR}"

# Copy application files (excluding dev/git/venv artifacts)
rsync -a \
    --exclude='.git' \
    --exclude='.github' \
    --exclude='env' \
    --exclude='venv' \
    --exclude='build' \
    --exclude='dist' \
    --exclude='tests' \
    --exclude='docs' \
    --exclude='media' \
    --exclude='*.sqlite3' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='logs/*.log' \
    "${ROOT_DIR}/" "${STAGE_DIR}/"

mkdir -p "${STAGE_DIR}/logs" "${STAGE_DIR}/public/static" "${STAGE_DIR}/public/media"

export PKG_ARCH PKG_VERSION

nfpm package --config packaging/nfpm.yaml --packager deb --target "${DIST_DIR}/"
nfpm package --config packaging/nfpm.yaml --packager rpm --target "${DIST_DIR}/"

(
    cd "${DIST_DIR}"
    sha256sum jasmin-web-panel*"${PKG_VERSION}"*.deb jasmin-web-panel*"${PKG_VERSION}"*.rpm > "SHA256SUMS-${PKG_ARCH}.txt"
)

echo "==> Built packages:"
ls -lh "${DIST_DIR}"
