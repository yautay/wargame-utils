---
name: nowy-projekt
description: Zakłada projekt gry dla wargame_utils — tworzy wgu.yaml w repozytorium gry, rozpoznaje źródła (PDF instrukcji, errata, arkusze tabel), odczytuje kolor zmian i font nagłówków, proponuje kolejne kroki (atomizacja, tłumaczenie, pomoce, digitalizacja). Używaj przy pierwszym uruchomieniu narzędzia w nowym repozytorium gry.
argument-hint: "[--id gra] [--skrot GRA]"
disable-model-invocation: true
---

# Nowy projekt gry

CLI: `python "${CLAUDE_PLUGIN_ROOT}/wgu.py"` (dalej `wgu`). Zależności: `pip install -r "${CLAUDE_PLUGIN_ROOT}/requirements.txt"`.

1. Sprawdź katalog: `git status`, lista PDF-ów (`docs/`, `sources/`), istniejące tłumaczenie (`*.tex`), stara baza (`docs/indeks/`).
2. `wgu init [--id … --short …]` → `wgu.yaml`. Uzupełnij `game`, `sources.rules` (role: current/previous),
   `sources.errata`, `sources.charts` (arkusze tabel), `translation.*`, jeśli istnieje tłumaczenie.
3. `wgu pdf analyze <pdf> --pages 3-6` → wpisz `pdf.accent_color` (kolor tekstu innego niż czarny, zwykle zmiany wersji),
   `pdf.heading_font`, `pdf.columns`. Niepewne wartości pokaż użytkownikowi.
4. Stara baza Markdown (`docs/indeks/` z dawnego `/indeksacja`) → zaproponuj `/wgu:atomizacja --import-legacy docs/indeks`.
5. `wgu config`: pokaż użytkownikowi wynik i zaproponuj kolejność:
   `/wgu:atomizacja` → (`/wgu:tlumaczenie`) → `/wgu:errata` → `/wgu:projekt-pomocy` → `/wgu:pomoce` → `/wgu:digitalizacja`.
6. W `.gitignore` projektu dodaj `kb/_views/` (jeśli widoki nie mają być w repo), `build/` i `pomoce/pdf/_png/`.
   Prywatne źródła (PDF-y wydawcy) commituj tylko, jeśli użytkownik tak robi dotychczas.
