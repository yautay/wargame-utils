# Weryfikacja autorstwa i oficjalnych klaryfikacji

XML API zwraca konto autora wpisu, ale nie dokumentuje powiązania konta z osobą projektanta
lub przedstawicielem wydawcy. Sam nick, nazwisko w profilu, treść wpisu czy ogólna odznaka
Designer nie stanowią dowodu roli dla konkretnej gry. Odznaki mogą dotyczyć różnych ról:
[BGG People and Company Guide](https://boardgamegeek.com/wiki/page/BGG_People_and_Company_Guide).
Nie korzystamy w tym celu z prywatnego JSON API ani scrapingu.

WGU sprawdza **lokalny rejestr dowodów zatwierdzonych przez operatora**. Nie wyszukuje samodzielnie
ani nie potwierdza prawdziwości wskazanych stron. Weryfikacja automatycznie dopasowuje dokładny nick,
identyfikator gry, datę wpisu i — dla oficjalnego rozstrzygnięcia — identyfikator konkretnego wpisu.
Rejestru nie wolno budować na samych deklaracjach zawartych w analizowanym wpisie.

Skopiuj [pusty wzór](../templates/bgg-authority.example.json) do zaufanej lokalizacji i ustaw
`BGG_AUTHORITY_FILE` na jego bezwzględną ścieżkę. Serwer odczytuje plik na każde wywołanie; nie ma
narzędzia MCP do zapisywania lub zatwierdzania dowodów. Plik jest konfiguracją zaufanego operatora,
nie danymi przyjmowanymi z forum lub od modelu. Dowody i oceny są dodatkowymi adnotacjami WGU;
oryginalna treść wpisów pozostaje bez zmian. Weryfikacja nie wykonuje dodatkowych żądań API.

Przykład struktury rekordu (fikcyjne dane, zastąp je rzeczywiście sprawdzonymi dowodami):

```json
{
  "game_id": 12345,
  "username": "exact-bgg-account",
  "role": "designer",
  "valid_from": "2020-01-01",
  "valid_until": "2026-10-17",
  "reviewed_by": "Imię osoby weryfikującej",
  "reviewed_on": "2026-10-17",
  "expires_on": "2027-01-17",
  "evidence": [
    {
      "url": "https://publisher.example/game-and-account-confirmation",
      "description": "Potwierdzenie, że to konto należy do autora tej konkretnej gry."
    }
  ],
  "official_posts": [
    {
      "article_id": 98765,
      "evidence": [
        {
          "url": "https://publisher.example/official-rulings",
          "description": "Potwierdzenie przyjęcia tego konkretnego wpisu jako oficjalnego rozstrzygnięcia."
        }
      ]
    }
  ]
}
```

Dodaj taki rekord do tablicy `entries`. Pole `official_posts` jest opcjonalne. Dla przedstawiciela
wydawcy użyj `publisher_representative` i dowodu umocowania w zakresie tej gry. Potwierdzony
uczestnik społeczności może otrzymać `community_member`; brak dowodu roli nie oznacza automatycznie,
że dana osoba jest graczem. `valid_from` / `valid_until` określają okres potwierdzonej roli,
a `expires_on` termin ponownego przeglądu dowodów. Nie rozszerzaj zakresu na inne wydania bez dowodu;
jeśli BGG łączy wydania pod jednym ID, zgodność z wydaniem instrukcji wymaga osobnej oceny.

Wynik `authority_verification` zawiera:

- `status`: `verified` lub `unverified` oraz powód;
- `role`, źródła `evidence`, osobę i daty przeglądu;
- `clarification_status`: `verified_role_statement` (potwierdzona rola, bez potwierdzenia oficjalności
  wpisu), `community_interpretation`, `official_clarification` albo `unverified`.

`official_clarification` wymaga osobnego dowodu dla ID wpisu i potwierdzonej roli autora/wydawcy.
Nieaktualny, uszkodzony, niejednoznaczny rejestr, brak daty wpisu lub brak dowodów pozostawiają
status niepotwierdzony. Pusty wzór nie potwierdza żadnego konta.

`bgg_search_posts` dodaje ocenę automatycznie w kontekście sprawdzanego forum gry.
`bgg_thread(..., game_id=...)` także dodaje ocenę; podane ID gry jest kontekstem zadeklarowanym
przez wywołującego — najpierw sprawdź przynależność wątku przez forum gry.
`bgg_verify_authority(game_id, username, postdate, article_id)` sprawdza sam rejestr;
parametry nicku, daty i ID muszą pochodzić z oryginalnych metadanych wpisu.
