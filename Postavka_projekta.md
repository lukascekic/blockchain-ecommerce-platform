# Sistem za upravljanje rada prodavnicom

## Uvod

Osnovni ciljevi projekta su:
- implementacija veb servisa koji čine dati sistem;
- pokretanje sistema pomoću alata za orkestiranje kontejnera;

Sistem je namenjen za višekorisnički rad i stoga treba pažljivo da bude dizajniran za potrebe ispravnog i efikasnog rada. Deo funkcionalnosti sistema je javno dostupan, dok je deo funkcionalnosti obezbeđen samo za korisnike koji mogu da se prijave na sistem.

Sistem je potrebno implementirati korišćenjem Python programskog jezika, Flask radnog okvira i SQLAlchemy biblioteka. Prilikom obrade zahteva korisnika neophodno je koristiti SQLAlchemy u što većoj meri, odnosno realizovati obradu pomoću upita svugde gde je to moguće. Pored koda, potrebno je priložiti datoteke na osnovu kojih se kreiraju Docker Image artefakti koji predstavljaju delove sistema i koji se mogu iskoristiti za pokretanje odgovarajućih kontejnera. Pored implementacije, potrebno je napisati konfiguracioni fajl pomoću kojeg se ceo sistem može pokrenuti korišćenjem Docker alata.

## Konceptualni opis sistema

Sistem treba da obezbedi registraciju korisnika (kupac ili kurir). Kupci mogu da vrše pretragu i da prave narudžbine. Kuriri mogu da vrše dostavljanje narudžbina.

Prilikom pokretanja sistema potrebno je unapred obezbediti naloge svim vlasnicima prodavnice. Vlasnici prodavnice mogu da dodaju proizvode i da vrše pregled statistike prodaja.

Svaki korisnik treba da bude registrovan pre korišćenja sistema. Za svakog korisnika se u okviru njegovog korisničkog naloga čuvaju sledeće informacije: imejl adresa i lozinka koje se koriste prilikom prijave, ime, prezime i uloga korisnika. Korisnik može imati ulogu kupca, vlasnika prodavnice ili kurira.

Za proizvode se pamte sledeće informacije: kategorija kojoj proizvod pripada (može ih biti više), ime proizvoda i njegova cena. Ime proizvoda je jedinstveno. Za svaku kategoriju se pamti njeno ime.

Kupci mogu da vrše pretragu proizvoda, da prave narudžbine i da vrše pregled napravljenih narudžbina.

Prilikom svake kupovine proizvoda u sistemu se pravi narudžbina. Za svaku narudžbinu se čuva spisak proizvoda, ukupna cena narudžbine, njen status i trenutak njenog kreiranja. Prilikom kreiranja, narudžbina je u stanju "čekanja" sve dok je neki od kurira ne pokupi kada prelazi u stanje "na putu". Kada kurir dostavi narudžbinu kupcu ona prelazi u stanje "izvršena".

## Funkcionalni opis sistema

Sistem se sastoji iz dva dela: jedan namenjen za upravljanje korisničkim nalozima i jedan namenjen za upravljanje prodavnicom. I jedan i drugi deo sistema se sastoje iz nekoliko komponenti koje su relizovane pomoću kontejnera kreiranih na osnovu Docker Image šablona. Deo ovih Docker Image šablona već postoji i nalazi se u okviru javnog repozitorijuma na adresi https://hub.docker.com/. Ostatak je neophodno implementirati. U nastavku je dat funkcionalni opis sistema.

## Upravljanje korisničkim nalozima

Izgled dela sistema koji je zadužen za upravljanje korisničkim nalozima dat je na slici 1.

**Slika 1. Izgled dela sistema za upravljanje korisničkim nalozima**

Ovaj deo sistema se sastoji iz jednog kontejnera i baze podataka u kojoj se nalaze samo podaci o korisnicima. Kontejner predstavlja veb servis pomoću kojeg korisnik može da se registruje i dobije JSON veb token sa kojim će moći da pristupi ostatku sistema.

Opis funkcionalnosti koje pruža ovaj veb servis dat je u nastavku. Svaka adresa je relativna u odnosu na IP adresu kontejnera i broj porta na kojem kontejner sluša.

### Registracija korisnika

**Adrese:** `/register_customer`, `/register_courier`

**Tip:** POST

**Zaglavlje:** -

**Telo:** Telo zahteva je JSON objekat sledećeg formata:
```json
{
  "forename": ".....",
  "surname": ".....",
  "email": ".....",
  "password": "....."
}
```

Sva polja su obavezna i njihov sadržaj je sledeći:
- **forename:** string od najviše 256 karaktera koji predstavlja ime korisnika;
- **surname:** string od najviše 256 karaktera koji predstavlja prezime korisnika;
- **email:** string od najviše 256 karaktera koji predstavlja imejl adresu korisnika;
- **password:** string od najviše 256 karaktera koji predstavlja lozinku korisnika, dužina lozinke mora biti 8 ili više znakova;

