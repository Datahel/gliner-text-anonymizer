#!/usr/bin/env python
"""
Debug script for NER Core Detection - Person Names, Addresses, Locations, Emails.

This script mirrors test_ner_person_recognizer.py and test_ner_location_recognizer.py
with labeled test sections, intermediate state output, and both positive/negative cases.

Usage:
    python debug_scripts/debug_ner_core.py              # Run all tests
    python debug_scripts/debug_ner_core.py --quick      # Run single example per category
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


def test_person_ner_finnish():
    """TEST 1: Finnish Person Names NER Recognition"""
    print_section_header(1, "Finnish Person Names NER Recognition", 5)

    params = {
        'labels': ['person_ner'],
        'language': 'Finnish',
        'format': 'First Name + Last Name'
    }
    print_example_case("Matti Meikäläinen", "Should detect NIMI and anonymize")

    test_cases = test_data['test_names_fi'][:5]  # First 5 for quick run
    bad_cases = ["vieläkään", "esim"]

    anonymizer = TextAnonymizer()
    passed = 0
    total = 0

    print(f"\n{len(test_cases)} positive cases:")
    for text in test_cases:
        result = run_single_test(text, ['person_ner'], anonymizer, is_negative=False)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    print(f"\n{len(bad_cases)} negative cases:")
    for text in bad_cases:
        result = run_single_test(text, ['person_ner'], anonymizer, is_negative=True)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    return passed, total


def test_person_ner_english():
    """TEST 2: English Person Names NER Recognition"""
    print_section_header(2, "English Person Names NER Recognition", 5)

    params = {
        'labels': ['person_ner'],
        'language': 'English',
        'format': 'Various English name patterns'
    }
    print_example_case("Andrew Smith", "Should detect person name and anonymize")

    test_cases = test_data['test_names_en'][:5]  # First 5
    bad_cases = ["vieläkään", "esim"]

    anonymizer = TextAnonymizer()
    passed = 0
    total = 0

    print(f"\n{len(test_cases)} positive cases:")
    for text in test_cases:
        result = run_single_test(text, ['person_ner'], anonymizer, is_negative=False)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    print(f"\n{len(bad_cases)} negative cases:")
    for text in bad_cases:
        result = run_single_test(text, ['person_ner'], anonymizer, is_negative=True)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    return passed, total


def test_address_ner_finnish():
    """TEST 3: Finnish Address NER Recognition"""
    print_section_header(3, "Finnish Address NER Recognition", 5)

    params = {
        'labels': ['address_ner'],
        'language': 'Finnish',
        'format': 'Street name + number, postal code, city'
    }
    print_example_case(
        "Muoniontie 181, 90000 Kalavankoski",
        "Should detect address components and anonymize"
    )

    test_cases = test_data['test_addresses'][:5]
    bad_cases = test_data['bad_address'][:3]

    anonymizer = TextAnonymizer()
    passed = 0
    total = 0

    print(f"\n{len(test_cases)} positive cases:")
    for text in test_cases:
        result = run_single_test(text, ['address_ner'], anonymizer, is_negative=False)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    print(f"\n{len(bad_cases)} negative cases:")
    for text in bad_cases:
        result = run_single_test(text, ['address_ner'], anonymizer, is_negative=True)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    return passed, total


def test_location_ner_finnish():
    """TEST 4: Finnish Location/Street NER Recognition"""
    print_section_header(4, "Finnish Location/Street NER Recognition", 5)

    params = {
        'labels': ['location_ner'],
        'language': 'Finnish',
        'format': 'Street names'
    }
    print_example_case("Alppikatu", "Should detect location name and anonymize")

    test_cases = test_data['test_street'][:5]
    bad_cases = []

    anonymizer = TextAnonymizer()
    passed = 0
    total = 0

    print(f"\n{len(test_cases)} positive cases:")
    for text in test_cases:
        result = run_single_test(text, ['location_ner'], anonymizer, is_negative=False)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    return passed, total


def test_email_ner():
    """TEST 5: Email Address NER Recognition"""
    print_section_header(5, "Email Address NER Recognition", 5)

    params = {
        'labels': ['email_ner'],
        'format': 'Various email formats'
    }
    print_example_case(
        "Contact me at john@example.com",
        "Should detect email and anonymize"
    )

    test_cases = ["Contact: matti@example.com", "Email: test.user@company.co.uk"]
    bad_cases = ["Not an email @", "contact us"]

    anonymizer = TextAnonymizer()
    passed = 0
    total = 0

    print(f"\n{len(test_cases)} positive cases:")
    for text in test_cases:
        result = run_single_test(text, ['email_ner'], anonymizer, is_negative=False)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    print(f"\n{len(bad_cases)} negative cases:")
    for text in bad_cases:
        result = run_single_test(text, ['email_ner'], anonymizer, is_negative=True)
        print_test_result(result, show_details=False)
        if result['passed']:
            passed += 1
        total += 1

    return passed, total


def main():
    """Run all NER core detection tests."""

    print("\n" + "="*80)
    print("NER CORE DETECTION DEBUG SCRIPT")
    print("Tests: person_ner, address_ner, location_ner, email_ner")
    print("="*80)

    all_passed = 0
    all_total = 0

    # Run all tests
    tests = [
        test_person_ner_finnish,
        test_person_ner_english,
        test_address_ner_finnish,
        test_location_ner_finnish,
        test_email_ner,
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

