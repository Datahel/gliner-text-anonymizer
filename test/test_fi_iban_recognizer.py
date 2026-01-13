import unittest

import test_data
from base_recoginizer_test import BaseRecognizerTest


class TestIBANRecognizer(unittest.TestCase):
    """
    Test Finnish IBAN regex recognizer.
    Tests detection and anonymization of Finnish IBAN format:
    - With spaces: FI49 5000 9420 0287 30
    - Without spaces: FI4950009420028730
    """

    def test_fi_iban_regex(self):
        """Test Finnish IBAN regex pattern."""
        test_cases = test_data.test_iban
        bad_cases = test_data.bad_iban
        test_base = BaseRecognizerTest('fi_iban_regex', test_cases, bad_cases)
        self.assertTrue(test_base.test_recognizer(), 'Finnish IBAN regex test failed.')


if __name__ == '__main__':
    unittest.main()