**Odgovor:** Ukoliko su svi traženi podaci prisutni u telu zahteva i ispunjavaju navedena ograničenja, rezultat zahteva je kreiranje novog korisnika sa ulogom kupca ili kurira (u zavisnosti od adrese na koju je poslat zahtev) i odgovor sa statusnim kodom 200 bez dodatno sadržaja.

U slučaju greške, rezultat zahteva je odgovor sa statusnim kodom 400 čiji je sadržaj JSON objekat sledećeg formata:
```json
{
  "message": "....."
}
```

Sadržaj polja message je:
- `"Field <fieldname> is missing."` ukoliko neko od polja nije prisutno ili je vrednost polja string dužine 0, `<fieldname>` je ime polja koje je očekivano u telo zahteva;
- `"Invalid email."` ukoliko polje email nije odgovarajuće formata;
- `"Invalid password."` ukoliko polje password nije odgovarajuće dužine;
- `"Email already exists."` ukoliko u bazi postoji korisnik sa istom imejl adresom;

Odgovarajuće provere se vrše u navedenom redosledu.

### Prijava korisnika

**Adresa:** `/login`

**Tip:** POST

**Zaglavlje:** -

**Telo:** Telo zahteva je JSON objekat sledećeg formata:
```json
{
  "email": ".....",
  "password": "....."
}
```

Sva polja su obavezna i njihov sadržaj je sledeći:
- **email:** string od najviše 256 karaktera koji predstavlja imejl adresu korisnika;
- **password:** string od najviše 256 karaktera koji predstavlja lozinku korisnika;

**Odgovor:** Ukoliko su svi traženi podaci prisutni u telu zahteva i ispunjavaju navedena ograničenja i u bazi podatak postoji korisnik sa navedenim kredencijalima, rezultat zahteva je odgovor sa statusnim kodom 200 čiji je sadržaj JSON objekat sledećeg formata:
```json
{
  "accessToken": "....."
}
```

Polje accessToken je string koji predstavlja JSON veb token koji se koristi za pristup ostalim funkcionalnostima sistema. Token je validan narednih sat vremena. Lice za koje se token izdaje se identifikuje na osnovu imejl adrese. Token sadrži dodatna polja čiji sadržaj predstavlja informacije koje je korisnik zadao prilikom registracije. Imena polja su ista kao ona navedena u opisu registracije.

U slučaju greške, rezultat zahteva je odgovor sa statusnim kodom 400 i JSON objektom sledećeg formata:
```json
{
  "message": "....."
}
```

Sadržaj polja message je:
- `"Field <fieldname> is missing."` ukoliko neko od polja nije prisutno ili je vrednost polja string dužine 0, `<fieldname>` je ime polja koje je očekivano u telo zahteva;
- `"Invalid email."` ukoliko polje imejl nije odgovarajućeg formata;
- `"Invalid credentials."` ukoliko korisnik ne postoji;

Odgovarajuće provere se vrše u navedenom redosledu.

### Brisanje korisnika

**Adresa:** `/delete`

**Tip:** POST

**Zaglavlje:** Zaglavlje i njihov sadržaj su:
```json
{
  "Authorization": "Bearer <ACCESS_TOKEN>"
}
```

Vrednost `<ACCESS_TOKEN>` je string koji predstavlja JSON veb token za pristup koji je izdat korisniku koji želi da obriše svoj nalog.

**Telo:** -

**Odgovor:** Ukoliko su sva tražena zaglavlja prisutna, rezultat zahteva je brisanje korisnika iz baze podataka i odgovor sa statusnim kodom 200 bez dodatnog sadržaj.

U slučaju da zaglavlje nedostaje, rezultat je odgovor sa statusnim kodom 401 i JSON objektom sledećeg formata i sadržaja:
```json
{
  "msg": "Missing Authorization Header"
}
```

U slučaju greške, rezultat zahteva je odgovor sa statusnim kodom 400 i JSON objektom sledećeg formata:
```json
{
  "message": "....."
}
```

Sadržaj polja message je:
- `"Unknown user."` ukoliko korisnik sa datom imejl adresom ne postoji;

Odgovarajuće provere se vrše u navedenom redosledu.

## Upravljanje prodavnicom

Izgled dela sistema koji je zadužen za upravljanje prodavnicom dat je slici 2.

**Slika 2. Izgled dela sistema za upravljanje prodavnicom**

Ovaj deo sistema se sastoji iz baze podatak u kojoj se čuvaju sve informacije neophodne za rad prodavnice, kontejnera koji predstavlja veb servis sa funkcionalnostima dostupni vlasnicima, kontejnera koji predstavlja veb servis sa funkcionalnostima dostupnim kupcima i kontejnera koji predstavlja veb servis sa funkcionalnostima dostupnim kuririma. U nastavku su dati opisi funkcionalnosti svakog kontejnera. Svaka adresa je relativna u odnosu na IP adresu kontejnera i broj porta na kojem kontejner sluša. Svaka od funkcionalnosti zahteva odgovarajući token za pristup.

Funkcionalnosti kontejnera koji namenjen za rad sa vlasnikom su date u nastavku.

### Dodavanje proizvoda

**Adresa:** `/update`

**Tip:** POST

