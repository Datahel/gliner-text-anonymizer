import unittest

import test_data
from base_recoginizer_test import BaseRecognizerTest

# TODO: THIS SHOULD BE TEST PERSON NER FI
class TestFiSpacyRecognizer(unittest.TestCase):
    """
    Test Finnish Person Name NER recognizer using GLiNER.
    Tests detection and anonymization of Finnish person names:
    - Simple names: Maija Mehiläinen, Silja Laine
    - Complex names: Marja Mustikkamäki, Mary Johnson-Smith
    - Single names: Virtanen, Keijo
    """

    def test_person_ner(self):
        """Test person name NER recognition."""
        test_cases = test_data.test_names_fi
        test_base = BaseRecognizerTest('person_ner', test_cases)
        self.assertTrue(test_base.test_recognizer(), 'Person NER test failed.')


if __name__ == '__main__':
    unittest.main()