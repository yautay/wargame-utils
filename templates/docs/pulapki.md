# Pułapki i rozwiązania (zebrane w projekcie GCACW-PL)

## Środowisko (Windows)
| Problem | Rozwiązanie |
|---|---|
| `miktex packages install` → „Timeout was reached” / „SSL connect error” | Zmień mirror: `initexmf --set-config-value="[MPM]RemoteRepository=https://ftp.fau.de/ctan/systems/win32/miktex/tm/packages/"` |
| Kompilacja staje na „File `X.sty' not found” mimo AutoInstall | `initexmf --set-config-value="[MPM]AutoInstall=1"`; pętla: kompiluj → parsuj brakujący plik → `miktex packages install <nazwa bez .sty>` |
| `latexmk` nie działa | Wymaga Perla. Kompiluj `lualatex` 2–3× ręcznie. |
| „lualatex: major issue: So far, you have not checked for MiKTeX updates” | Ostrzeżenie, nie błąd — ignoruj. |
| Read nie renderuje PDF („pdftoppm is not installed”) | `pip install pymupdf`, renderuj `wgu pdf render` i oglądaj PNG. |
| PowerShell: heredoc `<<'EOF'` → błąd parsera | Skrypty wieloliniowe uruchamiaj narzędziem **Bash** (Git Bash) albo zapisuj do pliku `.py` i uruchamiaj. |
| Kod Pythona z backslashami (LaTeX) w heredocu/`-c` psuje się (`\t`→TAB, `\r`, „invalid escape sequence”) | **Zapisz skrypt do pliku narzędziem Write** i używaj raw stringów `r"..."`. Do zmian w `.sty/.tex` używaj narzędzia Edit, nie sed/python. |
| `Set-Content -Encoding UTF8` w PS 5.1 dodaje BOM | Unikaj; zapisuj przez Write/Python (`encoding='utf-8'`). Usuń BOM, jeśli się pojawi. |
| Git: „LF will be replaced by CRLF” | Tylko ostrzeżenie. |

## Fonty (fontspec / LuaLaTeX)
| Problem | Rozwiązanie |
|---|---|
| „The font "Source Sans 3-RegularIt" cannot be found” | Odwołuj się po nazwie pliku: `\setsansfont{SourceSans3}[Extension=.otf, UprightFont=*-Regular, …]` |
| `\gra{}` (kursywa) w nagłówkach daje ostrzeżenia/prosty krój | Daj fontowi nagłówków `ItalicFont=*-SemiboldIt, BoldItalicFont=*-BoldIt`. Kapitaliki kursywne zwykle nie istnieją — akceptowalne. |
| `\newcommand{\th}` → „Command \th already defined” | `\th` to znak „þ”. Makro nagłówka tabeli nazwij `\tn`. |

## Układ (multicols, ramki, obrazy)
| Problem | Rozwiązanie |
|---|---|
| Nagłówek tabeli w kolumnie `p{}`/`X` wypada niżej (pusta pierwsza linia) | `\tn` zaczyna się od `\leavevmode` (już w szablonie). |
| Długi tytuł sekcji wychodzi poza czarny pasek | Pasek mierzy szerokość i zawija w `\parbox` (już w szablonie `\gcpasek`). |
| `wrapfigure` (`\zeton`) tuż przed `itemize`/`kroki`/tcolorbox w multicols → „Something's wrong--perhaps a missing \item”, rozjechane strony | Użyj `\zetonobok{tekst}{png}` (minipage) lub wstaw żeton po akapicie tekstu, nie przed listą. |
| Ramka `breakable` w multicols dzieli się brzydko / tytuł zostaje sam na dole strony | Dla krótkich ramek opcja `unbreakable`; dla dużych pełnej szerokości — `figure*[tbp]` (ląduje na górze następnej strony). |
| `\szerokostart/\szerokostop` rozbija ramkę | Tylko na najwyższym poziomie pliku; preferuj `figure*`. |
| Spis treści na 2 strony | `\fontsize{8.6}{10}\selectfont` + `\cftbeforesecskip=2pt` w multicols. |
| Słowniczek nie mieści się na stronie | 3 kolumny, `\footnotesize`, wpis w jednej linii „**en** -- pl” (generator już tak robi). |
| `\section*` nie trafia do spisu treści | Dodaj `\addcontentsline{toc}{section}{…}`. |
| hyperref: „Difference (2) between bookmark levels” | Kosmetyka (subsubsection po section*). Ignoruj. |
| `\nowe{}` w tytule sekcji psuje zakładki PDF | `\texorpdfstring{\nowe{…}}{…}`. |

## Grafiki
| Problem | Rozwiązanie |
|---|---|
| Żetony w nowym PDF mają niską rozdzielczość (75 px) | Szukaj tych samych w starszej edycji (`wgu pdf images --hires`); dopasowanie automatyczne **sprawdź wzrokowo** (zdarzył się przód i tył różnych jednostek). |
| Mapa przykładu to raster + nakładki wektorowe | Wytnij renderem strony (`wgu pdf render --page N --clip … --dpi 300`), nie ekstrakcją obrazu. |
| Proste diagramy (heksy, strzałki) z angielskimi etykietami | Przerysuj w TikZ z polskimi opisami. |
| Okładka z logo wydawcy/licencjodawcy | Użyj samej ilustracji; dopisek „Nieoficjalne tłumaczenie”; bez logo. |

## Tłumaczenie równoległe
- Agenci ukuwają różne odpowiedniki tych samych terminów (np. „pospieszny/pośpieszny”, „zwykły/normalny”,
  „Dowódcy w walce/Dowódcy a walka”) — po złożeniu grep wariantów i ujednolicenie; terminy do słowniczka.
- Agent nie widzi tytułów sekcji innych agentów — odwołania „patrz …” sprawdź po złożeniu.
- Zmiana w `.sty` w trakcie pracy agentów jest bezpieczna, jeśli tylko dodaje/naprawia (agenci kompilują własne pliki testowe).
- Odczytuj raporty agentów: zawierają wątpliwości co do źródła (literówki w oryginale) — przekaż je użytkownikowi.
