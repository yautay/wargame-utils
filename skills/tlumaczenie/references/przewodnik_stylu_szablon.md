# Przewodnik stylu tłumaczenia <GRA> PL (<tytuł instrukcji> v<wersja>)

> Szablon z procesu GCACW-PL. Reguły ogólne: `styl-przepisow.md` (ten przewodnik zapisuje decyzje właściciela, które mają pierwszeństwo). Sekcje 1–5 opisują **domyślny styl** (wypracowany przez M. Pielaszkiewicza
> w tłumaczeniu GCACW). Jeśli w projekcie istnieje wcześniejsze tłumaczenie — zastąp opisy faktycznymi
> cechami jego stylu (patrz „Jak analizować styl” na końcu), zachowując strukturę dokumentu.
> Gotowy plik zapisz w repo jako `docs/przewodnik_stylu.md`.

Dokument opisuje styl tłumaczenia i obowiązuje przy każdym nowym lub poprawianym fragmencie.

## 1. Rejestr i ton
- Polszczyzna formalna, regulaminowo-urzędowa, z nutą wojskowej sprawozdawczości:
  „Niniejsze zasady”, „w gestii gracza”, „determinuje”, „kwalifikująca się do aktywacji jednostka”.
- Podmiotem jest „gracz”, „gracz z inicjatywą”, „aktywny gracz”, „gracz <strony A/B>” albo konstrukcja
  bezosobowa. Chętnie strona bierna i „zostaje + imiesłów”: „jednostka zostaje zdezorganizowana”.
- Skróty urzędowe: „wg.”, „ww.”, „pt.3” (punkt procedury), „np.”, „tzw.”.
- Zdania średniej długości; zdanie złożone dzielimy, jeśli ma więcej niż ~2 przecinkowe wtrącenia.
- Wyjątek: wstępy, przedmowy, eseje autorów — rejestr literacki, ciepły, ale wierny.

## 2. Tłumaczenie objaśniające, ale wierne
- Treść każdej zasady = oryginał. Niczego nie pomijamy ani nie zmieniamy w warunkach, liczbach i wyjątkach.
- Dopuszczalne przekształcanie zdań w instrukcję krok po kroku i dopowiadanie sensu w obrębie oryginału
  („Gracz nie jest zobowiązany do wybrania każdej kwalifikującej się jednostki, lecz może tak uczynić.”).
- Wyjaśnienia **wykraczające** poza oryginał (porady, streszczenia, „na co uważać”) → ramka `wskazowka`
  („Notatka tłumacza”). Oszczędnie: 0–2 na podrozdział, przy procedurach i pułapkach zasad.
- Powtórzenia kluczowych warunków są dopuszczalne.

