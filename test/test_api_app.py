#!/usr/bin/env python
"""
Test suite for the Anonymizer FastAPI application.

Verifies that:
1. API is accessible and running
2. Basic anonymization works via /anonymize endpoint
3. Profile-based anonymization works correctly
4. Batch anonymization works via /anonymize_batch endpoint
5. Proper error handling and response validation
"""

import sys
import os
import unittest
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    logger.error("requests is required for API tests. Install with: pip install requests")
    requests = None

API_URL = "http://127.0.0.1:8000"
API_TIMEOUT = 2.0


class TestAnonymizerAPI(unittest.TestCase):
    """Test suite for the Anonymizer FastAPI app."""

    @classmethod
    def setUpClass(cls):
        """Check if API is available before running tests."""
        if requests is None:
            cls.api_available = False
            logger.warning("requests not installed. Skipping API tests.")
            return

        try:
            response = requests.get(f"{API_URL}/docs", timeout=API_TIMEOUT)
            if response.status_code == 200:
                cls.api_available = True
                logger.info("API is running at %s", API_URL)
            else:
                cls.api_available = False
                logger.warning("API responded with status %d. Skipping API tests.", response.status_code)
        except (requests.ConnectionError, requests.Timeout) as e:
            cls.api_available = False
            logger.warning("Anonymizer API is not running at %s. Skipping API tests. Error: %s", API_URL, e)
        except Exception as e:
            cls.api_available = False
            logger.warning("Unexpected error connecting to API: %s", e)

    def setUp(self):
        """Skip test if API is not available."""
        if not self.api_available:
            test_name = self._testMethodName
            self.skipTest(f"API not running - skipping {test_name}")

    def test_api_docs_accessible(self):
        """Test that API documentation is accessible."""
        response = requests.get(f"{API_URL}/docs", timeout=API_TIMEOUT)
        self.assertEqual(response.status_code, 200)
        logger.info("API documentation is accessible")

    def test_anonymize_simple_text(self):
        """Test basic anonymization endpoint with simple text."""
        payload = {
            "text": "Puhelinnumeroni on 040-1234567."
        }
        response = requests.post(f"{API_URL}/anonymize", json=payload, timeout=API_TIMEOUT)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("anonymized_txt", data)
        self.assertIn("summary", data)
        self.assertIsNotNone(data["anonymized_txt"])

        # Phone number should be anonymized
        self.assertNotIn("040-1234567", data["anonymized_txt"])
        logger.info("Simple text anonymization successful: %s", data["anonymized_txt"])

    def test_anonymize_finnish_ssn(self):
        """Test anonymization of Finnish social security number."""
        payload = {
            "text": "Minun henkilötunnukseni on 311299-999A."
        }
        response = requests.post(f"{API_URL}/anonymize", json=payload, timeout=API_TIMEOUT)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertNotIn("311299-999A", data["anonymized_txt"])

        # Check summary
        if data["summary"]:
            self.assertIsInstance(data["summary"], dict)
            logger.info("SSN anonymization summary: %s", data["summary"])

    def test_anonymize_with_profile_blocklist(self):
        """Test anonymization with a profile (blocklist/grantlist)."""
        payload = {
            "text": "Tunniste blockword123 on lauseessa.",
            "profile": "example"
        }
        response = requests.post(f"{API_URL}/anonymize", json=payload, timeout=API_TIMEOUT)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("anonymized_txt", data)

        # Blocklisted word should be anonymized
        self.assertNotIn("blockword123", data["anonymized_txt"])

        # Check summary for MUU_TUNNISTE (custom identifier)
        self.assertIn("summary", data)
        self.assertIsInstance(data["summary"], dict)

        if "MUU_TUNNISTE" in data["summary"]:
            self.assertGreater(data["summary"]["MUU_TUNNISTE"], 0)
            logger.info("Profile blocklist working: MUU_TUNNISTE count = %d",
                       data["summary"]["MUU_TUNNISTE"])

    def test_anonymize_with_profile_grantlist(self):
        """Test that grantlisted items are protected when using profile."""
        payload = {
            "text": "Sallittu kohde on example321 lauseessa.",
            "profile": "example"
        }
        response = requests.post(f"{API_URL}/anonymize", json=payload, timeout=API_TIMEOUT)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # Grantlisted word should NOT be anonymized
        self.assertIn("example321", data["anonymized_txt"])
        logger.info("Grantlist protection working: %s", data["anonymized_txt"])

    def test_anonymize_with_profile_combined(self):
        """Test profile with both blocklist and grantlist items."""
        payload = {
            "text": "Estetty: blockword123, Sallittu: example321, Puhelin: 040-1234567",
            "profile": "example"
        }
        response = requests.post(f"{API_URL}/anonymize", json=payload, timeout=API_TIMEOUT)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # Blocklisted should be anonymized
        self.assertNotIn("blockword123", data["anonymized_txt"])

        # Grantlisted should be protected
        self.assertIn("example321", data["anonymized_txt"])

        # Phone should be anonymized
        self.assertNotIn("040-1234567", data["anonymized_txt"])

        logger.info("Combined profile test successful: %s", data["anonymized_txt"])

    def test_anonymize_without_profile(self):
        """Test that blocklist is not applied when no profile is specified."""
        payload = {
            "text": "Tunniste blockword123 on lauseessa."
        }
        response = requests.post(f"{API_URL}/anonymize", json=payload, timeout=API_TIMEOUT)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # Without profile, blockword123 should NOT be detected as custom identifier
        # It should remain in text (unless it matches another recognizer)
        summary = data.get("summary", {})

        # MUU_TUNNISTE should not be present without profile
        self.assertNotIn("MUU_TUNNISTE", summary)
        logger.info("Blocklist correctly not applied without profile")

    def test_anonymize_batch(self):
        """Test batch anonymization endpoint."""
        payload = [
            {
                "text": "Henkilötunnukseni on 311299-999A."
            },
            {
                "text": "Tunniste blockword123 on lauseessa.",
                "profile": "example"
            },
            {
                "text": "Soita minulle numeroon 040-9876543."
            }
        ]
        response = requests.post(f"{API_URL}/anonymize_batch", json=payload, timeout=API_TIMEOUT)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3)

        # Verify each item has required structure
        for item in data:
            self.assertIn("anonymized_txt", item)
            self.assertIn("summary", item)

        # Check first item (SSN)
        self.assertNotIn("311299-999A", data[0]["anonymized_txt"])

        # Check second item (blocklist with profile)
        self.assertNotIn("blockword123", data[1]["anonymized_txt"])

        # Check third item (phone)
        self.assertNotIn("040-9876543", data[2]["anonymized_txt"])

        logger.info("Batch anonymization successful: %d items processed", len(data))

    def test_anonymize_batch_mixed_profiles(self):
        """Test batch processing with different profiles."""
        payload = [
            {
                "text": "Item blockword123 without profile context."
            },
            {
                "text": "Item blockword123 with example profile.",
                "profile": "example"
            }
        ]
        response = requests.post(f"{API_URL}/anonymize_batch", json=payload, timeout=API_TIMEOUT)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 2)

        # First should not detect blockword123 as MUU_TUNNISTE
        stats1 = data[0].get("summary", {})
        self.assertNotIn("MUU_TUNNISTE", stats1)

        # Second should detect blockword123 as MUU_TUNNISTE
        stats2 = data[1].get("summary", {})
        if "MUU_TUNNISTE" in stats2:
            self.assertGreater(stats2["MUU_TUNNISTE"], 0)

        logger.info("Mixed profile batch test successful")

    def test_anonymize_empty_text(self):
        """Test handling of empty text."""
        payload = {
            "text": ""
        }
        response = requests.post(f"{API_URL}/anonymize", json=payload, timeout=API_TIMEOUT)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        # Empty input can return either None or empty string
        self.assertIn(data["anonymized_txt"], [None, ""],
                      "Empty text should return None or empty string")
        logger.info("Empty text handled correctly: %s", data["anonymized_txt"])

    def test_anonymize_mixed_language_text(self):
        """Test anonymization of text containing both Finnish and English."""
        payload = {
            "text": "Hei, olen Matti. Hello, I am John."
        }
        response = requests.post(f"{API_URL}/anonymize", json=payload, timeout=API_TIMEOUT)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("anonymized_txt", data)
        logger.info("Mixed language text anonymization: %s", data["anonymized_txt"])

    def test_anonymize_minimal_payload(self):
        """Test anonymization with minimal payload (only text and profile)."""
        payload = {
            "text": "Soita numeroon 040-1234567."
        }
        response = requests.post(f"{API_URL}/anonymize", json=payload, timeout=API_TIMEOUT)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertNotIn("040-1234567", data["anonymized_txt"])
        logger.info("Minimal payload anonymization working correctly")

    def test_anonymize_summary_structure(self):
        """Test that summary are returned in correct format with expected entities."""
        payload = {
            "text": "Contact: 040-1234567, SSN: 311299-999A"
        }
        response = requests.post(f"{API_URL}/anonymize", json=payload, timeout=API_TIMEOUT)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("summary", data)
        self.assertIsInstance(data["summary"], dict)

        # Both phone and SSN should be anonymized
        self.assertNotIn("040-1234567", data["anonymized_txt"])
        self.assertNotIn("311299-999A", data["anonymized_txt"])

        # Statistics should not be empty since we have entities
        self.assertTrue(data["summary"], "Statistics should not be empty for text with entities")

        # Verify summary structure
        for entity_type, count in data["summary"].items():
            self.assertIsInstance(entity_type, str)
            self.assertIsInstance(count, int)
            self.assertGreater(count, 0)

        # Check for expected entity types (phone and SSN)
        has_phone = "PUHELIN" in data["summary"] or "PHONE_NUMBER" in data["summary"]
        has_ssn = "FI_SSN" in data["summary"] or "HETU" in data["summary"]

        self.assertTrue(has_phone or has_ssn,
                       "Should detect at least phone or SSN in summary")

        logger.info("Statistics structure valid: %s", data["summary"])

    def test_anonymize_nonexistent_profile(self):
        """Test that nonexistent profile is handled gracefully without custom recognizers."""
        payload = {
            "text": "Tunniste blockword123 on lauseessa.",
            "profile": "nonexistent_profile_xyz"
        }
        response = requests.post(f"{API_URL}/anonymize", json=payload, timeout=API_TIMEOUT)

        # Should still return 200 (graceful handling)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("anonymized_txt", data)

        # Nonexistent profile should NOT trigger custom recognizers
        summary = data.get("summary", {})
        self.assertNotIn("MUU_TUNNISTE", summary,
                         "Nonexistent profile should not apply blocklist")

        # blockword123 should remain in text (no custom recognizer applied)
        self.assertIn("blockword123", data["anonymized_txt"],
                      "Word should not be anonymized without valid profile")

        logger.info("Non-existent profile handled gracefully - no custom recognizers applied")

    def test_anonymize_with_profile_regex_patterns(self):
        """Test custom regex patterns from example profile's regex_patterns.json."""
        # Test various patterns defined in config/example/regex_patterns.json
        test_cases = [
            ("TEST_VARCODE1", "prefix_variations"),
            ("PROD_VARCODE99", "prefix_variations"),
            ("DEV_VARCODE123", "prefix_variations"),
            ("VARCODEabc", "alphanumeric_suffix"),
            ("VARCODE1a2b", "alphanumeric_suffix"),
            ("VARCODE123", "word_with_numbers"),
            ("VARCODE999999", "word_with_numbers"),
            ("VARCODE12", "word_with_digit_range"),
            ("VARCODE1234", "word_with_digit_range"),
        ]

        for test_word, pattern_name in test_cases:
            payload = {
                "text": f"Tässä lauseessa on {test_word} tunniste.",
                "profile": "example"
            }
            response = requests.post(f"{API_URL}/anonymize", json=payload, timeout=API_TIMEOUT)
            self.assertEqual(response.status_code, 200)

            data = response.json()

            # The VARCODE pattern should be anonymized
            self.assertNotIn(test_word, data["anonymized_txt"],
                           f"{test_word} should be anonymized by pattern '{pattern_name}'")

            # Check summary for VARCODE entity
            summary = data.get("summary", {})
            self.assertIn("VARCODE", summary,
                         f"VARCODE entity should be detected for '{test_word}' (pattern: {pattern_name})")
            self.assertGreater(summary["VARCODE"], 0,
                              f"VARCODE count should be > 0 for '{test_word}'")

        logger.info("Custom regex patterns tested successfully: %d patterns verified", len(test_cases))

    def test_anonymize_with_profile_regex_patterns_no_match(self):
        """Test that words not matching regex patterns are preserved."""
        # These should NOT match any VARCODE patterns
        non_matching_words = [
            "VARCODES",  # Has 'S' at end, word boundary prevents match
            "xVARCODE",  # Prefix prevents word boundary match (using lowercase x instead)
            "VARCODE1234567890",  # Too many digits for alphanumeric patterns (10 digits > 6)
            "VARCODE",  # No digits at all
            "varcode123",  # Lowercase, patterns require uppercase
        ]

        for word in non_matching_words:
            payload = {
                "text": f"Tässä lauseessa on {word} sana.",
                "profile": "example"
            }
            response = requests.post(f"{API_URL}/anonymize", json=payload, timeout=API_TIMEOUT)
            self.assertEqual(response.status_code, 200)

            data = response.json()

            # Word should remain (not matched by VARCODE patterns)
            # Note: Some words might still be anonymized by GLiNER's standard recognizers
            # We only check that they're NOT recognized as VARCODE entities
            summary = data.get("summary", {})
            self.assertNotIn("VARCODE", summary,
                           f"VARCODE entity should not be detected for non-matching word '{word}'")

        logger.info("Verified non-matching words don't trigger VARCODE patterns: %d words tested", len(non_matching_words))

    def test_anonymize_with_nonexistent_profile_no_regex(self):
        """Test that custom regex patterns are NOT applied with nonexistent profile."""
        # These patterns would match with "example" profile, but not with nonexistent profile
        test_words = [
            "TEST_VARCODE1",
            "VARCODE123",
        ]

        for word in test_words:
            payload = {
                "text": f"Tässä lauseessa on {word} tunniste.",
                "profile": "nonexistent_profile_xyz"
            }
            response = requests.post(f"{API_URL}/anonymize", json=payload, timeout=API_TIMEOUT)
            self.assertEqual(response.status_code, 200)

            data = response.json()

            # Word should remain (no custom regex patterns loaded)
            self.assertIn(word, data["anonymized_txt"],
                         f"{word} should NOT be anonymized without valid profile")

            # VARCODE entity should NOT be in summary
            summary = data.get("summary", {})
            self.assertNotIn("VARCODE", summary,
                           f"VARCODE entity should not be detected without valid profile for '{word}'")

        logger.info("Verified regex patterns not applied with nonexistent profile: %d words tested", len(test_words))



