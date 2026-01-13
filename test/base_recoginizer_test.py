from typing import List
from text_anonymizer import TextAnonymizer
'''
Base test class for testing single recognizer
Pass recognizer object and test strings as constructor parameters
'''


class BaseRecognizerTest():

    def __init__(self, regex_label, test_cases: List[str], bad_test_cases: List[str] = None):
        self.test_cases = test_cases
        self.bad_test_cases = bad_test_cases if bad_test_cases is not None else []
        self.anonymizer = TextAnonymizer(debug_mode=False)
        self.regex_label = regex_label

    # ...existing code...

    def test_recognizer(self):
        """
        Test recognizer by:
        1. Verifying entities are detected in positive test cases
        2. Verifying entities are anonymized in the output
        3. Verifying no entities are detected in negative test cases
        """
        test_pass = True

        # 1. Testing Positive Cases - Should find and anonymize entities
        for text in self.test_cases:
            current_test_pass = False
            res = self.anonymizer.anonymize(text=text, labels=[self.regex_label])

            # Check if entities were found
            entities_found = False
            if len(res.statistics) > 0:
                entities_found = True

            # Check if text was anonymized (changed from original)
            text_anonymized = res.anonymized_text != text and res.anonymized_text is not None

            # Check if details contain recognized entities
            details_exist = len(res.details) > 0

            # Test passes if entities were found AND text was anonymized
            current_test_pass = entities_found and text_anonymized and details_exist

            print(f'Positive test: "{text}"')
            print(f'  - Entities found: {entities_found} (statistics: {res.statistics})')
            print(f'  - Text anonymized: {text_anonymized}')
            print(f'    Original: "{text}"')
            print(f'    Anonymized: "{res.anonymized_text}"')
            print(f'  - Details populated: {details_exist} (details: {res.details})')
            print(f'  - Pass: {current_test_pass}')

            if not current_test_pass:
                test_pass = False

        # 2. Testing Negative Cases - Should NOT find entities
        for text in self.bad_test_cases:
            current_test_pass = True
            res = self.anonymizer.anonymize(text=text, labels=[self.regex_label])

            # Check that no entities are detected for this specific label
            entities_detected = len(res.statistics) > 0

            # Text should remain unchanged if no entities found
            text_unchanged = res.anonymized_text == text

            current_test_pass = not entities_detected and text_unchanged

            print(f'Negative test: "{text}"')
            print(f'  - No entities detected: {not entities_detected} (statistics: {res.statistics})')
            print(f'  - Text unchanged: {text_unchanged}')
            print(f'  - Pass: {current_test_pass}')

            if not current_test_pass:
                test_pass = False

        return test_pass

