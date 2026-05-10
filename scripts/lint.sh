#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

python3 -m compileall -q src
bash -n install.sh
bash -n uninstall.sh
find scripts -type f -name '*.sh' -print0 | xargs -0 -r bash -n

if command -v ruff >/dev/null 2>&1; then
  ruff check src
else
  echo "ruff not found; skipped optional ruff check"
fi

echo "Lint checks passed."
