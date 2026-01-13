import unittest

import test_data
from base_recoginizer_test import BaseRecognizerTest


class TestSSNRecognizer(unittest.TestCase):
    """
    Test Finnish Social Security Number (HETU) regex recognizer.
    Tests detection and anonymization of Finnish SSN format: DDMMYY-XXXX
    """

    def test_fi_hetu_regex(self):
        """Test Finnish HETU (Social Security Number) regex pattern."""
        test_cases = test_data.test_ssn
        bad_cases = test_data.bad_ssn
        test_base = BaseRecognizerTest('fi_hetu_regex', test_cases, bad_cases)
        self.assertTrue(test_base.test_recognizer(), 'Finnish HETU regex test failed.')


if __name__ == '__main__':
    unittest.main()