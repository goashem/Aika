# Aika – mahdollisia lisähaettavia tietoja (lista)

- Sään “nyt heti” -hyöty: nowcast ja tutka
    - sade-/lumitutka (0–2 h), “alkaa X min päästä, kestää Y”
    - näkyvyys ja pilvikorkeus
    - salamointi/ukkostutka (kausittain)

- Ennuste tiiviinä “päivän suunnitteluna”
    - seuraavat 12 h: sade-ikkunat, kovin tuuli, lämpötiladipit
    - 7 vrk: min/max, sademäärä, tuulisuus, “paras ulkoiluikkuna”
    - lumen kertymäennuste (cm)

- Aurinko ja valo: arjen kannalta “paljonko valoa”
    - päivänvalon pituus ja muutos eilisestä (+/- min)
    - golden hour / blue hour
    - aika auringonnousuun / -laskuun

- Revontulet “näenkö oikeasti” -arviona
    - Kp + pilvisyys + kuun kirkkaus + (jos saatavilla) Bz/aurinkotuuli
    - “ikkuna-arvio” (matala/kohtalainen/hyvä) + perustelut

- Sähkö: nykyhinnan lisäksi
    - tulevaisuuden halvin/kallein tunti + 3 halvinta seuraavaksi ✅ *(implemented with exact 15-minute timeslots)*
    - huomisen hinnat heti julkaisun jälkeen ✅ *(available through ENTSO-E day-ahead data)*
    - CO₂-intensiteetti (jos lähde saatavilla)

- Liikenne: häiriöiden lisäksi “miten pääsen nyt”
    - lähimmän pysäkin seuraavat lähdöt + viiveet
    - esiasetetut reitit: matka-aika nyt + poikkeamat
    - tie-/liikennekameralinkit + keli-korostus

- Kalenteri ja arki
    - nimipäivä, liputuspäivät, loma-ajat (valinnainen)
    - päivän agenda (Google Calendar / .ics): seuraava tapahtuma

- Vesistö ja rannikko
    - vedenkorkeus + trendi (nousee/laskee) + tulvariskit
    - meriveden lämpö, jäätiedote talvella

- Läpinäkyvyys ja käytettävyys
    - rivikohtaiset “lähde + päivitysaika”
    - output-moodit: tiivis/laaja, `--json`, `--ansi`
