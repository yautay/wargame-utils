---
name: czytelnosc
description: "Przygotowuje wydanie instrukcji o lepszej czytelności (np. wersja do nauki) — przebudowa kolejności wykładu, kroki, przykłady, odsyłacze, ramki z wyjątkami, zestawienia — bez zmiany treści zasad i z kontrolą wierności względem bazy wiedzy kb/. Wynik to osobne wydanie LaTeX obok tłumaczenia wiernego. Uruchamiaj ręcznie."
argument-hint: "[zakres rozdziałów] [--odbiorca nowicjusz|weteran] [--katalog wydania]"
disable-model-invocation: true
---

# Wydanie o lepszej czytelności

Argumenty: `$ARGUMENTS`. CLI: `python "${CLAUDE_PLUGIN_ROOT}/wgu.py"` (dalej `wgu`).

Wymagania: baza `kb/` (fundament kontroli wierności) i tłumaczenie lub oryginał. Brak bazy → `/wgu:atomizacja`.

1. Ustal z użytkownikiem (AskUserQuestion, tylko jeśli nie wynika z argumentów): odbiorca, zakres, katalog wydania
   (domyślnie `edycje/czytelna/`), czy zachować numerację reguł oryginału (zalecane: tak, jako odsyłacze).
2. Uruchom agenta `subagent_type: "wgu:redaktor"` z procedurą `${CLAUDE_PLUGIN_ROOT}/skills/czytelnosc/procedura.md`,
   pełną ścieżką CLI i ustaleniami. Duży zakres: kilku redaktorów na rozdziały, ale plan struktury (krok 1 procedury)
   robi jeden.
3. Po powrocie: `wgu tex build <plik główny wydania> --render 45`, przegląd 2–3 stron, raport wierności od agenta.
   Pokaż użytkownikowi: plan struktury, przykład przed/po, rozbieżności do decyzji.

## Git (zasada właściciela)
Po zakończeniu pracy i po każdym zamkniętym etapie commituj **wszystkie** zmiany w katalogu gry — także wygenerowane
PDF-y, PNG, podglądy `_png/`, tła, `kb/_views/`, `build/` i brudnopisy — i wypchnij bieżącą gałąź roboczą (`git push`),
bez osobnej prośby. Poza gitem zostają wyłącznie: sekrety (`.claude/settings.local.json`), cache BGG (`build/bgg/`,
bez redystrybucji) i pliki pośrednie (aux/log LaTeX-a, `__pycache__`, `_t_*`). Nie przełączaj gałęzi, nie pushuj na
`main` i nie używaj `--force` bez polecenia właściciela. Commit dotyczy tylko repo gry (i wskaźnika podmodułu, jeśli
commit podmodułu jest już na jego remote).
