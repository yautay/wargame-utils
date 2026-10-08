from pathlib import Path

import pytest

from wgu.config import INIT_TEMPLATE, find_workspace, resolve_project, workspace_projects


def _game(root: Path, directory: str, gid: str):
    game = root / "games" / directory
    game.mkdir(parents=True)
    (game / "wgu.yaml").write_text(INIT_TEMPLATE.format(id=gid, short=gid.upper()), encoding="utf-8")
    return game


def test_workspace_resolves_projects_and_shared_terminology(tmp_path):
    (tmp_path / "wgu-workspace.yaml").write_text(
        "schema: wgu/workspace@1\nprojects: [games/spqr, games/ukraine-43]\n"
        "terminology_root: shared/terminology\n",
        encoding="utf-8",
    )
    spqr = _game(tmp_path, "spqr", "spqr")
    _game(tmp_path, "ukraine-43", "ukraine43")
    workspace = find_workspace(spqr)
    assert workspace.root == tmp_path
    assert [p.data["game"]["id"] for p in workspace_projects(workspace)] == ["spqr", "ukraine43"]
    assert resolve_project("ukraine43", tmp_path).root == tmp_path / "games" / "ukraine-43"
    assert resolve_project("spqr", tmp_path).terminology_root == tmp_path / "shared" / "terminology"


def test_workspace_rejects_duplicate_game_ids(tmp_path):
    (tmp_path / "wgu-workspace.yaml").write_text(
        "schema: wgu/workspace@1\nprojects: [games/one, games/two]\n", encoding="utf-8"
    )
    _game(tmp_path, "one", "same")
    _game(tmp_path, "two", "same")
    with pytest.raises(SystemExit, match="duplicate game.id"):
        workspace_projects(find_workspace(tmp_path))
