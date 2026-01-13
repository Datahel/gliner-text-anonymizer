import unittest

import test_data
from base_recoginizer_test import BaseRecognizerTest


class TestEnSpacyRecognizer(unittest.TestCase):
    """
    Test English Person Name NER recognizer using GLiNER.
    Tests detection and anonymization of English person names:
    - Simple names: Andrew Smith, John Doe
    - Complex names: Mary Johnson-Smith, Jerome K. Jerome
    - International names: Zhao Lê, Anna K. Jerome
    """

    def test_person_ner(self):
        """Test person name NER recognition for English."""
        test_cases = test_data.test_names_en
        test_base = BaseRecognizerTest('person_ner', test_cases)
        self.assertTrue(test_base.test_recognizer(), 'English person NER test failed.')


if __name__ == '__main__':
    unittest.main()