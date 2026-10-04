# Jak projekt digitalizacji korzysta z bazy

1. W repo gry: `/wgu:atomizacja` → `/wgu:digitalizacja` → `wgu kb export` → `build/wgu-kb.json`.
2. W repo silnika skopiuj pakiet do katalogu danych (np. `docs/rules/wgu-kb.json`) i zapisz jego `source_rev`.
   Pakiet się regeneruje, nie edytuje.
3. Mapowanie na typowy silnik (wzór: repo `spqr`, silnik w TypeScript):

| Pakiet | Silnik |
|---|---|
| `rules[]` (`id`, `effect`, `exceptions`, `refs`) | sekcje reguł `### <ID>` i adnotacje `@rule <ID>` w kodzie |
| `relations[]` | kolejność stosowania reguł, wyjątki w kodzie procedur |
| `tables[].data` | pliki tabel ładowane przez dane (`ctx.ruleset.tables`), bez wartości w kodzie |
| `digital.sequence` + `aids[].nodes/edges` | ramki procedur (`ProcedureDef`, kroki `frame.step`) |
| `digital.decisions` | `DecisionRequest` (kto, opcje, reguła) |
| `digital.randomness` | `ctx.roll(rule, purpose)` z ustaloną kolejnością |
| `digital.modifiers` | `Modifier[]` z `RuleRef` w potoku obliczeń |
| `ambiguities[]` + `digital.interpretations` | rejestr `INT-###` (proposed/accepted) |
| `scenarios[]` (`given/when/then`) | golden testy `describe('<ID> …')` |
| `digital.blockers` | otwarte pytania (`OQ-###`) i karty zadań zablokowane do czasu rozwiązania |

4. ID reguł z pakietu są stabilne, więc kod i testy mogą się do nich odwoływać bez ryzyka przenumerowania.
