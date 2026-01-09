# Suomenkielinen aikatietojen skripti

Tämä skripti tarjoaa kattavat aika- ja päivämäärätiedot suomeksi, mukaan lukien aurinko- ja kuutiedot.

## Ominaisuudet

- Aika ilmaistuna luonnollisella suomeksi (esim. "noin varttia yli kaksitoista")
- Tarkat suomenkieliset vuorokaudenajat (aamuyö, aamu, aamupäivä, keskipäivä, iltapäivä, varhainen ilta, myöhäisilta, iltayö)
- Päivämäärätiedot suomeksi oikealla kieliopilla
- Vuoden prosentuaalinen valmistuminen (sisältäen kellonajan)
- Aurinkotiedot (nousu, lasku, korkeus, atsimuutti)
- Kuutiedot (vaiheen prosentti, kasvu-/vähennystila, korkeus, atsimuutti)

## Asennus

1. Kloonaa repositorio
2. Asenna riippuvuudet:
   ```bash
   pip install -r requirements.txt
   ```

Tai käytä valmiiksi asennettua virtuaaliympäristöä:

1. `.venv`-hakemisto sisältää kaikki tarvittavat riippuvuudet
2. Suorita skripti käyttämällä mukana tulevaa kääreskriptiä

## Käyttö

### Suora suoritus:
```bash
python time_info_fi.py
```

### Käyttämällä kääreskriptiä:
```bash
./run_time_info.sh
```

## Konfigurointi

Sijaintiasetukset voidaan säätää tiedostossa `config.ini`:
- `latitude`: Maantieteellinen leveyspiiri
- `longitude`: Maantieteellinen pituuspiiri
- `timezone`: Aikavyöhyketunniste

## Riippuvuudet

- `astral`: Aurinkolaskelmia varten
- `ephem`: Kuulaskelmia varten

Nämä ovat listattu tiedostossa `requirements.txt` ja esiasennettu `.venv`-hakemistoon.