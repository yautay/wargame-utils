# Przewodnik stylu tłumaczenia <GRA> PL (<tytuł instrukcji> v<wersja>)

> Szablon z procesu GCACW-PL. Sekcje 1–5 opisują **domyślny styl** (wypracowany przez M. Pielaszkiewicza
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

## 6. Słowniczek (EN → PL)
Obowiązujące tłumaczenia. Poniżej baza z GCACW (wargame heksowy, wojna secesyjna) — usuń zbędne,
dopisz terminy nowej gry **przed** rozpoczęciem tłumaczenia. Tabela musi mieć dokładnie 2 kolumny
(czyta ją `scripts/gen_glossary.py`).

| English | Polski |
|---|---|
| Standard (Series) Rules | Zasady Systemowe (ZS) |
| Basic Game / Advanced Game | Gra Podstawowa / Gra Zaawansowana |
| scenario | scenariusz |
| Union / Confederate (player) | Unia / Konfederacja (gracz Unii / gracz Konfederacji) |
| counter / playing piece | żeton |
| military unit | jednostka wojskowa (jednostka) |
| leader | dowódca |
| informational markers | żetony pomocnicze / znaczniki |
| Army / District / Corps / Division Leader | Dowódca Armii / Dowódca Regionalny / dowódca korpusu / dowódca dywizji |
| Tactical value / Command value / Artillery value | wartość taktyczna / wartość dowodzenia / wartość artyleryjska |
| Strength marker | znacznik siły |
| Manpower value | wartość siły (liczebność) |
| Combat value | wartość bojowa |
| organized / disorganized | zorganizowana / zdezorganizowana (strona znacznika siły) |
| normal side / exhausted side | strona normalna / strona wyczerpana |
| exhausted | wyczerpana (jednostka na rewersie) |
| Fatigue level / Fatigue marker | poziom zmęczenia / znacznik zmęczenia (**nie** „wyczerpanie”) |
| Movement Allowance (MA) | limit punktów ruchu (MA) |
| Movement Point (MP) | punkt ruchu (MP) |
| Movement Track | tor ruchu |
| Active Movement Allowance marker | znacznik „Aktywny limit ruchu” |
| Leader Movement Allowance marker | znacznik „Limit ruchu dowódcy” |
| march / march action | marsz (przemarsz) / akcja marszu |
| extended march / force march | marsz wydłużony / marsz forsowny |
| Activate Leader (action) | aktywacja dowódcy |
| Leader Activation marker | znacznik „Aktywacja dowódcy” |
| Activate Army Leader | aktywacja Dowódcy Armii |
| Assault / Grand Assault | szturm / *Grand Assault* (wielki szturm) |
| Burn RR Station | niszczenie stacji kolejowej |
| RR Station damaged / destroyed | stacja kolejowa uszkodzona / zniszczona |
| Entrench / Entrenchment (action) | okopywanie się / akcja budowy umocnień |
| entrenchments | umocnienia polowe |
| Abatis / Breastworks / Fort ; "-Build" | zasieki (*abatis*) / przedpiersia (*breastworks*) / fort ; „w budowie” |
| Redoubt | reduta |
| Action Cycle / Action Phase | cykl akcji / faza akcji |
| Initiative Segment / Activation Segment | segment inicjatywy / segment aktywacji |
| pass | pas / spasować |
| Random Events Phase | Faza wydarzeń losowych |
| Leader Transfer Phase / leader transfer | Faza przemieszczania dowódców / przemieszczenie dowódcy |
| Recovery Phase | Faza Reorganizacji |
| Turn Indication Phase | Faza oznaczenia tury (Koniec tury) |
| active unit / active leader / active player | jednostka aktywna / dowódca aktywny / gracz aktywny |
| Zone of Control (ZOC) / Restricted ZOC | strefa kontroli (ZOC) / ograniczona strefa kontroli |
| Command radius | zasięg dowodzenia |
| hex / hexside | heks / krawędź heksu |
| clear, rolling, rough, woods, city | równina, teren pagórkowaty, teren trudny, las, miasto |
| swamp, provisional swamp, hill, mountain, loess | bagno, sezonowe bagno, wzgórze, góry, less |
| river (major/minor), creek, ridge, bluff | rzeka (duża/mała), strumień, grzbiet, urwisko |
| ford, bridge, ferry, dam, county border | bród, most, przeprawa promowa, zapora, granica hrabstwa |
| village, pike, road, trail, landing | wioska, droga utwardzona (*pike*), droga gruntowa, szlak, przystań |
| stacking / stack | układanie w stos / stos |
| Force markers | znaczniki zgrupowania („Force”) |
| attack / attacker / defender | atak / atakujący / obrońca |
| Combat Chart | Tabela walki |
| die / dice / die roll | kość / kości / rzut kością |
| die roll modifier (DRM) | modyfikator rzutu |
| Ratio / Tactical / Artillery modifier | modyfikator stosunku sił / taktyczny / artyleryjski |
| Artillery Value Differential | różnica wartości artyleryjskich |
| flank attack | atak z flanki (oskrzydlenie) |
| Flanks Refused (marker) | zagięte skrzydła (znacznik „Flanks Refused”) |
| Combat results: letter / number results | wyniki literowe / liczbowe |
| retreat / rout | odwrót / ucieczka (*rout*) |
| retreat priorities | priorytety odwrotu |
| advance after combat | zajęcie pola po walce |
| Cavalry Retreat | wycofanie kawalerii |
| Defender's Voluntary Retreat | dobrowolny odwrót obrońcy |
| Manpower loss | strata siły |
| elimination | eliminacja |
| Demoralization (Dmorlz-1/-2) | demoralizacja (stopień 1 / 2) |
| Pontoon bridge | most pontonowy |
| dismantling | rozbiórka |
| repair | naprawa |
| Rain / Rain Number | deszcz / wskaźnik deszczu |
| fordable / unfordable | przekraczalna w bród / nieprzekraczalna w bród |
| Limited Intelligence | ograniczony wywiad |
| supply / out of supply | zaopatrzenie / bez zaopatrzenia |
| Victory Points (VP) | punkty zwycięstwa (VP) |
| OOB (order of battle) | ordre de bataille (OOB) |
| Column of Route / Hasty / Normal / Prepared attack | atak z kolumny marszowej / pośpieszny / normalny / przygotowany |
| Terrain Chart | Tabela terenu |
| major terrain | teren dominujący |
| Force Display | plansza zgrupowań |
| Detachment / substitute | wydzielanie oddziałów / oddział zastępczy |
| wagon train | tabor |
| Retreat Chart / Retreat Description | Tabela odwrotu / opis odwrotu |
| Priority Number | numer priorytetu |
| Overriding Retreat Priorities | odstąpienie od priorytetów odwrotu |
| Surrender | kapitulacja |
| Defense value | wartość obronna |
| End Action | koniec akcji |
| forage / levy | furażować / kontrybucja |
| refuse flanks | zaginanie skrzydeł |
| Attachment Phase | Faza przydziału |
| Naval Battery | bateria nadbrzeżna |
| permanent bridge / Fort | most stały / stały fort |
| Turn Track | tor tur |
| Random Events Table | Tabela wydarzeń losowych |
| dummy marker | znacznik pozorny |
| Assault Number / Grand Assault Number | wskaźnik szturmu / wskaźnik Grand Assault |
| basic / final flank bonus | podstawowa / końcowa premia za oskrzydlenie |
| Ratio Chart | Tabela stosunku sił |
| Insubordination | niesubordynacja |
| Demi-division | półdywizja |

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
