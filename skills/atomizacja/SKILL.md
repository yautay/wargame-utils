---
name: atomizacja
description: "Rozbija zasady gry na atomy. Czyta instrukcję (PDF oryginału, tłumaczenie, errata) i buduje lub aktualizuje kanoniczną bazę wiedzy YAML w repozytorium gry (kb/): reguły z cytatami, definicje, tabele, procedury, graf relacji „nadpisuje/wyjątek”, niejasności z wariantami, zmiany wersji, scenariusze kontrolne. Baza jest fundamentem tłumaczenia, pomocy do gry i digitalizacji. Uruchamiaj ręcznie po dodaniu lub zmianie instrukcji."
argument-hint: "[--zakres 'rozdz. 7–8'] [--import-legacy docs/indeks] [--tylko-qa]"
disable-model-invocation: true
---

# Atomizacja zasad: budowa bazy wiedzy

Argumenty: `$ARGUMENTS`

CLI narzędzia: `python "${CLAUDE_PLUGIN_ROOT}/wgu.py"` (dalej `wgu`). Agenci nie znają tej ścieżki, więc przekaż ją w poleceniu.

## Kroki (wykonujesz Ty, w sesji głównej)
1. **Projekt:** `wgu config`. Jeśli brak `wgu.yaml`, uruchom najpierw `/wgu:nowy-projekt`.
2. **Stan bazy:** `wgu kb stats` i `wgu kb lint` (jeśli `kb/` istnieje).
   - `--import-legacy DIR`: stara baza Markdown (format dawnego `/indeksacja`). Uruchom
     `wgu kb import-legacy DIR [--specs DIR_SPECYFIKACJI]`, potem `wgu kb lint` i `wgu kb render`.
     Pokaż użytkownikowi statystyki i ostrzeżenia. Agent nie jest potrzebny, chyba że użytkownik chce
     weryfikacji relacji ze statusem `imported`. Wtedy przejdź do kroku 3 z zakresem „weryfikacja relacji”.
3. **Agent:** uruchom narzędziem Agent `subagent_type: "wgu:analityk-zasad"` (w tle, jeśli zakres jest duży) z poleceniem:
   - ścieżka procedury: `${CLAUDE_PLUGIN_ROOT}/skills/atomizacja/procedura.md`,
   - polecenie CLI (pełna ścieżka jak wyżej), katalog projektu, zakres z argumentów,
   - tryb: `nowa baza` / `aktualizacja przyrostowa` / `tylko QA` (`--tylko-qa`).
   Przy dużej instrukcji (> 40 stron) możesz podzielić pracę: kilku agentów `wgu:analityk-zasad` na rozdziały
   (wyłącznie pliki `kb/rules/NN-*.yaml` swoich rozdziałów, terminy w osobnych plikach roboczych), potem jeden
   agent na przekrój: `relations`, `ambiguities`, `scenarios`, scalenie terminów. Dla rozdziałów możesz podać
   `model: "sonnet"` i porównać jakość ze wzorcem (zob. `docs/MODELE.md` w repo narzędzia).
4. **Weryfikacja (Ty):** `wgu kb lint` (0 błędów), `wgu kb render`, losowo `wgu kb show` dla 3 reguł
   i porównanie ze źródłem.
5. **Raport dla użytkownika (≤ 200 słów):** liczby z `wgu kb stats`, najważniejsze niejasności, blokery
   (np. brakujący arkusz tabel), proponowane kolejne kroki: `/wgu:projekt-pomocy`, `/wgu:digitalizacja`, `/wgu:errata`.
