"""Repair and parse BoardGameGeek XML API2 responses into plain dicts.

BGG XML is not always well-formed: raw HTML entities (`&nbsp;`), bare `&` and control characters appear in
names and post bodies. `repair()` fixes these before ElementTree sees the text. Dates are normalised to
ISO 8601 UTC (`2016-12-17T22:15:41Z`); forum lists use RFC 2822, threads use ISO 8601 with an offset.
"""
from __future__ import annotations

import html
import re
import unicodedata
from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

from .client import BGGError

_XML_ENTITIES = {"amp", "lt", "gt", "quot", "apos"}
_ENTITY = re.compile(r"&(#[0-9]+;|#[xX][0-9a-fA-F]+;|[A-Za-z][A-Za-z0-9]*;)?")
_CONTROL = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F￾￿]")


def _legal_char(cp: int) -> bool:
    return cp in (0x9, 0xA, 0xD) or 0x20 <= cp <= 0xD7FF or 0xE000 <= cp <= 0xFFFD or 0x10000 <= cp <= 0x10FFFF


def repair(data: bytes | str) -> str:
    s = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data

    def fix(m: re.Match) -> str:
        ent = m.group(1)
        if ent is None:
            return "&amp;"
        if ent.startswith("#"):
            cp = int(ent[2:-1], 16) if ent[1] in "xX" else int(ent[1:-1])
            return "&" + ent if _legal_char(cp) else ""
        if ent[:-1] in _XML_ENTITIES:
            return "&" + ent
        ch = html.unescape("&" + ent)
        if ch == "&" + ent:  # unknown entity: keep it as literal text
            return "&amp;" + ent
        return html.escape(ch, quote=False)

    return _CONTROL.sub("", _ENTITY.sub(fix, s))


def parse(data: bytes | str) -> ET.Element:
    try:
        return ET.fromstring(repair(data).encode("utf-8"))
    except (ET.ParseError, DefusedXmlException, ValueError):
        raise BGGError('Niepoprawny lub niebezpieczny XML BGG.') from None


