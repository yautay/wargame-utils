---
name: errata
description: Wersje, errata i poprawki zasad. Porównuje wersje instrukcji, wczytuje erratę, FAQ i wyjaśnienia autora, zapisuje zmiany w kb/changes.yaml, rozstrzyga niejasności (kb/ambiguities.yaml) i, jeśli trzeba, przygotowuje lub nanosi poprawki na tłumaczenie oraz wylicza pomoce wymagające aktualizacji. Uruchamiaj ręcznie, gdy pojawi się nowa wersja, errata lub FAQ albo gdy znaleziono błąd.
argument-hint: "[--nowa-wersja PDF] [--errata PLIK|URL] [--nanies] [--niejasnosci N-12 N-14]"
disable-model-invocation: true
---

# Errata, wersje, poprawki

Argumenty: `$ARGUMENTS`. CLI: `python "${CLAUDE_PLUGIN_ROOT}/wgu.py"` (dalej `wgu`).

1. `wgu config`, `wgu kb stats`. Brak bazy → najpierw `/wgu:atomizacja`. Nowe źródła (PDF wersji, errata)
   dopisz do `wgu.yaml` (`sources.rules` z `role`, `sources.errata`). Materiały z sieci pobieraj tylko za zgodą
   użytkownika (podaj adres i rozmiar).
2. Uruchom agenta `subagent_type: "wgu:analityk-zasad"` z procedurą `${CLAUDE_PLUGIN_ROOT}/skills/errata/procedura.md`,
   pełną ścieżką CLI, katalogiem projektu i argumentami. Agent aktualizuje **tylko** `kb/`.
3. Po powrocie: `wgu kb lint`, `wgu kb render`. Pokaż użytkownikowi listę zmian (ID, miejsce, skutek dla gry),
   rozstrzygnięte i nowe niejasności oraz listę dotkniętych miejsc: pliki tłumaczenia (`source.translation` reguł)
   i pomoce (`kb/aids/*`, których `refs` obejmują zmienione reguły).
4. `--nanies` (albo po akceptacji użytkownika): agent `subagent_type: "wgu:redaktor"` nanosi poprawki na tłumaczenie
   według `kb/changes.yaml` (oznaczenie zgodne z przewodnikiem stylu, np. `\nowe{}` lub ramka errata), kompiluje
   (`wgu tex build`) i raportuje. Pomoce do zmiany oznacz w specyfikacjach `status: issues` z opisem
   i zaproponuj `/wgu:projekt-pomocy --popraw …`.
