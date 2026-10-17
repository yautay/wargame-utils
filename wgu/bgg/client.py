"""Bounded, read-only BGG XML API access. Source text is never rewritten."""
from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import os
from pathlib import Path
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException
from ..bgg_authority import AuthorityRegistry

BASE = "https://boardgamegeek.com"
MAX_BYTES = 4 * 1024 * 1024


class SearchText(HTMLParser):
    """Visible text for matching only; returned source bodies remain unchanged."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in {"br", "p", "div", "li", "tr"}:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in {"p", "div", "li", "tr"}:
            self.parts.append(" ")


def search_text(body):
    parser = SearchText()
    parser.feed(body)
    return " ".join("".join(parser.parts).casefold().split())


class BGGError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward the bearer token to a redirect target.


def positive(value: int, maximum: int = 2**31 - 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise ValueError(f"Wymagana liczba całkowita 1–{maximum}.")
    return value


class BGGClient:
    def __init__(self, cache_dir=None, *, opener=None, sleep=time.sleep, clock=time.monotonic, index_path=None):
        self.cache = Path(cache_dir or os.environ.get("BGG_CACHE_DIR") or
                          Path.home() / ".cache" / "wgu" / "bgg")
        self.opener = opener or build_opener(NoRedirect())
        self.sleep, self.clock = sleep, clock
        self.lock = threading.Lock()
        self.last_request = None
        configured_index = os.environ.get('BGG_INDEX_PATH') or index_path
        self.index_path = Path(configured_index) if configured_index else self.cache / 'index.sqlite'

    def local_index(self):
        from .index import LocalIndex
        return LocalIndex(self.index_path)

    def xml(self, endpoint, **params):
        if endpoint not in {"search", "thing", "forumlist", "forum", "thread"}:
            raise ValueError("Niedozwolony endpoint.")
        if os.environ.get('BGG_OFFLINE', os.environ.get('WGU_BGG_OFFLINE', '0')) not in ('', '0'):
            raise BGGError('Tryb offline: korzystaj z lokalnego indeksu BGG.')
        token = os.environ.get("BGG_API_TOKEN", os.environ.get('WGU_BGG_TOKEN', '')).strip()
        if not token:
            raise BGGError("Ustaw zmienną środowiskową BGG_API_TOKEN.")
        url = f"{BASE}/xmlapi2/{endpoint}?{urlencode(sorted(params.items()))}"
        # Separate caches by application without storing the token itself.
        key = hashlib.sha256((token + url).encode()).hexdigest()
        path = self.cache / (key + ".xml")
        with self.lock:
            if path.exists() and time.time() - path.stat().st_mtime < 3600:
                try:
                    return ET.fromstring(path.read_bytes())
                except Exception:
                    pass  # Refetch a damaged cache entry.
            for attempt in range(3):
                if self.last_request is not None:
                    self.sleep(max(0, 5 - (self.clock() - self.last_request)))
                self.last_request = self.clock()
                try:
                    req = Request(url, headers={"Authorization": f"Bearer {token}",
                                                "User-Agent": "WGU-BGG/0.1"})
                    with self.opener.open(req, timeout=30) as response:
                        if response.status == 202:
                            raise BGGError("BGG przygotowuje dane. Spróbuj później.")
                        data = response.read(MAX_BYTES + 1)
                    if len(data) > MAX_BYTES:
                        raise BGGError("Odpowiedź przekracza limit 4 MiB; zawęź zapytanie.")
                    root = ET.fromstring(data)
                    if root.tag == "errors" or root.find("error") is not None:
                        raise BGGError("BGG zwróciło błąd dla tego zapytania.")
                    self.cache.mkdir(parents=True, exist_ok=True)
                    tmp = path.with_suffix(".tmp")
                    tmp.write_bytes(data)
                    tmp.replace(path)
                    return root
                except HTTPError as exc:
                    if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                        raise BGGError(f"BGG HTTP {exc.code}; zapytanie zatrzymane.") from None
                    retry_after = exc.headers.get("Retry-After", "") if exc.headers else ""
                    if retry_after:
                        if not retry_after.isdigit() or int(retry_after) > 60:
                            raise BGGError("BGG wymaga dłuższej przerwy; spróbuj później.") from None
                    self.sleep(max(5 * (2 ** attempt), int(retry_after or 0)))
                except (URLError, TimeoutError):
                    raise BGGError("Nie udało się połączyć z BGG.") from None
                except (ET.ParseError, DefusedXmlException, ValueError):
                    raise BGGError("Nieprawidłowa odpowiedź XML BGG.") from None

    def search_games(self, query):
        if not query.strip() or len(query) > 200:
            raise ValueError("Podaj nazwę gry (1–200 znaków).")
        root = self.xml("search", query=query, type="boardgame", exact=0)
        return [{"id": n.get("id"), "name": n.find("name").get("value"),
                 "url": f"{BASE}/boardgame/{n.get('id')}"} for n in root.findall("item")]

    def forums(self, game_id):
        root = self.xml("forumlist", id=positive(game_id), type="thing")
        forums = [dict(n.attrib) for n in root.findall("forum")]
        with self.local_index() as index:
            index.register_forums(game_id, forums)
        return forums

    def threads(self, forum_id, page=1):
        root = self.xml("forum", id=positive(forum_id), page=positive(page, 10000))
        threads = [dict(n.attrib, url=f"{BASE}/thread/{n.get('id')}")
                   for n in root.findall(".//thread")]
        with self.local_index() as index:
            index.register_threads(forum_id, threads)
        return threads

    def thread(self, thread_id, count=100, min_article_id=1, game_id=None):
        if game_id is not None:
            positive(game_id)
            with self.local_index() as index:
                index.check_game(thread_id, game_id)
        root = self.xml("thread", id=positive(thread_id), count=positive(count, 100),
                        minarticleid=positive(min_article_id))
        posts = [{"metadata": dict(n.attrib), "body": n.findtext("body", ""),
                  "subject": n.findtext("subject", ""),
                  "url": f"{BASE}/article/{n.get('id')}", "authority": "unverified"}
                 for n in root.findall(".//article")]
        if posts and min(int(p['metadata']['id']) for p in posts) < min_article_id:
            raise BGGError('BGG nie respektuje kursora wpisów; zapytanie zatrzymane.')
        if game_id is not None:
            AuthorityRegistry().annotate(posts, game_id)
        result = {"thread_id": thread_id, "posts": posts,
                "possibly_more": len(posts) == count,
                "next_min_article_id": max((int(p['metadata']['id']) for p in posts), default=min_article_id - 1) + 1}
        if game_id is not None:
            with self.local_index() as index:
                index.ingest(game_id, thread_id, result, min_article_id)
        return result

    def search_cached_posts(self, game_id, query, forum_id=None, author_role=None, limit=10):
        """Local FTS5 only: no token, metadata fetch, sync or implicit network request."""
        positive(game_id)
        positive(limit, 50)
        if forum_id is not None:
            positive(forum_id)
        if not query.strip() or len(query) > 200:
            raise ValueError('Podaj zapytanie (1–200 znaków).')
        with self.local_index() as index:
            return index.search(game_id, query, forum_id, author_role, limit)

    def game(self, game_id):
        from .xmlapi import thing
        data = thing(self.xml('thing', id=positive(game_id), versions=1))
        if data is None:
            raise BGGError('BGG nie zwróciło danych gry.')
        return data

    def find_clarifications(self, game_id, query, forum_id, pages=1):
        positive(pages, 3)
        words = query.casefold().split()
        if not words or len(query) > 200:
            raise ValueError("Podaj zapytanie (1–200 znaków).")
        if str(positive(forum_id)) not in {f["id"] for f in self.forums(game_id)}:
            raise ValueError("Forum nie należy do wskazanej gry.")
        matches, scanned = [], 0
        for page in range(1, pages + 1):
            threads = self.threads(forum_id, page)
            scanned += len(threads)
            matches.extend(t for t in threads if any(w in t.get("subject", "").casefold() for w in words))
            if len(threads) < 50:
                break
        return {"matches": matches, "threads_scanned": scanned,
                "scope": "Tytuły wątków na wskazanych stronach forum; bez przeszukania treści wpisów.",
                "warning": "Brak trafień nie oznacza braku klaryfikacji. Pobierz pasujące wątki narzędziem bgg_thread."}

    def search_posts(self, game_id, query, forum_id, page=1, thread_offset=0,
                     min_article_id=1, max_batches=5):
        """Search a bounded slice, including threads whose titles do not match."""
        positive(game_id)
        positive(forum_id)
        positive(page, 10000)
        positive(min_article_id)
        positive(max_batches, 5)
        if isinstance(thread_offset, bool) or not isinstance(thread_offset, int) or not 0 <= thread_offset < 50:
            raise ValueError("thread_offset musi mieścić się w zakresie 0–49.")
        needle = " ".join(query.casefold().split())
        if not needle or len(query) > 200:
            raise ValueError("Podaj frazę (1–200 znaków).")
        if str(forum_id) not in {f["id"] for f in self.forums(game_id)}:
            raise ValueError("Forum nie należy do wskazanej gry.")
        threads = self.threads(forum_id, page)
        registry = AuthorityRegistry()
        matches, visited = [], []
        batches = posts_scanned = 0
        cursor = None
        stop_reason = "forum_page_end"
        for offset in range(thread_offset, len(threads)):
            thread = threads[offset]
            article_id = min_article_id if offset == thread_offset else 1
            while True:
                cursor = {"page": page, "thread_offset": offset, "min_article_id": article_id}
                if batches == max_batches:
                    stop_reason = "budget_exhausted"
                    break
                try:
                    data = self.thread(int(thread["id"]), count=100, min_article_id=article_id)
                except BGGError as exc:
                    # Preserve partial results and stop immediately on BGG errors.
                    return {"matches": matches, "posts_scanned": posts_scanned,
                            "batches_scanned": batches, "visited": visited,
                            "next_cursor": cursor, "stop_reason": "bgg_error", "error": str(exc),
                            "scope": "Niepełne wyszukiwanie treści wpisów; oryginalne dane bez zmian."}
                batches += 1
                visited.append({"thread_id": thread["id"], "min_article_id": article_id,
                                "posts_scanned": len(data["posts"])})
                posts_scanned += len(data["posts"])
                registry.annotate(data['posts'], game_id)
                with self.local_index() as index:
                    index.ingest(game_id, int(thread['id']), data, article_id)
                for post in data["posts"]:
                    if needle in search_text(post["body"]):
                        matches.append({"thread": thread, "post": post})
                if not data["possibly_more"]:
                    break
                next_id = data["next_min_article_id"]
                if next_id <= article_id:
                    raise BGGError("BGG nie przesunęło pozycji wpisów; wyszukiwanie zatrzymane.")
                article_id = next_id
            if stop_reason == "budget_exhausted":
                break
        else:
            cursor = ({"page": page + 1, "thread_offset": 0, "min_article_id": 1}
                      if len(threads) == 50 and page < 10000 else None)
        return {"matches": matches, "posts_scanned": posts_scanned, "batches_scanned": batches,
                "visited": visited, "next_cursor": cursor, "stop_reason": stop_reason,
                "scope": "Treść wpisów na jednej stronie forum; fraza bez rozróżniania wielkości liter, po normalizacji odstępów i HTML tylko do dopasowania.",
                "warning": "Brak trafień nie dowodzi braku klaryfikacji. Forum zmienia się w czasie; kontynuacja po pozycji wątku może powtórzyć lub pominąć przesunięte wątki."}
