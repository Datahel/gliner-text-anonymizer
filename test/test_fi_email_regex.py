import unittest

import test_data
from base_recoginizer_test import BaseRecognizerTest


class TestEmailRegex(unittest.TestCase):
    '''
    Refactored regex test case.
    '''
    def test_self(self):

        test_cases = test_data.test_email
        bad_cases = test_data.bad_email
        test_base = BaseRecognizerTest('email_regex', test_cases, bad_cases)
        self.assertTrue(test_base.test_recognizer(), 'Recognizer self test failed.')


if __name__ == '__main__':
    unittest.main()