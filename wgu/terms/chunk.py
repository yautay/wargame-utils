"""Per-chunk term table for a translator agent (idea from deusyu/translate-book, adapted):
only concepts whose source term or variants occur in the chunk, plus homonym warnings, as a compact Markdown table.
Translators get this instead of the whole glossary; the full glossary stays the single source of truth."""
from __future__ import annotations

from pathlib import Path

from .store import forms, layer_paths, load, word_re


def for_chunk(project, src: Path) -> int:
    t = load(layer_paths(project))
    from ..check.segments import dehyphenate
    text = dehyphenate(src.read_text(encoding="utf-8"))
    rows, homonyms = [], {}
    for c in sorted(t.effective.values(), key=lambda c: c["source_term"].lower()):
        terms = [c["source_term"], *c.get("variants", [])]
        hits = sum(len(word_re(s, ignore_case=False).findall(text)) for s in terms)
        if not hits:
            continue
        homonyms.setdefault(c["source_term"].lower(), []).append(c)
        rej = "; ".join(r["pl"] for r in c.get("rejected", []))
        note = c.get("disambiguation", "") or ""
        first = (c.get("notation") or {}).get("first_use", "")
        rows.append(f"| {c['source_term']} | {c.get('pl', '—')} | {c['status']} | {first} | {rej} | {note} | {c['id']} |")
    print("| EN | PL (zatwierdzony / proponowany) | status | pierwsze użycie | NIE używać | rozróżnienie | id |")
    print("|---|---|---|---|---|---|---|")
    print("\n".join(rows))
    multi = {k: v for k, v in homonyms.items() if len(v) > 1}
    if multi:
        print("\nUwaga — wieloznaczne terminy w tym fragmencie (wybierz pojęcie według sensu):")
        for k, cs in multi.items():
            print(f"- {k}: " + "; ".join(f"{c['id']} → {c.get('pl')} ({c.get('disambiguation', '?')})" for c in cs))
    disputed = [c for c in t.effective.values() if c["status"] == "disputed"]
    if disputed:
        print("\nTerminy sporne (użyj podanej formy, zgłoś uwagi w pliku propozycji):", ", ".join(c["id"] for c in disputed))
    return 0
