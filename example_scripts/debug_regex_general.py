#!/usr/bin/env python
"""
Debug script for General Regex Patterns - Email and Filenames.

This script mirrors test_regex_general_patterns.py with labeled test sections,
intermediate state output, and comprehensive positive/negative test cases.

Patterns tested:
  - email_regex: Email addresses
  - tiedosto_regex: Filename/attachment patterns

Usage:
    python debug_scripts/debug_regex_general.py              # Run all tests
    python debug_scripts/debug_regex_general.py --quick      # Run single example per pattern
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from debug_utils import (
    print_section_header, print_example_case, run_single_test,
    print_test_result, print_summary, load_test_data
)
from text_anonymizer import TextAnonymizer

# Load test data
test_data = load_test_data()


def test_email_regex():
    """TEST 1: Email Address Regex"""
    print_section_header(1, "Email Address Regex Pattern", 2)

    params = {
        'pattern_label': 'email_regex',
        'format': 'name@domain.extension'
    }
    print_example_case(
        "osoite@palvelin.fi",
        "Should detect email and anonymize"
    )

    test_cases = test_data['test_email']
    bad_cases = test_data['bad_email']

    anonymizer = TextAnonymizer()
    passed = 0
    total = 0

    print(f"\n{len(test_cases)} positive cases:")
    for text in test_cases:
        result = run_single_test(text, ['email_regex'], anonymizer, is_negative=False)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    print(f"\n{len(bad_cases)} negative cases:")
    for text in bad_cases:
        result = run_single_test(text, ['email_regex'], anonymizer, is_negative=True)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    return passed, total


def test_filename_regex():
    """TEST 2: Filename/Attachment Regex"""
    print_section_header(2, "Filename/Attachment Regex Pattern", 2)

    params = {
        'pattern_label': 'tiedosto_regex',
        'supported_formats': ['txt', 'doc', 'docx', 'xls', 'xlsx', 'pdf',
                              'jpg', 'jpeg', 'png', 'gif', 'ppt', 'pptx',
                              'zip', 'rar', 'csv']
    }
    print_example_case(
        "raimon_raportti.xls",
        "Should detect filename and anonymize"
    )

    test_cases = test_data['test_filenames']
    bad_cases = test_data['bad_filenames']

    anonymizer = TextAnonymizer()
    passed = 0
    total = 0

    print(f"\n{len(test_cases)} positive cases:")
    for text in test_cases:
        result = run_single_test(text, ['tiedosto_regex'], anonymizer, is_negative=False)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    print(f"\n{len(bad_cases)} negative cases:")
    for text in bad_cases:
        result = run_single_test(text, ['tiedosto_regex'], anonymizer, is_negative=True)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    return passed, total


def main():
    """Run all general regex pattern tests."""

    print("\n" + "="*80)
    print("GENERAL REGEX PATTERNS DEBUG SCRIPT")
    print("Patterns: Email, Filename")
    print("="*80)

    all_passed = 0
    all_total = 0

    # Run all tests
    tests = [
        test_email_regex,
        test_filename_regex,
    ]

    for test_func in tests:
        try:
            passed, total = test_func()
            all_passed += passed
            all_total += total
        except Exception as e:
            print(f"\n✗ ERROR in {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()

    print_summary(all_passed, all_total)


if __name__ == "__main__":
    main()

