"""BGG operations shared by `wgu bgg …` and the MCP server: cache first, XML API2 when needed and allowed.

Incremental sync: forumlist → for each changed forum, `forum` pages (newest activity first) until the first
thread whose lastpostdate equals the synced one → changed threads synced oldest first with
`thread&minarticleid`. Every thread is committed on its own, so an interrupted sync resumes where it stopped.
"""
from __future__ import annotations

import time

from . import authority, xmlapi
from .client import BggError, BggOffline, Client
from .store import Store, age_seconds, now_iso

FORUM_PAGE = 50
THREAD_COUNT = 1000
GAME_TTL = 7 * 86400
FORUMS_TTL = 3600


class Budget(Exception):
    """Request budget of one sync run is used up."""


def settings(project) -> dict:
    cfg = dict(project.data.get("bgg") or {})
    cfg.setdefault("thing_id", None)
    cfg.setdefault("forums", [])
    cfg.setdefault("authorities", [])
    cfg.setdefault("cache", "build/bgg")
    cfg.setdefault("delay", 5)
    return cfg


class Bgg:
    def __init__(self, project, client: Client | None = None, store: Store | None = None):
        self.project = project
        self.cfg = settings(project)
        self.client = client or Client(delay=self.cfg["delay"])
        self.cache_path = project.root / self.cfg["cache"] / "bgg.sqlite"
        self._store = store
        self._budget_end: int | None = None

    @property
    def store(self) -> Store:
        if self._store is None:
            self._store = Store(self.cache_path)
        return self._store

    def close(self):
        if self._store is not None:
            self._store.close()

    # ------------------------------------------------------------ helpers
    def thing_id(self, thing_id=None) -> int:
        tid = thing_id or self.cfg.get("thing_id")
        if not tid:
            raise BggError("Brak bgg.thing_id w wgu.yaml (np. `bgg: {thing_id: 3263}`); id gry znajdziesz przez "
                           "`wgu bgg search-games \"nazwa\"`.")
        return int(tid)

    def _get(self, command: str, **params):
        if self._budget_end is not None and self.client.stats.requests >= self._budget_end:
            raise Budget()
        return xmlapi.parse(self.client.get(command, **params))

    def roles(self, thing_id: int | None = None) -> authority.Roles:
        game = None
        try:
            hit = self.store.game(self.thing_id(thing_id))
            game = hit[0] if hit else None
        except BggError:
            pass
        return authority.Roles(self.cfg.get("authorities"), game, self.store.users())

    # ------------------------------------------------------------ game, forums, threads
    def search_games(self, query: str, exact: bool = False) -> list[dict]:
        root = self._get("search", query=query, type="boardgame", exact=1 if exact else None)
        return xmlapi.search(root)[:20]

    def game(self, thing_id=None, refresh: bool = False) -> dict:
        tid = self.thing_id(thing_id)
        hit = self.store.game(tid)
        if hit and not refresh and age_seconds(hit[1]) < GAME_TTL:
            return {**hit[0], "_cached": hit[1]}
        try:
            g = xmlapi.thing(self._get("thing", id=tid, versions=1))
        except BggOffline:
            if hit:
                return {**hit[0], "_cached": hit[1], "_stale": True}
            raise
        if not g:
            raise BggError(f"BGG nie zna gry o id {tid}.")
        self.store.put_game(g)
        return g

    def forums(self, thing_id=None, refresh: bool = False) -> dict:
        tid = self.thing_id(thing_id)
        cached = self.store.forums(tid)
        fresh = cached and all(age_seconds(f["fetched_at"]) < FORUMS_TTL for f in cached)
        stale = False
        if refresh or not fresh:
            try:
                self.store.put_forums(tid, xmlapi.forumlist(self._get("forumlist", id=tid, type="thing")))
            except BggOffline:
                if not cached:
                    raise
                stale = True
        return {"thing_id": tid, "forums": self.store.forums(tid), "stale": stale}

    def threads(self, forum_id: int, page: int = 1) -> dict:
        forum = self.store.forum(forum_id)
        stale = False
        try:
            f = xmlapi.forum(self._get("forum", id=forum_id, page=page))
            self.store.put_threads(forum_id, forum["thing_id"] if forum else None, f["threads"])
            return {"forum_id": forum_id, "title": f["title"], "numthreads": f["numthreads"], "page": page,
                    "threads": [{**t, **self._thread_cache_info(t["thread_id"])} for t in f["threads"]],
                    "stale": False}
        except BggOffline:
            stale = True
        rows = self.store.threads(forum_id, (page - 1) * FORUM_PAGE, FORUM_PAGE)
        if not rows:
            raise BggOffline(f"Brak forum {forum_id} w cache, a BGG jest niedostępne: {self.client.offline_reason()}.")
        return {"forum_id": forum_id, "title": forum["title"] if forum else "", "numthreads": forum and forum["numthreads"],
                "page": page, "threads": [{**t, **self._thread_cache_info(t["thread_id"])} for t in rows], "stale": stale}

    def _thread_cache_info(self, thread_id: int) -> dict:
        t = self.store.thread(thread_id)
        return {"cached_posts": self.store.count_posts(thread_id),
                "synced": bool(t and t["synced_lastpostdate"] and t["synced_lastpostdate"] == t["lastpostdate"])}

    def _fetch_thread(self, thread_id: int, min_id: int | None, synced_lastpostdate: str | None) -> int:
        """Fetch posts (all, or from min_id) in batches of THREAD_COUNT; returns number of posts fetched."""
        got = 0
        while True:
            th = xmlapi.thread(self._get("thread", id=thread_id, minarticleid=min_id, count=THREAD_COUNT))
            if not self.store.thread(thread_id):
                self.store.put_threads(None, None, [{"thread_id": thread_id, "subject": th["subject"],
                                                     "numarticles": th["numarticles"]}])
            last_batch = len(th["posts"]) < THREAD_COUNT
            self.store.put_posts(thread_id, th["posts"], synced_lastpostdate if last_batch else None)
            got += len(th["posts"])
            if last_batch:
                return got
            min_id = max(p["post_id"] for p in th["posts"]) + 1

    def thread(self, thread_id: int, offset: int = 0, limit: int = 25, refresh: bool = False) -> dict:
        t = self.store.thread(thread_id)
        have = self.store.count_posts(thread_id)
        if not have:
            up_to_date = False
        elif t["lastpostdate"]:  # known from a forum listing: compare with the synced state
            up_to_date = t["synced_lastpostdate"] == t["lastpostdate"]
        else:  # fetched on its own: trust it for an hour
            up_to_date = age_seconds(t["posts_fetched_at"]) < FORUMS_TTL
        stale = False
        if refresh or not up_to_date:
            try:
                min_id = (t["max_post_id"] + 1) if (t and have and not refresh) else None
                self._fetch_thread(thread_id, min_id, (t["lastpostdate"] or None) if t else None)
            except BggOffline:
                if not have:
                    raise
                stale = True
        t = self.store.thread(thread_id) or {"thread_id": thread_id}
        roles = self.roles(t.get("thing_id"))
        posts = [{**p, "role": roles.role(p["username"])} for p in self.store.posts(thread_id, offset, limit)]
        return {"thread": t, "total": self.store.count_posts(thread_id), "offset": offset, "posts": posts,
                "stale": stale}

    # ------------------------------------------------------------ sync
    def sync(self, thing_id=None, forums: list[int] | None = None, max_requests: int | None = None,
             full: bool = False, progress=None) -> dict:
        tid = self.thing_id(thing_id)
        say = progress or (lambda msg: None)
        start_req, start_retry, t0 = self.client.stats.requests, self.client.stats.retries, time.monotonic()
        self._budget_end = start_req + max_requests if max_requests else None
        report = {"thing_id": tid, "forums": [], "threads_synced": 0, "posts_fetched": 0, "complete": True,
                  "remaining_threads": 0}
        wanted = [int(f) for f in (forums or self.cfg.get("forums") or [])]
        try:
            if not self.client.online:
                raise BggOffline(f"Sync wymaga dostępu do BGG: {self.client.offline_reason()}.")
            self.store.put_forums(tid, xmlapi.forumlist(self._get("forumlist", id=tid, type="thing")))
            for f in self.store.forums(tid):
                if wanted and f["forum_id"] not in wanted:
                    continue
                fr = {"forum_id": f["forum_id"], "title": f["title"], "changed_threads": 0, "skipped": False}
                report["forums"].append(fr)
                if not f["numthreads"] or (not full and f["synced_lastpostdate"] == f["lastpostdate"]):
                    fr["skipped"] = True
                    continue
                changed = self._changed_threads(f, tid, full)
                fr["changed_threads"] = len(changed)
                report["remaining_threads"] += len(changed)
                say(f"forum {f['forum_id']} {f['title']}: {len(changed)} wątków do pobrania")
                for t in sorted(changed, key=lambda x: (x["lastpostdate"], x["thread_id"])):  # oldest first
                    known = self.store.thread(t["thread_id"])
                    min_id = None if full or not known or not known["max_post_id"] else known["max_post_id"] + 1
                    n = self._fetch_thread(t["thread_id"], min_id, t["lastpostdate"])
                    report["threads_synced"] += 1
                    report["posts_fetched"] += n
                    report["remaining_threads"] -= 1
                    say(f"  wątek {t['thread_id']} {t['subject'][:60]}: +{n} postów")
                self.store.mark_forum_synced(f["forum_id"], f["lastpostdate"])
        except Budget:
            report["complete"] = False
            report["stopped"] = f"limit {max_requests} zapytań; uruchom sync ponownie, by kontynuować"
        finally:
            self._budget_end = None
        report["requests"] = self.client.stats.requests - start_req
        report["retries"] = self.client.stats.retries - start_retry
        report["seconds"] = round(time.monotonic() - t0, 1)
        report["finished_at"] = now_iso()
        self.store.set_meta(f"last_sync:{tid}", report)
        return report

    def _changed_threads(self, f: dict, tid: int, full: bool) -> list[dict]:
        changed, page = [], 1
        while True:
            listing = xmlapi.forum(self._get("forum", id=f["forum_id"], page=page))
            self.store.put_threads(f["forum_id"], tid, listing["threads"])
            for t in listing["threads"]:
                known = self.store.thread(t["thread_id"])
                if not full and known and known["synced_lastpostdate"] == t["lastpostdate"]:
                    return changed
                changed.append(t)
            if len(listing["threads"]) < FORUM_PAGE or page * FORUM_PAGE >= (listing["numthreads"] or f["numthreads"]):
                return changed
            page += 1

    # ------------------------------------------------------------ search, files, authorities, status
    def search_posts(self, query: str, thing_id=None, author_role: str | None = None, forum_id: int | None = None,
                     limit: int = 10) -> list[dict]:
        tid = self.thing_id(thing_id)
        roles = self.roles(tid)
        include = exclude = None
        if author_role:
            if author_role.rstrip("?") not in authority.ROLES:
                raise BggError(f"Nieznana rola {author_role!r}; dozwolone: {', '.join(authority.ROLES)}.")
            if author_role == "player":
                exclude = roles.authorities()
            else:
                include = roles.users_with_role(author_role)
        hits = self.store.search(query, tid, forum_id, include, exclude, limit=max(limit * 5, 50))
        for h in hits:
            h["role"] = roles.role(h["username"])
            h["rank"] = h["score"] * (1 + authority.boost(h["role"]))  # bm25 is negative: lower is better
        hits.sort(key=lambda h: h["rank"])
        return hits[:limit]

    def files(self, thing_id=None) -> dict:
        tid = self.thing_id(thing_id)
        return {"thing_id": tid, "files_page": f"https://boardgamegeek.com/boardgame/{tid}/x/files",
                "errata": list(self.project.data.get("sources", {}).get("errata") or [])}

    def authorities(self, thing_id=None, suggest: bool = False, min_posts: int = 3) -> dict:
        tid = self.thing_id(thing_id)
        out = {"configured": list(self.cfg.get("authorities") or []), "suggested": []}
        if suggest:
            game = self.game(tid)
            posters = [(u, n) for u, n in self.store.poster_counts(tid) if n >= min_posts]
            users: dict[str, dict | None] = {}
            for username, _ in posters:
                cached = self.store.user(username)
                if cached is None and self.client.online:
                    cached = xmlapi.user(self._get("user", name=username)) or {}
                    self.store.put_user(username, cached)
                users[username] = cached
            out["suggested"] = authority.suggest(game, posters, users, self.cfg.get("authorities"), min_posts)
        return out

    def status(self) -> dict:
        tid = self.cfg.get("thing_id")
        exists = self._store is not None or self.cache_path.exists()  # status must not create the cache
        return {"thing_id": tid, "online": self.client.online, "offline_reason": None if self.client.online
                else self.client.offline_reason(), "delay": self.client.delay, "cache": str(self.cache_path),
                "counts": self.store.counts() if exists else dict.fromkeys(("games", "forums", "threads", "posts", "users"), 0),
                "last_sync": self.store.meta(f"last_sync:{tid}") if exists and tid else None}