**Zaglavlje:** Zaglavlje i njihov sadržaj su:
```json
{
  "Authorization": "Bearer <ACCESS_TOKEN>"
}
```

Vrednost `<ACCESS_TOKEN>` je string koji predstavlja JSON veb token za pristup koji je izdat vlasniku prilikom prijave.

**Telo:** U telu zahteva se nalazi polje sa nazivom file čija vrednost predstavlja CSV datoteku sa informacijama o proizvodima koje je potrebno dodati. Svaki red datoteke odgovara jednom proizvodu i sadrži sledeće vrednosti:
- Imena kategorija kojima ovaj proizvod pripada, imena su razdvojena znakom "|";
- Ime proizvoda;
- Njegova cena (ceo broj);

**Odgovor:** Ukoliko su svi podaci prisutni i ispunjavaju sva navedena ograničenja, informacije o proizvodima se smeštaju u bazu podataka i rezultat zahteva je odgovor sa statusnim kodom 200 bez dodatnog sadržaja.

U slučaju da je zaglavlje izostavljeno, rezultat je odgovor sa statusnim kodom 401 i JSON objektom sledećeg formata i sadržaja:
```json
{
  "msg": "Missing Authorization Header"
}
```

U slučaju da neko polje tela nedostaje ili je nekorektnog formata, rezultat zahteva je odgovor sa statusnim kodom 400 i JSON objektom sledećeg formata:
```json
{
  "message": "....."
}
```

Sadržaj polja message je:
- `"Field file missing."` ukoliko polje file nije prisutno u telu zahteva;
- `"Incorrect number of values on line 2."` ukoliko neka od linija u datoteci ne sadrži tačno tri vrednost, poruka treba da sadrži i broj linije koja ne zadovoljava uslov, numeracija linija kreće od 0;
- `"Incorrect price on line 2."` ukoliko neka od linija u datoteci ne sadrži odgovarajući cenu, cena je realan broj veći od 0, poruka treba da sadrži i broj linije koja ne zadovoljava uslov, numeracija linija kreće od 0;
- `"Product <NAME> already exists."` ukoliko proizvod sa nazivom `<NAME>` već postoji, ukoliko makar jedan od proizvoda u prosleđenoj datoteci već postoji ne treba dodati nijedan proizvod iz prosleđene datoteke;

Odgovarajuće provere se vrše u navedenom redosledu.

### Dohvatanje statistike o proizvodima

**Adresa:** `/product_statistics`

**Tip:** GET

**Zaglavlje:** Zaglavlje i njihov sadržaj su:
```json
{
  "Authorization": "Bearer <ACCESS_TOKEN>"
}
```

Vrednost `<ACCESS_TOKEN>` je string koji predstavlja JSON veb token za pristup koji je izdat vlasniku prilikom prijave.

**Telo:** -

**Odgovor:** Ukoliko su sva tražena zaglavlja prisutna i ispunjavaju navedena ograničenja, rezultat zahteva je odgovor sa statusnim kodom 200 čiji je sadržaj JSON objekat sledećeg formata:
```json
{
  "statistics": [
    {
      "name": "Product0",
      "sold": 4,
      "waiting": 1
    },
    {
      "name": "Product1",
      "sold": 12,
      "waiting": 2
    },
    {
      "name": "Product9",
      "sold": 4,
      "waiting": 0
    }
  ]
}
```

Polje statistics predstavlja niz JSON objekata. Svaki objekat predstavlja proizvod koji ima makar jednu prodaju i sadrži sledeća polja:
- **name** – ime proizvoda;
- **sold** – ukupno količina prodatih primeraka datog proizvoda, uzeti u obzir samo one proizvode koji pripadaju narudžbinama koje su dostavljene kupcima;
- **waiting** – broj primeraka proizvoda koji pripadaju narudžbinama koje tek treba dostaviti kupcima;

U slučaju da zaglavlje nedostaje, rezultat je odgovor sa statusnim kodom 401 i JSON objektom sledećeg formata i sadržaja:
```json
{
  "msg": "Missing Authorization Header"
}
```

### Dohvatanje statistike o kategorijama

**Adresa:** `/category_statistics`

**Tip:** GET

**Zaglavlje:** Zaglavlje i njihov sadržaj su:
```json
{
  "Authorization": "Bearer <ACCESS_TOKEN>"
}
```

Vrednost `<ACCESS_TOKEN>` je string koji predstavlja JSON veb token za pristup koji je izdat vlasniku prilikom prijave.

**Telo:** -

**Odgovor:** Ukoliko su sva tražena zaglavlja prisutna i ispunjavaju navedena ograničenja, rezultat zahteva je odgovor sa statusnim kodom 200 čiji je sadržaj JSON objekat sledećeg formata:
```json
{
  "statistics": [
    "Category1",
    "Category0",
    "Category2",
    "Category3",
    "Category4",
    "Category5",
    "Category6"
  ]
}
```

