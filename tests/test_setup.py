import json
import subprocess

import pymupdf

from wgu.config import find_project
from wgu.project_setup import setup


def _pdf(path):
    d = pymupdf.open()
    pg = d.new_page()
    for i in range(30):
        pg.insert_text((50, 60 + i * 14), "Body text of the rules for testing purposes.", fontname="tiro", fontsize=10)
    pg.insert_text((50, 30), "HEADING", fontname="hebo", fontsize=18)
    pg.insert_text((50, 500), "Changed text", fontname="tiro", fontsize=10, color=(0, 0, 1))
    pg.insert_text((50, 520), "Changed again in blue", fontname="tiro", fontsize=10, color=(0, 0, 1))
    d.save(path)


def test_setup_sorts_files_and_writes_project(tmp_path):
    _pdf(tmp_path / "Rules.pdf")
    (tmp_path / "map.jpg").write_bytes(b"x")
    log = setup(tmp_path, "gra43", "G43", None, [], git=False, plugin=False, plugin_path=tmp_path / "plugin")
    assert (tmp_path / "docs" / "Rules.pdf").exists() and (tmp_path / "png" / "map.jpg").exists()
    assert not (tmp_path / "Rules.pdf").exists()
    pr = find_project(tmp_path)
    assert pr.get("sources")["rules"][0]["path"] == "docs/Rules.pdf"
    assert pr.get("pdf")["accent_color"] == "0000FF"
    assert "build/" in (tmp_path / ".gitignore").read_text()
    cfg = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    assert cfg["enabledPlugins"] == {"wgu@wargame-utils": True}
    assert log


def test_setup_refuses_second_run(tmp_path):
    import pytest
    _pdf(tmp_path / "Rules.pdf")
    setup(tmp_path, None, None, None, [], git=False, plugin=False)
    with pytest.raises(SystemExit):
        setup(tmp_path, None, None, None, [], git=False, plugin=False)


def test_install_plugin_without_claude_gives_manual_hint(tmp_path, monkeypatch):
    from wgu import project_setup
    monkeypatch.setattr(project_setup, "find_claude", lambda: None)
    log = []
    project_setup.install_plugin(tmp_path, tmp_path / "plugin", log)
    assert "plugin install wgu@wargame-utils" in log[0]


def test_measure_ignores_style_variants_of_body_font(tmp_path):
    from wgu.project_setup import measure_pdf
    d = pymupdf.open()
    pg = d.new_page()
    for i in range(20):
        pg.insert_text((50, 60 + i * 14), "Body text " * 6, fontname="tiro", fontsize=10)
    for i in range(10):
        pg.insert_text((50, 400 + i * 14), "Italic note " * 6, fontname="tiit", fontsize=10)
    pg.insert_text((50, 30), "HEAD", fontname="hebo", fontsize=18)
    d.save(tmp_path / "a.pdf")
    assert measure_pdf(tmp_path / "a.pdf")["heading_font"].lower().startswith("helvetica")


def test_help_topics(capsys):
    import pytest
    from wgu import cli
    cli.main(["help"])
    assert "nowa-gra" in capsys.readouterr().out
    cli.main(["help", "nowa-gra"])
    out = capsys.readouterr().out
    assert "init --setup" in out and "LOCALAPPDATA" in out
    with pytest.raises(SystemExit):
        cli.main(["help", "nie-ma"])


def test_find_claude_msix_location(tmp_path, monkeypatch):
    from wgu import project_setup
    exe = tmp_path / "Packages" / "Claude_abc" / "LocalCache" / "Roaming" / "Claude" / "claude-code" / "1.0" / "h" / "claude.exe"
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    monkeypatch.setattr(project_setup.shutil, "which", lambda _: None)
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert project_setup.find_claude() == str(exe)


def test_setup_does_not_create_nested_git_repository(tmp_path, monkeypatch):
    from wgu import project_setup
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    game = tmp_path / "games" / "test"
    game.mkdir(parents=True)
    pdf = game / "Rules.pdf"
    pdf.write_bytes(b"not inspected in this test")
    monkeypatch.setattr(project_setup, "measure_pdf", lambda _: {
        "pages": 1, "body_font": "", "heading_font": "", "accent_color": ""
    })
    log = setup(game, "test", "T", pdf, [], git=True, plugin=False)
    assert not (game / ".git").exists()
    assert any("pominięto git init" in line for line in log)
