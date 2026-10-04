---
name: regula
description: Szybkie wyszukanie reguły, terminu, tabeli, procedury, niejasności lub scenariusza w bazie wiedzy kb/ projektu gry (po ID albo słowie) wraz z relacjami, które ją nadpisują, i powiązanymi niejasnościami. Używaj, gdy użytkownik pyta o konkretną zasadę gry, jej ID albo znaczenie terminu w projekcie z plikiem wgu.yaml.
argument-hint: "<ID lub termin> [kolejne…]"
model: haiku
---

# Wyszukanie w bazie zasad

Uruchom: `python "${CLAUDE_PLUGIN_ROOT}/wgu.py" kb show $ARGUMENTS`

- Wypisz wynik. Przy pytaniu o interpretację zastosuj protokół z `kb/manifest.yaml` (`interpretation_protocol`):
  werdykt → łańcuch reguł z ID → zastrzeżenia (niejasności, zasady tytułu, opcje).
- „not found”: spróbuj `grep -ril "<słowo>" kb/rules kb/terms.yaml` i pokaż znalezione ID przez `kb show`.
- Nie czytaj PDF instrukcji. Jeśli baza nie wystarcza, powiedz to i zaproponuj `/wgu:atomizacja` dla uzupełnienia.