Polje statistics predstavlja niz imena svih kategorija koje se trenutno nalaze u bazi. Niz je sortiran opadajuće po broju dostavljenih primeraka proizvoda koji pripadaju toj kategoriji. Ukoliko se proizvod pripada više od jednoj kategoriji, računati ga kao dostavljenog u svim njegovim kategorijama. Ukoliko dve kategorije imaju isti broj dostavljenih proizvoda, sortirati ih rastuće po imenu.

U slučaju da zaglavlje nedostaje, rezultat je odgovor sa statusnim kodom 401 i JSON objektom sledećeg formata i sadržaja:
```json
{
  "msg": "Missing Authorization Header"
}
```

Funkcionalnosti kontejnera koji namenjen za rad sa kupcima su date u nastavku.

### Pretraga proizvoda

**Adresa:** `/search?name=<PRODUCT_NAME>&category=<CATEGORY_NAME>`

Parametri `<PRODUCT_NAME>` i `<CATEGORY_NAME>` su stringovi koji predstavljaju parametre za pretragu proizvoda. Oba parametra su opciona.

**Tip:** GET

**Zaglavlje:** Zaglavlje i njihov sadržaj su:
```json
{
  "Authorization": "Bearer <ACCESS_TOKEN>"
}
```

Vrednost `<ACCESS_TOKEN>` je string koji predstavlja JSON veb token za pristup koji je izdat kupcu prilikom prijave.

**Telo:** -

**Odgovor:** Ukoliko su sva tražena zaglavlja prisutna, rezultat zahteva je odgovor sa statusnim kodom 200 čiji je sadržaj JSON objekat sledećeg formata:
```json
{
  "categories": [
    "Category2",
    "Category1"
  ],
  "products": [
    {
      "categories": [
        "Category1",
        "Category2"
      ],
      "id": 3,
      "name": "Product2",
      "price": 29.89
    }
  ]
}
```

Sadržaj polja categories je lista stringova. Svaki string predstavlja kategoriju u čijem se imenu nalazi string koji je prosleđen kao parametar category i kojoj pripada makar jedan proizvod u čijem se imenu nalazi parametar name.

Sadržaj polja products je lista JSON objekata. Svaki objekat prestavlja ime proizvoda u čijem se imenu nalazi string koji je prosleđen kao parametar name i koji pripada makar jednoj kategoriji u čijem se imenu nalazi parametar category.

Svaki od JSON objekata u listi products sadrži sledeća polja:
- **categories** – niz stringova koji predstavljaju imena kategorija kojima ovaj proizvod pripada;
- **id** – celобројni identifikator proizvoda;
- **name** – string koji predstavlja ime proizvoda;
- **price** – realan broj koji predstavlja trenutnu cenu proizvoda;

U slučaju da zaglavlje nedostaje, rezultat je odgovor sa statusnim kodom 401 i JSON objektom sledećeg formata i sadržaja:
```json
{
  "msg": "Missing Authorization Header"
}
```

### Naručivanje

**Adresa:** `/order`

**Tip:** POST

**Zaglavlje:** Zaglavlje i njihov sadržaj su:
```json
{
  "Authorization": "Bearer <ACCESS_TOKEN>"
}
```

Vrednost `<ACCESS_TOKEN>` je string koji predstavlja JSON veb token za pristup koji je izdat kupcu prilikom prijave.

**Telo:** Telo zahteva je JSON objekat sledećeg formata:
```json
{
  "requests": [
    {
      "id": 1,
      "quantity": 2
    },
    {
      "id": 2,
      "quantity": 3
    }
  ]
}
```

Sva polja su obavezna. Polje requests predstavlja niz proizvoda koje kupac želi da kupi. Svaki element predstavlja JSON objekat koji sadrži dva polja. Polje id predstavlja identifikator proizvoda, a polje quantity predstavlja količinu koju kupac želi da kupi.

**Odgovor:** Ukoliko su sva tražena zaglavlja prisutna i svi traženi podaci prisutni u telu zahteva i ispunjavaju navedena ograničenja, rezultat zahteva je kreiranje narudžbine i odgovor sa statusnim kodom 200 čiji je sadržaj JSON objekat sledećeg formata:
```json
{
  "id": 1
}
```

Polje id predstavlja celobrojni identifikator kreirane narudžbine.

U slučaju da zaglavlje nedostaje, rezultat je odgovor sa statusnim kodom 401 i JSON objektom sledećeg formata i sadržaja:
```json
{
  "msg": "Missing Authorization Header"
}
```

U slučaju da neko polje tela nedostaje ili je nekorektno, rezultat zahteva je odgovor sa statusnim kodom 400 i JSON objektom sledećeg formata:
```json
{
  "message": "....."
}
```

Sadržaj polja message je:
- `"Field requests is missing."` ukoliko polje requests nije prisutno;
- `"Product id is missing for request number 1."` ukoliko u nekom od JSON objekata nedostaje polje id, numeracija objekata kreće od 0;
- `"Product quantity is missing for request number 1."` ukoliko u nekom od JSON objekata nedostaje polje quantity, numeracija objekata kreće od 0;
- `"Invalid product id for request number 1."` ukoliko neki od identifikatora proizvoda nije ceo broj veći od 0, numeracija objekata kreće od 0;
- `"Invalid product quantity for request number 1."` ukoliko neka od traženih količina nije ceo broj broj veći od 0, numeracija objekata kreće od 0;
- `"Invalid product for request number 1."` ukoliko neki od navedenih proizvoda ne postoji u bazi podataka, numeracija objekata kreće od 0;

