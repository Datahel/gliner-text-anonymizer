#!/usr/bin/env python
"""
Shared utilities for debug scripts.

Provides reusable functions for test output formatting, result comparison,
and standardized test execution across all debug scripts.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from text_anonymizer import TextAnonymizer
from typing import List, Dict, Any, Optional, Tuple


def print_section_header(section_num: int, section_name: str, total_sections: Optional[int] = None):
    """Print a formatted section header."""
    header = f"\n{'='*80}"
    if total_sections:
        header += f"\nTEST {section_num}/{total_sections}: {section_name}"
    else:
        header += f"\nTEST {section_num}: {section_name}"
    header += f"\n{'='*80}"
    print(header)


def print_test_parameters(params: Dict[str, Any]):
    """Print test parameters in concise format."""
    print("\nPARAMETERS:")
    for key, value in params.items():
        if isinstance(value, list) and len(value) > 0:
            print(f"  {key}: {value}")
        elif isinstance(value, (str, int, float, bool)):
            print(f"  {key}: {value}")


def print_example_case(text: str, expected_behavior: str = None):
    """Print example text and expected behavior."""
    print(f"\nEXAMPLE TEXT: {text}")
    if expected_behavior:
        print(f"EXPECTED: {expected_behavior}")


def run_single_test(
    text: str,
    labels: List[str],
    anonymizer: TextAnonymizer = None,
    test_name: str = "",
    is_negative: bool = False,
    **anonymize_kwargs
) -> Dict[str, Any]:
    """
    Run a single anonymization test and return results with intermediate state.

    Args:
        text: Text to anonymize
        labels: Labels to use for anonymization
        anonymizer: TextAnonymizer instance (created if None)
        test_name: Name of this test case
        is_negative: If True, expects NO entities to be found
        **anonymize_kwargs: Additional kwargs for anonymize() method

    Returns:
        Dict with results including: text, anonymized_text, summary, details,
        entities_found, text_changed, passed
    """
    if anonymizer is None:
        anonymizer = TextAnonymizer(debug_mode=False)

    result = anonymizer.anonymize(text=text, labels=labels, **anonymize_kwargs)

    entities_found = len(result.summary) > 0
    text_changed = result.anonymized_text != text

    if is_negative:
        # Negative test: should NOT find entities
        passed = not entities_found and not text_changed
    else:
        # Positive test: should find entities and anonymize
        passed = entities_found and text_changed and len(result.details) > 0

    return {
        'text': text,
        'anonymized_text': result.anonymized_text,
        'summary': result.summary,
        'details': result.details,
        'entities_found': entities_found,
        'text_changed': text_changed,
        'passed': passed,
        'test_name': test_name,
        'is_negative': is_negative
    }


def print_test_result(result: Dict[str, Any], show_details: bool = True):
    """
    Print formatted test result.

    Args:
        result: Result dict from run_single_test()
        show_details: If True, show details of found entities
    """
    status = "✓ PASS" if result['passed'] else "✗ FAIL"
    test_type = "NEGATIVE" if result['is_negative'] else "POSITIVE"

    print(f"\n{status} | {test_type} TEST")
    print(f"  Input:      {result['text']}")
    print(f"  Entities found: {result['entities_found']} | Text changed: {result['text_changed']}")
    print(f"  Output:     {result['anonymized_text']}")
    print(f"  Summary:    {result['summary']}")

    if show_details and result['details']:
        print(f"  Details:    {result['details']}")


def run_test_suite(
    test_cases: List[str],
    labels: List[str],
    anonymizer: TextAnonymizer = None,
    bad_cases: List[str] = None,
    print_results: bool = True
) -> Tuple[int, int]:
    """
    Run a suite of positive and negative test cases.

    Args:
        test_cases: List of positive test cases (should find entities)
        labels: Labels to use
        anonymizer: TextAnonymizer instance (created if None)
        bad_cases: List of negative test cases (should NOT find entities)
        print_results: If True, print results

    Returns:
        Tuple of (passed_count, total_count)
    """
    if anonymizer is None:
        anonymizer = TextAnonymizer(debug_mode=False)

    if bad_cases is None:
        bad_cases = []

    total = len(test_cases) + len(bad_cases)
    passed = 0

    print(f"\nRunning {len(test_cases)} positive cases...")
    for text in test_cases:
        result = run_single_test(text, labels, anonymizer, is_negative=False)
        if result['passed']:
            passed += 1
        if print_results:
            print_test_result(result, show_details=False)

    print(f"\nRunning {len(bad_cases)} negative cases...")
    for text in bad_cases:
        result = run_single_test(text, labels, anonymizer, is_negative=True)
        if result['passed']:
            passed += 1
        if print_results:
            print_test_result(result, show_details=False)

    return passed, total


def print_summary(passed: int, total: int):
    """Print test summary."""
    percentage = (passed / total * 100) if total > 0 else 0
    status = "✓ ALL PASS" if passed == total else "✗ SOME FAIL"

    print(f"\n{'='*80}")
    print(f"SUMMARY: {status}")
    print(f"  Passed: {passed}/{total} ({percentage:.1f}%)")
    print(f"{'='*80}\n")


def verify_config_files() -> Dict[str, bool]:
    """
    Verify that required configuration files exist and are readable.

    Returns:
        Dict with file path as key and True/False for existence
    """
    import os

    config_files = {
        'label_mappings': '/Users/manu/Projects/gliner-text-anonymizer/config/label_mappings.txt',
        'default_patterns': '/Users/manu/Projects/gliner-text-anonymizer/config/default/regex_patterns.txt',
        'example_patterns': '/Users/manu/Projects/gliner-text-anonymizer/config/example/regex_patterns.txt',
    }

    print("\n" + "="*80)
    print("CONFIG FILE VERIFICATION")
    print("="*80)

    results = {}
    for name, path in config_files.items():
        exists = os.path.exists(path)
        status = "✓" if exists else "✗"
        results[name] = exists
        print(f"{status} {name}: {path}")

    all_exist = all(results.values())
    print(f"\n{'✓ All config files found' if all_exist else '✗ Some config files missing'}")
    print("="*80 + "\n")

    return results


def load_test_data():
    """
    Load common test data from test module.

    Returns:
        Dict with all test data
    """
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'test'))

    try:
        import common_test_data as test_data
        return {
            'test_phonenumbers': test_data.test_phonenumbers,
            'test_phonenumbers_fi': test_data.test_phonenumbers_fi,
            'bad_phonenumbers': test_data.bad_phonenumbers,
            'test_names_fi': test_data.test_names_fi,
            'test_names_en': test_data.test_names_en,
            'test_register_number': test_data.test_register_number,
            'bad_register_number': test_data.bad_register_number,
            'test_property_identifier': test_data.test_property_identifier,
            'test_ssn': test_data.test_ssn,
            'bad_ssn': test_data.bad_ssn,
            'test_addresses': test_data.test_addresses,
            'test_street': test_data.test_street,
            'bad_address': test_data.bad_address,
            'test_email': test_data.test_email,
            'bad_email': test_data.bad_email,
            'test_iban': test_data.test_iban,
            'test_filenames': test_data.test_filenames,
            'bad_filenames': test_data.bad_filenames,
        }
    except ImportError as e:
        print(f"Error loading test data: {e}")
        return {}


if __name__ == "__main__":
    print("debug_utils.py - Utility functions for debug scripts")
    print("Import this module in other debug scripts to use helper functions")

