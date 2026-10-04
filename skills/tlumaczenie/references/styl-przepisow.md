# Styl polskiej instrukcji: reguły redakcyjne

Obowiązuje razem z przewodnikiem stylu projektu (`translation.glossary`, zwykle `docs/przewodnik_stylu.md`).
Hierarchia (decyzja właściciela 2026-10-04, `docs/decyzje.md`):
1. **Normy polszczyzny** (ortografia, interpunkcja, fleksja, pisownia wielkich liter, skróty) obowiązują zawsze, także
   wbrew wcześniejszym konwencjom projektu. Właściciel: „poprawiamy zawsze zgodnie z zasadami polszczyzny”.
2. **Decyzje właściciela** (terminy, preferencje redakcyjne zgodne z normą) mają pierwszeństwo przed regułami tego dokumentu.
3. Reguły tego dokumentu.
Jeśli przewodnik projektu narusza normę, popraw tekst zgodnie z normą i zgłoś to w raporcie.

## 1. Cztery rodzaje tekstu, cztery rejestry
| Rodzaj | Rejestr | Zasady |
|---|---|---|
| **Przepisy** (reguły, procedury, tabele, definicje) | rzeczowy, precyzyjny, regulaminowy | jedno pojęcie = jeden termin; zdania jednoznaczne; wierność według `wiernosc-zasad.md` |
| **Przykłady** (*Example*, *Play Example*) | rzeczowy, narracyjny | czas teraźniejszy; te same terminy co w przepisach; liczby jak w oryginale |
| **Komentarze historyczne i uwagi autora** (*Historical Note*, *Design Note*, wstępy, eseje) | publicystyczny lub literacki, staranny | słownictwo epoki tam, gdzie jest ugruntowane w polskiej historiografii; bez archaizacji |
| **Uwagi tłumacza** | rzeczowy | wyłącznie w ramce przewidzianej w przewodniku; oszczędnie; jasno oddzielone od przepisów |

Terminy gry (nazwy mechanik) są takie same we wszystkich rodzajach tekstu. W komentarzu historycznym słowo
„kohorta” oznacza jednostkę wojskową w historii. Jeśli gra używa „kohorty” jako typu żetonu, zachowaj spójność
i nie mieszaj znaczeń w jednym zdaniu.

## 2. Terminy zdefiniowane
- Używaj **wyłącznie** zatwierdzonego odpowiednika z glosariusza (`wgu terms for-chunk`). **Nie zastępuj terminu
  synonimem dla urozmaicenia tekstu.** W przepisach powtórzenie jest zaletą, a nie wadą stylu.
- Słowo ogólne, które nie jest terminem gry, tłumacz swobodnie. Gdy przypomina termin, wybierz takie, którego czytelnik
  nie pomyli z mechaniką (np. nie pisz „wycofać” w znaczeniu ogólnym, jeśli „wycofanie” jest nazwą mechaniki).
- **Oryginał przy terminie** (decyzja właściciela 2026-10-04): przy pierwszym wystąpieniu w podrozdziale każdego
  **pojęcia mechaniki gry** (nazwy akcji, stanów, faz, parametrów, testów, znaczników i tabel, np. uporządkowane
  wycofanie, reorganizacja, test TQ) dodaj angielski oryginał makrem `\ang{}`. Makro drukuje go kursywą w **stałym
  kolorze** (`wgang`), więc gracz od razu rozpoznaje nazwę z komponentów i angielskich materiałów. Zapis według
  `notation.first_use`. Nie glosuj słów ogólnych (dowódca, tura, jednostka bojowa) ani kolejnych wystąpień w tym samym podrozdziale.
- Skróty: tak, jak ustalono w glosariuszu (`pl_abbrev`). Nie twórz nowych. Skrót obcy (MA, TQ, DRM) zostawiaj tylko wtedy,
  gdy widnieje na komponentach lub tak zdecydował właściciel.
- Nazwy widoczne na komponentach (żetony, tabele, plansza): zgodnie z `notation.component_text`. Gracz musi znaleźć
  na stole to, o czym czyta.

## 3. Czego unikać (typowe błędy przekładu maszynowego)
**Neologizmy i kalki.** Nie twórz nowych słów. Jeśli polszczyzna nie ma ugruntowanego odpowiednika, użyj opisu
albo pozostaw termin oryginalny kursywą i zgłoś propozycję w pliku propozycji. Nie wprowadzaj neologizmu do tekstu
bez zatwierdzenia.

