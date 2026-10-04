---
name: projekt-pomocy
description: Projektuje pomoce do nauki i kontroli zasad przy stole (algorytmy, schematy blokowe, drzewa decyzyjne, tabele decyzyjne, karty-ściągi, infografiki) na podstawie bazy wiedzy kb/. Wynik to plan i specyfikacje YAML (węzły, krawędzie, ID reguł, przykład, układ, kryteria akceptacji) sprawdzane przez `wgu aids validate`, gotowe dla /wgu:pomoce i jako szkielet procedur silnika. Uruchamiaj ręcznie po /wgu:atomizacja.
argument-hint: "[zakres, np. 'walka i odwrót'] [--max N] [--odbiorca nowicjusz|weteran] [--popraw P04 P09]"
disable-model-invocation: true
---

# Projekt pomocy do gry

Argumenty: `$ARGUMENTS`. CLI: `python "${CLAUDE_PLUGIN_ROOT}/wgu.py"` (dalej `wgu`).

1. `wgu config` i `wgu kb stats`. Brak bazy (`kb/`) → zaproponuj najpierw `/wgu:atomizacja` i przerwij,
   chyba że użytkownik chce pracować bez bazy.
2. `wgu aids validate`: stan istniejących specyfikacji (do poprawy przy `--popraw`).
3. Uruchom agenta `subagent_type: "wgu:projektant-pomocy"` z poleceniem: procedura
   `${CLAUDE_PLUGIN_ROOT}/skills/projekt-pomocy/procedura.md`, pełna ścieżka CLI, katalog projektu, argumenty.
4. Po powrocie: `wgu aids validate` (0 błędów) i `wgu kb render`. Pokaż użytkownikowi listę pomocy
   (ID, tytuł, typ, priorytet), ostrzeżenia walidatora i polecenie, np. `/wgu:pomoce P01 P04` lub `/wgu:pomoce --priorytet 1`.
