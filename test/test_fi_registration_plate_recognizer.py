import unittest

import test_data
from base_recoginizer_test import BaseRecognizerTest


class TestCarRecognizer(unittest.TestCase):
    """
    Test Finnish Vehicle Registration Plate (Rekisterikilpi) regex recognizer.
    Tests detection and anonymization of Finnish registration plate formats:
    - Car format: ABC-123
    - Motorcycle format: AB-123
    - Diplomat plates: CD-1234
    """

    def test_fi_rekisteri_regex(self):
        """Test Finnish vehicle registration plate regex pattern."""
        test_cases = test_data.test_register_number
        bad_cases = test_data.bad_register_number
        test_base = BaseRecognizerTest('fi_rekisteri_regex', test_cases, bad_cases)
        self.assertTrue(test_base.test_recognizer(), 'Finnish registration plate regex test failed.')


if __name__ == '__main__':
    unittest.main()