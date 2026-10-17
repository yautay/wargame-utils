"""`wgu help [TOPIC]`: short procedures printed in the terminal (user-facing text in Polish)."""
from __future__ import annotations

TOPICS: dict[str, tuple[str, str]] = {
    "nowa-gra": ("Start tłumaczenia zasad nowej gry", """\
Jeden katalog projektu na jedną grę. Może to być osobne repozytorium albo `games/<id>` w workspace.
Dane gry żyją tam, a nie w wargame_utils.

1. Katalog gry obok innych (np. C:/dev/mojagra) albo w monorepo (np. games/mojagra), a w nim PDF instrukcji.
   Gdy w katalogu jest kilka PDF-ów, wskaż właściwy przez --pdf. Pozostałe PDF-y
   (scenariusze, karty, tabele) przenieś ręcznie do docs/.
   Gdy gra ma już własne repozytorium implementacji cyfrowej (kod, zadania), nie dokładaj do niego wgu.yaml:
   zrób osobny katalog gry i skopiuj tam tylko PDF.

2. Przygotowanie katalogu (z katalogu gry; WGU nie utworzy zagnieżdżonego Git-a w workspace):
     python C:/dev/wargame_utils/wgu.py init --setup --id ID --short SKROT --pdf "plik.pdf"
   Tworzy docs/, kb/, translation/, wgu.yaml (z pomiarem koloru i fontu nagłówków),
   .gitignore, .claude/settings.json, instaluje plugin wgu (zakres: projekt) i robi git init.

3. Gdy init nie znalazł `claude` (komunikat „nie znaleziono claude"): aplikacja Claude z MSIX
   ma wirtualizowany %APPDATA%, więc kopia leży pod %LOCALAPPDATA%:
     $c = (Get-ChildItem "$env:LOCALAPPDATA\\Packages\\Claude_*\\LocalCache\\Roaming\\Claude\\claude-code\\*\\*\\claude.exe" | Select-Object -Last 1).FullName
     & $c plugin marketplace add C:/dev/wargame_utils --scope project
     & $c plugin install wgu@wargame-utils --scope project
   Po zmianach w narzędziu: `plugin update wgu@wargame-utils`.

4. Uzupełnij wgu.yaml:
   - game.title, game.rules_version, game.publisher;
   - pdf.accent_color: kolor tekstu „zmienione w tej wersji". Pomiar to heurystyka;
     czysty niebieski (0000FF) to zwykle hiperłącza, nie zmiany. Sprawdź w PDF-ie;
   - terminology.layers: domyślnie tylko [common]. Dodaj warstwy epoki i serii z
     <wargame_utils>/terminology/ (era/<x>, series/<x>), jeśli istnieją dla tej gry;
   - sources.errata / charts / scenarios: dodatkowe dokumenty (starsze wydanie jako role: previous).

5. NOWA sesja Claude Code w katalogu gry (plugin ładuje się dopiero wtedy):
     /wgu:nowy-projekt          rozpoznanie źródeł, kolor zmian, fonty
     /wgu:atomizacja            baza reguł kb/ (agent analityk-zasad: Opus, effort max)
     /wgu:tlumaczenie --proba   próba na 5 fragmentach, potem całość

6. Dodatkowe materiały (moduł Vassal, skany): zostaw jako źródło tylko do odczytu, np. w
   vassal_module/. Sprawdź licencję grafik przed publikacją.

Workspace wielu gier:
  - w katalogu głównym utwórz wgu-workspace.yaml z listą `projects`;
  - `wgu workspace list` pokazuje gry;
  - `wgu -C ID config` i pozostałe polecenia wybierają grę z katalogu głównego;
  - `terminology_root` wskazuje współdzielone warstwy terminologii.

Zob. też: README.md (Szybki start), docs/MODELE.md (przypisanie modeli).
"""),
    "bgg": ("BGG: celowane źródła i lokalny FTS5", """\
Token: BGG_API_TOKEN w środowisku, rejestr dowodów: BGG_AUTHORITY_FILE.
W wgu.yaml: bgg: {thing_id: 3263, cache: build/bgg}.
Najpierw lokalnie (bez sieci): wgu bgg search "retreat priority" --role designer
Selekcja: wgu bgg forums; wgu bgg threads FORUM_ID --page 1
Celowane pobranie: wgu bgg sync --forum FORUM_ID --threads ID1,ID2 --max-batches 1
Oryginały: wgu bgg thread ID --count 100 --min-article-id 1
MCP: wgu mcp lub wgu bgg serve (jeden serwer, SDK MCP 1.x).
Sync: 1–5 wskazanych wątków, domyślnie jedna partia, najwyżej 5 po 100 wpisów;
metadane osobno. Kontynuacja ręczna przez pending_thread_ids; bez pełnego zrzutu forum.
Odstęp >=5 s, cache XML 1 h, maksymalnie 3 próby HTTP. Po błędzie zatrzymaj kwerendę.
BGG_OFFLINE=1 blokuje sieć. WGU_BGG_TOKEN/OFFLINE to aliasy zgodności.
Role wyłącznie z BGG_AUTHORITY_FILE; bgg.authorities i nazwisko nie są dowodem.
Nieznane konto: unverified. Rola autora nie potwierdza oficjalności konkretnego wpisu.
Indeks: build/bgg/bgg.sqlite w grze; MCP poza grą: ~/.cache/wgu/bgg/index.sqlite.
BGG_INDEX_PATH pozwala użyć tego samego indeksu w CLI i MCP.
Oryginały, metadane, linki i daty są zachowane; FTS5 jest osobną pochodną do wyszukiwania.
Cache poza Git, cytaty evidence <=25 słów. Protokół: docs/BGG-MCP-WORKFLOW.md.
"""),
}


def render(topic: str | None = None) -> str:
    if topic is None:
        rows = [f"  {k:<12} {title}" for k, (title, _) in TOPICS.items()]
        return "Tematy pomocy (wgu help TEMAT):\n" + "\n".join(rows) + "\n\nPozostałe polecenia: wgu --help"
    if topic not in TOPICS:
        raise SystemExit(f"nieznany temat „{topic}”. Dostępne: {', '.join(TOPICS)}")
    title, body = TOPICS[topic]
    return f"{title}\n{'=' * len(title)}\n\n{body}"
