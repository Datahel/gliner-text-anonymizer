#!/usr/bin/env python
"""
Consolidated test for Location/Address NER recognizer.

This test combines:
- Finnish Address NER (test_fi_spacy_address_recognizer.py)
- Finnish Location/Street NER (test_fi_spacy_loc_recognizer.py)

Tests detection and anonymization of addresses and street names using GLiNER NER:
- Addresses: Muoniontie 181, 90000 Kalavankoski, Mannerheimintie 5 A
- Streets: Alppikatu, Ahjokuja, Ahmatie, Mannerheimintie
"""

import unittest

import test_data
from base_recoginizer_test import BaseRecognizerTest


class TestAddressNERFinnish(unittest.TestCase):
    """Test Finnish Address NER recognizer."""

    def test_address_ner_finnish(self):
        """Test Finnish address NER recognition."""
        test_cases = test_data.test_addresses
        bad_cases = test_data.bad_address
        test_base = BaseRecognizerTest('address_ner', test_cases, bad_cases)
        self.assertTrue(test_base.test_recognizer(), 'Finnish address NER test failed.')


class TestLocationNERFinnish(unittest.TestCase):
    """Test Finnish Location/Street NER recognizer."""

    def test_location_ner_finnish(self):
        """Test Finnish location/street NER recognition."""
        test_cases = test_data.test_street
        test_base = BaseRecognizerTest('location_ner', test_cases)
        self.assertTrue(test_base.test_recognizer(), 'Finnish location NER test failed.')


if __name__ == '__main__':
    unittest.main()