Odgovarajuće provere se vrše u navedenom redosledu.

### Pregled narudžbina

**Adresa:** `/status`

**Tip:** GET

**Zaglavlje:** Zaglavlje i njihov sadržaj su:
```json
{
  "Authorization": "Bearer <ACCESS_TOKEN>"
}
```

Vrednost `<ACCESS_TOKEN>` je string koji predstavlja JSON veb token za pristup koji je izdat kupcu prilikom prijave.

**Telo:** -

**Odgovor:** Ukoliko su sva tražena zaglavlja prisutna i ispunjavaju navedena ograničenja, rezultat zahteva je odgovor sa statusnim kodom 200 čiji je sadržaj JSON objekat sledećeg formata:
```json
{
  "orders": [
    {
      "products": [
        {
          "categories": [
            "Category0"
          ],
          "name": "Product0",
          "price": 27.34,
          "quantity": 2
        }
      ],
      "price": 179.0,
      "status": "COMPLETE",
      "timestamp": "2022-05-22T20:32:17Z"
    }
  ]
}
```

Polje orders predstavlja niz JSON objekat gde svaki objekat predstavlja jednu narudžbinu kupca koji je pozvao ovaj servis. Svaki objekat sadrži sledeća polja:
- **price** – ukupna cena narudžbine;
- **status** – status narudžbine, CREATED ukoliko je kreirana, PENDING ukoliko je neko od kurira pokupilo datu narudžbinu ili COMPLETE ukoliko je narudžbina dostavljena;
- **timestamp** – string koji predstavlja datum i vreme kreiranja narudžbine dat u ISO 8601 formatu;
- **orders** – niz JSON objekata u kojem svaki objekat predstavlja jedan proizvodi sadrži sledeća polja:
  - **categories** – niz stringova koji predstavljaju imena kategorija kojima ovaj proizvod pripada;
  - **id** – celobrojni identifikator proizvoda;
  - **name** – string koji predstavlja ime proizvoda;
  - **price** – realan broj koji predstavlja cenu proizvoda;
  - **quantity** – ceo broj koji predstavlja traženu količinu;

U slučaju da zaglavlje nedostaje, rezultat je odgovor sa statusnim kodom 401 i JSON objektom sledećeg formata i sadržaja:
```json
{
  "msg": "Missing Authorization Header"
}
```

### Potvrda dostave

**Adresa:** `/delivered`

**Tip:** POST

**Zaglavlje:** Zaglavlje i njihov sadržaj su:
```json
{
  "Authorization": "Bearer <ACCESS_TOKEN>"
}
```

Vrednost `<ACCESS_TOKEN>` je string koji predstavlja JSON veb token za pristup koji je izdat kupcu prilikom prijave.

**Telo:** Telo zahteva je JSON objekat sledećeg formata:
```json
{
  "id": 1
}
```

Polje id predstavlja identifikator pristigle narudžbine.

**Odgovor:** Ukoliko su sva tražena zaglavlja i polja prisutna i ispunjavaju navedena ograničenja, rezultat zahteva je promena stanja odgovarajuće narudžbine i odgovor sa statusnim kodom 200 bez sadržaja.

U slučaju da zaglavlje nedostaje, rezultat je odgovor sa statusnim kodom 401 i JSON objektom sledećeg formata i sadržaja:
```json
{
  "msg": "Missing Authorization Header"
}
```

U slučaju da neko polje nedostaje ili je nekorektno, rezultat zahteva je odgovor sa statusnim kodom 400 i JSON objektom sledećeg formata:
```json
{
  "message": "....."
}
```

Sadržaj polja message je:
- `"Missing order id."` ukoliko polje id nedostaje;
- `"Invalid order id."` ukoliko polje id ne predstavlja ceo broj veći od 0 ili u bazi ne postoji narudžbina sa datim identifikatorom ili datu narudžbinu nije preuzeo neko od kurira;

Odgovarajuće provere se vrše u navedenom redosledu.

Funkcionalnosti kontejnera koji namenjen za rad sa kuririma su date u nastavku.

### Pregled narudžbina koje treba dostaviti

**Adresa:** `/orders_to_deliver`

**Tip:** GET

**Zaglavlje:** Zaglavlje i njihov sadržaj su:
```json
{
  "Authorization": "Bearer <ACCESS_TOKEN>"
}
```

Vrednost `<ACCESS_TOKEN>` je string koji predstavlja JSON veb token za pristup koji je izdat kuriru prilikom prijave.

**Telo:** -

**Odgovor:** Ukoliko su sva tražena zaglavlja prisutna i ispunjavaju navedena ograničenja, rezultat zahteva je odgovor sa statusnim kodom 200 čiji je sadržaj JSON objekat sledećeg formata:
```json
{
  "orders": [
    {
      "id": 1,
      "email": "…"
    },
    {
      "id": 2,
      "email": "…"
    }
  ]
}
```

