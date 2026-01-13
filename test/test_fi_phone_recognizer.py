import unittest

import test_data
from base_recoginizer_test import BaseRecognizerTest


class TestPhoneRecognizer(unittest.TestCase):
    """
    Test Finnish phone number regex recognizer.
    Tests detection and anonymization of Finnish phone numbers in various formats:
    - Local format: 040-1234567, 09 123 4567
    - International format: +358401234567
    - Organization format: (09) 12345678
    """

    def test_fi_puhelin_regex(self):
        """Test Finnish phone number regex pattern."""
        test_cases = test_data.test_phonenumbers_fi
        bad_cases = test_data.bad_phonenumbers
        test_base = BaseRecognizerTest('fi_puhelin_regex', test_cases, bad_cases)
        self.assertTrue(test_base.test_recognizer(), 'Finnish phone number regex test failed.')


if __name__ == '__main__':
    unittest.main()