---
name: pomoce
description: Rysuje pomoce do gry (schematy blokowe, drzewa decyzyjne, algorytmy, karty pomocy) jako PDF w LaTeX/TikZ według specyfikacji YAML z kb/aids/ (z /wgu:projekt-pomocy). Styl domyślnie przejmuje z instrukcji projektu; użytkownik może podać własne zalecenia. Tańszy model nie interpretuje zasad, tylko wiernie implementuje specyfikację.
argument-hint: "[P01 P02 … | --priorytet N | --wszystkie] [--styl \"opis stylu\"]"
disable-model-invocation: true
---

# Pomoce do gry: implementacja w LaTeX/TikZ

Argumenty: `$ARGUMENTS`. CLI: `python "${CLAUDE_PLUGIN_ROOT}/wgu.py"` (dalej `wgu`).

1. `wgu config`, potem `wgu aids validate <ID…>`. Specyfikacja z błędami walidatora → nie rysuj jej,
   poleć `/wgu:projekt-pomocy --popraw <ID>`. Brak specyfikacji → poleć `/wgu:projekt-pomocy`.
2. Wybór: lista ID, `--priorytet N` (priorytet ≤ N i `status: spec`) albo `--wszystkie`. Domyślnie priorytet 1.
3. Uruchom agenta `subagent_type: "wgu:grafik"`: jednego na 1–3 pomoce, kilku równolegle w jednej wiadomości.
   W poleceniu przekaż: procedurę `${CLAUDE_PLUGIN_ROOT}/skills/pomoce/procedura.md`, pełną ścieżkę CLI,
   katalog projektu, ID pomocy, ewentualne `--styl`, szablon `${CLAUDE_PLUGIN_ROOT}/templates/latex/pomoce-tikz.sty`.
   Jeśli równolegle pracuje kilku agentów, tylko pierwszy może tworzyć lub zmieniać wspólny `aids.tikz` (styl).
   Pozostali czekają na jego wynik albo dostają polecenie, by go nie zmieniać.
4. Po powrocie: `wgu aids build <ID…>` dla kontroli i obejrzenie 1–2 PNG. Zeszyt zbiorczy (jeśli agent go
   zaktualizował): `wgu tex build "<aids.tex>/Pomoce PL.tex"`. Raport dla użytkownika: ścieżki PDF,
   odstępstwa od specyfikacji, problemy do `/wgu:projekt-pomocy`.
