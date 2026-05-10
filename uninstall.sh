#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "ERROR: OpenStream uninstaller must run as root." >&2
  echo "Use: sudo ./uninstall.sh" >&2
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ -d "${SCRIPT_DIR}/src/openstream" ]]; then
  export PYTHONPATH="${SCRIPT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"
fi

if "${PYTHON_BIN}" -c 'import openstream.installer' >/dev/null 2>&1; then
  exec "${PYTHON_BIN}" -m openstream.installer uninstall "$@"
fi

if [[ -x /usr/local/bin/opst ]]; then
  exec /usr/local/bin/opst uninstall "$@"
fi

echo "ERROR: Could not find installed OpenStream Python module or /usr/local/bin/opst." >&2
exit 1
