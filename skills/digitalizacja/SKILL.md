---
name: digitalizacja
description: "Przygotowuje fundament pod komputerową implementację gry na podstawie bazy wiedzy kb/ — model stanu, punkty decyzji i reakcji, losowość, informację ukrytą, potok modyfikatorów, tabele w postaci maszynowej, scenariusze testowe given/when/then i listę blokerów — oraz eksportuje pakiet JSON (wgu/kb-bundle@1) dla repozytorium digitalizacji (np. silnik w TypeScript). Uruchamiaj ręcznie po /wgu:atomizacja, przed startem projektu digitalizacji."
argument-hint: "[zakres, np. 'walka'] [--tylko-eksport] [--cel ../spqr]"
disable-model-invocation: true
---

# Fundament digitalizacji

Argumenty: `$ARGUMENTS`. CLI: `python "${CLAUDE_PLUGIN_ROOT}/wgu.py"` (dalej `wgu`).

1. `wgu config`, `wgu kb stats`, `wgu kb lint`. Błędy lintu najpierw napraw (`/wgu:atomizacja --tylko-qa`).
2. `--tylko-eksport`: `wgu kb export` → podaj ścieżkę pakietu i zakończ.
3. Uruchom agenta `subagent_type: "wgu:architekt-digitalizacji"` z procedurą
   `${CLAUDE_PLUGIN_ROOT}/skills/digitalizacja/procedura.md`, pełną ścieżką CLI, katalogiem projektu i zakresem.
   Agent pisze `digital.dir` (domyślnie `kb/digital/`) oraz pola `digital` reguł, `data` tabel i
   `given/when/then` scenariuszy.
4. Po powrocie: `wgu kb lint`, `wgu kb export`. Raport dla użytkownika: blokery (`kb/digital/blockers.yaml`)
   z wpływem, decyzje do podjęcia przez właściciela, ścieżka pakietu.
5. `--cel <repo>`: pokaż, jak repo digitalizacji ma konsumować pakiet (zob. `docs/DIGITALIZACJA.md` w repo narzędzia).
   Plików w repo docelowym nie zmieniaj bez zgody użytkownika.
