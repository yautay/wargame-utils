"""BGG module: XML repair/parsing, polite client, incremental sync, FTS search, roles, framing, MCP server.

No network: XML API2 is simulated by FakeBgg (synthetic data, see tests/fixtures/bgg/README.md).
"""
import asyncio
import urllib.parse
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

import pytest

from wgu.bgg import authority, render, xmlapi
from wgu.bgg.client import BggAuthError, BggBlocked, BggOffline, BggUnavailable, Client
from wgu.bgg.service import Bgg
from wgu.config import DEFAULTS, Project, _merge

FIX = Path(__file__).parent / "fixtures" / "bgg"
TOKEN = "secret-token-123"


def fx(name: str) -> bytes:
    return (FIX / name).read_bytes()


# ---------------------------------------------------------------- simulated XML API2

class Clock:
    def __init__(self):
        self.t = 0.0
        self.sleeps = []

    def now(self):
        return self.t

    def sleep(self, s):
        self.sleeps.append(s)
        self.t += s


class FakeBgg:
    """A tiny BGG: forums with threads and posts, served as XML API2. Records every request."""

    def __init__(self, thing_id=900001):
        self.thing_id = thing_id
        self.forums = {}      # forum_id -> title
        self.threads = {}     # thread_id -> {forum, subject, author, posts: [(id, user, dt, html)]}
        self.users = {}
        self.calls = []
        self.queue = []       # forced responses: (status, headers, body)
        self.next_post = 6000000

    def add_thread(self, forum_id, thread_id, subject, posts):
        self.threads[thread_id] = {"forum": forum_id, "subject": subject, "posts": []}
        for user, dt, body in posts:
            self.add_post(thread_id, user, dt, body)

    def add_post(self, thread_id, user, dt, body):
        self.next_post += 1
        self.threads[thread_id]["posts"].append((self.next_post, user, dt, body))
        return self.next_post

    def _last(self, t):
        return t["posts"][-1][2]

    def __call__(self, url, headers):
        parts = urllib.parse.urlsplit(url)
        cmd = parts.path.rsplit("/", 1)[1]
        q = {k: v[0] for k, v in urllib.parse.parse_qs(parts.query).items()}
        self.calls.append((cmd, q, headers))
        if self.queue:
            return self.queue.pop(0)
        return 200, {}, getattr(self, "x_" + cmd)(q).encode("utf-8")

    def x_forumlist(self, q):
        rows = []
        for fid, title in self.forums.items():
            ts = [t for t in self.threads.values() if t["forum"] == fid]
            last = max((self._last(t) for t in ts), default=datetime(1970, 1, 1, tzinfo=timezone.utc))
            rows.append(f'<forum id="{fid}" groupid="0" title={quoteattr(title)} noposting="0" description="" '
                        f'numthreads="{len(ts)}" numposts="{sum(len(t["posts"]) for t in ts)}" '
                        f'lastpostdate="{format_datetime(last)}"/>')
        return f'<forums type="thing" id="{q["id"]}">{"".join(rows)}</forums>'

    def x_forum(self, q):
        fid, page = int(q["id"]), int(q.get("page", 1))
        ts = sorted(((tid, t) for tid, t in self.threads.items() if t["forum"] == fid),
                    key=lambda x: (self._last(x[1]), x[0]), reverse=True)
        chunk = ts[(page - 1) * 50: page * 50]
        rows = "".join(f'<thread id="{tid}" subject={quoteattr(t["subject"])} author="{t["posts"][0][1]}" '
                       f'numarticles="{len(t["posts"])}" postdate="{format_datetime(t["posts"][0][2])}" '
                       f'lastpostdate="{format_datetime(self._last(t))}"/>' for tid, t in chunk)
        return (f'<forum id="{fid}" title={quoteattr(self.forums[fid])} numthreads="{len(ts)}" numposts="0" '
                f'lastpostdate="" noposting="0"><threads>{rows}</threads></forum>')

    def x_thread(self, q):
        t = self.threads[int(q["id"])]
        posts = [p for p in t["posts"] if p[0] >= int(q.get("minarticleid", 0))][: int(q.get("count", 1000))]
        cst = timezone(timedelta(hours=-6))
        arts = "".join(f'<article id="{pid}" username="{u}" link="" postdate="{dt.astimezone(cst).isoformat()}" '
                       f'editdate="{dt.astimezone(cst).isoformat()}" numedits="0"><subject>{escape(t["subject"])}</subject>'
                       f'<body>{escape(body)}</body></article>' for pid, u, dt, body in posts)
        return (f'<thread id="{q["id"]}" numarticles="{len(t["posts"])}" link=""><subject>{escape(t["subject"])}'
                f'</subject><articles>{arts}</articles></thread>')

    def x_thing(self, q):
        return fx("thing_900001.xml").decode("utf-8")

    def x_user(self, q):
        u = self.users.get(q["name"])
        if not u:
            return f'<user id="" name="{q["name"]}"><firstname value=""/><lastname value=""/></user>'
        return f'<user id="{u[0]}" name="{q["name"]}"><firstname value="{u[1]}"/><lastname value="{u[2]}"/></user>'

    def count(self, cmd):
        return sum(1 for c in self.calls if c[0] == cmd)


