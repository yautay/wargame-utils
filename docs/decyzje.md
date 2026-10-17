# Decyzje właściciela (rejestr)

Decyzje dotyczące wszystkich gier lub całych serii. Rejestr tylko się dopisuje. Decyzje terminologiczne są też zapisane
w rekordach glosariusza (`terminology/…`, pola `status: approved`, `decided_by: user`, `history`).

## 2026-10-04

| # | Decyzja | Zakres | Gdzie wdrożono |
|---|---|---|---|
| D-01 | *Rally* → **reorganizacja** (termin utrwalony w grach wojennych). *Recovery* (SPQR 10.16) dostaje osobny termin; propozycja: „odzyskanie spójności” | seria GBoH | `gboh.rally` (approved), `gboh.recovery` (proposal) |
| D-02 | *Depleted* → **osłabiona / osłabienie** | seria GBoH | `gboh.depleted` |
| D-03 | *Skirmisher* → **harcownik** (świadomie, mimo węższej definicji w WSJP) | seria GBoH | `gboh.skirmisher` (`preference: true`) |
| D-04 | *Orderly Withdrawal* → **uporządkowane wycofanie**; „odwrót” zostaje dla *retreat* | seria GBoH | `gboh.orderly-withdrawal` |
| D-05 | Angielski oryginał pojęć mechaniki przy pierwszym wystąpieniu w podrozdziale, **w stałym kolorze** | wszystkie gry | `\ang` w `wgu-base.sty` (kolor `wgang`, `spec.colors.gloss`); `styl-przepisow.md` §2 |
| D-06 | MA → **limit punktów ruchu**; Game Turn → **tura** (ujednolicenie z GCACW) | seria GBoH | `gboh.movement-allowance`, `gboh.game-turn` |
| D-07 | **Tytuł gry zawsze w oryginale** (także pagina i skróty tytułów) | wszystkie gry | `styl-przepisow.md` §5; `wgu tex style` (domyślnie tytuł z oryginału) |
| D-08 | **Zawsze poprawiamy zgodnie z normami polszczyzny**, także wcześniejsze konwencje właściciela („wg”, nie „wg.”; nazwy faz i rodzajów dowódców małą literą) | wszystkie gry | `styl-przepisow.md` (hierarchia, §5); korekty w `series/gcacw.yaml` (z historią); szablon przewodnika |
| D-09 | Warstwa wspólna zatwierdzona: heks, krawędź heksu, strefa kontroli, modyfikator rzutu, stos | wszystkie gry | `terminology/common.yaml` |
| D-10 | Oprawa każdego przekładu odwzorowuje oryginał danej instrukcji (nie poprzedni projekt) | wszystkie gry | `wgu pdf layout` / `wgu tex style` / `wgu pdf compare`; skill `tlumaczenie` faza 4 |

## 2026-10-11

| # | Decyzja | Zakres | Gdzie wdrożono |
|---|---|---|---|
| D-11 | Dostęp do BoardGameGeek **tylko przez XML API2 z tokenem** zarejestrowanej aplikacji (niekomercyjnej); właściciel rejestruje aplikację | narzędzie | `wgu/bgg/`, zmienna `BGG_API_TOKEN` (dawniej `WGU_BGG_TOKEN`); `docs/research/bgg-mcp.md` §1 |
| D-12 | **Całkowita rezygnacja z api.geekdo.com** (admin BGG: endpointy JSON poza licencją, możliwe naruszenie ToS); bez stron HTML i obchodzenia Cloudflare | narzędzie | `docs/design/bgg-mcp.md` §1 |
| D-13 | **ConsimWorld pominięty** (forum za logowaniem, `robots.txt: Disallow: /`); pole `evidence` przyjmuje dowolne źródło wpisane ręcznie | narzędzie | `kb.schema.json` (`ambiguity.evidence`) |
| D-14 | Moduł BGG budowany przed otrzymaniem tokenu na próbkach syntetycznych; test akceptacyjny na Ukraine '43 po otrzymaniu tokenu | narzędzie | `tests/test_bgg.py`, `tests/test_bgg_acceptance.py` |

Integracja 2026-10-17: [BGG-INTEGRATION.md](BGG-INTEGRATION.md) zastępuje historyczne szczegóły pełnego sync, dopasowania nazwisk i SDK MCP 2.x.
