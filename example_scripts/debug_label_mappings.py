#!/usr/bin/env python
"""
Debug script for Label Mapping Verification.

This script verifies and displays label mapping behavior:
  - Loads label mappings from config/label_mappings.txt
  - Shows internal → output label transformations
  - Tests mapping functionality with real examples
  - Verifies correct label names appear in results

Usage:
    python debug_scripts/debug_label_mappings.py              # Full verification
    python debug_scripts/debug_label_mappings.py --quick      # Quick check
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from debug_utils import print_section_header, print_example_case
from text_anonymizer import TextAnonymizer
from text_anonymizer.config_cache import ConfigCache


def test_label_mappings_loaded():
    """TEST 1: Verify Label Mappings are Loaded"""
    print_section_header(1, "Label Mappings File Verification", 4)

    print("\nPARAMETERS:")
    print("  File: config/label_mappings.txt")
    print("  Expected: Mapping file with internal→output label pairs")

    config_cache = ConfigCache()
    mappings = config_cache.get_label_mappings()

    print(f"\n✓ Label mappings loaded: {len(mappings)} mappings found")

    print("\n\nMAPPINGS:")
    print("-" * 60)
    for internal_label, output_label in sorted(mappings.items()):
        print(f"  {internal_label:30} → {output_label}")
    print("-" * 60)

    status = "✓ PASS" if len(mappings) > 0 else "✗ FAIL"
    print(f"\nStatus: {status} (Found {len(mappings)} mappings)")

    return 1 if len(mappings) > 0 else 0


def test_person_ner_mapping():
    """TEST 2: Test person_ner → NIMI Mapping"""
    print_section_header(2, "Person NER → NIMI Mapping", 4)

    text = "Matti Meikäläinen asuu Helsingissä"

    params = {
        'text': text,
        'internal_label': 'person_ner',
        'expected_output': 'NIMI'
    }

    print("\nPARAMETERS:")
    print(f"  Text: {text}")
    print(f"  Input label: {params['internal_label']}")
    print(f"  Expected output label: {params['expected_output']}")

    anonymizer = TextAnonymizer()

    print("\n\nTest: Anonymizing with person_ner label")
    print_example_case(text, "Should map to NIMI in output")

    result = anonymizer.anonymize(text=text, labels=['person_ner'])

    print(f"\n  Raw summary: {result.summary}")
    print(f"  Output text: {result.anonymized_text}")

    has_nimi = 'NIMI' in result.summary
    no_person = 'PERSON' not in result.summary

    print(f"\n  Contains 'NIMI': {has_nimi}")
    print(f"  Does NOT contain 'PERSON': {no_person}")

    status = "✓ PASS" if (has_nimi and no_person) else "✗ FAIL"
    print(f"  Status: {status}")

    return 1 if (has_nimi and no_person) else 0


def test_phone_number_mapping():
    """TEST 3: Test phone_number_ner → PUHELIN Mapping"""
    print_section_header(3, "Phone Number NER → PUHELIN Mapping", 4)

    text = "Soita numeroon 040-1234567"

    params = {
        'text': text,
        'internal_label': 'phone_number_ner',
        'expected_output': 'PUHELIN'
    }

    print("\nPARAMETERS:")
    print(f"  Text: {text}")
    print(f"  Input label: {params['internal_label']}")
    print(f"  Expected output label: {params['expected_output']}")

    anonymizer = TextAnonymizer()

    print("\n\nTest: Anonymizing with phone_number_ner label")
    print_example_case(text, "Should map to PUHELIN in output")

    result = anonymizer.anonymize(text=text, labels=['phone_number_ner'])

    print(f"\n  Raw summary: {result.summary}")
    print(f"  Output text: {result.anonymized_text}")

    has_puhelin = 'PUHELIN' in result.summary
    no_phone_number = 'PHONE_NUMBER' not in result.summary

    print(f"\n  Contains 'PUHELIN': {has_puhelin}")
    print(f"  Does NOT contain 'PHONE_NUMBER': {no_phone_number}")

    status = "✓ PASS" if (has_puhelin and no_phone_number) else "✗ FAIL"
    print(f"  Status: {status}")

    return 1 if (has_puhelin and no_phone_number) else 0


def test_regex_label_mapping():
    """TEST 4: Test Regex Label Mappings (fi_hetu_regex, etc.)"""
    print_section_header(4, "Regex Label Mappings", 4)

    test_cases = [
        {
            'text': 'HETU: 311299-999A',
            'label': 'fi_hetu_regex',
            'expected': 'HETU'
        },
        {
            'text': 'Rekisteri: ABA-303',
            'label': 'fi_rekisteri_regex',
            'expected': 'REKISTERI'
        },
        {
            'text': 'IBAN: FI49 5000 9420 0287 30',
            'label': 'fi_iban_regex',
            'expected': 'IBAN'
        },
    ]

    print("\nPARAMETERS:")
    print("  Testing regex label mappings:")
    for case in test_cases:
        print(f"    {case['label']} → {case['expected']}")

    anonymizer = TextAnonymizer()
    passed = 0

    for i, case in enumerate(test_cases, 1):
        print(f"\n\nTest 4.{i}: {case['label']} mapping")
        print_example_case(case['text'], f"Should map to {case['expected']}")

        result = anonymizer.anonymize(text=case['text'], labels=[case['label']])

        print(f"  Summary: {result.summary}")
        print(f"  Output: {result.anonymized_text}")

        has_expected = case['expected'] in result.summary
        print(f"  Contains '{case['expected']}': {has_expected}")

        status = "✓ PASS" if has_expected else "✗ FAIL"
        print(f"  Status: {status}")

        if has_expected:
            passed += 1

    return passed


def test_default_profile_mappings():
    """TEST 5: Verify Default Profile Uses Correct Mappings"""
    print_section_header(5, "Default Profile Label Mappings", 4)

    text = """
    Asiakas: Matti Meikäläinen
    HETU: 311299-999A
    Puhelin: 040-1234567
    Sähköposti: matti@example.com
    """

    params = {
        'text': 'Customer record',
        'profile': 'default',
        'expected_labels': ['NIMI', 'HETU', 'PUHELIN', 'SÄHKÖPOSTI']
    }

    print("\nPARAMETERS:")
    print(f"  Profile: {params['profile']}")
    print(f"  Expected output labels: {', '.join(params['expected_labels'])}")

    anonymizer = TextAnonymizer()

    print("\n\nTest: Using default profile")
    print_example_case(text.strip()[:50] + "...",
                       "Should use mapped labels from default profile")

    result = anonymizer.anonymize(text=text, profile='default')

    print(f"\n  Summary: {result.summary}")
    print(f"  Output preview: {result.anonymized_text[:100]}...")

    # Check if we have the expected labels
    found_labels = []
    for label in params['expected_labels']:
        if label in result.summary:
            found_labels.append(label)

    print(f"\n  Expected labels: {', '.join(params['expected_labels'])}")
    print(f"  Found labels: {', '.join(found_labels)}")
    print(f"  Coverage: {len(found_labels)}/{len(params['expected_labels'])}")

    # Status: pass if at least some expected labels found
    passed = len(found_labels) > 0
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  Status: {status}")

    return 1 if passed else 0


def main():
    """Run all label mapping verification tests."""

    print("\n" + "="*80)
    print("LABEL MAPPING VERIFICATION DEBUG SCRIPT")
    print("Verifies internal→output label mapping from config/label_mappings.txt")
    print("="*80)

    all_passed = 0

    try:
        all_passed += test_label_mappings_loaded()
        all_passed += test_person_ner_mapping()
        all_passed += test_phone_number_mapping()
        all_passed += test_regex_label_mapping()
        all_passed += test_default_profile_mappings()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print(f"SUMMARY: {all_passed} test sections passed")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

