import textwrap
from pathlib import Path

import pytest

from wgu.aids.validate import check_aid
from wgu.config import Project, DEFAULTS
from wgu.kb import legacy_import, lint
from wgu.kb.store import extract_ids, known, load_kb


def test_extract_ids_ranges_and_mixed():
    assert extract_ids("R-2.2.4–7") == ["R-2.2.4", "R-2.2.5", "R-2.2.6", "R-2.2.7"]
    assert extract_ids("R-7.8.1–R-7.8.4") == ["R-7.8.1", "R-7.8.2", "R-7.8.3", "R-7.8.4"]
    # cross-section range is not expanded
    assert extract_ids("R-4.0.1–R-4.4.1") == ["R-4.0.1", "R-4.4.1"]
    assert extract_ids("R-OTR-1 → R-OPT-LI.2; N-12, Q-04, T-LUKA, P-03a, P09") == \
        ["R-OTR-1", "R-OPT-LI.2", "N-12", "Q-04", "T-LUKA", "P-03a", "P09"]


def test_known_subpoints_and_wildcards():
    ids = {"R-6.3.6": "rule"}
    assert known("R-6.3.6", ids) and known("R-6.3.6a", ids) and known("R-OPT-LI.x", ids)
    assert not known("R-6.3.7", ids)


def _aid(nodes, edges):
    return {"id": "P99", "title": "t", "nodes": [dict(zip(("id", "shape", "text", "refs"), n)) for n in nodes],
            "edges": [dict(zip(("from", "to", "label"), e)) for e in edges]}


def test_validate_graph_ok_and_errors():
    ids = {"R-1": "rule"}
    ok = _aid([("S", "start", "s", []), ("D", "decyzja", "d?", ["R-1"]), ("E1", "koniec", "a", ["R-1"]),
               ("E2", "koniec", "b", ["R-1"])], [("S", "D", ""), ("D", "E1", "tak"), ("D", "E2", "nie")])
    e, w = check_aid(ok, ids)
    assert e == [] and w == []
    bad = _aid([("S", "start", "s", []), ("D", "decyzja", "d?", ["R-1"]), ("E1", "koniec", "a", ["R-1"])],
               [("S", "D", ""), ("D", "E1", "tak"), ("D", "X", "nie")])
    e, w = check_aid(bad, ids)
    assert any("unknown to node 'X'" in x for x in e)


LEGACY_RULES = textwrap.dedent("""\
    # Reguły
    Konwencje: test.

    ## 7.0 Combat / Walka

    ### R-7.1.1 Kto atakuje
    - **Źródło:** oryg. 7.1, s. 12; PL `tex/07_1_walka.tex:5-9`
    - **Kiedy:** jednostka aktywna
    - **Skutek:** atakuje; wyjątek → R-7.1.2
    - **Słowa kluczowe:** atak, aktywna

    ### R-7.1.2 Wyjątek
    - **Źródło:** oryg. 7.1, s. 12
    - **Skutek:** nie atakuje, gdy **D**.
      (kontynuacja linii)
    """)
LEGACY_AMB = textwrap.dedent("""\
    # Niejasności

    ## A. Błędy

    ### N-01 Coś
    - **Cytaty:** „x”
    - **Rekomendacja:** (a), **Pewna**.
    """)


def test_legacy_import_and_lint(tmp_path: Path):
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / "reguly.md").write_text(LEGACY_RULES, encoding="utf-8")
    (legacy / "niejasnosci.md").write_text(LEGACY_AMB, encoding="utf-8")
    kb_dir = tmp_path / "kb"
    stats = legacy_import.run(legacy, kb_dir, None, {"schema": "wgu/kb@1", "game": {"id": "t"}})
    assert stats["rules"] == 2 and stats["ambiguities"] == 1
    kb = load_kb(kb_dir)
    r1, r2 = kb["rules"]
    assert r1["source"]["pages"] == "12" and r1["source"]["translation"] == [{"file": "tex/07_1_walka.tex", "lines": "5-9"}]
    assert r1["keywords"] == ["atak", "aktywna"] and r1["refs"] == ["R-7.1.2"]
    assert "(kontynuacja linii)" in r2["effect"]
    assert kb["ambiguities"][0]["strength"] == "certain"
    errors, warnings = lint.check(kb_dir)
    assert errors == []
