"""Polite, read-only client for the BoardGameGeek XML API2.

Only GET requests to /xmlapi2/ exist here: no login, cookies, HTML pages or file downloads. The token comes
from the environment and never appears in messages. One request at a time, at least `delay` seconds apart.
The transport, sleep and clock are injectable, so tests run without network and without waiting.
"""
from __future__ import annotations

import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

BASE = "https://boardgamegeek.com/xmlapi2/"
TOKEN_ENV = "WGU_BGG_TOKEN"
OFFLINE_ENV = "WGU_BGG_OFFLINE"
USER_AGENT = "wgu-bgg/0.1 (+https://github.com/yautay/wargame-utils)"
COMMANDS = {"search", "thing", "forumlist", "forum", "thread", "user"}
MIN_DELAY = 2.0
QUEUED_WAITS = (2, 5, 10, 30)          # 202: BGG is preparing the response
ERROR_WAITS = (10, 30, 90)             # 429 / 5xx / network errors
RETRYABLE = {429, 500, 502, 503, 504}
MAX_RETRY_AFTER = 120


class BggError(Exception):
    """Any problem with BGG access; the message is meant for the user (Polish)."""


class BggOffline(BggError):
    pass


class BggAuthError(BggError):
    pass


class BggBlocked(BggError):
    pass


class BggNotFound(BggError):
    pass


class BggUnavailable(BggError):
    pass


def urllib_fetch(url: str, headers: dict, timeout: float = 60) -> tuple[int, dict, bytes]:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers.items()), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict((e.headers or {}).items()), (e.read() if e.fp else b"")


def _header(headers: dict, name: str) -> str:
    for k, v in headers.items():
        if k.lower() == name.lower():
            return v
    return ""


def _looks_like_html(body: bytes) -> bool:
    head = body[:512].lstrip().lower()
    return head.startswith(b"<!doctype html") or head.startswith(b"<html")


def _retry_after(headers: dict) -> float | None:
    v = _header(headers, "Retry-After").strip()
    if v.isdigit():
        return min(float(v), MAX_RETRY_AFTER)
    return None


@dataclass
class Stats:
    requests: int = 0
    retries: int = 0
    started: float = field(default_factory=time.monotonic)

    def elapsed(self) -> float:
        return time.monotonic() - self.started


class Client:
    def __init__(self, token: str | None = None, delay: float = 5.0, fetch=None, sleep=time.sleep,
                 clock=time.monotonic, offline: bool | None = None):
        self.token = (os.environ.get(TOKEN_ENV, "") if token is None else token).strip()
        self.delay = max(MIN_DELAY, float(delay))
        self.offline = os.environ.get(OFFLINE_ENV, "") not in ("", "0") if offline is None else offline
        self._fetch = fetch or urllib_fetch
        self._sleep = sleep
        self._clock = clock
        self._last: float | None = None
        self._lock = threading.Lock()
        self.stats = Stats()

    @property
    def online(self) -> bool:
        return bool(self.token) and not self.offline

    def offline_reason(self) -> str:
        if self.offline:
            return f"tryb offline ({OFFLINE_ENV}=1)"
        return f"brak tokenu XML API2 (zmienna {TOKEN_ENV})"

    def _wait_turn(self):
        if self._last is not None:
            remaining = self.delay - (self._clock() - self._last)
            if remaining > 0:
                self._sleep(remaining)

    def get(self, command: str, **params) -> bytes:
        """GET /xmlapi2/<command>?<params> and return the XML body (bytes)."""
        if command not in COMMANDS:
            raise ValueError(f"unsupported XML API2 command: {command}")
        if not self.online:
            raise BggOffline(f"Brak dostępu do BGG: {self.offline_reason()}. Dostępne są tylko dane z cache.")
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        url = BASE + command + ("?" + query if query else "")
        what = f"{command}?{query}" if query else command
        headers = {"Authorization": f"Bearer {self.token}", "User-Agent": USER_AGENT,
                   "Accept": "application/xml, text/xml"}
        queued = errors = 0
        with self._lock:
            while True:
                self._wait_turn()
                try:
                    status, hdrs, body = self._fetch(url, headers)
                except (urllib.error.URLError, TimeoutError, OSError):
                    status, hdrs, body = None, {}, b""
                self._last = self._clock()
                self.stats.requests += 1
                if status == 200:
                    if _looks_like_html(body):
                        raise BggBlocked(f"BGG zwróciło stronę HTML zamiast XML ({what}); przerywam bez ponowień.")
                    return body
                if status in (401, 403):
                    if _looks_like_html(body):
                        raise BggBlocked(f"BGG zablokowało zapytanie (HTTP {status}, strona HTML) ({what}); "
                                         "przerywam bez ponowień i bez prób obejścia.")
                    raise BggAuthError(f"BGG odrzuciło token (HTTP {status}) ({what}). Sprawdź {TOKEN_ENV} i stan "
                                       "aplikacji na https://boardgamegeek.com/applications.")
                if status == 404:
                    raise BggNotFound(f"BGG: nie znaleziono ({what}).")
                if status == 202 and queued < len(QUEUED_WAITS):
                    self._sleep(QUEUED_WAITS[queued])
                    queued += 1
                    self.stats.retries += 1
                    continue
                if status is None or status in RETRYABLE or status == 202:
                    if errors < len(ERROR_WAITS):
                        self._sleep(_retry_after(hdrs) or ERROR_WAITS[errors])
                        errors += 1
                        self.stats.retries += 1
                        continue
                    shown = "błąd sieci" if status is None else f"HTTP {status}"
                    raise BggUnavailable(f"BGG niedostępne ({shown}) po {errors} ponowieniach ({what}).")
                raise BggError(f"BGG: nieoczekiwana odpowiedź HTTP {status} ({what}).")