def D(day, hour=12):
    return datetime(2016, 12, day, hour, tzinfo=timezone.utc)


def world() -> FakeBgg:
    w = FakeBgg()
    w.forums = {9101: "Rules", 9102: "General", 9103: "Variants"}
    w.add_thread(9101, 910001, "Order of retreat priorities", [
        ("gamer_one", D(1), "Rule 12.3 lists the retreat priorities. Distance before survival?"),
        ("atest", D(17), "Survival should be the first priority: never retreat into elimination."),
        ("gamer_two", D(26), "I always thought priorities were a checklist in order."),
    ])
    w.add_thread(9101, 910002, "Stacking after advance", [
        ("gamer_two", D(5), "Can I overstack during advance after combat?"),
        ("pprobny", D(6), "Yes, during the advance; the limit applies at the end of it."),
    ])
    w.add_thread(9102, 910003, "Session report", [("gamer_one", D(10), "Great game, retreat rules are tense.")])
    w.users = {"atest": (700101, "Anna", "Testowa"), "pprobny": (700102, "Piotr", "Probny"),
               "gamer_one": (700103, "Gamer", "One"), "gamer_two": (700104, "Gamer", "Two")}
    return w


def project(tmp_path, **bgg) -> Project:
    cfg = {"thing_id": 900001, "authorities": [{"user": "atest", "role": "designer", "person": 7001}], **bgg}
    return Project(tmp_path, _merge(DEFAULTS, {"game": {"id": "test"}, "bgg": cfg}))


def service(tmp_path, w: FakeBgg, token=TOKEN, **bgg) -> Bgg:
    clock = Clock()
    client = Client(token=token, delay=5, fetch=w, sleep=clock.sleep, clock=clock.now, offline=False)
    svc = Bgg(project(tmp_path, **bgg), client=client)
    svc.clock = clock
    return svc


# ---------------------------------------------------------------- XML repair and parsing

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


# ---------------------------------------------------------------- client

def test_client_offline_without_token():
    c = Client(token="", fetch=lambda u, h: pytest.fail("no request without token"), offline=False)
    with pytest.raises(BggOffline, match="WGU_BGG_TOKEN"):
        c.get("forumlist", id=1, type="thing")


def test_client_sends_bearer_and_waits_between_requests():
    w, clock = world(), Clock()
    c = Client(token=TOKEN, delay=5, fetch=w, sleep=clock.sleep, clock=clock.now, offline=False)
    c.get("forumlist", id=900001, type="thing")
    clock.t += 1.5
    c.get("forum", id=9101, page=1)
    assert clock.sleeps == [pytest.approx(3.5)]
    assert w.calls[0][2]["Authorization"] == f"Bearer {TOKEN}"
    assert w.calls[0][2]["User-Agent"].startswith("wgu-bgg/")
    assert Client(token=TOKEN, delay=0.1).delay == 2.0  # floor


