from pathlib import Path
from wgu.bgg import xmlapi
FIX=Path(__file__).parent/"fixtures"/"bgg"
def fx(name): return (FIX/name).read_bytes()

def test_repair_fixes_entities_ampersands_and_control_chars():
    raw = '<a t="R&D&nbsp;x">caf&eacute; &bogus; &#1; ok&amp;&lt;\x01\x0b</a>'.encode()
    root = xmlapi.parse(raw)
    assert root.get("t") == "R&D x"
    assert root.text == "café &bogus;  ok&<"


def test_parse_forumlist_dates_and_epoch():
    forums = xmlapi.forumlist(xmlapi.parse(fx("forumlist_900001.xml")))
    assert [f["forum_id"] for f in forums] == [9101, 9102, 9103]
    assert forums[0]["lastpostdate"] == "2016-12-17T22:15:41Z"
    assert forums[2]["lastpostdate"] == "" and forums[2]["numthreads"] == 0


def test_parse_thing_credits_and_versions():
    g = xmlapi.thing(xmlapi.parse(fx("thing_900001.xml")))
    assert g["name"] == "Testowa Ofensywa '43" and g["year"] == "2001"
    assert [p["id"] for p in g["designers"]] == [7001, 7003]
    assert g["developers"] == [{"id": 7002, "name": "Piotr Próbny"}]
    assert g["publishers"][0]["name"] == "Wydawnictwo Testowe"
    assert [(v["name"], v["year"], v["languages"]) for v in g["versions"]] == \
        [("First edition", "2001", ["English"]), ("Second edition (living rules)", "2017", ["Polish"])]


def test_parse_user_search_and_unknown_user():
    u = xmlapi.user(xmlapi.parse(fx("user_atest.xml")))
    assert (u["username"], u["firstname"], u["lastname"]) == ("atest", "Anna", "Testowa")
    assert xmlapi.user(xmlapi.parse('<user id="" name="nobody"><firstname value=""/></user>')) is None
    hits = xmlapi.search(xmlapi.parse(fx("search_testowa.xml")))
    assert hits[0] == {"id": 900001, "type": "boardgame", "name": "Testowa Ofensywa '43", "year": "2001"}
    assert hits[1]["year"] == ""


def test_parse_thread_converts_body_and_dates():
    th = xmlapi.thread(xmlapi.parse(fx("thread_910001.xml")))
    assert th["subject"] == "Order of retreat priorities" and len(th["posts"]) == 3
    first, designer = th["posts"][0], th["posts"][1]
    assert first["postdate"] == "2016-11-26T17:10:01Z"
    assert designer["postdate"] == "2016-12-17T16:15:41Z" and designer["numedits"] == 1
    assert "Should a unit prefer distance over survival? It seems odd." in first["body_text"]
    assert "my map <https://example.invalid/map.png>" in first["body_text"] and "[obraz]" in first["body_text"]
    assert designer["body_text"].startswith("[cytat: gamer_one] Should a unit prefer distance over survival? [/cytat]")
    assert "Survival should be the first priority" in designer["body_text"]
    assert "R&D note" in designer["body_text"]


def test_html_to_text_bbcode_quote_and_long_quote_clipped():
    t = xmlapi.html_to_text('[q="Simon"]' + "x " * 300 + "[/q]Answer.")
    assert t.startswith("[cytat: Simon] x x") and "…" in t and t.endswith("Answer.")
    assert len(t) < 260


def test_normalize_name():
    assert xmlapi.normalize_name("  Jan  Drugi (I) ") == "jan drugi"
    assert xmlapi.normalize_name("Piotr Próbny") == xmlapi.normalize_name("piotr probny")



def test_evidence_schema_lint_and_render():
    from wgu.kb import lint, render as kb_render
    good = {"source": "bgg", "url": "https://boardgamegeek.com/thread/910001/article/5000002#5000002",
            "author": "atest", "role": "designer", "date": "2016-12-17",
            "quote": "Survival should be the first priority", "supports": "b", "weight": "strong"}
    amb = {"id": "N-07", "title": "Kolejność priorytetów odwrotu", "status": "open", "strength": "probable",
           "evidence": [good]}
    v = lint.validator("ambiguity")
    assert list(v.iter_errors(amb)) == []
    errors, warnings = lint.check_evidence(amb)
    assert errors == [] and any('verification' in warning for warning in warnings)
    assert "**Dowód** [bgg, waga strong, wspiera b] atest · designer · 2016-12-17" in kb_render.amb_md(amb)

    bad = dict(good, url="", quote="word " * 26, role="player", date="17.12.2016")
    amb_bad = dict(amb, evidence=[bad, good, good])
    assert any("date" in str(e.path) or "17.12.2016" in e.message for e in v.iter_errors(amb_bad))
    errors, warnings = lint.check_evidence(amb_bad)
    assert any("26 words" in e for e in errors) and any("requires url" in e for e in errors)
    assert any("strong evidence from a player" in w for w in warnings)
    assert any("duplicate" in w for w in warnings)
    assert list(v.iter_errors(dict(amb, evidence=[{"source": "faq", "quote": "x"}])))  # supports/weight required
