# wargame_utils: wskazówki dla Claude

- To repo **narzędzia**: plugin Claude Code (`skills/`, `agents/`, `.claude-plugin/`) i CLI Python (`wgu/`).
  Dane gier żyją w repozytoriach gier (`wgu.yaml` + `kb/`). Nie dodawaj tu niczego specyficznego dla jednej gry.
- Kontrakt danych: `wgu/schemas/kb.schema.json`. Zmiana schematu = zmiana kontraktu z projektami digitalizacji.
  Dodawaj pola opcjonalne. Pola usuwane lub przemianowane wymagają podbicia wersji (`wgu/kb@2`) i opisu migracji.
- Kod: Python ≥ 3.10, zależności tylko z `requirements.txt`. Nazwy pól i kod po angielsku. Skille, agenci i
  komunikaty dla użytkownika po polsku.
- Skille to orkiestratory. Szczegółowe instrukcje dla agentów są w `skills/<skill>/procedura.md`. Agenci pluginu
  nie znają `${CLAUDE_PLUGIN_ROOT}`, więc skill przekazuje im pełne polecenie CLI.
- Testy: `python -m pytest tests`. Pilot do testów ręcznych: `C:/dev/GCACW-PL` (`wgu kb lint`, `wgu aids validate`).
- Windows: skrypty z backslashami (LaTeX) pisz do plików narzędziem Write, nie przez heredoc. Zob. `templates/docs/pulapki.md`.