Polje orders predstavlja niz narudžbina koje nisu preuzete. Svaki element predstavlja JSON objekat koji sadrži dva polja. Polje id predstavlja identifikator nardužbine, a polje email predstavlja imejl adresu kupca kome treba dostaviti narudžbinu.

U slučaju da zaglavlje nedostaje, rezultat je odgovor sa statusnim kodom 401 i JSON objektom sledećeg formata i sadržaja:
```json
{
  "msg": "Missing Authorization Header"
}
```

### Preuzimanje narudžbine

**Adresa:** `/pick_up_order`

**Tip:** POST

**Zaglavlje:** Zaglavlje i njihov sadržaj su:
```json
{
  "Authorization": "Bearer <ACCESS_TOKEN>"
}
```

Vrednost `<ACCESS_TOKEN>` je string koji predstavlja JSON veb token za pristup koji je izdat kuriru prilikom prijave.

**Telo:** Telo zahteva je JSON objekat sledećeg formata:
```json
{
  "id": 1
}
```

Polje id predstavlja identifikator narudžbine koju kurir želi da preuzme i dostavi kupcu.

**Odgovor:** Ukoliko su sva tražena zaglavlja prisutna i svi traženi podaci prisutni u telu zahteva i ispunjavaju navedena ograničenja, rezultat zahteva je promena stanja odgovarajuće narudžbine odgovor sa statusnim kodom 200 bez ikаkvog sadržaja.

U slučaju da zaglavlje nedostaje, rezultat je odgovor sa statusnim kodom 401 i JSON objektom sledećeg formata i sadržaja:
```json
{
  "msg": "Missing Authorization Header"
}
```

U slučaju da neko polje nedostaje ili je nekorektno, rezultat zahteva je odgovor sa statusnim kodom 400 i JSON objektom sledećeg formata:
```json
{
  "message": "....."
}
```

Sadržaj polja message je:
- `"Missing order id."` ukoliko polje id nedostaje;
- `"Invalid order id."` ukoliko polje id ne predstavlja ceo broj veći od 0, ukoliko bazi ne postoji narudžbina sa datim identifikatorom ili je već preuzeta ili dostavljena;

Odgovarajuće provere se vrše u navedenom redosledu.

## Pokretanje sistema

Potrebno je napisati konfiguracioni fajl pomoću kojeg se sistem može pokrenuti. Konfiguracioni fajl je namenjen za Docker-Compose alat. Sve informacije neophodne za rad kontejner (kao na primer URL baze podatak) proslediti kao varijable okruženja. Potrebno je obezbediti sledeća ograničenja:

- Potrebno je zabraniti spoljašnji pristup bazama podataka i obezbediti njihovu automatsku inicijalizaciju prilikom pokretanja celog sistema, inicijalizacija podrazumeva kreiranje svih neophodnih tabela i dodavanje jednog vlasnika sa sledećim informacijama:

```json
{
  "forename": "Scrooge",
  "surname": "McDuck",
  "email": "onlymoney@gmail.com",
  "password": "evenmoremoney"
}
```

- Potrebno je obezbediti očuvanja podataka u bazama podataka ukoliko odgovarajući kontejneri prestanu sa radom;
- Potrebno je obezbediti da kontejneri iz dela sistema namenjenom za autentikaciju i autorizaciju ne mogu da pristupe kontejnerima iz dela sistema koji služe za upravljanje rada prodavnice i obratno.

Na samoj odbrani, od studenata se očekuje da pomoću ovog fajla pokrenu sistem i demonstriraju njegov rad.

## Naplata

