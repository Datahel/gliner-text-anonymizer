#!/usr/bin/env python
"""
Debug script for Finnish Regex Patterns - HETU, Phone, IBAN, Property ID, Registration Plate.

This script mirrors test_regex_finnish_identifiers.py with labeled test sections,
intermediate state output, and comprehensive positive/negative test cases.

Patterns tested:
  - fi_hetu_regex: Social Security Number (DDMMYY-XXXX)
  - fi_puhelin_regex: Phone numbers (040-1234567, +358 9 12345678, etc.)
  - fi_iban_regex: International Bank Account Number
  - fi_kiinteisto_regex: Real Property Identifier
  - fi_rekisteri_regex: Vehicle Registration Plate (ABC-123)

Usage:
    python debug_scripts/debug_regex_finnish.py              # Run all tests
    python debug_scripts/debug_regex_finnish.py --quick      # Run single example per pattern
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


def test_hetu_regex():
    """TEST 1: Finnish HETU (Social Security Number) Regex"""
    print_section_header(1, "Finnish HETU (SSN) Regex Pattern - DDMMYY-XXXX", 5)

    params = {
        'pattern_label': 'fi_hetu_regex',
        'format': 'DDMMYY-XXXX (century marker: -, +, or A)',
        'examples': '311299-999A, 150320-, 080320A242K'
    }
    print_example_case("311299-999A", "Should detect HETU and anonymize to <HETU>")

    test_cases = test_data['test_ssn']
    bad_cases = test_data['bad_ssn']

    anonymizer = TextAnonymizer()
    passed = 0
    total = 0

    print(f"\n{len(test_cases)} positive cases:")
    for text in test_cases[:5]:  # Show first 5
        result = run_single_test(text, ['fi_hetu_regex'], anonymizer, is_negative=False)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    print(f"\n{len(bad_cases)} negative cases:")
    for text in bad_cases[:3]:  # Show first 3
        result = run_single_test(text, ['fi_hetu_regex'], anonymizer, is_negative=True)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    return passed, total


def test_phone_regex():
    """TEST 2: Finnish Phone Number Regex"""
    print_section_header(2, "Finnish Phone Number Regex Pattern", 5)

    params = {
        'pattern_label': 'fi_puhelin_regex',
        'formats': ['Local: 040-1234567, 09 123 4567',
                    'Intl: +358401234567, +358 9 123 4567',
                    'Org: (09) 12345678']
    }
    print_example_case("040-1234567", "Should detect phone number and anonymize")

    test_cases = test_data['test_phonenumbers_fi']
    bad_cases = test_data['bad_phonenumbers']

    anonymizer = TextAnonymizer()
    passed = 0
    total = 0

    print(f"\n{len(test_cases)} positive cases:")
    for text in test_cases:
        result = run_single_test(text, ['fi_puhelin_regex'], anonymizer, is_negative=False)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    print(f"\n{len(bad_cases)} negative cases:")
    for text in bad_cases[:5]:
        result = run_single_test(text, ['fi_puhelin_regex'], anonymizer, is_negative=True)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    return passed, total


def test_iban_regex():
    """TEST 3: Finnish IBAN Regex"""
    print_section_header(3, "Finnish IBAN Regex Pattern", 5)

    params = {
        'pattern_label': 'fi_iban_regex',
        'formats': ['With spaces: FI49 5000 9420 0287 30',
                    'No spaces: FI4950009420028730']
    }
    print_example_case(
        "FI49 5000 9420 0287 30",
        "Should detect IBAN and anonymize"
    )

    test_cases = test_data['test_iban']
    bad_cases = test_data['bad_email'][:2]  # Using email as bad IBAN

    anonymizer = TextAnonymizer()
    passed = 0
    total = 0

    print(f"\n{len(test_cases)} positive cases:")
    for text in test_cases:
        result = run_single_test(text, ['fi_iban_regex'], anonymizer, is_negative=False)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    print(f"\n{len(bad_cases)} negative cases:")
    for text in bad_cases:
        result = run_single_test(text, ['fi_iban_regex'], anonymizer, is_negative=True)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    return passed, total


def test_property_id_regex():
    """TEST 4: Finnish Real Property Identifier Regex"""
    print_section_header(4, "Finnish Property ID Regex Pattern", 5)

    params = {
        'pattern_label': 'fi_kiinteisto_regex',
        'format': 'municipality-district-block-unit[-section]',
        'examples': '091-404-0001-0034, 1-1-1-1'
    }
    print_example_case(
        "091-404-0001-0034",
        "Should detect property identifier"
    )

    test_cases = test_data['test_property_identifier'][:8]  # First 8
    bad_cases = []

    anonymizer = TextAnonymizer()
    passed = 0
    total = 0

    print(f"\n{len(test_cases)} positive cases:")
    for text in test_cases:
        result = run_single_test(text, ['fi_kiinteisto_regex'], anonymizer, is_negative=False)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    return passed, total


def test_registration_plate_regex():
    """TEST 5: Finnish Vehicle Registration Plate Regex"""
    print_section_header(5, "Finnish Registration Plate Regex Pattern", 5)

    params = {
        'pattern_label': 'fi_rekisteri_regex',
        'formats': ['Car: ABC-123',
                    'Motorcycle: AB-123',
                    'Diplomat: CD-1234']
    }
    print_example_case(
        "ABA-303",
        "Should detect vehicle registration plate"
    )

    test_cases = test_data['test_register_number']
    bad_cases = test_data['bad_register_number']

    anonymizer = TextAnonymizer()
    passed = 0
    total = 0

    print(f"\n{len(test_cases)} positive cases:")
    for text in test_cases:
        result = run_single_test(text, ['fi_rekisteri_regex'], anonymizer, is_negative=False)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    print(f"\n{len(bad_cases)} negative cases:")
    for text in bad_cases:
        result = run_single_test(text, ['fi_rekisteri_regex'], anonymizer, is_negative=True)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    return passed, total


def main():
    """Run all Finnish regex pattern tests."""

    print("\n" + "="*80)
    print("FINNISH REGEX PATTERNS DEBUG SCRIPT")
    print("Patterns: HETU, Phone, IBAN, Property ID, Registration Plate")
    print("="*80)

    all_passed = 0
    all_total = 0

    # Run all tests
    tests = [
        test_hetu_regex,
        test_phone_regex,
        test_iban_regex,
        test_property_id_regex,
        test_registration_plate_regex,
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

