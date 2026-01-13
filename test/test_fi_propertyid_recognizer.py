import unittest

import test_data
from base_recoginizer_test import BaseRecognizerTest


class TestPropertyIDRecognizer(unittest.TestCase):
    """
    Test Finnish Real Property Identifier (Kiinteistötunnus) regex recognizer.
    Tests detection and anonymization of Finnish property ID format:
    - Basic format: 091-404-0001-0034 (municipality-district-block-unit)
    - Extended format: 091-404-0001-0034-M001
    """

    def test_fi_kiinteisto_regex(self):
        """Test Finnish property identifier regex pattern."""
        test_cases = test_data.test_property_identifier
        bad_cases = test_data.bad_property_identifier
        test_base = BaseRecognizerTest('fi_kiinteisto_regex', test_cases, bad_cases)
        self.assertTrue(test_base.test_recognizer(), 'Finnish property identifier regex test failed.')


if __name__ == '__main__':
    unittest.main()