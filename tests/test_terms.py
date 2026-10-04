from pathlib import Path

from wgu.check.fidelity import compare, cues, numbers
from wgu.check.segments import segments_of
from wgu.kb.store import write_yaml
from wgu.terms import ops
from wgu.terms.store import load, word_re


def _layer(tmp: Path, name: str, level: str, concepts: list) -> Path:
    p = tmp / f"{name}.yaml"
    write_yaml(p, {"layer": {"id": name, "level": level}, "concepts": concepts})
    return p


ROUT = {"id": "gboh.rout", "source_term": "Rout", "variants": ["routs", "Routed"], "sense": "ucieczka jednostki",
        "pl": "ucieczka", "pl_forms": ["ucieczki", "ucieczkę", "uciekająca"], "status": "approved", "decided_by": "user",
        "rejected": [{"pl": "rozbicie", "reason": "inne pojęcie"}],
        "history": [{"date": "2026-10-04", "from": "pogrom", "reason": "test"}]}


def test_layers_override_and_forms(tmp_path):
    common = _layer(tmp_path, "common", "common", [{"id": "common.zoc", "source_term": "ZOC", "sense": "s", "pl": "strefa kontroli", "status": "approved"}])
    game = _layer(tmp_path, "game", "game", [{"id": "spqr.zoc", "source_term": "ZOC", "sense": "s2", "pl": "strefa kontroli (SPQR)",
                                               "status": "approved", "overrides": "common.zoc"}, ROUT])
    t = load([common, game])
    assert "common.zoc" not in t.effective and "spqr.zoc" in t.effective
    assert word_re("strefa kontroli").search("w strefie kontroli") is None      # inflection needs pl_forms
    assert word_re("strefa kontroli").search("ta strefa\nkontroli")


def test_check_and_impact(tmp_path, capsys, monkeypatch):
    game = _layer(tmp_path, "game", "game", [ROUT])
    monkeypatch.setattr(ops, "layer_paths", lambda pr: [game])
    tex = tmp_path / "a.tex"
    tex.write_text("%@ 10.2\nJednostka wpada w rozbicie.\n%@ 10.3\nPo pogromie jednostka…\n% rozbicie w komentarzu\n", encoding="utf-8")
    assert ops.check(None, [str(tex)]) == 1
    out = capsys.readouterr().out
    assert "rejected form 'rozbicie'" in out and "old equivalent 'pogrom'" not in out   # 'pogromie' ≠ 'pogrom' (no stem matching)
    src = tmp_path / "s.md"
    src.write_text("%@ 10.2\nThe unit routs.\n%@ 10.3\nA Routed unit…\n", encoding="utf-8")
    ops.impact(None, "gboh.rout", [str(tex)], [str(src)])
    out = capsys.readouterr().out
    assert "[10.2] rejected: rozbicie" in out
    assert "[10.3]  CHECK" in out


def test_fidelity_flags():
    en = "A unit may not move more than 2 hexes unless it is a Skirmisher (see 6.13)."
    good = "Jednostka nie może przejść więcej niż 2 heksy, chyba że jest harcownikiem (patrz 6.13)."
    bad = "Jednostka może przejść 3 heksy, jeśli jest harcownikiem."
    assert compare(en, good) == []
    flags = compare(en, bad)
    assert any("numbers missing" in f for f in flags) and any("prohibition" in f for f in flags)
    assert any("cross-refs missing" in f for f in flags)
    assert numbers("two hexes and ½", "en") == numbers("dwa heksy i ½", "pl")
    assert cues("nie może i może", "pl")["prohibition"] == 1 and cues("nie może i może", "pl")["permission"] == 1


def test_segments(tmp_path):
    p = tmp_path / "x.tex"
    p.write_text("pre\n%@ 1.1\nA\n%@ hist-1\nB\nC\n", encoding="utf-8")
    assert segments_of(p) == {"1.1": "A", "hist-1": "B\nC"}


def test_shipped_layers_validate():
    import json
    from jsonschema import Draft202012Validator
    from wgu.kb.store import read_yaml
    root = Path(__file__).resolve().parent.parent
    v = Draft202012Validator(json.loads((root / "wgu/schemas/terminology.schema.json").read_text(encoding="utf-8")))
    files = list((root / "terminology").rglob("*.yaml"))
    assert files
    for f in files:
        errs = [e.message for e in v.iter_errors(read_yaml(f))]
        assert not errs, (f, errs[:3])


def test_fidelity_regression_own_texts():
    """Own (non-copyrighted) rule-like sentences: correct PL must not be flagged, seeded errors must be."""
    en = ("A unit may move only once per Orders Phase. There is no limit per Game Turn. "
          "Once Depleted, a unit remains so. Units that are already Depleted do not suffer additional Depletions.")
    good = ("Jednostka może poruszyć się tylko raz w każdej Fazie Rozkazów. Liczba ruchów w turze nie jest ograniczona. "
            "Osłabiona jednostka pozostaje w tym stanie. Jednostki już osłabione nie podlegają kolejnemu osłabieniu.")
    assert compare(en, good) == []
    bad = ("Jednostka może się poruszać w każdej Fazie Rozkazów. Liczba ruchów w turze jest dowolna. "
           "Osłabiona jednostka pozostaje w tym stanie. Jednostki już osłabione mogą podlegać kolejnemu osłabieniu.")
    flags = compare(en, bad)
    assert any(f.startswith("scope") for f in flags) and any(f.startswith("negation") for f in flags)


def test_check_detects_capitalisation_change(tmp_path, capsys, monkeypatch):
    c = {"id": "x.phase", "source_term": "Orders Phase", "sense": "s", "pl": "faza rozkazów",
         "pl_forms": ["faza rozkazów", "fazie rozkazów"], "status": "approved",
         "history": [{"date": "2026-10-04", "from": "Faza Rozkazów", "from_forms": ["Faza Rozkazów", "Fazie Rozkazów"]}]}
    game = _layer(tmp_path, "game", "game", [c])
    monkeypatch.setattr(ops, "layer_paths", lambda pr: [game])
    tex = tmp_path / "a.tex"
    tex.write_text("W Fazie Rozkazów gracz…\nFaza rozkazów zaczyna się…\nw fazie rozkazów\n", encoding="utf-8")
    ops.check(None, [str(tex)])
    out = capsys.readouterr().out
    assert "a.tex:1" in out and "a.tex:2" not in out and "a.tex:3" not in out
