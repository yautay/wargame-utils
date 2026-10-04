# wargame_utils: architektura

## 1. Cel
Jedno narzędzie do pracy z zasadami gier planszowych i wargame'ów, wielokrotnego użytku między grami:

```
instrukcja (PDF) ──► /wgu:atomizacja ──► kb/ (YAML, źródło prawdy) ──┬─► /wgu:tlumaczenie   → tłumaczenie LaTeX
errata / FAQ   ──► /wgu:errata     ──┘                               ├─► /wgu:czytelnosc    → wydanie do nauki
                                                                      ├─► /wgu:projekt-pomocy → kb/aids/*.yaml (grafy)
                                                                      │        └─► /wgu:pomoce → PDF (TikZ)
                                                                      └─► /wgu:digitalizacja → kb/digital/ + build/wgu-kb.json
                                                                                                 └─► repo silnika gry
```

**Repo narzędzia ≠ repo gry.** `wargame_utils` zawiera kod, skille, agentów, schematy i szablony. Każda gra ma
własne repozytorium z plikiem `wgu.yaml`, źródłami, bazą `kb/`, tłumaczeniem i pomocami. Repo digitalizacji
(np. `spqr`) konsumuje wyeksportowany pakiet JSON i niczego nie importuje z narzędzia.

## 2. Składniki
| Składnik | Gdzie | Rola |
|---|---|---|
| Plugin Claude Code `wgu` | `.claude-plugin/`, `skills/`, `agents/` | orkiestracja pracy modeli: skille `/wgu:*`, agenci `wgu:*` |
| CLI `wgu` (Python) | `wgu/`, `wgu.py` | wszystko, co nie wymaga modelu: PDF, LaTeX, import, lint, render, eksport, walidacja grafów |
| Kontrakt danych | `wgu/schemas/kb.schema.json` | JSON Schema bazy: wspólny język narzędzia i projektów digitalizacji |
| Terminologia wspólna | `terminology/common.yaml`, `terminology/era/*.yaml`, `terminology/series/*.yaml` | warstwy glosariusza pojęciowego (`wgu/terms@1`, `wgu/schemas/terminology.schema.json`); warstwa gry w repo gry |
| Oprawa | `wgu pdf layout` → `layout.yaml` (wgu/layout@1) → `wgu tex style` → `<gra>-style.sty` na API `templates/latex/wgu-base.sty`; `wgu pdf compare` | styl każdego przekładu odwzorowuje oryginał tej instrukcji; tekst używa wyłącznie makr API |
| Szablony | `templates/latex/`, `templates/docs/` | styl LaTeX instrukcji i pomocy (kolory ról `wg*`), pułapki środowiska |

Skille są **cienkimi orkiestratorami** w sesji głównej. Uruchamiają agentów pluginu (`subagent_type: "wgu:…"`)
i przekazują im ścieżkę procedury (`skills/<skill>/procedura.md`) oraz pełne polecenie CLI. Pole `agent:`
we frontmatterze skilla nie obsługuje agentów z pluginu. `${CLAUDE_PLUGIN_ROOT}` jest podstawiany tylko w treści skilla.

## 3. Repo gry
```
wgu.yaml                 # konfiguracja (wgu init); wszystkie ścieżki niżej są konfigurowalne
kb/
  manifest.yaml          # gra, źródła, protokół interpretacji, historia analiz
  rules/NN-<slug>.yaml   # atomowe reguły (rdzeń)
  terms.yaml tables.yaml procedures.yaml relations.yaml
  ambiguities.yaml changes.yaml scenarios.yaml
  notes/*.md             # proza: przegląd gry, narracja zależności
  aids/PNN-*.yaml        # specyfikacje pomocy (grafy decyzyjne)
  digital/*.yaml         # model stanu, decyzje, losowość, modyfikatory, blokery
  _views/                # Markdown generowany przez `wgu kb render` (nie edytować)
build/wgu-kb.json        # pakiet dla digitalizacji (`wgu kb export`)
```

### Identyfikatory (stabilne, nigdy nie przenumerowywane)
| Prefiks | Byt | Przykład |
|---|---|---|
| `R-` | reguła; `R-OPT-…` opcjonalna, `R-<TYTUŁ>-n` tytułu, `R-SUM-n` podsumowanie | `R-7.6.3` |
| `T-` | tabela | `T-02` |
| `P-` | procedura | `P-03a` |
| `N-` / `N-T` | niejasność oryginału / tłumaczenia | `N-12` |
| `C-` | zmiana (wersja, errata, FAQ) | `C-A11` |
| `Q-` | scenariusz kontrolny | `Q-04` |
| `P` + 2 cyfry | pomoc do gry | `P09` |
| `DEC-`, `RNG-`, `MOD-`, `INT-`, `BLK-` | elementy digitalizacji | `RNG-03` |

Pole `refs` każdego rekordu zawiera wszystkie wspomniane ID. Na `refs` opierają się lint, `kb show`
(relacje, niejasności, scenariusze reguły) i eksport.

## 4. Dlaczego YAML, a nie baza wektorowa
- Baza jednej gry ma ok. 200 KB. Mieści się w kontekście albo daje się przeszukać grepem i `kb show`.
- Odpowiedź o zasadę wymaga **wszystkich** wyjątków, które ją nadpisują. Jawny graf `relations.yaml` zapewnia to
  deterministycznie, a podobieństwo semantyczne nie.
- Embeddingi mogą się przydać dopiero przy wyszukiwaniu mechanik **między wieloma grami**. Wtedy jako indeks
  pochodny, generowany z eksportów, nigdy jako źródło prawdy.

## 5. Kontrakt z digitalizacją
Pakiet `wgu/kb-bundle@1` (JSON) zawiera manifest, reguły, kolekcje, pomoce i `digital`, a także `source_rev`
(commit repo gry) i liczbę ostrzeżeń lintu. Repo silnika przypina konkretny pakiet. Zob. `docs/DIGITALIZACJA.md`.

## 6. Podział pracy model ↔ skrypt
Zob. `docs/MODELE.md`.
