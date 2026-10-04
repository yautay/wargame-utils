"""`wgu help [TOPIC]`: short procedures printed in the terminal (user-facing text in Polish)."""
from __future__ import annotations

TOPICS: dict[str, tuple[str, str]] = {
    "nowa-gra": ("Start tłumaczenia zasad nowej gry", """\
Jedno repozytorium (katalog) na jedną grę. Dane gry żyją tam, a nie w wargame_utils.

1. Katalog gry obok innych (np. C:/dev/mojagra), a w nim PDF instrukcji.
   Gdy w katalogu jest kilka PDF-ów, wskaż właściwy przez --pdf. Pozostałe PDF-y
   (scenariusze, karty, tabele) przenieś ręcznie do docs/.
   Gdy gra ma już własne repozytorium (kod, zadania), nie dokładaj do niego wgu.yaml:
   zrób osobny katalog gry i skopiuj tam tylko PDF.

2. Przygotowanie katalogu (z katalogu gry):
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

Zob. też: README.md (Szybki start), docs/MODELE.md (przypisanie modeli).
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
