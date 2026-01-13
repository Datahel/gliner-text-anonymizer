import unittest

import test_data
from base_recoginizer_test import BaseRecognizerTest


class TestFiSpacyLocationRecognizer(unittest.TestCase):
    """
    Test Finnish Location/Street NER recognizer using GLiNER.
    Tests detection and anonymization of Finnish street names and locations:
    - Street names: Alppikatu, Ahjokuja, Ahmatie
    - Major streets: Mannerheimintie
    """

    def test_location_ner(self):
        """Test location/street NER recognition."""
        test_cases = test_data.test_street
        test_base = BaseRecognizerTest('location_ner', test_cases)
        self.assertTrue(test_base.test_recognizer(), 'Location NER test failed.')


if __name__ == '__main__':
    unittest.main()