def iso_utc(value: str | None) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    try:
        dt = datetime.fromisoformat(v.replace("Z", "+00:00")) if v[:4].isdigit() else parsedate_to_datetime(v)
    except (ValueError, TypeError, IndexError):
        return v
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if dt.year <= 1970:  # BGG uses the epoch for "never"
        return ""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _int(v, default=0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _value(el: ET.Element | None, tag: str) -> str:
    if el is None:
        return ""
    child = el.find(tag)
    return (child.get("value") or "") if child is not None else ""


# ---------------------------------------------------------------- commands

def search(root: ET.Element) -> list[dict]:
    out = []
    for it in root.findall("item"):
        name = it.find("name")
        out.append({"id": _int(it.get("id")), "type": it.get("type", ""),
                    "name": name.get("value", "") if name is not None else "", "year": _value(it, "yearpublished")})
    return out


CREDIT_LINKS = {"boardgamedesigner": "designers", "boardgamedeveloper": "developers",
                "boardgamepublisher": "publishers", "boardgameartist": "artists"}


def thing(root: ET.Element) -> dict | None:
    it = root.find("item")
    if it is None:
        return None
    names = it.findall("name")
    primary = next((n.get("value", "") for n in names if n.get("type") == "primary"), "")
    out = {"id": _int(it.get("id")), "type": it.get("type", ""), "name": primary,
           "alternate_names": [n.get("value", "") for n in names if n.get("type") != "primary"],
           "year": _value(it, "yearpublished"), **{v: [] for v in CREDIT_LINKS.values()}, "versions": []}
    for link in it.findall("link"):
        key = CREDIT_LINKS.get(link.get("type", ""))
        if key:
            out[key].append({"id": _int(link.get("id")), "name": link.get("value", "")})
    for v in it.findall("versions/item"):
        vnames = v.findall("name")
        links = v.findall("link")
        out["versions"].append({
            "id": _int(v.get("id")),
            "name": next((n.get("value", "") for n in vnames if n.get("type") == "primary"), ""),
            "year": _value(v, "yearpublished"),
            "publishers": [x.get("value", "") for x in links if x.get("type") == "boardgamepublisher"],
            "languages": [x.get("value", "") for x in links if x.get("type") == "language"],
            "productcode": _value(v, "productcode"),
        })
    return out


def forumlist(root: ET.Element) -> list[dict]:
    return [{"forum_id": _int(f.get("id")), "title": f.get("title", ""), "numthreads": _int(f.get("numthreads")),
             "numposts": _int(f.get("numposts")), "lastpostdate": iso_utc(f.get("lastpostdate")),
             "noposting": f.get("noposting") == "1"} for f in root.findall("forum")]


def forum(root: ET.Element) -> dict:
    return {"forum_id": _int(root.get("id")), "title": root.get("title", ""),
            "numthreads": _int(root.get("numthreads")), "numposts": _int(root.get("numposts")),
            "lastpostdate": iso_utc(root.get("lastpostdate")),
            "threads": [{"thread_id": _int(t.get("id")), "subject": t.get("subject", ""),
                         "author": t.get("author", ""), "numarticles": _int(t.get("numarticles")),
                         "postdate": iso_utc(t.get("postdate")), "lastpostdate": iso_utc(t.get("lastpostdate"))}
                        for t in root.findall("threads/thread")]}


def thread(root: ET.Element) -> dict:
    posts = []
    for a in root.findall("articles/article"):
        body = a.findtext("body") or ""
        posts.append({"post_id": _int(a.get("id")), "username": a.get("username", ""), "link": a.get("link", ""),
                      "postdate": iso_utc(a.get("postdate")), "editdate": iso_utc(a.get("editdate")),
                      "numedits": _int(a.get("numedits")), "subject": (a.findtext("subject") or "").strip(),
                      "body_html": body, "body_text": html_to_text(body)})
    return {"thread_id": _int(root.get("id")), "subject": (root.findtext("subject") or "").strip(),
            "numarticles": _int(root.get("numarticles")), "link": root.get("link", ""), "posts": posts}


def user(root: ET.Element) -> dict | None:
    if not root.get("id"):  # BGG answers unknown users with an empty record
        return None
    return {"user_id": _int(root.get("id")), "username": root.get("name", ""),
            "firstname": _value(root, "firstname"), "lastname": _value(root, "lastname"),
            "yearregistered": _value(root, "yearregistered")}


# ---------------------------------------------------------------- post body → text

QUOTE_LIMIT = 200
_BLOCK = {"p", "div", "br", "li", "ul", "ol", "tr", "table", "blockquote", "h1", "h2", "h3", "h4", "pre", "hr"}
_BBQUOTE = re.compile(r'\[q(?:="([^"]*)")?\](.*?)\[/q\]', re.S | re.I)


def _quote(author: str | None, text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > QUOTE_LIMIT:
        text = text[:QUOTE_LIMIT].rstrip() + "…"
    who = f": {author}" if author else ""
    return f"\n[cytat{who}] {text} [/cytat]\n"


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.bufs: list[list[str]] = [[]]
        self.divs: list[bool] = []          # True = div opens a quote
        self.links: list[str | None] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div":
            is_quote = "quote" in (a.get("class") or "").split()
            self.divs.append(is_quote)
            if is_quote:
                self.bufs.append([])
                return
        if tag == "img":
            self.bufs[-1].append(" [obraz] ")
        elif tag == "a":
            self.links.append(a.get("href"))
        if tag in _BLOCK:
            self.bufs[-1].append("\n")

    def handle_endtag(self, tag):
        if tag == "div" and self.divs and self.divs.pop():
            text = "".join(self.bufs.pop())
            m = re.match(r"\s*(.+?) wrote:\s*", text)
            self.bufs[-1].append(_quote(m.group(1).strip() if m else None, text[m.end():] if m else text))
            return
        if tag == "a" and self.links:
            href = self.links.pop()
            if href and href.startswith("http") and href not in "".join(self.bufs[-1][-3:]):
                self.bufs[-1].append(f" <{href}>")
        if tag in _BLOCK:
            self.bufs[-1].append("\n")

    def handle_data(self, data):
        self.bufs[-1].append(data)

    def text(self) -> str:
        while len(self.bufs) > 1:  # unclosed quote divs
            inner = "".join(self.bufs.pop())
            self.bufs[-1].append(_quote(None, inner))
        return "".join(self.bufs[0])


def html_to_text(body: str) -> str:
    s = _BBQUOTE.sub(lambda m: _quote(m.group(1), m.group(2)), body or "")
    p = _Text()
    p.feed(s)
    p.close()
    lines = [re.sub(r"[ \t ]+", " ", ln).strip() for ln in p.text().splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def normalize_name(name: str) -> str:
    """'Mark  Simonitch (I)' → 'mark simonitch' (for matching user names with credited persons)."""
    name = re.sub(r"\(.*?\)", " ", name or "")
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", name).strip().casefold()