Potrebno je obezbediti naplatu narudžbina putem Ethereum Blockchain platforme. Za simulaciju ove platforme iskoristi Docker Image šablone dostupan na Docker Hub (https://hub.docker.com/r/trufflesuite/ganache-cli/) repozitorijumu.

Za svaku kreiranu narudžbinu potrebno je kreirati jedan pametni ugovor. Obezbediti da dostavu (a i vezivanje kurira za ugovor) nije moguće izvršiti sve dok kupac ne prebaci traženu količinu kriptovaluta (izraženu u wei apoenima) na sam ugovor. Količina kriptovaluta koju treba naplatiti (izražena u wei apoenima) se dobija pomoću formule `order_price * 100`. Po potvrdi dostave od strane kupca, 80% prebačenih sredstava dati vlasniku prodavnice, a ostalih 20% prebaciti kuriru.

Za navedenog vlasnika kreirati par ključeva i obezbediti mu dovoljno količinu kriptovaluta tako da može da pokrije troškove ugovora koji odgovaraju narudžbinama. Sredstva prebaciti sa prvog od deset računa koji se kreiraju prilikom pokretanja simulatora platforme.

Prilikom kreiranja ugovora potrebno ga je vezati za kupca koji kreirao narudžbinu, ali potrebno ostaviti opciju da se kurir tek kasnije priključi ugovoru. Vlasnik takođe snosi troškove vezivanja kurira za neki od ugovora.

Prilikom prebacivanja sredstava od strane kupca, potrebno je obezbediti da samo onaj kupac koji je vezan za dati ugovor može da izvrši prebacivanja sredstava. Pored toga, obezbediti da vezani kupac mora da prebaci tačnu svotu novca pre nego što kurir može da preuzme narudžbinu i krene sa dostavom. Kupac snosi trošak prebacivanja sredstava.

Prilikom odabira narudžbine za dostavu od strane kurira vezati istog za odgovarajući ugovor. Prilikom potvrde dostave od strane kupca izvršiti transfer sredstava na račun kurira i vlasnika i zabraniti bilo koju dalju interakciju sa odgovarajućim ugovorom. Zabraniti kupcima da vrše potvrdu dostave pre vezivanja nekog kurira za dati ugovor.

Prilikom realizacije naplata potrebno je doraditi sledeće funkcionalnosti kontejnera koji namenjen za rad sa kupcima (promene su obojene sivom bojom):

### Naručivanje

**Adresa:** `/order`

**Tip:** POST

**Zaglavlje:** Zaglavlje i njihov sadržaj su:
```json
{
  "Authorization": "Bearer <ACCESS_TOKEN>"
}
```

Vrednost `<ACCESS_TOKEN>` je string koji predstavlja JSON veb token za pristup koji je izdat kupcu prilikom prijave.

**Telo:** Telo zahteva je JSON objekat sledećeg formata:
```json
{
  "requests": [
    {
      "id": 1,
      "quantity": 2
    },
    {
      "id": 2,
      "quantity": 3
    }
  ],
  "address": "..."
}
```

Sva polja su obavezna. Polje requests predstavlja niz proizvoda koje kupac želi da kupi. Svaki element predstavlja JSON objekat koji sadrži dva polja. Polje id predstavlja identifikator proizvoda, a polje quantity predstavlja količinu koju kupac želi da kupi. Polje address je string koji predstavlja račun datog kupca.

**Odgovor:** Ukoliko su sva tražena zaglavlja prisutna i svi traženi podaci prisutni u telu zahteva i ispunjavaju navedena ograničenja, rezultat zahteva je kreiranje narudžbine, kreiranje odgovarajućeg pametnog ugovora i odgovor sa statusnim kodom 200 čiji je sadržaj JSON objekat sledećeg formata:
```json
{
  "id": 1
}
```

Polje id predstavlja celobrojni identifikator kreirane narudžbine.

U slučaju da zaglavlje nedostaje, rezultat je odgovor sa statusnim kodom 401 i JSON objektom sledećeg formata i sadržaja:
```json
{
  "msg": "Missing Authorization Header"
}
```

U slučaju da neko polje tela nedostaje ili je nekorektno, rezultat zahteva je odgovor sa statusnim kodom 400 i JSON objektom sledećeg formata:
```json
{
  "message": "....."
}
```

Sadržaj polja message je:
- `"Field requests is missing."` ukoliko polje requests nije prisutno;
- `"Product id is missing for request number 1."` ukoliko u nekom od JSON objekata nedostaje polje id, numeracija objekata kreće od 0;
- `"Product quantity is missing for request number 1."` ukoliko u nekom od JSON objekata nedostaje polje quantity, numeracija objekata kreće od 0;
- `"Invalid product id for request number 1."` ukoliko neki od identifikatora proizvoda nije ceo broj veći od 0, numeracija objekata kreće od 0;
- `"Invalid product quantity for request number 1."` ukoliko neka od traženih količina nije ceo broj broj veći od 0, numeracija objekata kreće od 0;
- `"Invalid product for request number 1."` ukoliko neki od navedenih proizvoda ne postoji u bazi podataka, numeracija objekata kreće od 0;
- `"Field address is missing."` ukoliko polje address nije prisutno;
- `"Invalid adress."` ukoliko polje address ne predstavlja validan račun;

Odgovarajuće provere se vrše u navedenom redosledu.

### Potvrda dostave

**Adresa:** `/delivered`

**Tip:** POST

**Zaglavlje:** Zaglavlje i njihov sadržaj su:
```json
{
  "Authorization": "Bearer <ACCESS_TOKEN>"
}
```

Vrednost `<ACCESS_TOKEN>` je string koji predstavlja JSON veb token za pristup koji je izdat kupcu prilikom prijave.

**Telo:** Telo zahteva je JSON objekat sledećeg formata:
```json
{
  "id": 1
}
```

Polje id predstavlja identifikator pristigle narudžbine.

**Odgovor:** Ukoliko su sva tražena zaglavlja i polja prisutna i ispunjavaju navedena ograničenja, rezultat zahteva je promena stanja odgovarajuće narudžbine, transfer sredstava na račune kurira i vlasnika i odgovor sa statusnim kodom 200 bez sadržaja. Troškove transfera snosi vlasnik.

U slučaju da zaglavlje nedostaje, rezultat je odgovor sa statusnim kodom 401 i JSON objektom sledećeg formata i sadržaja:
```json
{
  "msg": "Missing Authorization Header"
}
```

U slučaju da neko polje nedostaje ili je nekorektno, rezultat zahteva je odgovor sa statusnim kodom 400 i JSON objektom sledećeg formata:
```json
{
  "message": "....."
}
```

Sadržaj polja message je:
- `"Missing order id."` ukoliko polje id nedostaje;
- `"Invalid order id."` ukoliko polje id ne predstavlja ceo broj veći od 0 ili u bazi ne postoji narudžbina sa datim identifikatorom ili datu narudžbinu nije preuzeo neko od kurira;
- `"Delivery not complete."` ukoliko nijedan od kurira nije pokupilo datu narudžbinu;

Odgovarajuće provere se vrše u navedenom redosledu.

Prilikom realizacije naplata potrebno je doraditi sledeće funkcionalnosti kontejnera koji namenjen za rad sa kuririma (promene su obojene sivom bojom):

### Preuzimanje narudžbine

**Adresa:** `/pick_up_order`

**Tip:** POST

**Zaglavlje:** Zaglavlje i njihov sadržaj su:
```json
{
  "Authorization": "Bearer <ACCESS_TOKEN>"
}
```

Vrednost `<ACCESS_TOKEN>` je string koji predstavlja JSON veb token za pristup koji je izdat kuriru prilikom prijave.

**Telo:** Telo zahteva je JSON objekat sledećeg formata:
```json
{
  "id": 1,
  "address": "..."
}
```

Polje id predstavlja identifikator narudžbine koju kurir želi da preuzme i dostavi kupcu. Polje address predstavlja račun kurira.

**Odgovor:** Ukoliko su sva tražena zaglavlja prisutna i svi traženi podaci prisutni u telu zahteva i ispunjavaju navedena ograničenja, rezultat zahteva je promena stanja odgovarajuće narudžbine, vezivanje kurira za odgovarajući pametni ugovor i odgovor sa statusnim kodom 200 bez ikаkvog sadržaja.

U slučaju da zaglavlje nedostaje, rezultat je odgovor sa statusnim kodom 401 i JSON objektom sledećeg formata i sadržaja:
```json
{
  "msg": "Missing Authorization Header"
}
```

U slučaju da neko polje nedostaje ili je nekorektno, rezultat zahteva je odgovor sa statusnim kodom 400 i JSON objektom sledećeg formata:
```json
{
  "message": "....."
}
```

Sadržaj polja message je:
- `"Missing order id."` ukoliko polje id nedostaje;
- `"Invalid order id."` ukoliko polje id ne predstavlja ceo broj veći od 0, ukoliko bazi ne postoji narudžbina sa datim identifikatorom ili je već dostavljena;
- `"Missing address."` ukoliko polje address nije prisutno;
- `"Invalid adress."` ukoliko polje аddress ne predstavlja validan račun;
- `"Transfer not complete."` ukoliko kupac nije izvršio transfer novca na ugovor koji odgovara navedenoj narudžbini;

Odgovarajuće provere se vrše u navedenom redosledu.

Prilikom realizacije naplata potrebno je dodati sledeće funkcionalnosti kontejneru koji namenjen za rad sa kupcima:

### Plaćanje

**Adresa:** `/generate_invoice`

**Tip:** POST

**Zaglavlje:** Zaglavlje i njihov sadržaj su:
```json
{
  "Authorization": "Bearer <ACCESS_TOKEN>"
}
```

Vrednost `<ACCESS_TOKEN>` je string koji predstavlja JSON veb token za pristup koji je izdat kupcu prilikom prijave.

**Telo:** Telo zahteva je JSON objekat sledećeg formata:
```json
{
  "id": 1,
  "address": "..."
}
```

Polje id predstavlja identifikator narudžbine za koju se vrši naplata. Polje address predstavlja račun kupca.

**Odgovor:** Ukoliko su sva tražena zaglavlja i polja prisutna i ispunjavaju navedena ograničenja, rezultat zahteva je odgovor sa statusnim kodom 200 sa sledećim JSON objektom:
```json
{
  "invoice": "....."
}
```

Polje invoice predstavlja transakciju koju kupac treba da izvrši da bi platio narudžbinu.

U slučaju da zaglavlje nedostaje, rezultat je odgovor sa statusnim kodom 401 i JSON objektom sledećeg formata i sadržaja:
```json
{
  "msg": "Missing Authorization Header"
}
```

U slučaju da neko polje nedostaje ili je nekorektno, rezultat zahteva je odgovor sa statusnim kodom 400 i JSON objektom sledećeg formata:
```json
{
  "message": "....."
}
```

Sadržaj polja message je:
- `"Missing order id."` ukoliko polje id nedostaje;
- `"Invalid order id."` ukoliko polje id ne predstavlja ceo broj veći od 0 ili u bazi ne postoji narudžbina sa datim identifikatorom;
- `"Missing address."` ukoliko polje address nije prisutno;
- `"Invalid adress."` ukoliko polje аddress ne predstavlja validan račun;
- `"Transfer already complete."` ukoliko je transfer sredstava na odgovarajući ugovor već izvršen;

Odgovarajuće provere se vrše u navedenom redosledu.