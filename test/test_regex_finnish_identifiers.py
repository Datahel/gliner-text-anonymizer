#!/usr/bin/env python
"""
Consolidated test for Finnish-specific regex identifiers.

This test combines individual regex recognizer tests for various Finnish identifiers:
- test_fi_phone_recognizer.py → test_fi_puhelin_regex
- test_fi_ssn_recognizer.py → test_fi_hetu_regex
- test_fi_iban_recognizer.py → test_fi_iban_regex
- test_fi_propertyid_recognizer.py → test_fi_kiinteisto_regex
- test_fi_registration_plate_recognizer.py → test_fi_rekisteri_regex

Tests detection and anonymization of Finnish identifiers using regex patterns.
"""

import unittest

import test_data
from base_recoginizer_test import BaseRecognizerTest


class TestFinnishPhoneRecognizer(unittest.TestCase):
    """Test Finnish phone number regex recognizer."""

    def test_fi_puhelin_regex(self):
        """Test Finnish phone number regex pattern.

        Formats tested:
        - Local format: 040-1234567, 09 123 4567
        - International format: +358401234567
        - Organization format: (09) 12345678
        """
        test_cases = test_data.test_phonenumbers_fi
        bad_cases = test_data.bad_phonenumbers
        test_base = BaseRecognizerTest('fi_puhelin_regex', test_cases, bad_cases)
        self.assertTrue(test_base.test_recognizer(), 'Finnish phone number regex test failed.')


class TestFinnishSSNRecognizer(unittest.TestCase):
    """Test Finnish Social Security Number (HETU) regex recognizer."""

    def test_fi_hetu_regex(self):
        """Test Finnish HETU (Social Security Number) regex pattern.

        Format: DDMMYY-XXXX
        """
        test_cases = test_data.test_ssn
        bad_cases = test_data.bad_ssn
        test_base = BaseRecognizerTest('fi_hetu_regex', test_cases, bad_cases)
        self.assertTrue(test_base.test_recognizer(), 'Finnish HETU regex test failed.')


class TestFinnishIBANRecognizer(unittest.TestCase):
    """Test Finnish IBAN regex recognizer."""

    def test_fi_iban_regex(self):
        """Test Finnish IBAN regex pattern.

        Formats tested:
        - With spaces: FI49 5000 9420 0287 30
        - Without spaces: FI4950009420028730
        """
        test_cases = test_data.test_iban
        bad_cases = test_data.bad_iban
        test_base = BaseRecognizerTest('fi_iban_regex', test_cases, bad_cases)
        self.assertTrue(test_base.test_recognizer(), 'Finnish IBAN regex test failed.')


class TestFinnishPropertyIDRecognizer(unittest.TestCase):
    """Test Finnish Real Property Identifier (Kiinteistötunnus) regex recognizer."""

    def test_fi_kiinteisto_regex(self):
        """Test Finnish property identifier regex pattern.

        Formats tested:
        - Basic format: 091-404-0001-0034 (municipality-district-block-unit)
        - Extended format: 091-404-0001-0034-M001
        """
        test_cases = test_data.test_property_identifier
        bad_cases = test_data.bad_property_identifier
        test_base = BaseRecognizerTest('fi_kiinteisto_regex', test_cases, bad_cases)
        self.assertTrue(test_base.test_recognizer(), 'Finnish property identifier regex test failed.')


class TestFinnishVehicleRegistrationRecognizer(unittest.TestCase):
    """Test Finnish Vehicle Registration Plate (Rekisterikilpi) regex recognizer."""

    def test_fi_rekisteri_regex(self):
        """Test Finnish vehicle registration plate regex pattern.

        Formats tested:
        - Car format: ABC-123
        - Motorcycle format: AB-123
        - Diplomat plates: CD-1234
        """
        test_cases = test_data.test_register_number
        bad_cases = test_data.bad_register_number
        test_base = BaseRecognizerTest('fi_rekisteri_regex', test_cases, bad_cases)
        self.assertTrue(test_base.test_recognizer(), 'Finnish registration plate regex test failed.')


if __name__ == '__main__':
    unittest.main()

