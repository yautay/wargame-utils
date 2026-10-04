# wargame_utils

Narzędzie do analizy zasad gier planszowych i wargame'ów, wielokrotnego użytku między grami:

- **atomizacja zasad**: kanoniczna baza wiedzy YAML (reguły z cytatami, definicje, tabele, procedury, graf relacji,
  niejasności, zmiany wersji, scenariusze kontrolne),
- **errata i wersje**: porównanie wersji, errata, FAQ, rozstrzygnięcia niejasności, poprawki tłumaczenia,
- **tłumaczenie** instrukcji do LaTeX/PDF w oprawie oryginału: pojęciowy glosariusz w trzech warstwach
  (`terminology/`), kontrola wierności przepisów i trzy przebiegi weryfikacji (terminologia, znaczenie zasad,
  redakcja językowa),
- **wydanie o lepszej czytelności** z kontrolą wierności względem bazy,
- **pomoce do gry**: algorytmy, schematy blokowe, drzewa decyzyjne, karty (specyfikacje YAML → PDF TikZ),
- **fundament digitalizacji**: model stanu, decyzje, losowość, modyfikatory, testy given/when/then, pakiet JSON.

Architektura: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · modele i koszty: [docs/MODELE.md](docs/MODELE.md) ·
digitalizacja: [docs/DIGITALIZACJA.md](docs/DIGITALIZACJA.md).

## Instalacja
```bash
pip install -r requirements.txt          # pyyaml, jsonschema, pymupdf
pip install -e .                         # opcjonalnie: polecenie `wgu` w PATH
```
LaTeX: LuaLaTeX (MiKTeX lub TeX Live). Pułapki środowiska: [templates/docs/pulapki.md](templates/docs/pulapki.md).

### Plugin Claude Code (w repo gry)
```bash
claude plugin marketplace add C:/dev/wargame_utils --scope project
claude plugin install wgu@wargame-utils --scope project
```
Do pracy nad samym pluginem: `claude --plugin-dir C:/dev/wargame_utils`.

## Szybki start w repo gry
```bash
python C:/dev/wargame_utils/wgu.py init --id mojagra --short MG
python C:/dev/wargame_utils/wgu.py pdf analyze docs/rules.pdf --pages 3-6
```
Potem w Claude Code: `/wgu:atomizacja` → `/wgu:projekt-pomocy` → `/wgu:pomoce` → `/wgu:digitalizacja`
(opcjonalnie `/wgu:tlumaczenie`, `/wgu:errata`, `/wgu:czytelnosc`; pytania o zasady: `/wgu:regula R-7.6.3`).

## CLI
```
wgu init | config
wgu pdf analyze|extract|images|render …
wgu kb import-legacy DIR [--specs DIR] | lint [--strict] | render | show ID… | stats | export [--out F]
wgu aids validate [ID…] | build ID… [--dpi N]
wgu tex build FILE [--runs N] [--outdir D] [--render DPI]
wgu terms lint | show Q | check TEX… | impact ID --tex … [--src …] | for-chunk SRC | glossary-tex OUT | import-md …
wgu text mark SRC OUT                    # markery segmentów %@ przed numerami reguł
wgu check fidelity SRC TEX…              # liczby, odsyłacze, modalność, terminy w segmentach
```

## Testy
```bash
python -m pytest tests
python tests/roundtrip_check.py <stara baza md> <kb> [<specs>]   # bezstratność importu
```

Pilot: GCACW-PL (Great Campaigns of the American Civil War, Zasady Systemowe v1.6). Tłumaczenia i pomoce
tworzone tym narzędziem są nieoficjalne. Nie publikuj materiałów wydawców bez zgody.
