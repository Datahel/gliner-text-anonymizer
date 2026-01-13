import unittest

import test_data
from base_recoginizer_test import BaseRecognizerTest


class TestFileRecognizer(unittest.TestCase):
    """
    Test Filename/Attachment regex recognizer.
    Tests detection and anonymization of filenames and URLs with common extensions:
    - Local files: raimon_raportti.xls, document.pdf
    - URL files: https://example.com/file.pdf
    - Supported formats: txt, doc, docx, xls, xlsx, pdf, jpg, jpeg, png, gif, ppt, pptx, zip, rar, csv
    """

    def test_tiedosto_regex(self):
        """Test filename/attachment regex pattern."""
        test_cases = test_data.test_filenames
        bad_cases = test_data.bad_filenames
        test_base = BaseRecognizerTest('tiedosto_regex', test_cases, bad_cases)
        self.assertTrue(test_base.test_recognizer(), 'Filename regex test failed.')


if __name__ == '__main__':
    unittest.main()