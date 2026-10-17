"""SQLite cache of BGG data with an FTS5 index of posts.

Lives in the game directory outside git (`bgg.cache`, default build/bgg/bgg.sqlite). Posts are indexed with
the Porter stemmer, so "retreat priority" finds "Priorities in the Retreat".
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1

DDL = """
CREATE TABLE IF NOT EXISTS games(thing_id INTEGER PRIMARY KEY, name TEXT, year TEXT, data TEXT, fetched_at TEXT);
CREATE TABLE IF NOT EXISTS forums(forum_id INTEGER PRIMARY KEY, thing_id INTEGER, title TEXT, numthreads INTEGER,
    numposts INTEGER, lastpostdate TEXT, synced_lastpostdate TEXT, fetched_at TEXT);
CREATE TABLE IF NOT EXISTS threads(thread_id INTEGER PRIMARY KEY, forum_id INTEGER, thing_id INTEGER, subject TEXT,
    author TEXT, numarticles INTEGER, postdate TEXT, lastpostdate TEXT, synced_lastpostdate TEXT,
    max_post_id INTEGER NOT NULL DEFAULT 0, fetched_at TEXT, posts_fetched_at TEXT);
CREATE INDEX IF NOT EXISTS threads_forum ON threads(forum_id, lastpostdate);
CREATE TABLE IF NOT EXISTS posts(post_id INTEGER PRIMARY KEY, thread_id INTEGER NOT NULL, username TEXT,
    postdate TEXT, editdate TEXT, numedits INTEGER, subject TEXT, body_html TEXT, body_text TEXT);