## 3. Terminologia dwujęzyczna
- Przy pierwszym wystąpieniu ważnego terminu w podrozdziale: polski termin + `\ang{oryginał}` → „zmęczenie/*fatigue*”.
  W pogrubionych nazwach: `\textbf{Znaczniki siły\ang{Strength Markers}}`.
- Nazwy mechanik bez dobrego polskiego odpowiednika zostają w oryginale (kursywą).
- Skróty tytułów gier/modułów: `\gra{XYZ}` (kursywa jak w oryginale).
- Spolszczenia: „spasować”, „pas”, „przemarsz”, „aktywować”.

## 4. Typografia i struktura (makra z `<projekt>-style.sty`)
- Pogrubiamy warunki, liczby i zakazy będące istotą reguły; 1–3 wyróżnienia na akapit.
- `\wyjatek`, `\wyjatki`, `\uwaga` → „**Wyjątek**:”, „**Uwaga**:”. „(Optional)” → `\opcja` lub ramka `opcjonalna`.
- Procedury: `\begin{kroki} \item … \end{kroki}`, podpunkty `podkroki` (a., b., c.).
- Odsyłacze do reguł: „[7.7]” lub „(patrz 7.7)”.
- `\section{…}` (→ „7.0”), `\subsection{…}` (→ „7.1”), `\subsubsection{…}` (podtytuł bez numeru).
- Tekst w kolorze zmian wersji → `\nowe{…}`; dłuższe → `nowyblok`.
- Przykład → `przyklad[z \gra{X}]`; duży z tytułem → `przykladtytul{…}`; „Special Rule …” → `specjalna{…}`;
  podsumowania → `podsumowanie{…}`.
- Tabele: `tabularx` na `\linewidth`; nagłówek `\naglowektabeli \tn{Kol1} & \tn{Kol2}\\`, co drugi wiersz `\szarywiersz`.
- Żetony: `\zeton{nazwa}` / `\zeton[r]{nazwa}` / `\zetony{a}{b}` / `\zetonwiersz{a}`;
  przed listą lub ramką użyj `\zetonobok{tekst}{nazwa}` (wrapfigure psuje listy w multicols).
  Lista dostępnych plików PNG: <uzupełnij po ekstrakcji grafik>.
- Cudzysłowy „…”, półpauza ` -- `, zakresy `1--4`, ułamki „½”.
- Interpunkcja polska: przecinek przed „który”, „że”, „aby”, „jeśli”.
- Pliki UTF-8 **bez BOM**. Nagłówek pliku: `%! Author = <autor>` i `%! Date = <data>`.

## 5. Kolory i ramki
| Element | Znaczenie |
|---|---|
| `\nowe{}` (kolor zmian z oryginału) | zmiana/dodatek w bieżącej wersji |
| ramka `opcjonalna` (fiolet) | zasada opcjonalna |
| ramka `specjalna` | zasada specjalna tytułu/scenariusza (ramka „Special Rule”) |
| ramka `przyklad` (szara) | przykład z oryginału |
| ramka `wskazowka` (pergamin, sepia, ornament) | notatka tłumacza — wyłącznie treści spoza oryginału |

## 6. Terminologia
Glosariusz **nie** jest tabelą w tym przewodniku. Obowiązujące terminy są w warstwach terminologii
(`wgu.yaml` → `terminology`; zasady: `references/polityka-terminologiczna.md`). Tutaj zapisz tylko:
- warstwy używane przez projekt (np. `common`, `era/ancient`, `series/gboh`, `kb/terminology.yaml`),
- **preferencje redakcyjne właściciela** dotyczące zapisu terminów (wielkie litery w nazwach faz i tabel, zapis
  dwujęzyczny, pozostawianie oryginału kursywą, skróty), z datą decyzji,
- znane konflikty między przewodnikiem a `styl-przepisow.md` i ich rozstrzygnięcie.
Słowniczek do druku generuje `wgu terms glossary-tex`. Wcześniejszą tabelę 2-kolumnową można zaimportować
poleceniem `wgu terms import-md`.

---

## Jak analizować styl istniejącego tłumaczenia
Przeczytaj **wszystkie** pliki tłumaczenia i odpowiedz na pytania (z cytatami-przykładami):
1. **Rejestr**: urzędowy / potoczny / techniczny? Charakterystyczne zwroty i skróty („wg.”, „ww.”, „pt.”)?
2. **Składnia**: strona bierna czy czynna? Podmiot („gracz”, bezosobowo)? Długość zdań?
3. **Wierność**: dosłownie czy objaśniająco? Czy autor dopowiada sens, dzieli zdania na kroki?
4. **Terminy**: jak zapisuje oryginał (ukośnik „pl/en”, nawias, kursywa)? Co zostawia nieprzetłumaczone?
   Gdzie terminologia jest niespójna (to trafia do słowniczka jako decyzja)?
5. **Typografia**: co pogrubia, co kursywą; jak oznacza „Wyjątek”, „Przykład”, „Uwaga”; jak numeruje procedury.
6. **Własne konwencje**: kolory, ramki, dopiski — co oznaczają? (Zachowaj je jako makra/ramki w stylu.)
7. **Błędy do poprawy bez zmiany stylu**: literówki, błędy faktów, interpunkcja, niespójne cudzysłowy/myślniki.
Wynik wpisz w sekcje 1–5 powyżej i pokaż użytkownikowi skrót przed tłumaczeniem.
