#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "ERROR: OpenStream installer must run as root." >&2
  echo "Use: sudo ./install.sh" >&2
  exit 1
fi

REPO_TARBALL_URL="${OPENSTREAM_TARBALL_URL:-https://github.com/Amir-A664/OpenStream/archive/refs/tags/v1.0.0.tar.gz}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd 2>/dev/null || pwd)"
SOURCE_ROOT="${SCRIPT_DIR}"
TMP_DIR=""
PYTHON_BIN="${PYTHON_BIN:-python3}"

cleanup() {
  if [[ -n "${TMP_DIR}" && -d "${TMP_DIR}" ]]; then
    rm -rf "${TMP_DIR}"
  fi
}
trap cleanup EXIT

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "ERROR: python3 was not found. Install Python 3.10+ first." >&2
  exit 1
fi

if [[ ! -d "${SOURCE_ROOT}/src/openstream" ]]; then
  if ! command -v curl >/dev/null 2>&1 || ! command -v tar >/dev/null 2>&1; then
    echo "ERROR: source tree not found and curl/tar are required for remote bootstrap." >&2
    echo "Clone the repository, then run: sudo ./install.sh" >&2
    exit 1
  fi
  TMP_DIR="$(mktemp -d)"
  echo "OpenStream source tree not found next to install.sh; downloading repository snapshot..."
  curl -fsSL "${REPO_TARBALL_URL}" | tar -xz -C "${TMP_DIR}" --strip-components=1
  SOURCE_ROOT="${TMP_DIR}"
fi

export PYTHONPATH="${SOURCE_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
exec "${PYTHON_BIN}" -m openstream.installer install --source-root "${SOURCE_ROOT}" "$@"
