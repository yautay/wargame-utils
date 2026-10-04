import json

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
    log = setup(tmp_path, "gra43", "G43", None, [], git=False, plugin_path=tmp_path / "plugin")
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
    setup(tmp_path, None, None, None, [], git=False)
    with pytest.raises(SystemExit):
        setup(tmp_path, None, None, None, [], git=False)
