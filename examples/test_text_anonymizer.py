# Test
from text_anonymizer import TextAnonymizer
import time

'''
Example code to test TextAnonymizer
Also used in the performance testing.
'''

ITERATIONS = 10

# Init anonymizer to work in mask mode and two languages
text_anonymizer = TextAnonymizer()


text_fi = ('Nimet: Toivo, Sami, Seppo, Ahti, Veikko, Jaana, Tiina, Minna, Aura, Lumi, Virtanen, Salminen, Gröönroos, Suomi.' \
           '\n\nRekisterinumerot: ABC-123, CCC-111, DDD-222, CBA-321' \
           '\n  Lisää: AB-123 (moottoripyörä), CD-1234 (diplomaatti), XYZ 789' \
           '\n  Negatiivinen testi: on 040 (ei rekisteri), 300-223 (virheellinen)' \
           '\n\nSähköpostiosoitteet: testi-veikko.nieminen@example.com, 28j30d2@example.com'  \
           '\n  Lisää: etunimi.sukunimi@yritys.fi, test123@example.org' \
           '\n\nIP-Osoitteet: 192.168.177.111, 127.0.0.1, 1.1.1.1, 10.0.0.1, 8.8.8.8' \
           '\n  IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334' \
           '\n\nPuhelinnumerot (kansainväliset): +358448888888, +358 40 123 4567, +358 9 310 1111' \
           '\nPuhelinnumerot (paikalliset välilyönneillä): 040 123 4567, 050 987 6543, 09 310 1111' \
           '\nPuhelinnumerot (paikalliset ilman välilyöntejä): 044888888, 0401234567' \
           '\nPuhelinnumerot (viivoilla): 040-1234567, 09-3101111' \
           '\nPuhelinnumerot (useita välilyöntejä): 09 123 4567, 044 888 8888' \
           '\nPuhelinnumerot (sulkeet): (09) 12345678, (040) 1234567' \
           '\nPuhelinnumerot (ilman 0-alkua): 555 9876 (pitäisi tunnistaa GLiNERillä)' \
           '\n  Negatiivinen testi: 23.10.2021, 00600, 30.13' \
           '\n\nHenkilötunnukset: 010130A100K, 020300-001G, 311299-999A, 150320-' \
           '\n  Osittainen: 121212-123A, 010101-000A' \
           '\n  Negatiivinen: 0441234567, 421399-999L' \
           '\n\nIban testinumerot: FI49 5000 9420 0287 30, FI4950009420028730' \
           '\n  Ulkomaiset: GB33BUKB20201555555555, DE89370400440532013000' \
           '\n  Välilyönneillä: SE35 5000 0000 0549 1000 0003' \
           '\n\nOsoitteet: Meriharjuntie 1 A 1, 40100 Helsinki, Mannerheimintie 2' \
           '\n  Lisää: Pohjoisesplanadi 11-13, PL 1 00099 HELSINGIN KAUPUNKI' \
           '\n  Katunimet: Insinöörinkatu 3B, Leväluhdantiellä' \
           '\n\nKiinteistötunnukset: 092-416-11-123, 999-999-12-44-M601, 91-7-104-3' \
           '\n  Lyhyt muoto: 1-1-1-1, 22-22-4444-333' \
           '\n  Negatiivinen: 23.10.2021, 040-0001119 (puhelin)' \
           '\n\nTiedostot: exceli.xlsx, dokkari.pdf, kuva.jpg, esitys.pptx' \
           '\n  Lisää: data.csv, tiedosto.txt, arkisto.zip' \
           '\n  URL-tiedostot: http://example.com/file.pdf' \
           '\n\nURL:t: http://www.google.com, https://helsinki.fi, www.example.com' \
           '\n  Lisää: https://sub.domain.fi/path/to/page, ftp://files.server.com' \
           '\n\nSekalaiset tapaukset:' \
           '\n  Teksti: Naapurini Matti Virtanen osoitteesta Esimerkkitie 5 on huomannut.' \
           '\n  Puhelin lauseessa: Minut tavoittaa numerosta 040 1234567 tai +358401234567.' \
           '\n  Rekisteri lauseessa: Auton rekisteri on ABC-123 ja se on punainen.' \
           '\n  Puhelin vs rekisteri: Hänen numeronsa on 040 ja auto on AB-123.'
           )

print("Anonymizer running...")
start_time = round(time.time() * 1000)
for i in range(ITERATIONS):
    anonymized_fi = text_anonymizer.anonymize_text(text_fi)
print(text_fi)
print("--")
print(anonymized_fi)
print(" ")
time_ms = round(time.time() * 1000)-start_time
print("{i} iterations took {ms}ms, avg {avg}ms".format(i=ITERATIONS, ms=time_ms, avg=time_ms/ITERATIONS))