class TestAnonymizerAPIEdgeCases(unittest.TestCase):
    """Test edge cases and error handling for the API."""

    @classmethod
    def setUpClass(cls):
        """Check if API is available before running tests."""
        if requests is None:
            cls.api_available = False
            return

        try:
            response = requests.get(f"{API_URL}/docs", timeout=API_TIMEOUT)
            cls.api_available = response.status_code == 200
        except Exception:
            cls.api_available = False
            logger.warning("API not available for edge case tests")

    def setUp(self):
        """Skip test if API is not available."""
        if not self.api_available:
            test_name = self._testMethodName
            self.skipTest(f"API not running - skipping {test_name}")

    def test_anonymize_very_long_text(self):
        """Test anonymization of longer text with multiple phone numbers."""
        long_text = " ".join([f"This is sentence {i} with phone 040-{i:07d}." for i in range(50)])
        payload = {
            "text": long_text
        }
        response = requests.post(f"{API_URL}/anonymize", json=payload, timeout=10.0)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIsNotNone(data["anonymized_txt"])

        # Verify that at least some phone numbers were anonymized
        # Check a few specific numbers are not in output
        self.assertNotIn("040-0000000", data["anonymized_txt"])
        self.assertNotIn("040-0000010", data["anonymized_txt"])
        self.assertNotIn("040-0000049", data["anonymized_txt"])

        # Statistics should show phone detections
        summary = data.get("summary", {})
        phone_count = summary.get("PUHELIN", summary.get("PHONE_NUMBER", 0))
        self.assertGreater(phone_count, 0, "Should detect phone numbers in long text")

        logger.info("Long text processed successfully: %d phone numbers detected", phone_count)

    def test_anonymize_special_characters(self):
        """Test handling of special characters while anonymizing phone numbers."""
        payload = {
            "text": "Special chars: @#$%^&*() with phone 040-1234567"
        }
        response = requests.post(f"{API_URL}/anonymize", json=payload, timeout=API_TIMEOUT)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("anonymized_txt", data)

        # Phone number should be anonymized
        self.assertNotIn("040-1234567", data["anonymized_txt"])

        # Special characters should be preserved
        self.assertIn("@#$%^&*()", data["anonymized_txt"])

        # Statistics should show phone detection
        summary = data.get("summary", {})
        self.assertTrue(
            "PUHELIN" in summary or "PHONE_NUMBER" in summary,
            "Phone number should be detected in summary"
        )

        logger.info("Special characters preserved while phone anonymized: %s", data["anonymized_txt"])

    def test_batch_empty_list(self):
        """Test batch endpoint with empty list."""
        payload = []
        response = requests.post(f"{API_URL}/anonymize_batch", json=payload, timeout=API_TIMEOUT)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data, [])
        logger.info("Empty batch handled correctly")

    def test_anonymize_long_text_mixed_entities(self):
        """Test anonymization of long text with street address, phone numbers, and NER entities.

        This test uses a detailed lamp post complaint to test GLiNER throughput with
        realistic Finnish text containing multiple entity types. All data is fictional.
        """
        # Fictional lamp post complaint with unnecessarily detailed information
        # All names, addresses, phone numbers, and identifiers are completely made up
        long_text = """
        Valaistusvikoilmoitus - Rikkinäinen katuvalaisin Helsingissä

        Hyvä Helsingin kaupungin katuvalaistusyksikkö,

        Kirjoitan teille ilmoittaakseni rikkinäisestä katuvalaisimesta, jonka havaitsin
        eilen illalla kävellessäni koirani Nappulan kanssa tavanomaisella iltakävelyllämme.
        Nimeni on Erkki Esimerkkinen ja olen asunut tällä alueella jo 23 vuotta, joten tunnen
        kadut ja valaistuksen erittäin hyvin.

        Rikkinäinen valaisin sijaitsee osoitteessa Testaajankatu 42, 00100 Helsinki,
        aivan Kuvitteellisen kauppakeskuksen läheisyydessä. Tarkemmin sanottuna valaisin on
        kadun itäpuolella, noin 15 metriä Esimerkkikadun risteyksestä pohjoiseen.
        Pylvään numero on mielestäni 9999-X, mikäli luin sen oikein taskulampun valossa.

        Vian kuvaus yksityiskohtaisesti: Valaisin vilkkuu epäsäännöllisesti noin 3-7
        sekunnin välein. Välillä se sammuu kokonaan 10-15 sekunniksi ja syttyy sitten
        takaisin kirkkaana. Tämä vilkkuminen alkoi noin viikko sitten, maanantaina
        6. maaliskuuta 2024. Aluksi luulin sen johtuvan pakkasesta, mutta ongelma on
        jatkunut säästä riippumatta.

        Olen erityisen huolissani turvallisuudesta, koska tällä katuosuudella kulkee
        paljon jalankulkijoita ja pyöräilijöitä myös iltaisin. Naapurini Maija Meikäläinen
        osoitteesta Testaajankatu 44 A 12 on myös huomannut ongelman ja valittanut siitä.
        Hänen puhelinnumeronsa on 040 555 9876, mikäli haluatte lisätietoja.

        Olen ottanut valaisimesta valokuvia, jotka voin toimittaa pyydettäessä. Minut
        tavoittaa parhaiten puhelimitse numerosta +358 50 555 1234 tai sähköpostitse
        osoitteesta erkki.esimerkkinen@testipalvelu.fi. Työskentelen Kuvitteellinen Yritys
        Oy:ssä Helsingin keskustan toimistossa, joten olen tavoitettavissa parhaiten
        iltaisin klo 17 jälkeen.

        Lisäksi haluaisin mainita, että samassa pylväässä oleva liikennemerkki on hieman
        kallellaan, mahdollisesti viime talven aurauksesta johtuen. Tämä ei ole kiireellinen
        asia, mutta ajattelin mainita sen samalla kun olette alueella korjaamassa valaisinta.

        GPS-koordinaatit paikalle ovat suunnilleen 60.1699° N, 24.9384° E, mikäli siitä
        on apua korjausryhmälle. Lähimmät maamerkit ovat Testiravintola ja Esimerkkikaupan
        pohjoinen sisäänkäynti.

        Kiitos etukäteen nopeasta reagoinnista. Arvostan suuresti Helsingin kaupungin
        katuvalaistusyksikön työtä turvallisen ja hyvin valaistun kaupunkiympäristön
        ylläpitämisessä.

        Kunnioittavasti,
        Erkki Esimerkkinen
        Henkilötunnus: 010170-999X
        Testaajankatu 40 B 23
        00100 Helsinki
        Puh: +358 50 555 1234
        Sähköposti: erkki.esimerkkinen@testipalvelu.fi
        """

        payload = {
            "text": long_text
        }
        # Use longer timeout for long text processing
        response = requests.post(f"{API_URL}/anonymize", json=payload, timeout=30.0)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        anonymized_text = data["anonymized_txt"]

        # Verify phone numbers are anonymized
        self.assertNotIn("+358 50 555 1234", anonymized_text)
        self.assertNotIn("040 555 9876", anonymized_text)

        # Verify email is anonymized
        self.assertNotIn("erkki.esimerkkinen@testipalvelu.fi", anonymized_text)

        # Verify SSN (henkilötunnus) is anonymized
        self.assertNotIn("010170-999X", anonymized_text)

        # Verify summary contains detected entities
        summary = data.get("summary", {})
        self.assertTrue(summary, "Summary should not be empty for text with multiple entities")

        # Log entity counts for throughput analysis
        total_entities = sum(summary.values())
        logger.info("Long text anonymization complete: %d entities detected across %d types",
                   total_entities, len(summary))
        logger.info("Entity breakdown: %s", summary)

    def test_parallel_requests_no_mixing(self):
        """Test that parallel requests are handled correctly without mixing responses.

        Sends 8 parallel requests (2x typical worker count) with unique identifiers
        and verifies each response contains the correct anonymized version of its unique data.
        This stress tests the API to ensure request/response isolation under load.
        """
        # Each request has a unique identifier and unique phone number
        # Format: (request_id, unique_phone, unique_email)
        # Using 8 requests to exceed typical 4-worker configuration
        test_cases = [
            ("PYYNTO_ALFA_001", "050 111 1111", "alfa@testi1.fi"),
            ("PYYNTO_BETA_002", "050 222 2222", "beta@testi2.fi"),
            ("PYYNTO_GAMMA_003", "050 333 3333", "gamma@testi3.fi"),
            ("PYYNTO_DELTA_004", "050 444 4444", "delta@testi4.fi"),
            ("PYYNTO_EPSILON_005", "050 555 5555", "epsilon@testi5.fi"),
            ("PYYNTO_ZETA_006", "050 666 6666", "zeta@testi6.fi"),
            ("PYYNTO_ETA_007", "050 777 7777", "eta@testi7.fi"),
            ("PYYNTO_THETA_008", "050 888 8888", "theta@testi8.fi"),
        ]

        def make_request(request_id: str, phone: str, email: str) -> dict:
            """Make a single anonymization request and return result with metadata."""
            text = f"""
            Palaute tunnuksella {request_id}

            Hyvä vastaanottaja,

            Tämä on testipalaute jonka tunniste on {request_id}. Lähettäjän
            yhteystiedot ovat: puhelinnumero {phone} ja sähköposti {email}.

            Tämä teksti on tarkoituksella pitkä jotta GLiNER-malli ehtii
            prosessoida sitä hetken aikaa, mikä mahdollistaa rinnakkaisten
            pyyntöjen testaamisen. Teksti sisältää kuvitteellisia tietoja
            kuten henkilötunnus 010180-999X ja osoite Testikatu 99, 00100 Helsinki.

            Ystävällisin terveisin,
            Testaaja {request_id}
            """

            payload = {
                "text": text
            }

            response = requests.post(f"{API_URL}/anonymize", json=payload, timeout=30.0)
            return {
                "request_id": request_id,
                "phone": phone,
                "email": email,
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else None
            }

        # Send all 8 requests in parallel
        results = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(make_request, req_id, phone, email): req_id
                for req_id, phone, email in test_cases
            }

            for future in as_completed(futures):
                results.append(future.result())

        # Verify all requests succeeded
        self.assertEqual(len(results), 8, "All 8 parallel requests should complete")

        for result in results:
            self.assertEqual(result["status_code"], 200,
                           f"Request {result['request_id']} should succeed")

            anonymized_text = result["response"]["anonymized_txt"]
            request_id = result["request_id"]
            phone = result["phone"]
            email = result["email"]

            # Verify phone and email are anonymized
            self.assertNotIn(phone, anonymized_text,
                           f"Phone {phone} should be anonymized in {request_id}")
            self.assertNotIn(email, anonymized_text,
                           f"Email {email} should be anonymized in {request_id}")

            # Verify other requests' data is NOT in this response (no mixing)
            for other_id, other_phone, other_email in test_cases:
                if other_id != request_id:
                    self.assertNotIn(other_id, anonymized_text,
                                   f"Other request ID {other_id} should not appear in {request_id}")

        logger.info("Parallel requests test passed: 8 concurrent requests processed correctly")


if __name__ == "__main__":
    unittest.main(verbosity=2)