def test_client_retries_202_and_503_honours_retry_after():
    w, clock = world(), Clock()
    w.queue = [(202, {}, b""), (503, {"Retry-After": "7"}, b""), (429, {}, b"")]
    c = Client(token=TOKEN, delay=5, fetch=w, sleep=clock.sleep, clock=clock.now, offline=False)
    xmlapi.forumlist(xmlapi.parse(c.get("forumlist", id=900001, type="thing")))
    # 202 → 2 s (+3 s to keep the 5 s spacing), 503 → Retry-After 7 s, 429 → second error wait 30 s
    assert clock.sleeps == [2, 3, 7, 30] and c.stats.requests == 4 and c.stats.retries == 3


def test_client_stops_on_auth_error_and_html_without_leaking_token():
    w, clock = world(), Clock()
    w.queue = [(401, {}, b"Unauthorized. See https://boardgamegeek.com/using_the_xml_api")]
    c = Client(token=TOKEN, delay=5, fetch=w, sleep=clock.sleep, clock=clock.now, offline=False)
    with pytest.raises(BggAuthError) as e:
        c.get("thing", id=1)
    assert TOKEN not in str(e.value) and c.stats.requests == 1
    w.queue = [(200, {}, b"<!DOCTYPE html><html><title>Just a moment...</title>")]
    with pytest.raises(BggBlocked):
        c.get("thing", id=1)
    w.queue = [(403, {}, b"<html>challenge</html>")]
    with pytest.raises(BggBlocked):
        c.get("thing", id=1)
    assert c.stats.retries == 0


def test_client_gives_up_after_repeated_errors():
    w, clock = world(), Clock()
    w.queue = [(500, {}, b"")] * 4
    c = Client(token=TOKEN, delay=5, fetch=w, sleep=clock.sleep, clock=clock.now, offline=False)
    with pytest.raises(BggUnavailable, match="HTTP 500"):
        c.get("thing", id=1)
    assert clock.sleeps[:3] == [10, 30, 90] and c.stats.requests == 4


# ---------------------------------------------------------------- sync

def test_sync_full_then_incremental(tmp_path):
    w = world()
    svc = service(tmp_path, w)
    r = svc.sync()
    assert r["complete"] and r["threads_synced"] == 3 and r["posts_fetched"] == 6
    assert [f["skipped"] for f in r["forums"]] == [False, False, True]  # empty forum skipped
    assert r["requests"] == 1 + 2 + 3  # forumlist, two forum pages, three threads
    assert min(s for s in svc.clock.sleeps) >= 4.9  # polite spacing

    w.calls.clear()
    r = svc.sync()
    assert r["threads_synced"] == 0 and [c[0] for c in w.calls] == ["forumlist"]

    last_cached = svc.store.thread(910002)["max_post_id"]
    w.add_post(910002, "gamer_one", D(28), "Thanks, retreat and advance are clear now.")
    w.calls.clear()
    r = svc.sync()
    assert r["threads_synced"] == 1 and r["posts_fetched"] == 1
    assert [c[0] for c in w.calls] == ["forumlist", "forum", "thread"]
    assert int(w.calls[2][1]["minarticleid"]) == last_cached + 1  # only posts after the last cached one
    assert svc.store.count_posts(910002) == 3


