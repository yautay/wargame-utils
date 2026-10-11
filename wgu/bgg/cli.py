"""`wgu bgg …` — the same core as the MCP server, for the terminal and for plugin agents (via Bash)."""
from __future__ import annotations

import sys

from . import render
from .client import BggError

ACTIONS = ["status", "game", "forums", "threads", "thread", "sync", "search", "files", "authorities",
           "search-games", "serve"]


def add_parser(sp):
    p = sp.add_parser("bgg", help="BoardGameGeek: fora, wątki, wyszukiwanie dowodów (XML API2, cache)")
    p.add_argument("action", choices=ACTIONS)
    p.add_argument("args", nargs="*")
    p.add_argument("--thing", type=int, help="BGG thing id (default: bgg.thing_id from wgu.yaml)")
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int)
    p.add_argument("--refresh", action="store_true")
    p.add_argument("--forums", help="comma-separated forum ids for sync")
    p.add_argument("--forum", type=int, help="search only in this forum")
    p.add_argument("--max-requests", type=int)
    p.add_argument("--full", action="store_true")
    p.add_argument("--role", help="designer | developer | publisher | player")
    p.add_argument("--suggest", action="store_true")
    p.add_argument("--exact", action="store_true")
    return p


def run(a, project_loader) -> int:
    if a.action == "serve":
        from .server import main
        main()
        return 0
    from .service import Bgg
    svc = Bgg(project_loader())
    try:
        out = _dispatch(svc, a)
    except BggError as e:
        print(f"BŁĄD: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Przerwano; postęp syncu jest zapisany (uruchom ponownie, by kontynuować).", file=sys.stderr)
        return 130
    finally:
        svc.close()
    print(out)
    return 0


def _need(a, n, usage):
    if len(a.args) < n:
        raise BggError(f"użycie: wgu bgg {usage}")


def _dispatch(svc, a) -> str:
    if a.action == "status":
        return render.status(svc.status())
    if a.action == "game":
        return render.game(svc.game(a.thing, refresh=a.refresh))
    if a.action == "forums":
        return render.forums(svc.forums(a.thing, refresh=a.refresh))
    if a.action == "threads":
        _need(a, 1, "threads FORUM_ID [--page N]")
        return render.threads(svc.threads(int(a.args[0]), a.page))
    if a.action == "thread":
        _need(a, 1, "thread THREAD_ID [--offset N] [--limit N] [--refresh]")
        return render.thread(svc.thread(int(a.args[0]), a.offset, a.limit or 25, a.refresh))
    if a.action == "sync":
        forums = [int(x) for x in a.forums.split(",")] if a.forums else None
        r = svc.sync(a.thing, forums, a.max_requests, a.full, progress=lambda m: print(m, file=sys.stderr, flush=True))
        return render.sync(r)
    if a.action == "search":
        _need(a, 1, 'search "zapytanie" [--role designer] [--forum ID] [--limit N]')
        q = " ".join(a.args)
        return render.search(svc.search_posts(q, a.thing, a.role, a.forum, a.limit or 10), q)
    if a.action == "files":
        return render.files(svc.files(a.thing))
    if a.action == "authorities":
        return render.authorities(svc.authorities(a.thing, suggest=a.suggest))
    if a.action == "search-games":
        _need(a, 1, 'search-games "nazwa" [--exact]')
        hits = svc.search_games(" ".join(a.args), a.exact)
        return "\n".join(f"- {h['id']} · {h['name']} ({h['year'] or '?'})" for h in hits) or "Brak wyników."
    raise BggError(f"nieznana akcja {a.action}")
