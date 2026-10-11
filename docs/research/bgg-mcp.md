# Badanie: serwer MCP „bgg” dla wgu

Data badania: 2026-10-11. Etap 1 zadania „serwer MCP bgg”: warunki korzystania, mapa endpointów, autorytety,
uprzejmość, istniejące projekty. Kod powstaje dopiero po decyzjach właściciela z sekcji 7.

Wszystkie odpowiedzi API opisane niżej sprawdzono na żywo 2026-10-11 (curl, przeglądarkowy User-Agent z dopiskiem
`wgu-research`, przerwy 1,5–2 s, łącznie ok. 35 zapytań). Przykłady pochodzą z gry Ukraine '43 (thing 3263).

## Wnioski w skrócie

1. **api.geekdo.com nie nadaje się na źródło dla narzędzia.** Admin BGG (Daniel Karp, „dakarp”) napisał
   2025-11-05 w wątku o XML API, że tych endpointów JSON nie należy używać. Licencja ich nie obejmuje, a użycie poza
   zwykłym przeglądaniem może być uznane za naruszenie Terms of Service. Wiki `BGG_JSON_API` mówi to samo. Jedyną
   legalną drogą jest XML API2 z tokenem zarejestrowanej aplikacji.
2. **XML API2 pokrywa główny przypadek użycia:** `thing` (wydania, credits), `forumlist`, `forum` (50 wątków na
   stronę, sortowanie wg ostatniego posta), `thread` (z `minarticleid`/`minarticledate`, czyli sync przyrostowy
   wprost), `user`, `search`. Nie pokrywa **plików gry**, **powiązania osoba ↔ konto** ani pełnotekstowego
   wyszukiwania forów (to ostatnie nie istnieje nigdzie; robimy lokalne FTS5).
3. **Warunki XML API2:** rejestracja obowiązkowa także dla użytku niekomercyjnego; tylko cele niekomercyjne;
   atrybucja BGG; zakaz trenowania AI/LLM na danych; zakaz udostępniania API innym aplikacjom; zalecany cache.
   Nasz przypadek (lokalny cache, odczyt na żądanie, osobisty projekt hobbystyczny) mieści się w tych warunkach,
   ale dane z forów trafiają do kontekstu modelu (Claude). To nie jest trenowanie, mimo to trzeba to uczciwie
   opisać we wniosku o aplikację (szczegóły w sekcji 1.4).
4. **robots.txt boardgamegeek.com blokuje agenty AI** (`anthropic-ai`, `ClaudeBot`, `Claude-Web`,
   `Perplexity-User` i in.). Dotyczy to stron serwisu, a XML API2 ma własną licencję. Jest to jednak wyraźny
   sygnał stanowiska BGG, więc serwer MCP nie może pobierać stron HTML ani udawać przeglądarki.
5. **Autorytety** da się ustalić bez api.geekdo.com tylko przybliżeniem: imię i nazwisko z `user` dopasowane do
   osoby z credits, plus ręczna lista `bgg.authorities` w `wgu.yaml` (sekcja 3).

Badanie odbyło się, zanim znaleźliśmy wypowiedź admina: ok. 35 zapytań do api.geekdo.com w głównym badaniu i kilkadziesiąt
od dwóch agentów badawczych, anonimowo, co 1,5–5 s. Od chwili znalezienia wypowiedzi nie wysyłamy tam zapytań. Opis
endpointów JSON w sekcji 2.2 zostaje jako dokumentacja tego, czego **nie** używamy, i powodu, dla którego
prototyp `bgg_dump.py` nie trafi do narzędzia.

## 1. Warunki korzystania

Strony `boardgamegeek.com/terms`, `/using_the_xml_api` i wiki są za Cloudflare. Ich treść znamy z wyników
wyszukiwarek i z dwóch postów adminów przeczytanych w całości. Przed rejestracją aplikacji właściciel powinien
przeczytać je w przeglądarce. Cytaty z wyników wyszukiwarek oznaczam [wyciąg].

### 1.1. Terms of Use BGG (`boardgamegeek.com/terms`)

