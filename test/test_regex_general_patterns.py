#!/usr/bin/env python
"""
Consolidated test for general (language-independent) regex patterns.

This test combines:
- test_fi_email_regex.py → email_regex
- test_file_recognizer.py → tiedosto_regex

Tests detection and anonymization of general patterns using regex.
"""

import unittest

from common_test_data import test_email, bad_email, test_filenames, bad_filenames
from common_regex_test_base import BaseRegexTest


class TestEmailRecognizer(unittest.TestCase):
    """Test email regex recognizer."""

    def test_email_regex(self):
        """Test email regex pattern."""
        test_cases = test_email
        bad_cases = bad_email
        test_base = BaseRegexTest('email_regex', test_cases, bad_cases)
        self.assertTrue(test_base.test_recognizer(), 'Email regex test failed.')


class TestFilenameRecognizer(unittest.TestCase):
    """Test filename/attachment regex recognizer."""

    def test_tiedosto_regex(self):
        """Test filename/attachment regex pattern.

        Supported formats: txt, doc, docx, xls, xlsx, pdf, jpg, jpeg, png, gif, ppt, pptx, zip, rar, csv
        """
        test_cases = test_filenames
        bad_cases = bad_filenames
        test_base = BaseRegexTest('tiedosto_regex', test_cases, bad_cases)
        self.assertTrue(test_base.test_recognizer(), 'Filename regex test failed.')


if __name__ == '__main__':
    unittest.main()

