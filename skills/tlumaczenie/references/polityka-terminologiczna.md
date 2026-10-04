# Polityka terminologiczna

## 1. Jednostka glosariusza: pojęcie w kontekście
Rekordem glosariusza jest **pojęcie** (mechanika, parametr, stan, element gry) w określonym zakresie, a nie angielskie słowo.
- Jedno słowo źródłowe może oznaczać kilka pojęć i mieć kilka odpowiedników. W SPQR *Line* to szyk, ale też część nazwy
  *Line Command*. Każde pojęcie dostaje osobny rekord z polem `disambiguation`.
- Dwie odrębne mechaniki nie dostają wspólnego odpowiednika tylko dlatego, że ich nazwy są w języku ogólnym synonimami
  (*retreat*, *withdrawal*, *rout* to trzy różne pojęcia). `wgu terms lint` ostrzega, gdy jedna forma polska
  obsługuje kilka pojęć.
- Format i pola: `wgu/schemas/terminology.schema.json` (`wgu/terms@1`).

## 2. Trzy poziomy (warstwy)
| Poziom | Plik | Przykłady pojęć | Kto zatwierdza |
|---|---|---|---|
| **wspólny dla gier wojennych** (`common`) | `<wargame_utils>/terminology/common.yaml` | heks, żeton, modyfikator rzutu, strefa kontroli, stos | właściciel; zmiana dotyczy wszystkich gier |
| **epoka / seria** (`era`, `series`) | `terminology/era/<epoka>.yaml`, `terminology/series/<seria>.yaml` | legion, manipuł (starożytność); spójność, ucieczka (GBoH); zmęczenie, szturm (GCACW) | właściciel; obowiązuje w serii |
| **gra i wydanie** (`game`) | `<repo gry>/kb/terminology.yaml` | nazwy znaczników, tabel, faz i zasad specjalnych danego tytułu | właściciel projektu gry |

Projekt gry wskazuje warstwy w `wgu.yaml` (`terminology.layers`). Warstwa bardziej szczegółowa wygrywa, ale zastąpienie
pojęcia z wyższej warstwy musi być jawne (`overrides: <id>` z uzasadnieniem). Lint wykrywa duplikaty i nieopisane konflikty.

## 3. Status i pochodzenie decyzji
- `proposal`: propozycja tłumacza lub analityka. **Nie jest obowiązująca.** Tłumacz może jej użyć w roboczym tekście,
  ale fragment nie przechodzi kontroli końcowej, dopóki status się nie zmieni.
- `approved`: zatwierdzone. Pole `decided_by` mówi, kto zdecydował: `user` (właściciel), `publisher-usage`
  (przejęte z publikacji wydawcy za zgodą właściciela), `imported` (przejęte z wcześniej zatwierdzonej tabeli).
- `disputed`: spór otwarty. Tłumacz używa formy z rekordu i zgłasza uwagi w pliku propozycji.
- `deprecated`: wycofane (zostaje dla historii i `wgu terms impact`).
- `preference: true` oznacza **preferencję redakcyjną** właściciela, a nie ustalenie słownikowe. Oba rodzaje są wiążące,
  ale należy je odróżniać w uzasadnieniu (`rationale`).
- Analityk i tłumacz **nie nadają** statusu `approved`. Nadaje go właściciel (bezpośrednio albo zatwierdzając listę).

## 4. Dowody (`evidence`) i ich waga
Każdy dowód ma pole `supports`, które mówi, **co** potwierdza:
- `existence`: słowo istnieje w polszczyźnie (słownik ogólny, np. WSJP). **Nie dowodzi**, że jest właściwym odpowiednikiem pojęcia gry.
- `sense`: znaczenie słownikowe pasuje do opisu mechaniki (definicja, kwalifikator, np. *hist.*, *wojsk.*).
- `military-usage`: użycie w polskich tekstach wojskowych lub historycznych danej epoki (regulaminy, opracowania naukowe, przekłady autorów antycznych).
- `usage-in-games`: użycie w polskich wydaniach gier (np. tłumaczenie udostępnione przez wydawcę). Pokazuje praktykę,
  ale nie gwarantuje poprawności ani zgodności z późniejszym wydaniem gry.
- `against`: dowód przeciw (np. słowo ma inne ugruntowane znaczenie, jest anachroniczne).
Rejestr źródeł z oceną wiarygodności i skrótami: `zrodla.md`.

## 5. Terminologia współczesna a historyczna
- Słowniki wojskowe współczesne (np. AAP-6 PL) służą do rozumienia **pojęć ogólnych** i ich definicji.
  **Nie przenoś automatycznie terminów NATO do realiów starożytnych, napoleońskich ani wojny secesyjnej.**
  Przykładowo współczesne nazwy rodzajów wojsk, szczebli i działań nie pasują do armii manipułowej.
- Dla realiów historycznych pierwszeństwo mają polska historiografia danej epoki i przekłady źródeł.
- Nazwa mechaniki gry nie musi być terminem historycznym. Jeśli autor gry nadał słowu znaczenie techniczne
  (np. *Cohesion*), odpowiednik ma oddawać tę mechanikę. Historyczna nazwa jest właściwa tam, gdzie gra nazywa realia
  (typ jednostki, szyk, broń).

## 6. Procedura dla nowego pojęcia
1. Opisz mechanikę własnymi słowami (`sense`) z numerami reguł (`rules`). Sprawdź w `kb/`, czy to nie jest już
   istniejące pojęcie pod inną nazwą.
2. Sprawdź warstwy wyższe (`wgu terms show <termin>`). Jeśli pojęcie tam jest, użyj go albo przygotuj jawne `overrides`.
3. Zbierz kandydatów i dowody: wydania polskie gier serii, polska literatura przedmiotu, słowniki. Dla każdego kandydata
   zapisz, co dowód potwierdza (`supports`).
4. Odrzuć kandydatów z powodem (`rejected`): anachronizm, kolizja z innym pojęciem, kalka, neologizm, niejednoznaczność.
5. Ustal formy odmiany (`pl_forms`). Użyj WSJP, jeśli hasło tam jest. Formy służą do kontroli spójności.
6. Ustal zapis (`notation`): pierwsze użycie, wielkie litery, tekst na komponentach.
7. Zapisz rekord jako `proposal` i przedstaw właścicielowi do decyzji.

## 7. Zmiana zatwierdzonego terminu
Starą formę przenieś do `history` (`from`, `from_forms`, `date`, `reason`), wpisz nową. Potem uruchom
`wgu terms impact <id> --tex <pliki> --src <źródła z markerami>`, popraw wskazane miejsca punktowo,
a na koniec `wgu terms check` musi dawać 0 pozycji „update”. Szczegóły w `weryfikacja.md`.
