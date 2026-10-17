# Integracja branchy BGG — 2026-10-17

Scalono `main` (a58ded7) i `feat/bgg-mcp` (0576b39), zachowując ich historię.
Główny branch pozostaje `main`. Dokumenty `docs/design/bgg-mcp.md` i
`docs/research/bgg-mcp.md` są historycznymi materiałami projektowymi.

## Jedna implementacja

- `wgu/bgg/client.py`: transport z `main`; importy `from wgu.bgg import BGGClient`
  pozostają zgodne po zastąpieniu pliku `wgu/bgg.py` pakietem.
- `wgu/bgg_mcp.py`: jeden serwer FastMCP, SDK `mcp>=1.12,<2`.
  `wgu mcp`, `wgu bgg serve` i `python -m wgu.bgg.server` uruchamiają ten sam serwer.
  `.mcp.json` zachowuje uruchamianie pluginu przez uv. SDK 2.x usunięto z zależności.
- `wgu/bgg/store.py`: SQLite/FTS5 z brancha feature; `index.py` dodaje osobny zapis
  oryginalnych wpisów. Znormalizowane dane FTS nie zastępują oryginałów.
- CLI `wgu bgg`: metadane gry, fora, strony wątków, pojedyncze partie wpisów,
  celowana synchronizacja i wyszukiwanie wyłącznie lokalne.
- `evidence` w niejasnościach, renderowanie dowodów, lint i skill `dowody` zachowano
  i dostosowano do weryfikacji opartej na źródłach. Zmiany schematu są opcjonalne.
- Zachowano zasadę właściciela o commitowaniu wyników projektów gier; sekrety i cache
  pozostają wyłączone. Repo narzędzia nadal ignoruje własne katalogi robocze `build/`.

## Zachowane ograniczenia

Jedna instancja klienta dla tokenu, odstęp co najmniej 5 sekund, cache XML 1 h,
odpowiedź do 4 MiB, do trzech prób HTTP, ograniczony Retry-After, bez przekierowań
i z bezpiecznym parserem XML. Sieć wyłącznie przez udokumentowane XML API2.
Zachowano istniejące narzędzia MCP i ich parametry; dodano `bgg_game`,
`bgg_search_cached_posts` i `bgg_sync`. To limity WGU, nie gwarancja przydziału BGG.

`sync` wymaga wybranych ID z jednej strony forum potwierdzonego dla gry. Limit to
1–5 partii po 100 wpisów, domyślnie jedna. Metadane forum wymagają osobnych wywołań;
wszystkie podlegają wspólnemu limiterowi i cache. Bez pełnego zrzutu i dodatkowych retry.
Po błędzie nie pobiera się kolejnych wątków; zapisane wcześniejsze partie pozostają.
Kursor pozwala ręcznie wznowić od ostatniej zapisanej partii. Edycje starszych wpisów
nie są automatycznie odświeżane; potrzebny jest celowany odczyt konkretnej partii.

## Autorstwo i migracja

`BGG_API_TOKEN` to główna zmienna; `WGU_BGG_TOKEN` jest aliasem zgodności.
`BGG_OFFLINE=1` blokuje sieć (`WGU_BGG_OFFLINE` to stary alias).
Role i oficjalność są ustalane wyłącznie przez aktualny `BGG_AUTHORITY_FILE`,
z uwzględnieniem gry, konta, dat i ID wpisu. Nieznane konto pozostaje `unverified`.
Nie przejęto dopasowania nazwisk, prowizorycznego `designer?` ani domyślnej roli gracza.
Stare `bgg.authorities`, `delay` i listy forów nie przywracają starego zachowania.

Weryfikacja następuje na nowo przy każdym wyszukiwaniu offline, więc zmiana lub
wygaśnięcie rejestru nie zostawia aktywnego starego przypisania roli w indeksie.
Indeks ze starego brancha bez oryginalnych metadanych nie daje zweryfikowanych
wyników; wpisy trzeba ponownie pobrać celowanymi partiami, bez automatycznej migracji ról.

CLI i MCP uruchomione w tej samej grze używają `build/bgg/bgg.sqlite` (lub `bgg.cache`).
MCP poza grą używa `~/.cache/wgu/bgg/index.sqlite`; `BGG_INDEX_PATH` pozwala obu
interfejsom wskazać ten sam plik. Nie usuwaj cache ani indeksu w celu obchodzenia limitów.

## Weryfikacja

Testy obejmują dotychczasowe zabezpieczenia transportu i rejestru, XML i FTS5,
zachowanie źródeł, izolację gier, odrzucanie dawnych domysłów o roli, wznowienie po
limicie, zatrzymanie po błędzie oraz zgodność CLI/MCP. Testy domyślne nie łączą się z BGG.
Test akceptacyjny wymaga jawnego włączenia i konkretnych ID; nie wykonuje pełnego sync.

Nie zmieniono przypięcia submodule w `wargame-projects` ani danych żadnej gry.