| Zamiast | Pisz | Uwagi |
|---|---|---|
| dokonuje ataku, dokonuje ruchu, przeprowadza test | atakuje, porusza się, wykonuje test / testuje | nominalizacje z „dokonywać” |
| następuje rozstrzygnięcie | walkę rozstrzyga się | |
| jednostka posiada wartość 5 | jednostka ma wartość 5 | „posiadać” tylko o własności |
| aplikować / zaaplikować modyfikator | stosować modyfikator, uwzględnić modyfikator | |
| jest w stanie | może | |
| gracz może wybrać, aby… | gracz może… | kalka *may choose to* |
| w przypadku gdy, w sytuacji gdy | gdy, jeśli | |
| w celu wykonania | aby wykonać | |
| na swojej turze | w swojej turze | kalka *on his turn* |
| bazując na, w oparciu o | na podstawie, według | |
| efektywnie (*effectively*) | w praktyce, w rzeczywistości | fałszywy przyjaciel |
| ewentualnie (*eventually*) | ostatecznie, w końcu | fałszywy przyjaciel |
| aktualnie (*actually*) | w rzeczywistości | fałszywy przyjaciel |
| dedykowany (*dedicated*) | przeznaczony, specjalny | |
| kluczowy, istotny, znaczący (bez potrzeby) | konkretne określenie albo nic | nadużywane wzmacniacze |
| Jeśli…, wtedy… | Jeśli…, to… lub bez „to” | kalka *if…, then…* |
| A, B, i C | A, B i C | brak przecinka przed „i”, „oraz”, „lub” w wyliczeniu |
| jego (o jednostce, *its*) | ta jednostka, jej… albo konstrukcja bezosobowa | nadmiar zaimków dzierżawczych |

**Archaizacja i żargon.** W przepisach nie stylizuj języka na dawny. W komentarzach historycznych używaj nazw realiów
epoki przyjętych w polskiej historiografii (manipuł, kohorta, falanga, tyraliera), ale nie dawnej składni ani słownictwa
wyłącznie dla efektu. Współczesnego żargonu wojskowego (NATO) nie stosuj do realiów starożytnych ani XIX-wiecznych
(zob. `polityka-terminologiczna.md` §5).

## 4. Składnia przepisu
- Jedno zdanie, jeden przepis. Długie zdanie warunkowe dziel tylko wtedy, gdy nie zmienia to zakresu warunków.
- Podmiot jawny („gracz”, „jednostka”, „dowódca”) albo konstrukcja bezosobowa. Strona bierna dopuszczalna,
  ale nie łańcuchami „zostaje …, po czym zostaje …”.
- Czas teraźniejszy („jednostka traci punkt”), nie przyszły.
- Szyk polski: określenia przy określanym, temat na początku. Nie kopiuj angielskiego szyku zdania.

## 5. Typografia i zapis
- Nagłówki: wielka litera tylko na początku i w nazwach własnych („Ruch i strefy kontroli”), nie *Title Case*.
  Wersaliki w nagłówku są dopuszczalne wyłącznie jako zabieg typograficzny oprawy (np. `\MakeUppercase` w stylu), nie w tekście źródłowym.
- **Wielkie litery w terminach:** nazwy faz, akcji, stanów, rodzajów dowódców i wariantów gry to nazwy pospolite, więc
  piszemy je małą literą („faza rozkazów”, „dowódca armii”, „gra podstawowa”). Tytuły dokumentów, tabel i arkuszy
  piszemy wielką literą tylko w pierwszym wyrazie („Tabela walki”, „Zasady systemowe”). Napis na żetonie przytaczamy
  w cudzysłowie, tak jak jest wydrukowany („Moved”).
- **Tytuły gier, modułów i serii zawsze w oryginale** (decyzja właściciela 2026-10-04): *SPQR: Great Battles of the
  Roman Republic*, *Great Battles of History*, skróty tytułów (*RTG*, *HSN*), także w paginie. Polski opis może
  stać obok (np. w uwadze tłumacza), ale nie zastępuje tytułu.
- Cudzysłów „…”, wewnętrzny ‚…’. Półpauza ze spacjami jako myślnik, bez spacji w zakresach (1–4).
- Liczby: wartości gry zawsze cyframi (3 heksy, +1, 1d10). Słownie tylko w tekście ogólnym i komentarzach.
- Skróty według norm polszczyzny: z kropką skróty, które nie kończą się ostatnią literą wyrazu (np., tzw., tj., itd., m.in.),
  bez kropki ściągnięcia zawierające ostatnią literę wyrazu (wg, nr, pkt, dr). Zatem **„wg”, nie „wg.”** i „pkt 3”, nie „pt.3”.
- Liczebnik i rzeczownik: „2 heksy”, „5 heksów”, „22 heksy”. Uzgadniaj formy.
