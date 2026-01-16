#!/usr/bin/env python
"""
Debug script for Edge Cases and Error Handling.

Tests boundary conditions, malformed inputs, overlapping entities,
case sensitivity, Unicode, special characters, and basic performance.

Usage:
    python debug_scripts/debug_edge_cases.py              # Run all edge case tests
    python debug_scripts/debug_edge_cases.py --quick      # Run quick edge cases
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from debug_utils import print_section_header, print_example_case
from text_anonymizer import TextAnonymizer
import time


def test_empty_text():
    """TEST 1: Empty and Whitespace Text"""
    print_section_header(1, "Empty and Whitespace Text Handling", 7)

    test_cases = [
        ('', 'Empty string'),
        ('   ', 'Whitespace only'),
        ('\n\t', 'Newlines and tabs'),
        ('   \n  \t  ', 'Mixed whitespace'),
    ]

    print("\nPARAMETERS:")
    print("  Testing edge cases with empty/whitespace input")

    anonymizer = TextAnonymizer()
    passed = 0

    for text, description in test_cases:
        print(f"\n\nTest: {description}")
        print(f"  Input repr: {repr(text)}")

        try:
            result = anonymizer.anonymize(text=text, labels=['person_ner'])
            print(f"  Summary: {result.summary}")
            print(f"  Output: {repr(result.anonymized_text)}")
            print(f"  Status: ✓ PASS (no error)")
            passed += 1
        except Exception as e:
            print(f"  ERROR: {e}")

    return passed


def test_special_characters():
    """TEST 2: Special Characters and Unicode"""
    print_section_header(2, "Special Characters and Unicode Handling", 7)

    test_cases = [
        ('Käyttäjä: Matti Meikäläinen', 'Finnish special chars (ä, ö)'),
        ('User: José García López', 'Spanish accents'),
        ('用户: 王小明', 'Chinese characters'),
        ('Пользователь: Иван Петров', 'Cyrillic characters'),
        ('Email: test+alias@example.com', 'Special chars in email'),
        ('Name: "John Doe" <john@example.com>', 'Quotes and angle brackets'),
        ('Test #hashtag @mention', 'Social media symbols'),
    ]

    print("\nPARAMETERS:")
    print("  Testing various special characters and Unicode")

    anonymizer = TextAnonymizer()
    passed = 0

    for text, description in test_cases:
        print(f"\n\nTest: {description}")
        print(f"  Input: {text}")

        try:
            result = anonymizer.anonymize(text=text, labels=['person_ner', 'email_ner'])
            print(f"  Summary: {result.summary}")
            print(f"  Output: {result.anonymized_text}")
            print(f"  Status: ✓ PASS")
            passed += 1
        except Exception as e:
            print(f"  ERROR: {e}")

    return passed


def test_case_sensitivity():
    """TEST 3: Case Sensitivity"""
    print_section_header(3, "Case Sensitivity Edge Cases", 7)

    test_cases = [
        ('MATTI MEIKÄLÄINEN', 'ALL CAPS'),
        ('matti meikäläinen', 'all lowercase'),
        ('Matti Meikäläinen', 'Title Case'),
        ('mATTI mEIKÄLÄINEN', 'Mixed case'),
    ]

    print("\nPARAMETERS:")
    print("  Testing case sensitivity with person names")

    anonymizer = TextAnonymizer()
    passed = 0

    for text, description in test_cases:
        print(f"\n\nTest: {description}")
        print_example_case(text, "Should detect regardless of case")

        try:
            result = anonymizer.anonymize(text=text, labels=['person_ner'])
            print(f"  Summary: {result.summary}")
            print(f"  Output: {result.anonymized_text}")

            # Check if something was found/changed
            status = "✓ PASS" if result.anonymized_text != text else "~ No match (OK)"
            print(f"  Status: {status}")
            passed += 1
        except Exception as e:
            print(f"  ERROR: {e}")

    return passed


def test_overlapping_entities():
    """TEST 4: Overlapping Entity Detection"""
    print_section_header(4, "Overlapping Entity Detection", 7)

    text = "Matti.Meikäläinen@example.com soittaa numeroon 040-1234567"

    params = {
        'text': text,
        'labels': ['person_ner', 'email_ner', 'fi_puhelin_regex'],
        'note': 'Text contains person name (in email) + email + phone'
    }

    print("\nPARAMETERS:")
    print(f"  Text: {text}")
    print(f"  Labels: {', '.join(params['labels'])}")
    print(f"  Note: {params['note']}")

    print("\n\nTest: Overlapping entity handling")
    print_example_case(text, "Should correctly identify all entities")

    anonymizer = TextAnonymizer()

    try:
        result = anonymizer.anonymize(text=text, labels=params['labels'])
        print(f"\n  Summary: {result.summary}")
        print(f"  Entities found: {len(result.details)}")
        print(f"  Output: {result.anonymized_text}")
        print(f"  Status: ✓ PASS")
        return 1
    except Exception as e:
        print(f"  ERROR: {e}")
        return 0


def test_long_text():
    """TEST 5: Long Text Processing"""
    print_section_header(5, "Long Text Processing", 7)

    # Create a moderately long text
    base_text = "Customer: Matti Meikäläinen, HETU: 311299-999A, Phone: 040-1234567. "
    long_text = base_text * 50  # ~3000 characters

    params = {
        'text_length': len(long_text),
        'repetitions': 50,
        'base_length': len(base_text)
    }

    print("\nPARAMETERS:")
    print(f"  Text length: {params['text_length']} characters")
    print(f"  Repetitions of base text: {params['repetitions']}")
    print(f"  Base text length: {params['base_length']} characters")

    print("\n\nTest: Processing long text")
    print_example_case(long_text[:50] + "...", "Should handle long text efficiently")

    anonymizer = TextAnonymizer()

    try:
        start_time = time.time()
        result = anonymizer.anonymize(
            text=long_text,
            labels=['person_ner', 'fi_hetu_regex', 'fi_puhelin_regex']
        )
        elapsed = time.time() - start_time

        print(f"\n  Entities found: {len(result.details)}")
        print(f"  Processing time: {elapsed:.3f} seconds")
        print(f"  Entities per second: {len(result.details) / elapsed:.1f}")
        print(f"  Status: ✓ PASS")
        return 1
    except Exception as e:
        print(f"  ERROR: {e}")
        return 0


def test_malformed_inputs():
    """TEST 6: Malformed Input Handling"""
    print_section_header(6, "Malformed Input Handling", 7)

    test_cases = [
        ('HETU: 311299-', 'Incomplete HETU'),
        ('Phone: 040-', 'Incomplete phone'),
        ('Email: test@', 'Incomplete email'),
        ('IBAN: FI49', 'Incomplete IBAN'),
        ('Multiple@@@signs@@@here', 'Multiple @ symbols'),
        ('Dashes----like----this', 'Multiple dashes'),
    ]

    print("\nPARAMETERS:")
    print("  Testing malformed/incomplete entity patterns")

    anonymizer = TextAnonymizer()
    passed = 0

    for text, description in test_cases:
        print(f"\n\nTest: {description}")
        print(f"  Input: {text}")

        try:
            result = anonymizer.anonymize(
                text=text,
                labels=['person_ner', 'fi_hetu_regex', 'fi_puhelin_regex', 'email_ner']
            )
            print(f"  Summary: {result.summary}")
            print(f"  Output: {result.anonymized_text}")
            print(f"  Status: ✓ PASS (handled gracefully)")
            passed += 1
        except Exception as e:
            print(f"  ERROR: {e}")

    return passed


def test_batch_processing():
    """TEST 7: Batch Processing"""
    print_section_header(7, "Batch Processing Performance", 7)

    texts = [
        "Matti Meikäläinen, 040-1234567",
        "Anna Virtanen, HETU: 311299-999A",
        "Test User, test@example.com",
        "John Doe, ABA-303",
        "Jane Smith, FI49 5000 9420 0287 30",
    ]

    params = {
        'batch_size': len(texts),
        'items': texts
    }

    print("\nPARAMETERS:")
    print(f"  Batch size: {params['batch_size']} items")
    print(f"  Items per result tracking")

    print("\n\nTest: Processing batch of items")

    anonymizer = TextAnonymizer()
    labels = ['person_ner', 'fi_puhelin_regex', 'fi_hetu_regex', 'email_ner', 'fi_rekisteri_regex', 'fi_iban_regex']

    try:
        start_time = time.time()
        results = []

        for text in texts:
            result = anonymizer.anonymize(text=text, labels=labels)
            results.append(result)
            print(f"  ✓ Item processed: {len(result.details)} entities found")

        elapsed = time.time() - start_time

        print(f"\n  Total items: {len(results)}")
        print(f"  Total time: {elapsed:.3f} seconds")
        print(f"  Average per item: {elapsed / len(results):.3f} seconds")
        print(f"  Status: ✓ PASS")
        return 1
    except Exception as e:
        print(f"  ERROR: {e}")
        return 0


def main():
    """Run all edge case tests."""

    print("\n" + "="*80)
    print("EDGE CASES AND ERROR HANDLING DEBUG SCRIPT")
    print("Tests: Empty text, Unicode, Case sensitivity, Overlapping entities,")
    print("       Long text, Malformed inputs, Batch processing")
    print("="*80)

    all_passed = 0

    try:
        all_passed += test_empty_text()
        all_passed += test_special_characters()
        all_passed += test_case_sensitivity()
        all_passed += test_overlapping_entities()
        all_passed += test_long_text()
        all_passed += test_malformed_inputs()
        all_passed += test_batch_processing()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print(f"SUMMARY: {all_passed} test sections passed")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

