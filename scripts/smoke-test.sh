#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

python3 -m compileall -q src
PYTHONPATH="${ROOT}/src" python3 - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from openstream.auth import detect_auth_method
from openstream.ovpn_patch import patch_ovpn_config

sample = """client
dev tun
proto udp
remote vpn.example.com 1194
auth-user-pass
compat-mode 2.4
cipher AES-128-CBC
<ca>
REDACTED_CA
</ca>
"""
assert detect_auth_method(sample) == "hybrid"
with TemporaryDirectory() as td:
    root = Path(td)
    auth = root / "auth.txt"
    auth.write_text("u\np\n")
    result = patch_ovpn_config(
        sample,
        auth_method="hybrid",
        auth_file=auth,
        profile_source_dir=root,
        external_dir=root / "external-files",
    )
    assert "dev tun-opst" in result.text
    assert "compat-mode 2.4" not in result.text
    assert "data-ciphers AES-128-CBC" in result.text
    assert f"auth-user-pass {auth}" in result.text
    assert "<ca>\nREDACTED_CA\n</ca>" in result.text
print("Python smoke test passed.")
PY

if python3 -m pytest --version >/dev/null 2>&1; then
  PYTHONPATH="${ROOT}/src" python3 -m pytest -q
else
  echo "pytest is not installed; skipping pytest suite. Install it with: python3 -m pip install pytest"
fi

echo "Smoke test passed."
