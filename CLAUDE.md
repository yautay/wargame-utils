# wargame_utils: wskazówki dla Claude

- To repo **narzędzia**: plugin Claude Code (`skills/`, `agents/`, `.claude-plugin/`) i CLI Python (`wgu/`).
  Dane gier żyją w repozytoriach gier (`wgu.yaml` + `kb/`). Nie dodawaj tu niczego specyficznego dla jednej gry.
- Klaryfikacje z BGG: najpierw lokalna baza i MCP WGU, według
  [protokołu dla AI](docs/BGG-MCP-WORKFLOW.md). Nie otwieraj ponownie stron BGG dla treści
  już dostępnej przez MCP. Jedna instancja, małe partie, bez obchodzenia cache, blokad lub limitów.
- Kontrakt danych: `wgu/schemas/kb.schema.json`. Zmiana schematu = zmiana kontraktu z projektami digitalizacji.
  Dodawaj pola opcjonalne. Pola usuwane lub przemianowane wymagają podbicia wersji (`wgu/kb@2`) i opisu migracji.
- Kod: Python ≥ 3.10, zależności z `requirements.txt`; `requirements-mcp.txt` jest zgodnym odsyłaczem.
  Jeden SDK MCP 1.x, jedna implementacja `wgu/bgg_mcp.py`. Nazwy pól i kod po angielsku. Skille, agenci i komunikaty dla użytkownika
  po polsku.
- BGG: tylko XML API2 z tokenem `BGG_API_TOKEN` (`WGU_BGG_TOKEN` to alias zgodności), nigdy api.geekdo.com ani strony HTML.
  Najpierw lokalny FTS5, potem celowane pobrania do 5 partii po 100 wpisów; bez pełnego zrzutu forum.
  Role i oficjalność wyłącznie z `BGG_AUTHORITY_FILE`, bez dopasowania nazwisk i zgadywania „player”.
  Testy bez sieci, na syntetycznych próbkach `tests/fixtures/bgg/`.
- Skille to orkiestratory. Szczegółowe instrukcje dla agentów są w `skills/<skill>/procedura.md`. Agenci pluginu
  nie znają `${CLAUDE_PLUGIN_ROOT}`, więc skill przekazuje im pełne polecenie CLI.
- Testy: `python -m pytest tests`. Pilot do testów ręcznych: `C:/dev/GCACW-PL` (`wgu kb lint`, `wgu aids validate`).
- Windows: skrypty z backslashami (LaTeX) pisz do plików narzędziem Write, nie przez heredoc. Zob. `templates/docs/pulapki.md`.