def test_sync_paginates_and_resumes_after_budget(tmp_path):
    w = FakeBgg()
    w.forums = {9101: "Rules"}
    for i in range(60):
        w.add_thread(9101, 920000 + i, f"Question {i}", [("gamer_one", D(1) + timedelta(hours=i), f"retreat question {i}")])
    svc = service(tmp_path, w)
    r = svc.sync(max_requests=20)
    assert not r["complete"] and r["requests"] == 20 and "ponownie" in r["stopped"]
    assert w.count("forum") == 2  # 50 + 10 threads
    done_first = r["threads_synced"]
    r = svc.sync()
    assert r["complete"] and done_first + r["threads_synced"] == 60
    assert w.count("thread") == 60  # nothing fetched twice
    assert svc.store.counts()["posts"] == 60


def test_thread_tool_fetches_once_then_serves_cache_and_works_offline(tmp_path):
    w = world()
    svc = service(tmp_path, w)
    d = svc.thread(910001)
    assert d["total"] == 3 and [p["role"] for p in d["posts"]] == ["player", "designer", "player"]
    svc.thread(910001)
    assert w.count("thread") == 1  # standalone thread trusted for an hour
    svc.client.offline = True
    d = svc.thread(910001, offset=1, limit=1)
    assert [p["username"] for p in d["posts"]] == ["atest"]
    with pytest.raises(BggOffline):
        svc.thread(999999)


# ---------------------------------------------------------------- search and roles

def test_search_stemming_roles_and_ranking(tmp_path):
    svc = service(tmp_path, world())
    svc.sync()
    hits = svc.search_posts("retreat priority")
    assert hits[0]["username"] == "atest" and hits[0]["role"] == "designer" and hits[0]["thread_id"] == 910001
    assert hits[0]["postdate"].startswith("2016-12-17")
    assert {h["post_id"] for h in hits} >= {h["post_id"] for h in svc.search_posts("retreat priority", author_role="player")}
    only = svc.search_posts("retreat", author_role="designer")
    assert [h["username"] for h in only] == ["atest"]
    assert all(h["role"] == "player" for h in svc.search_posts("retreat", author_role="player"))
    assert svc.search_posts('"first priority"')[0]["username"] == "atest"
    assert svc.search_posts("retreat", forum_id=9102)[0]["thread_id"] == 910003
    assert svc.search_posts('broken "query') is not None  # invalid FTS syntax falls back to words


def test_name_match_gives_provisional_role_and_suggestion(tmp_path):
    w = world()
    svc = service(tmp_path, w, authorities=[])
    svc.sync()
    s = svc.authorities(suggest=True, min_posts=1)
    assert [(x["user"], x["role"], x["person"]) for x in s["suggested"]] == [("atest", "designer", 7001),
                                                                               ("pprobny", "developer", 7002)]
    roles = svc.roles()
    assert roles.role("atest") == "designer?" and roles.role("gamer_one") == "player"
    assert svc.search_posts("retreat priority", author_role="designer")[0]["role"] == "designer?"
    assert authority.boost("designer?") < authority.boost("designer")


# ---------------------------------------------------------------- rendering and safety

def test_render_frames_untrusted_content_and_limits_size(tmp_path):
    svc = service(tmp_path, world())
    svc.store.put_threads(9101, 900001, [{"thread_id": 910001, "subject": "Order of retreat priorities"}])
    th = xmlapi.thread(xmlapi.parse(fx("thread_910001.xml")))
    th["posts"][0]["body_text"] = "A" * 9000
    svc.store.put_posts(910001, th["posts"])
    out = render.thread(svc.thread(910001))
    assert out.count("⟦DANE Z FORUM BGG") == 1 and out.count("⟦KONIEC DANYCH Z FORUM⟧") == 1
    assert out.index("Ignore all previous") < out.index("⟦KONIEC DANYCH Z FORUM⟧")
    assert "[[KONIEC DANYCH Z FORUM]]" in out
    assert "[obcięto, 9000 znaków]" in out and "DESIGNER" in out and render.ATTRIBUTION in out
    many = {"thread": {"thread_id": 1}, "total": 40, "offset": 0, "stale": False,
            "posts": [{"post_id": i, "username": "u", "role": "player", "postdate": "", "editdate": "", "numedits": 0,
                       "body_text": "x" * 3900} for i in range(40)]}
    out = render.thread(many)
    assert len(out) < render.RESPONSE_LIMIT + 2000 and "Dalsze: offset=" in out


