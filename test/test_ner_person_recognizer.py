#!/usr/bin/env python
"""
Consolidated test for Person Name NER recognizer across multiple languages.

This test combines:
- Finnish person names (test_fi_spacy_recognizer.py)
- English person names (test_en_spacy_recognizer.py)

Tests detection and anonymization of person names using GLiNER NER:
- Finnish: Maija Mehiläinen, Silja Laine, Marja Mustikkamäki
- English: Andrew Smith, John Doe, Mary Johnson-Smith
- International: Zhao Lê, Jerome K. Jerome
"""

import unittest

import test_data
from base_recoginizer_test import BaseRecognizerTest


class TestPersonNERFinnish(unittest.TestCase):
    """Test Finnish Person Name NER recognizer."""

    def test_person_ner_finnish(self):
        """Test Finnish person name NER recognition."""
        test_cases = test_data.test_names_fi
        test_base = BaseRecognizerTest('person_ner', test_cases)
        self.assertTrue(test_base.test_recognizer(), 'Finnish person NER test failed.')


class TestPersonNEREnglish(unittest.TestCase):
    """Test English Person Name NER recognizer."""

    def test_person_ner_english(self):
        """Test English person name NER recognition."""
        test_cases = test_data.test_names_en
        test_base = BaseRecognizerTest('person_ner', test_cases)
        self.assertTrue(test_base.test_recognizer(), 'English person NER test failed.')


if __name__ == '__main__':
    unittest.main()