- Obejmują BGG, RPGGeek, VideoGameGeek i geekdo.com.
- Zakazy [wyciąg]: obciążanie serwerów robotami i pająkami („Don't slam our servers with 'robots' or 'spiders'”),
  systematyczne zbieranie danych użytkowników, trenowanie AI/LLM, użytek komercyjny, nieautoryzowane kopie
  treści serwisu.
- Posty należą do autorów. BGG dostaje licencję niewyłączną i wieczystą, a inni użytkownicy też dostają licencję
  (dokładnego zakresu nie udało się ustalić). Konsekwencja dla nas: w `kb/` trzymamy krótkie cytaty (≤ 25 słów)
  z atrybucją i linkiem, nie całe wątki.
- Brak osobnego zapisu o cache'owaniu.

### 1.2. XML API2: rejestracja i licencja

- Ogłoszenie: Scott Alden („Aldie”), 2025-07-09, <https://boardgamegeek.com/thread/3539581>. Każdy użytkownik
  XML API, komercyjny i niekomercyjny, musi się zarejestrować. Wdrożenie fazami: faza 3 to obowiązkowa
  autoryzacja (obecny stan, potwierdzony przez 401), faza 4 to limity i kwoty, faza 5 to opłaty za użycie
  komercyjne lub masowe.
- Procedura [wyciąg]: wniosek na <https://boardgamegeek.com/applications>. Odpowiedź może przyjść po tygodniu
  lub później. Po akceptacji tworzy się token w zakładce „Tokens” i wysyła go w nagłówku
  `Authorization: Bearer <token>`. Zużycie widać w zakładce „Usage”. BGG prosi o minimum zapytań i o cache'owanie
  wyników. Używaj hosta `boardgamegeek.com` bez `www`.
- XML API Terms of Use (<https://boardgamegeek.com/wiki/page/XML_API_Terms_of_Use>) [wyciąg]: licencja tylko
  na cele ściśle niekomercyjne, z obowiązkiem wymienienia BGG z nazwy. Trenowanie AI/LLM na danych z API jest
  zabronione. BGG może monitorować użycie, które nie może przeciążać serwerów. Logo „Powered by BGG” jest
  wymagane w aplikacjach publicznych.
- Daniel Karp („dakarp”), 2025-07-18: BGG nie zatwierdzi aplikacji, która udostępnia API innym aplikacjom.
  Przetwarzanie danych po stronie aplikacji jest dozwolone. Nasz serwer MCP działa lokalnie, dla jednego
  użytkownika i z jego tokenem, więc nie jest publicznym pośrednikiem.

### 1.3. api.geekdo.com

- dakarp, 2025-11-05, <https://boardgamegeek.com/thread/3539581/article/46842948> (wątek przeczytany przez
  agenta badawczego, autor potwierdzony jako admin): tych endpointów JSON nie należy używać, licencja nie
  obejmuje prywatnych endpointów, użycie poza zwykłym przeglądaniem może naruszać ToS, a aplikacje będą się psuć
  „wielokrotnie i bez ostrzeżenia”.
- Wiki `BGG_JSON_API` [wyciąg]: XML API Terms of Use nie obejmuje tego API.
- `robots.txt` api.geekdo.com (`Allow: /`, `Crawl-delay: 5`) to konwencja dla crawlerów, a nie licencja. Nie
  zmienia powyższego.

**Rekomendacja:** XML API2 z tokenem jako jedyne źródło sieciowe. api.geekdo.com nie trafia do narzędzia,
także jako fallback. Zastrzeżenie z zadania („fallback tylko do forów, jeśli XML API2 ich nie obejmuje”) nie
zachodzi, bo XML API2 fora obejmuje. Brakujące elementy (pliki gry, konta osób) uzupełnia ręczna konfiguracja
i człowiek z przeglądarką.

### 1.4. Ryzyka prawne i co napisać we wniosku o aplikację

| Ryzyko | Ocena | Środek zaradczy |
|---|---|---|
| Treść forów trafia do kontekstu modelu językowego | ToU zakazuje **trenowania**, a nie przetwarzania. BGG jest jednak wyraźnie niechętne AI (robots.txt) | Uczciwy opis we wniosku: „lokalne narzędzie wspierające nieoficjalne tłumaczenie zasad; asystent AI czyta pojedyncze wątki na żądanie użytkownika; dane nie służą do trenowania, nie są publikowane ani redystrybuowane”. Jeśli BGG odmówi, rezygnujemy z modułu sieciowego |
| Użycie komercyjne | Projekt hobbystyczny, tłumaczenia nieoficjalne i bezpłatne | Zapis w README: moduł tylko do użytku niekomercyjnego |
| Redystrybucja treści | Cache leży w `build/bgg/` poza gitem. W `kb/` są tylko krótkie cytaty z linkiem | Limit 25 słów na cytat w `evidence` (walidowany przez `wgu kb lint`), cache nigdy w repo |
| Przyszłe limity i opłaty (fazy 4–5) | Nieznane wartości | Opóźnienie ≥ 5 s, sync przyrostowy, licznik zapytań w raporcie syncu |
| Cofnięcie tokenu | Możliwe | Tryb offline na istniejącym cache |


## 2. Mapa endpointów

### 2.1. XML API2 (`boardgamegeek.com/xmlapi2/…`)

Bez tokenu każde polecenie zwraca `401 Unauthorized. See https://boardgamegeek.com/using_the_xml_api`
(sprawdzone: `thing?id=3263&versions=1`, `forumlist?id=3263&type=thing`). Zakres poleceń i warunki tokenu: sekcja 1.

Polecenia według wiki `BGG_XML_API2` (bez tokenu nie da się sprawdzić, czy fora nadal działają; to pierwszy test
po otrzymaniu tokenu):

| Cel | Polecenie | Paginacja / parametry | Dla nas |
|---|---|---|---|
| Wyszukiwanie gier | `search?query=…&type=boardgame[&exact=1]` | brak | `bgg_search_games` |
| Gra: credits, wydania | `thing?id=<thing>&versions=1` | brak; do 20 id naraz | `link type="boardgamedesigner/boardgamedeveloper/boardgamepublisher"` (id osoby/firmy + nazwa), `<versions>` (nazwa, rok, wydawca, język, kod produktu) |
| Fora gry | `forumlist?id=<thing>&type=thing` | brak | `forumid`, tytuł, `numthreads`, `numposts`, `lastpostdate` |
| Wątki forum | `forum?id=<forum>&page=N` | **50 wątków na stronę**, sortowanie wg ostatniego posta | id, temat, autor, `numarticles`, `lastpostdate` |
| Posty | `thread?id=<thread>[&minarticleid=…][&minarticledate=YYYY-MM-DD[ HH:MM:SS]][&count=N]` | `count` do 1000 | każdy `article`: `id`, **`username`**, `postdate`, `editdate`, `subject`, `body` (HTML). Sync przyrostowy: `minarticleid` = ostatni znany post + 1 |
| Użytkownik | `user?name=<login>` | brak | `firstname`, `lastname`, `yearregistered`; **brak** `designerid` |
| Osoba (projektant) | nie istnieje w XML API2 | — | powiązanie osoba ↔ konto: sekcja 3 |
| Pliki gry | nie istnieje | — | ręcznie (sekcja 2.4) |
| Geeklisty | tylko XML API v1 `/xmlapi/geeklist/<id>` | — | poza zakresem |

Format: XML (parsujemy `xml.etree.ElementTree` z biblioteki standardowej). Odpowiedź 202 oznacza „w kolejce,
ponów” (dotyczy głównie `collection`). Przy przeciążeniu serwer zwraca 429, 500 lub 503.

### 2.2. JSON API front-endu (`api.geekdo.com/api/…`): dokumentacja, nie do użycia

> [!WARNING]
> Niżej opisuję to, co zobaczyliśmy w badaniu. BGG zabrania używania tego API (sekcja 1.3), więc narzędzie
> z niego nie korzysta. Opis zostaje, bo wyjaśnia, skąd interfejs BGG bierze odznakę „Designer” (sekcja 3)
> i czego XML API2 nie daje.

Wszystkie odpowiedzi to `application/json` z nginx + Varnish (nagłówki `Etag`, `Last-Modified`, `Age`), bez
Cloudflare i bez nagłówków limitów. Czas odpowiedzi 0,2–1,3 s.

| Cel | Endpoint | Paginacja | Uwagi |
|---|---|---|---|
| Dane gry, credits, wydania (skrót) | `GET /api/geekitems?objectid=<thing>&objecttype=thing` | brak | `item.links.boardgamedesigner / boardgamedeveloper / boardgamepublisher / boardgameversion / …` (każdy: `objectid`, `name`, `href`); `primaryname`, `alternatenames`, `yearpublished`, `linkcounts` |
| Wydania (pełne) | `GET /api/geekitem/linkeditems?linkdata_index=boardgameversion&objectid=<thing>&objecttype=thing&pageid=N&showcount=25` | `pageid`, `config.numitems` | rok, nazwa, status wydania, wydawcy i artyści wydania, filtr języka |
| Osoba (projektant, developer) | `GET /api/geekitems?objectid=<person>&objecttype=person` | brak | **`item.special_user = {username, userid}`** — konto BGG powiązane z osobą (np. 140 → Simon7itch/73772, 672 → tcurtis/154656) |
| Fora gry | `GET /api/forums?objectid=<thing>&objecttype=thing` | brak | `forumid`, `title`, `numthreads`, `numposts` |
| Wątki forum | `GET /api/forums/threads?forumid=<f>&objectid=<thing>&objecttype=thing&pageid=N` | **10 wątków na stronę**, `config.endpage`, `config.numthreads`; strona za końcem zwraca `threads: []` | sortowanie domyślne: `lastpostdate` malejąco (to pozwala na sync przyrostowy: zatrzymaj się na pierwszym wątku bez zmian); `sort=recent` daje to samo |
| Wątek (meta) | `GET /api/threads/<thread>` | brak | `subject`, `numposts`, `numpages`, `pagesize` (25), `creator`, `forumid`, `source` (thing) |
| Posty | `GET /api/articles?threadid=<thread>&pageid=N` | **25 postów na stronę**, `total`, `perPage` | `id`, `author` (userid), `postdate`, `editdate` (ISO 8601), `body` (BBCode: `[q="user"]…[/q]`, `[url]`, `[img]`, `[b]`), `bodyXml`, `canonical_link`, `firstPost` |
| Użytkownik | `GET /api/users/<userid>` | brak | `username`, `firstname`, `lastname`, **`designerid`**, **`publisherid`**, **`creditBadges`** (np. `{badge: gamedesigner, href: /boardgamedesigner/140/…}`), `adminBadges` |
| Pliki gry (lista) | `GET /api/files?objectid=<thing>&objecttype=thing&pageid=N` | 10 na stronę, `config.endpage`, `config.numitems` | `filepageid`, `fileid`, `filename`, `size`, `title`, `description.rendered` (HTML), `postdate`, `language`, `user.username`, `numpositive`, `href` |
| Strona pliku | `GET /api/filepages/<filepageid>`, `GET /api/filepage/<id>/file` | brak | `downloadCount`, `approvedate`, `filestate`, opis; **brak adresu pobrania** |
| Geeklisty z grą | `GET /api/geeklists?objectid=<thing>&objecttype=thing&pageid=N` | `pageid` | listy sortowane popularnością, dla zasad mało przydatne |

Czego nie ma:

- **Wyszukiwanie gier.** `boardgamegeek.com/search/boardgame?q=…` (JSON autouzupełniania) zwraca 403 z challenge
  Cloudflare; zgadnięte `api.geekdo.com/api/search` i `/api/geeksearch` dają 404. Wyszukiwanie po nazwie wymaga
  XML API2 (`search`) albo ręcznego podania `thing_id` w `wgu.yaml`.
- **Pełnotekstowe wyszukiwanie forów.** Nie znaleziono endpointu; `robots.txt` blokuje `/forum/search`
  i `/forums/search`. Rozwiązanie: lokalny indeks FTS5 po syncu.
- **Pobieranie plików.** Pobranie idzie przez `boardgamegeek.com/file/download…` (Cloudflare, wymaga
  zalogowania, `Disallow: /file/download`). Narzędzie zwraca link do strony pliku; plik pobiera człowiek.

**Uszkodzony JSON.** W sesji Ukraine '43 (2026-10-10) odpowiedzi `/api/articles` zawierały `"collapsed":,`.
2026-10-11 nie powtórzyło się to na sprawdzonych wątkach, ale naprawa (`"klucz":,` / `"klucz":}` → `null`) zostaje,
z testem. Naprawa działa tylko poza łańcuchami znaków (treść postu może zawierać `":,`), więc parser trzeba
zrobić porządnie, a nie jednym `re.sub` po całym tekście.

### 2.3. Koszt zrzutu: Ukraine '43, fora 63–69

Liczby wątków i postów pochodzą z badania (stan 2026-10-11).

| Forum | Wątki | Posty | Strony `forum` (XML, 50/str.) | Strony wątków (JSON, 10/str.) |
|---|---|---|---|---|
| 63 Reviews | 6 | 55 | 1 | 1 |
| 64 Sessions | 5 | 35 | 1 | 1 |
| 65 General | 62 | 380 | 2 | 7 |
| 66 Rules | 118 | 467 | 3 | 12 |
| 67 Strategy | 4 | 54 | 1 | 1 |
| 68 News | 4 | 44 | 1 | 1 |
| 69 Variants | 3 | 13 | 1 | 1 |
| **razem** | **202** | **1048** | **10** | **24** |

| | XML API2 (rekomendowane) | api.geekdo.com (dla porównania) |
|---|---|---|
| Lista forów + gra | 2 | 2 + osoby z credits |
| Listy wątków | 10 | 24 |
| Posty | 202 (jeden `thread` na wątek, do 1000 postów) | ≈ 210 (25 postów na stronę) |
| Autorzy | 0 (login jest w poście); `user` tylko dla kandydatów na autorytet | ≈ 200–300 |
| **Pierwszy sync** | **≈ 215 zapytań, ≈ 18 min przy 5 s** | ≈ 450–550 zapytań, ≈ 40 min |
| Sync przyrostowy | 1 `forumlist` + 1 strona `forum` na zmienione forum + 1 `thread` (z `minarticleid`) na zmieniony wątek | podobnie |

### 2.4. Pliki gry bez API

XML API2 nie ma listy plików. Plan zastępczy: `bgg_files` zwraca link do strony plików gry
(`https://boardgamegeek.com/boardgame/<thing>/x/files`), a człowiek w przeglądarce wskazuje istotne pliki
(errata, FAQ, living rules) i dopisuje je do `wgu.yaml` → `sources.errata` (z `url`, wersją i datą). Tak działa
już dziś skill `/wgu:errata`: pobiera materiały z sieci tylko za zgodą użytkownika.

## 3. Autorytety: projektant, developer, wydawca

**Skąd BGG to wie (ustalone w badaniu api.geekdo.com).** Odznaka „Designer” przy poście nie jest polem posta.
Wynika z powiązania osoby z kontem: rekord osoby ma `special_user = {username, userid}` (np. osoba 140
Mark Simonitch → konto Simon7itch/73772, osoba 672 Tony Curtis → tcurtis/154656). Rekord użytkownika ma
`designerid`, `publisherid` i `creditBadges`. **XML API2 tego powiązania nie udostępnia**: `thing` podaje osobę
(id + nazwisko), `thread` podaje login autora posta, a `user` imię i nazwisko konta.

**Co robimy zamiast tego.** Trzy źródła, w kolejności ważności:

1. **Ręczna lista w `wgu.yaml`** (decyzja właściciela, wpisywana raz na grę i weryfikowana w przeglądarce na
   profilu osoby):
   ```yaml
   bgg:
     thing_id: 3263
     authorities:
       - {user: Simon7itch, role: designer, person: 140}
       - {user: tcurtis, role: designer, person: 672}
       - {user: <login>, role: developer, note: "potwierdzone przez GMT w wątku …"}
   ```
2. **Dopasowanie nazwiska (propozycja, nie pewnik):** jeśli login autora posta w wątku gry ma w `user`
   imię i nazwisko równe osobie z `boardgamedesigner`/`boardgamedeveloper` gry, oznaczamy go jako
   `designer?`/`developer?`. Polecenie `wgu bgg authorities --suggest` wypisuje takich kandydatów do
   zatwierdzenia w `wgu.yaml`. Koszt: jedno zapytanie `user` na kandydata, ale tylko dla autorów z co najmniej
   N postami w forum Rules (np. N=3). Pozostałe zapytania nie są potrzebne.
3. **Wszyscy pozostali:** `player`.

Reguła rozpoznania autorytetu dla posta w wątku gry (po ustaleniu listy):

| Rola | Warunek | Waga dowodu |
|---|---|---|
| `designer` | login w `bgg.authorities` z rolą `designer` | najwyższa |
| `developer` | rola `developer` | wysoka |
| `publisher` | rola `publisher` (np. konto wydawcy) | wysoka (oficjalne stanowisko wydawcy) |
| `designer?` / `developer?` | dopasowanie nazwiska, niezatwierdzone | jak wyżej, ale z flagą „do potwierdzenia” |
| `player` | pozostali | niska, chyba że cytuje erratę lub regułę (wtedy waga zależy od cytowanego źródła) |

Ograniczenia: osoba może nie mieć konta lub nie powiązać go z profilem; credits developera bywają puste (Ukraine '43: `boardgamedeveloper: []`, a na forum Rules często i stanowczo
odpowiada użytkownik Hugewally, którego roli nie da się ustalić z API). Dlatego `wgu.yaml` gry dostaje ręczne
uzupełnienie, ustalane przez właściciela: `bgg.authorities: [{user: <login>, role: developer, note: …}]`.

Przykład (test akceptacyjny): wątek 1679334 „Priorities in the Retreat”, post Simon7itch z 2016-12-17 →
Simon7itch jest w `bgg.authorities` jako `designer` (osoba 140 w credits gry 3263) → rola `designer`. Bez wpisu
w `wgu.yaml` dopasowanie nazwiska („Mark Simonitch” = osoba 140) da `designer?`.

## 4. Rate limiting i uprzejmość

- `robots.txt` api.geekdo.com: `User-Agent: * / Crawl-delay: 5 / Allow: /`. To samo `Crawl-delay: 5` ma
  boardgamegeek.com.
- `robots.txt` boardgamegeek.com (pobrany curlem 2026-10-11, HTTP 200) **całkowicie blokuje agenty AI**, m.in. `anthropic-ai`, `ClaudeBot`,
  `Claude-Web`, `GPTBot`, `PerplexityBot` i `Perplexity-User` (ten ostatni to agent działający na polecenie
  użytkownika). Blokuje też `/xmlapi` (dla crawlerów; XML API ma własne zasady), `/forum/search`, `/file/download`,
  `/thread/*/article/*`, `/user`, `/profile`. robots.txt api.geekdo.com takiej listy nie ma.
- W odpowiedziach nie ma nagłówków limitów (`X-RateLimit-*`, `Retry-After`) przy ok. 30 zapytaniach co 1,5–2 s.

- Stanowisko BGG: oficjalnych limitów jeszcze nie opublikowano („faza 4”). Admini piszą, że kwoty mogą zależeć
  od sposobu logowania (dakarp, 2025-10-29). Stara wiki XML API: zbyt wiele zapytań kończy się 500/503, a odstęp
  5 s między zapytaniami „wydaje się wystarczać”. BGG prosi o minimum zapytań i cache'owanie.

Rekomendacja dla klienta:

- opóźnienie między zapytaniami: **5 s domyślnie** (zgodnie z Crawl-delay), konfigurowalne, z dolną granicą 2 s;
- jedno połączenie naraz, bez równoległości;
- backoff przy 429, 5xx i błędach sieci: 10 s, 30 s, 90 s, potem przerwanie syncu z zachowaniem postępu
  (sync jest wznawialny, bo zapisuje wątki pojedynczo); respektowanie `Retry-After`, jeśli się pojawi;
- przy 401/403 lub stronie challenge (HTML zamiast JSON): natychmiastowe przerwanie, bez ponowień i bez prób
  obejścia;
- tożsamość niesie token (`Authorization: Bearer`). User-Agent ma być uczciwy, z nazwą narzędzia i adresem
  repozytorium, np. `wgu-bgg/0.1 (+https://github.com/yautay/wargame-utils)`, nigdy udający przeglądarkę;
- host `boardgamegeek.com` bez `www`;
- cache: posty praktycznie się nie zmieniają (edycje widać po `editdate`); listy wątków odświeżane wg
  `lastpostdate`; dane gry z TTL 7 dni; dane użytkowników bezterminowo;
- `202` (kolejka): ponowienie po 2, 5, 10, 30 s;
- licznik zapytań i czas w raporcie każdego syncu (też jako dane do ewentualnego wniosku o wyższe limity).

## 5. Istniejące projekty open source

### 5.1. Klienci Pythona

| Pakiet | Repo | Stan | Licencja | Token Bearer | Fora | Ocena |
|---|---|---|---|---|---|---|
| `bgg-api` (następca boardgamegeek2) | <https://github.com/SukiCZ/boardgamegeek> | 1.1.19, 2026-07-28; aktywny | BSD-3 | tak | **nie** | parsuje tylko część credits (bez `boardgamedeveloper`); zależność od `requests` + `requests-cache` |
| `boardgamegeek2` | <https://github.com/lcosmin/boardgamegeek> | 2019 | BSD-3 | nie | nie | martwy |
| `bgg-pi` | <https://github.com/seanmccabe/bgg-pi> | 0.1.1, 2026-01 | MIT | opcjonalnie | nie | niszowy |

**Wniosek:** nie zależymy od żadnego. Potrzebujemy sześciu poleceń XML API2 (`search`, `thing`, `forumlist`,
`forum`, `thread`, `user`), a parser `ElementTree` z biblioteki standardowej i `urllib` to ok. 300 linii bez
nowych zależności dla CLI. Z `bgg-api` warto przejąć logikę ponowień 202/503.

### 5.2. Serwery MCP dla BGG

| Projekt | Język, licencja | Źródło danych | Co warto wziąć |
|---|---|---|---|
| **kkjdaniel/bgg-mcp** <https://github.com/kkjdaniel/bgg-mcp> (w oficjalnym rejestrze MCP jako `io.github.kkjdaniel/bgg-mcp`, v1.6.1, aktywny) | Go, MIT | XML API2 przez własną bibliotekę `gogeek` (thing, forumlist, forum, thread, search); token `BGG_API_KEY` | narzędzie `bgg-rules` (wątki forum Rules dla pytania), wątek jako zasób MCP `bgg://thread/{id}`, backoff 202/429/503; brak cache |
| faegents/bgg-mcp | Go, MIT | fork powyższego | — |
| fzerorubigd/bggo | Go, MIT | XML API2 z tokenem, bez forów | — |
| kilka mniejszych (Java, C#, Ruby, TS, Python/Gradio) | różne | XML API2 | — |

Żaden znaleziony serwer nie ma lokalnego indeksu postów, rozpoznawania autorytetów ani powiązania z bazą
niejasności. Własny serwer w Pythonie jest uzasadniony. Wzorujemy się na kkjdaniel/bgg-mcp (nazwy narzędzi,
wątek jako zasób), ale nie kopiujemy kodu (inny język).

### 5.3. ConsimWorld (moduł 2): niewykonalny

- Forum `talk.consimworld.com` **nie zostało przeniesione**: nadal działa na WebCrossing 6.4 (build z czerwca
  2026). Stare linki WebX nie działają, bo zmieniły się identyfikatory folderów, a nie platforma.
- Forum wymaga logowania (są też płatne subskrypcje). Kanały RSS folderów przekierowują na stronę logowania.
- `robots.txt` forum: `Disallow: /`. Regulamin jest dostępny dopiero po zalogowaniu.
- Serwis informacyjny `consimworld.com` (WordPress) ma RSS `/feed/` i `Crawl-delay: 10`, ale nie ma tam
  odpowiedzi autorów na pytania o zasady.

**Wniosek:** automatyczny dostęp do forum CSW wymagałby logowania danymi użytkownika i zgody CSW. Nie robimy
tego. Zamiast tego proponuję **ręczny import**: człowiek kopiuje z przeglądarki wątek lub post (albo zapisuje
stronę), a `wgu evidence add --source csw --url … --author … --date … --quote "…"` dopisuje dowód do
`kb/ambiguities.yaml` z tą samą walidacją co BGG. To samo polecenie obsłuży e-mail od autora, wpis z Discorda
czy PDF z FAQ.

## 6. Skutki dla projektu (zmiany względem zadania)

| Zadanie zakładało | Po badaniu |
|---|---|
| api.geekdo.com jako fallback do forów | **odpada**: zakaz admina, a XML API2 obejmuje fora |
| `bgg_files(thing_id)` z listą plików | XML API2 nie ma plików → narzędzie zwraca link do strony plików i listę plików już wpisanych do `wgu.yaml` (`sources.errata`) |
| Autorytety z credits | XML API2 nie łączy osób z kontami → `bgg.authorities` w `wgu.yaml` + polecenie `--suggest` (dopasowanie nazwisk) |
| `bgg_sync` wg `lastpostdate` | tak, a do tego `thread&minarticleid` pobiera tylko nowe posty |
| Test akceptacyjny: sync 63–69, czas i liczba zapytań | ≈ 215 zapytań, ≈ 18 min przy 5 s; **wymaga tokenu** |
| Moduł ConsimWorld | automatyczny dostęp niewykonalny → ręczny `wgu evidence add` (wspólny dla wszystkich źródeł) |
| Nagrane fixtures do testów | XML z odpowiedzi XML API2 po otrzymaniu tokenu; do tego czasu ręcznie przygotowane próbki według schematu z wiki (oznaczone jako syntetyczne) |

Zależności: rdzeń (klient, cache, FTS5, CLI) używa tylko biblioteki standardowej (`urllib`, `xml.etree`,
`sqlite3`). SDK `mcp` (ciągnie `pydantic`, `httpx`, `starlette`, `anyio`…) jest potrzebne tylko serwerowi MCP,
więc proponuję dodatek `pyproject` `[project.optional-dependencies] mcp = ["mcp>=1.x"]` i osobny
`requirements-mcp.txt`. Serwer uruchamiany przez `uv run --with mcp` albo z venv narzędzia. Dzięki temu `wgu`
działa bez SDK, a CLAUDE.md („zależności tylko z requirements.txt”) dostaje jedno zdanie o wyjątku.

## 7. Decyzje właściciela (przed etapem 2)

1. **Token XML API2.** Czy rejestrujesz aplikację na <https://boardgamegeek.com/applications> (niekomercyjna,
   opis zgodny z sekcją 1.4)? Bez tokenu nie ma modułu sieciowego. Akceptacja trwa zwykle co najmniej tydzień.
2. **api.geekdo.com.** Rekomenduję całkowitą rezygnację (zakaz admina BGG). Alternatywa: tylko jednorazowe,
   ręczne użycie przez właściciela w przeglądarce.
3. **Zakres przed tokenem.** Czy w czasie oczekiwania na token budować etapy 2–3 na próbkach syntetycznych
   (klient, cache, FTS5, `evidence` w schemacie, `wgu evidence add`, skill `/wgu:dowody`), a test akceptacyjny
   na Ukraine '43 zrobić po otrzymaniu tokenu?
4. **ConsimWorld.** Zgoda na „tylko ręczny import” (`wgu evidence add`) zamiast modułu sieciowego?
5. **Opóźnienie.** 5 s domyślnie (pierwszy sync Ukraine '43 ≈ 18 min), czy dopuszczasz 2 s?
6. **Cache z badania.** Surowe odpowiedzi api.geekdo.com z badania leżą tylko w scratchpadzie sesji. Proponuję
   ich nie używać (ani jako fixtures, ani jako danych) i pozwolić im zniknąć razem z sesją. Dotyczy to też
   zrzutu `bgg-3263.md` z sesji Ukraine '43.

## 8. Prototyp i test akceptacyjny

Stan 2026-10-11: moduł zbudowany według [projektu](../design/bgg-mcp.md) (`wgu/bgg/`, `wgu bgg …`, serwer MCP
`bgg` rejestrowany w `.mcp.json`, pole `evidence`, skill `/wgu:dowody`).

- Testy bez sieci (`tests/test_bgg.py`, 22 testy na syntetycznych próbkach XML i symulatorze XML API2): naprawa
  XML, parsowanie sześciu poleceń, odstępy i ponowienia klienta, przerwanie przy 401/403/HTML, sync przyrostowy
  z `minarticleid`, paginacja i wznowienie po limicie zapytań, FTS5 ze stemmingiem, role i podpowiedzi
  autorytetów, ramka danych niezaufanych, limity rozmiaru, walidacja `evidence`, serwer MCP.
- Serwer uruchamia się poleceniem z `.mcp.json` (`uv run --with-requirements requirements-mcp.txt …`) i odpowiada
  na `initialize` i `tools/list`. Pierwsze uruchomienie trwa ok. 11 s (uv instaluje SDK do swojego cache).
- **Test akceptacyjny na Ukraine '43 czeka na token XML API2** (D-14): `tests/test_bgg_acceptance.py`, uruchomienie
  `WGU_BGG_ACCEPTANCE=1 python -m pytest tests/test_bgg_acceptance.py -s`. Oczekiwane: sync forów 63–69
  ≈ 215 zapytań i ≈ 18 min; `search "retreat priority"` zwraca post Simon7itch z 2016-12-17 w wątku 1679334
  z rolą `designer`. Faktyczny czas i liczbę zapytań wpisać tutaj po pierwszym przebiegu.
- Pierwszy krok po otrzymaniu tokenu: sprawdzić, czy `forumlist`/`forum`/`thread` nadal działają w XML API2
  (wiki opisuje je, ale bez tokenu nie dało się tego potwierdzić).

