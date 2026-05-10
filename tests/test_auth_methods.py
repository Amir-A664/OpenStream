from pathlib import Path

from openstream.auth import detect_auth_method, iter_directive_lines

FIXTURES = Path(__file__).parent / "fixtures"


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_detects_username_password_basic_auth() -> None:
    assert detect_auth_method(read_fixture("basic-auth.ovpn")) == "userpass"


def test_detects_inline_certificate_auth() -> None:
    assert detect_auth_method(read_fixture("cert-inline.ovpn")) == "cert"


def test_detects_external_certificate_auth() -> None:
    assert detect_auth_method(read_fixture("cert-external.ovpn")) == "cert"


def test_detects_hybrid_auth() -> None:
    assert detect_auth_method(read_fixture("hybrid.ovpn")) == "hybrid"


def test_detects_static_key_auth() -> None:
    assert detect_auth_method(read_fixture("static-key.ovpn")) == "static_key"


def test_inline_block_contents_are_not_treated_as_directives() -> None:
    text = """
client
<ca>
auth-user-pass should-not-count
remote should-not-count.example.com 1194
</ca>
"""
    lines = iter_directive_lines(text)
    assert lines == ["client"]
    assert detect_auth_method(text) == "cert"
    assert all("auth-user-pass" not in line for line in lines)