CREATE INDEX IF NOT EXISTS posts_thread ON posts(thread_id, post_id);
CREATE INDEX IF NOT EXISTS posts_user ON posts(username COLLATE NOCASE);
CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY COLLATE NOCASE, user_id INTEGER, firstname TEXT,
    lastname TEXT, fetched_at TEXT);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts USING fts5(subject, body_text, content='posts', content_rowid='post_id',
    tokenize='porter unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS posts_ai AFTER INSERT ON posts BEGIN
    INSERT INTO posts_fts(rowid, subject, body_text) VALUES (new.post_id, new.subject, new.body_text); END;
CREATE TRIGGER IF NOT EXISTS posts_ad AFTER DELETE ON posts BEGIN
    INSERT INTO posts_fts(posts_fts, rowid, subject, body_text) VALUES ('delete', old.post_id, old.subject, old.body_text); END;
CREATE TRIGGER IF NOT EXISTS posts_au AFTER UPDATE ON posts BEGIN
    INSERT INTO posts_fts(posts_fts, rowid, subject, body_text) VALUES ('delete', old.post_id, old.subject, old.body_text);
    INSERT INTO posts_fts(rowid, subject, body_text) VALUES (new.post_id, new.subject, new.body_text); END;
"""

_FTS_SYNTAX = re.compile(r'["*():^]|\b(AND|OR|NOT|NEAR)\b')


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def age_seconds(iso: str | None) -> float:
    if not iso:
        return float("inf")
    try:
        then = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return float("inf")
    return (datetime.now(timezone.utc) - then).total_seconds()


def fts_query(text: str) -> str:
    """Plain words → AND of quoted tokens; text using FTS5 syntax (quotes, OR, NEAR, *) is passed through."""
    if _FTS_SYNTAX.search(text):
        return text
    tokens = re.findall(r"\w+", text)
    return " ".join('"' + t.replace('"', '""') + '"' for t in tokens)


class Store:
    def __init__(self, path: Path | str):
        self.path = Path(path) if str(path) != ":memory:" else path
        if isinstance(self.path, Path):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(self.path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        if isinstance(self.path, Path):
            self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(DDL)
        self.db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        self.db.commit()

    def close(self):
        self.db.close()

    # ------------------------------------------------------------ games
    def put_game(self, game: dict):
        self.db.execute("INSERT INTO games VALUES (?,?,?,?,?) ON CONFLICT(thing_id) DO UPDATE SET name=excluded.name, "
                        "year=excluded.year, data=excluded.data, fetched_at=excluded.fetched_at",
                        (game["id"], game["name"], game["year"], json.dumps(game, ensure_ascii=False), now_iso()))
        self.db.commit()

    def game(self, thing_id: int) -> tuple[dict, str] | None:
        r = self.db.execute("SELECT data, fetched_at FROM games WHERE thing_id=?", (thing_id,)).fetchone()
        return (json.loads(r["data"]), r["fetched_at"]) if r else None

    # ------------------------------------------------------------ forums
    def put_forums(self, thing_id: int, forums: list[dict]):
        ts = now_iso()
        for f in forums:
            self.db.execute(
                "INSERT INTO forums(forum_id, thing_id, title, numthreads, numposts, lastpostdate, fetched_at) "
                "VALUES (?,?,?,?,?,?,?) ON CONFLICT(forum_id) DO UPDATE SET thing_id=excluded.thing_id, "
                "title=excluded.title, numthreads=excluded.numthreads, numposts=excluded.numposts, "
                "lastpostdate=excluded.lastpostdate, fetched_at=excluded.fetched_at",
                (f["forum_id"], thing_id, f["title"], f["numthreads"], f["numposts"], f["lastpostdate"], ts))
        self.db.commit()

    def forums(self, thing_id: int) -> list[dict]:
        rows = self.db.execute(
            "SELECT f.*, (SELECT COUNT(*) FROM threads t WHERE t.forum_id=f.forum_id) AS cached_threads, "
            "(SELECT COUNT(*) FROM posts p JOIN threads t ON p.thread_id=t.thread_id WHERE t.forum_id=f.forum_id) "
            "AS cached_posts FROM forums f WHERE thing_id=? ORDER BY forum_id", (thing_id,)).fetchall()
        return [dict(r) for r in rows]

    def forum(self, forum_id: int) -> dict | None:
        r = self.db.execute("SELECT * FROM forums WHERE forum_id=?", (forum_id,)).fetchone()
        return dict(r) if r else None

    def mark_forum_synced(self, forum_id: int, lastpostdate: str):
        self.db.execute("UPDATE forums SET synced_lastpostdate=? WHERE forum_id=?", (lastpostdate, forum_id))
        self.db.commit()

    # ------------------------------------------------------------ threads
    def put_threads(self, forum_id: int | None, thing_id: int | None, threads: list[dict]):
        ts = now_iso()
        for t in threads:
            self.db.execute(
                "INSERT INTO threads(thread_id, forum_id, thing_id, subject, author, numarticles, postdate, "
                "lastpostdate, fetched_at) VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(thread_id) DO UPDATE SET "
                "forum_id=COALESCE(excluded.forum_id, forum_id), thing_id=COALESCE(excluded.thing_id, thing_id), "
                "subject=COALESCE(NULLIF(excluded.subject,''), subject), author=COALESCE(NULLIF(excluded.author,''), author), "
                "numarticles=MAX(excluded.numarticles, numarticles), postdate=COALESCE(NULLIF(excluded.postdate,''), postdate), "
                "lastpostdate=COALESCE(NULLIF(excluded.lastpostdate,''), lastpostdate), fetched_at=excluded.fetched_at",
                (t["thread_id"], forum_id, thing_id, t.get("subject", ""), t.get("author", ""),
                 t.get("numarticles", 0), t.get("postdate", ""), t.get("lastpostdate", ""), ts))
        self.db.commit()

    def thread(self, thread_id: int) -> dict | None:
        r = self.db.execute("SELECT t.*, f.title AS forum_title FROM threads t LEFT JOIN forums f "
                            "ON f.forum_id=t.forum_id WHERE thread_id=?", (thread_id,)).fetchone()
        return dict(r) if r else None

    def threads(self, forum_id: int, offset: int = 0, limit: int = 50) -> list[dict]:
        rows = self.db.execute("SELECT * FROM threads WHERE forum_id=? ORDER BY lastpostdate DESC, thread_id DESC "
                               "LIMIT ? OFFSET ?", (forum_id, limit, offset)).fetchall()
        return [dict(r) for r in rows]

    def put_posts(self, thread_id: int, posts: list[dict], synced_lastpostdate: str | None = None):
        """Upsert posts of one thread and (optionally) mark the thread synced, in one transaction."""
        with self.db:
            for p in posts:
                self.db.execute(
                    "INSERT INTO posts VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(post_id) DO UPDATE SET "
                    "username=excluded.username, postdate=excluded.postdate, editdate=excluded.editdate, "
                    "numedits=excluded.numedits, subject=excluded.subject, body_html=excluded.body_html, "
                    "body_text=excluded.body_text",
                    (p["post_id"], thread_id, p["username"], p["postdate"], p["editdate"], p["numedits"],
                     p["subject"], p["body_html"], p["body_text"]))
            mx = self.db.execute("SELECT COALESCE(MAX(post_id),0) FROM posts WHERE thread_id=?", (thread_id,)).fetchone()[0]
            self.db.execute("UPDATE threads SET max_post_id=?, posts_fetched_at=? WHERE thread_id=?",
                            (mx, now_iso(), thread_id))
            if synced_lastpostdate is not None:
                self.db.execute("UPDATE threads SET synced_lastpostdate=? WHERE thread_id=?",
                                (synced_lastpostdate, thread_id))

    def posts(self, thread_id: int, offset: int = 0, limit: int = 25) -> list[dict]:
        rows = self.db.execute("SELECT * FROM posts WHERE thread_id=? ORDER BY post_id LIMIT ? OFFSET ?",
                               (thread_id, limit, offset)).fetchall()
        return [dict(r) for r in rows]

    def count_posts(self, thread_id: int) -> int:
        return self.db.execute("SELECT COUNT(*) FROM posts WHERE thread_id=?", (thread_id,)).fetchone()[0]

    def poster_counts(self, thing_id: int) -> list[tuple[str, int]]:
        rows = self.db.execute("SELECT p.username, COUNT(*) n FROM posts p JOIN threads t ON p.thread_id=t.thread_id "
                               "WHERE t.thing_id=? GROUP BY p.username COLLATE NOCASE ORDER BY n DESC", (thing_id,))
        return [(r["username"], r["n"]) for r in rows]

    # ------------------------------------------------------------ search
    def search(self, query: str, thing_id: int | None = None, forum_id: int | None = None,
               include_users: list[str] | None = None, exclude_users: list[str] | None = None,
               limit: int = 50) -> list[dict]:
        where, args = ["posts_fts MATCH ?"], [fts_query(query)]
        if thing_id is not None:
            where.append("t.thing_id=?"); args.append(thing_id)
        if forum_id is not None:
            where.append("t.forum_id=?"); args.append(forum_id)
        for users, op in ((include_users, "IN"), (exclude_users, "NOT IN")):
            if users is not None:
                where.append(f"p.username COLLATE NOCASE {op} ({','.join('?' * len(users))})" if users
                             else ("0" if op == "IN" else "1"))
                args += list(users)
        sql = ("SELECT p.post_id, p.thread_id, p.username, p.postdate, t.subject AS thread_subject, t.forum_id, "
               "f.title AS forum_title, bm25(posts_fts, 0.5, 1.0) AS score, "
               "snippet(posts_fts, 1, '«', '»', ' … ', 28) AS snippet "
               "FROM posts_fts JOIN posts p ON p.post_id=posts_fts.rowid "
               "LEFT JOIN threads t ON t.thread_id=p.thread_id LEFT JOIN forums f ON f.forum_id=t.forum_id "
               f"WHERE {' AND '.join(where)} ORDER BY score LIMIT ?")
        try:
            rows = self.db.execute(sql, args + [limit]).fetchall()
        except sqlite3.OperationalError:  # invalid FTS5 syntax typed by the user: fall back to plain words
            args[0] = " ".join('"' + t + '"' for t in re.findall(r"\w+", query))
            if not args[0]:
                return []
            rows = self.db.execute(sql, args + [limit]).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------ users, meta
    def put_user(self, username: str, u: dict | None):
        u = u or {}
        self.db.execute("INSERT INTO users VALUES (?,?,?,?,?) ON CONFLICT(username) DO UPDATE SET "
                        "user_id=excluded.user_id, firstname=excluded.firstname, lastname=excluded.lastname, "
                        "fetched_at=excluded.fetched_at",
                        (username, u.get("user_id"), u.get("firstname", ""), u.get("lastname", ""), now_iso()))
        self.db.commit()

    def user(self, username: str) -> dict | None:
        r = self.db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        return dict(r) if r else None

    def users(self) -> list[dict]:
        return [dict(r) for r in self.db.execute("SELECT * FROM users")]

    def set_meta(self, key: str, value):
        self.db.execute("INSERT INTO meta VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                        (key, json.dumps(value, ensure_ascii=False)))
        self.db.commit()

    def meta(self, key: str, default=None):
        r = self.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return json.loads(r["value"]) if r else default

    def counts(self) -> dict:
        return {t: self.db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in ("games", "forums", "threads", "posts", "users")}
