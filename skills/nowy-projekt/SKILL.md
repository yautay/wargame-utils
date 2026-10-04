---
name: nowy-projekt
description: "Zakłada projekt gry dla wargame_utils — tworzy wgu.yaml w repozytorium gry, rozpoznaje źródła (PDF instrukcji, errata, arkusze tabel), odczytuje kolor zmian i font nagłówków, proponuje kolejne kroki (atomizacja, tłumaczenie, pomoce, digitalizacja). Używaj przy pierwszym uruchomieniu narzędzia w nowym repozytorium gry."
argument-hint: "[--id gra] [--skrot GRA] [--pdf plik.pdf]"
disable-model-invocation: true
---

# Nowy projekt gry

CLI: `python "${CLAUDE_PLUGIN_ROOT}/wgu.py"` (dalej `wgu`). Zależności: `pip install -r "${CLAUDE_PLUGIN_ROOT}/requirements.txt"`.

1. Sprawdź katalog: `git status`, lista PDF-ów i obrazów (w katalogu głównym, `docs/`, `sources/`), istniejące
   tłumaczenie (`*.tex`), stara baza (`docs/indeks/`).
2. Część mechaniczna jedną komendą (nie nadpisuje, przy istniejącym `wgu.yaml` odmawia):
   `wgu init --setup [--id … --short …] [--pdf <plik.pdf>] [--image <plik>…] [--no-git]`.
   Przenosi PDF do `docs/`, obrazy (mapa, żetony) do `png/`, tworzy `wgu.yaml` ze zmierzonym `pdf.accent_color`
   i `pdf.heading_font`, `.gitignore`, `.claude/settings.json` (włącza plugin) oraz `git init`, a także puste `kb/`
   i `translation/`. Bez `--pdf` i `--image` wykrywa pliki w katalogu głównym (PDF musi być jeden).
   Potem uzupełnij ręcznie w `wgu.yaml`: `game.title`, `game.rules_version`, `game.publisher`, `sources.rules[].version`
   (ze strony tytułowej PDF-u), `sources.errata`, `sources.charts`, `translation.*`, jeśli istnieje tłumaczenie.
3. Zweryfikuj pomiar: `wgu pdf analyze <pdf> --pages 3-6` i render strony (`wgu pdf render`). Kolor zmian wersji
   (`pdf.accent_color`: kolor inny niż czarny i szary, zwykle zmiany wersji), `pdf.heading_font`, `pdf.columns`
   (liczbę kolumn ustal wzrokiem). Niepewne wartości pokaż użytkownikowi.
4. Stara baza Markdown (`docs/indeks/` z dawnego `/indeksacja`) → zaproponuj `/wgu:atomizacja --import-legacy docs/indeks`.
5. `wgu config`: pokaż użytkownikowi wynik i zaproponuj kolejność:
   `/wgu:atomizacja` → (`/wgu:tlumaczenie`) → `/wgu:errata` → `/wgu:projekt-pomocy` → `/wgu:pomoce` → `/wgu:digitalizacja`.
6. `.gitignore` zawiera już `build/`, `kb/_views/` i `pomoce/pdf/_png/` (usuń `kb/_views/`, jeśli widoki mają być w repo).
   Prywatne źródła (PDF-y wydawcy) commituj tylko, jeśli użytkownik tak robi dotychczas.
