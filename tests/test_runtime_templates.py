from pathlib import Path


def test_namespace_helper_parses_remote_port_and_proto() -> None:
    template = Path("src/openstream/templates/opst-netns.sh.tpl").read_text(encoding="utf-8")

    assert '$1=="remote" && NF>=3 {print $3; exit}' in template
    assert '$1=="remote" && NF>=4 {print $4; exit}' in template


def test_installer_targets_v1_release_tarball() -> None:
    install_sh = Path("install.sh").read_text(encoding="utf-8")

    assert "refs/tags/v1.0.0.tar.gz" in install_sh
    assert "refs/heads/main.tar.gz" not in install_sh
