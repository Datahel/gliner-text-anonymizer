import unittest

import test_data
from base_recoginizer_test import BaseRecognizerTest


class TestFiSpacyAddressRecognizer(unittest.TestCase):
    """
    Test Finnish Address NER recognizer using GLiNER.
    Tests detection and anonymization of Finnish addresses in various formats:
    - Simple addresses: Muoniontie 181, 90000 Kalavankoski
    - Complex addresses with postal codes: PL 1 (Pohjoisesplanadi 11-13), 00099 HELSINGIN KAUPUNKI
    - Multi-line addresses: Mannerheimintie 5 A\n00100 Helsinki
    - Organization names: VALSSIMYLLYNKATU 11
    """

    def test_address_ner(self):
        """Test address NER recognition."""
        test_cases = test_data.test_addresses
        bad_cases = test_data.bad_address
        test_base = BaseRecognizerTest('address_ner', test_cases, bad_cases)
        self.assertTrue(test_base.test_recognizer(), 'Address NER test failed.')


if __name__ == '__main__':
    unittest.main()