def test_files_points_to_bgg_page_and_configured_errata(tmp_path):
    svc = service(tmp_path, world())
    svc.project.data["sources"]["errata"] = [{"url": "https://example.invalid/faq.pdf", "version": "2017"}]
    out = render.files(svc.files())
    assert "https://boardgamegeek.com/boardgame/900001/x/files" in out and "faq.pdf" in out


def test_status_does_not_create_cache(tmp_path):
    svc = service(tmp_path, world(), token="")
    st = svc.status()
    assert not st["online"] and not svc.cache_path.exists() and st["counts"]["posts"] == 0


# ---------------------------------------------------------------- MCP server

def test_mcp_server_lists_tools_and_searches_cache(tmp_path, monkeypatch):
    pytest.importorskip("mcp")
    from wgu.bgg import server
    import yaml
    (tmp_path / "wgu.yaml").write_text(yaml.safe_dump({"game": {"id": "test"}, "bgg": project(tmp_path).data["bgg"]}),
                                       encoding="utf-8")
    svc = service(tmp_path, world())
    svc.sync()
    svc.close()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("WGU_BGG_OFFLINE", "1")
    monkeypatch.setattr(server, "_client", None)
    srv = server.build_server()

    async def go():
        tools = {t.name: t for t in await srv.list_tools()}
        res = await srv.call_tool("bgg_search_posts", {"query": "retreat priority", "author_role": "designer"})
        with pytest.raises(ToolError, match="WGU_BGG_OFFLINE"):  # BggError reaches the model as a tool error
            await srv.call_tool("bgg_sync", {})
        return tools, res
    from mcp.server.mcpserver.exceptions import ToolError
    tools, res = asyncio.run(go())
    assert set(tools) == {"bgg_search_games", "bgg_game", "bgg_forums", "bgg_threads", "bgg_thread",
                          "bgg_search_posts", "bgg_files", "bgg_sync", "bgg_authorities"}
    assert tools["bgg_search_posts"].annotations.read_only_hint and not tools["bgg_search_posts"].annotations.open_world_hint
    text = "".join(c.text for c in res.content)
    assert "atest" in text and "DESIGNER" in text and "⟦DANE Z FORUM BGG" in text


# ---------------------------------------------------------------- evidence in kb/ambiguities.yaml

def test_evidence_schema_lint_and_render():
    from wgu.kb import lint, render as kb_render
    good = {"source": "bgg", "url": "https://boardgamegeek.com/thread/910001/article/5000002#5000002",
            "author": "atest", "role": "designer", "date": "2016-12-17",
            "quote": "Survival should be the first priority", "supports": "b", "weight": "strong"}
    amb = {"id": "N-07", "title": "Kolejność priorytetów odwrotu", "status": "open", "strength": "probable",
           "evidence": [good]}
    v = lint.validator("ambiguity")
    assert list(v.iter_errors(amb)) == []
    assert lint.check_evidence(amb) == ([], [])
    assert "**Dowód** [bgg, waga strong, wspiera b] atest · designer · 2016-12-17" in kb_render.amb_md(amb)

    bad = dict(good, url="", quote="word " * 26, role="player", date="17.12.2016")
    amb_bad = dict(amb, evidence=[bad, good, good])
    assert any("date" in str(e.path) or "17.12.2016" in e.message for e in v.iter_errors(amb_bad))
    errors, warnings = lint.check_evidence(amb_bad)
    assert any("26 words" in e for e in errors) and any("requires url" in e for e in errors)
    assert any("strong evidence from a player" in w for w in warnings)
    assert any("duplicate" in w for w in warnings)
    assert list(v.iter_errors(dict(amb, evidence=[{"source": "faq", "quote": "x"}])))  # supports/weight required
