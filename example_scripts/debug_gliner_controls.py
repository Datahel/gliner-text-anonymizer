#!/usr/bin/env python
"""
Debug script for GLiNER Controls - Labels, Thresholds, Configurations, and Controls.

This script mirrors test_ner_gliner_controls.py with detailed testing of:
  - Label parameter control
  - GLiNER threshold adjustments
  - Underscore-to-space label conversion
  - Multi-word label handling
  - Regex pattern detection with profiles
  - Blocklist/grantlist protection
  - Config cache loading verification
  - Combined controls (full pipeline)

Usage:
    python debug_scripts/debug_gliner_controls.py              # Run all tests
    python debug_scripts/debug_gliner_controls.py --quick      # Run quick tests
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from debug_utils import print_section_header, print_example_case, print_test_result
from text_anonymizer import TextAnonymizer


def test_labels_parameter():
    """TEST 1: Labels Parameter Control"""
    print_section_header(1, "Labels Parameter Control", 6)

    params = {
        'text': "Matti Meikäläinen (matti@example.com) puhelin: 040-1234567",
        'test1': "labels=['person_ner']",
        'test2': "labels=['person_ner', 'email_ner']",
        'test3': "labels=['person_ner', 'email_ner', 'fi_puhelin_regex']"
    }

    print("\nPARAMETERS:")
    print(f"  Text: {params['text']}")
    print("\nVARIATIONS:")
    for key, val in params.items():
        if key != 'text':
            print(f"  {key}: {val}")

    anonymizer = TextAnonymizer()

    # Test 1: Only person
    print("\n\nTest 1a: Only person_ner label")
    print_example_case(params['text'], "Should detect only person, not email/phone")
    result1 = anonymizer.anonymize(
        text=params['text'],
        labels=['person_ner']
    )
    print(f"  Summary: {result1.summary}")
    print(f"  Output: {result1.anonymized_text}")
    print(f"  Status: {'✓ PASS' if 'NIMI' in result1.summary or 'PERSON' in result1.summary else '✗ FAIL'}")

    # Test 1b: Person + Email
    print("\n\nTest 1b: person_ner + email_ner labels")
    print_example_case(params['text'], "Should detect person and email")
    result2 = anonymizer.anonymize(
        text=params['text'],
        labels=['person_ner', 'email_ner']
    )
    print(f"  Summary: {result2.summary}")
    print(f"  Output: {result2.anonymized_text}")
    has_person = 'NIMI' in result2.summary or 'PERSON' in result2.summary
    has_email = 'EMAIL' in result2.summary or 'SÄHKÖPOSTI' in result2.summary
    print(f"  Status: {'✓ PASS' if has_person and has_email else '✗ FAIL'}")

    # Test 1c: Person + Email + Phone
    print("\n\nTest 1c: Multiple labels (person, email, phone)")
    print_example_case(params['text'], "Should detect all three entity types")
    result3 = anonymizer.anonymize(
        text=params['text'],
        labels=['person_ner', 'email_ner', 'fi_puhelin_regex']
    )
    print(f"  Summary: {result3.summary}")
    print(f"  Output: {result3.anonymized_text}")
    passed = len(result3.summary) >= 2  # Should have at least 2 different entity types
    print(f"  Status: {'✓ PASS' if passed else '✗ FAIL'}")

    return 3 if passed else 2


def test_gliner_threshold():
    """TEST 2: GLiNER Threshold Control"""
    print_section_header(2, "GLiNER Threshold Control", 6)

    text = "Matti Meikäläinen asuu Helsingissä. Yhteyshenkilö Liisa Virtanen."

    params = {
        'text': text,
        'low_threshold': 0.2,
        'high_threshold': 0.7,
        'label': 'person_ner'
    }

    print("\nPARAMETERS:")
    print(f"  Text: {text}")
    print(f"  Label: {params['label']}")
    print(f"  Low threshold: {params['low_threshold']} (more detections)")
    print(f"  High threshold: {params['high_threshold']} (fewer detections)")

    anonymizer = TextAnonymizer()

    # Low threshold
    print("\n\nTest 2a: Low threshold (0.2)")
    result_low = anonymizer.anonymize(
        text=text,
        labels=['person_ner'],
        gliner_threshold=0.2
    )
    print(f"  Summary: {result_low.summary}")
    print(f"  Entities found: {len(result_low.details)}")
    print(f"  Output: {result_low.anonymized_text}")

    # High threshold
    print("\n\nTest 2b: High threshold (0.7)")
    result_high = anonymizer.anonymize(
        text=text,
        labels=['person_ner'],
        gliner_threshold=0.7
    )
    print(f"  Summary: {result_high.summary}")
    print(f"  Entities found: {len(result_high.details)}")
    print(f"  Output: {result_high.anonymized_text}")

    # Analysis
    print("\n\nAnalysis:")
    print(f"  Low threshold found {len(result_low.details)} entities")
    print(f"  High threshold found {len(result_high.details)} entities")
    print(f"  Status: {'✓ PASS' if len(result_low.details) >= len(result_high.details) else '✗ FAIL'}")

    return 2


def test_underscore_label_conversion():
    """TEST 3: Underscore-to-Space Label Conversion"""
    print_section_header(3, "Underscore-to-Space Label Conversion", 6)

    text = "Soita numeroon 040-1234567"

    params = {
        'text': text,
        'underscore_label': 'phone_number_ner',
        'space_label': 'phone number',
    }

    print("\nPARAMETERS:")
    print(f"  Text: {text}")
    print(f"  Underscore label: {params['underscore_label']}")
    print(f"  Space label: {params['space_label']}")
    print("\nEXPECTED: Both should produce same result")

    anonymizer = TextAnonymizer()

    # Test with underscore
    print("\n\nTest 3a: Using underscore label (phone_number_ner)")
    result1 = anonymizer.anonymize(
        text=text,
        labels=['phone_number_ner']
    )
    print(f"  Summary: {result1.summary}")
    print(f"  Output: {result1.anonymized_text}")

    # Test with space
    print("\n\nTest 3b: Using space label (phone number)")
    result2 = anonymizer.anonymize(
        text=text,
        labels=['phone number']
    )
    print(f"  Summary: {result2.summary}")
    print(f"  Output: {result2.anonymized_text}")

    # Comparison
    print("\n\nComparison:")
    same_summary = result1.summary == result2.summary
    same_output = result1.anonymized_text == result2.anonymized_text
    print(f"  Same summary: {same_summary}")
    print(f"  Same output: {same_output}")
    print(f"  Status: {'✓ PASS' if same_summary and same_output else '✗ FAIL (labels not equivalent)'}")

    return 2


def test_multi_word_labels():
    """TEST 4: Multi-word Label Handling"""
    print_section_header(4, "Multi-word Label Handling", 6)

    test_cases = [
        ('phone_number_ner', 'Numero: 040-1234567'),
        ('date_of_birth_ner', 'Syntymäaika: 31.12.1999'),
        ('email_ner', 'Email: test@example.com'),
    ]

    print("\nPARAMETERS:")
    print("  Testing various multi-word NER labels")
    for label, text in test_cases:
        print(f"    - {label}: '{text}'")

    anonymizer = TextAnonymizer()
    passed = 0

    for label, text in test_cases:
        print(f"\n\nTest: {label}")
        print_example_case(text, f"Should handle label: {label}")

        try:
            result = anonymizer.anonymize(text=text, labels=[label])
            print(f"  Summary: {result.summary}")
            print(f"  Output: {result.anonymized_text}")

            # Check if processing succeeded
            success = result.anonymized_text is not None
            print(f"  Status: {'✓ PASS' if success else '✗ FAIL'}")
            if success:
                passed += 1
        except Exception as e:
            print(f"  ERROR: {e}")

    return passed


def test_regex_with_profile():
    """TEST 5: Regex Pattern Detection with Profile"""
    print_section_header(5, "Regex Pattern Detection with Profile", 6)

    text = "Henkilötunnus 311299-999A ja rekisteri ABA-303"

    params = {
        'text': text,
        'profile': 'default',
        'labels': 'auto (from profile)'
    }

    print("\nPARAMETERS:")
    print(f"  Text: {text}")
    print(f"  Profile: {params['profile']}")
    print(f"  Labels: Will use regex patterns from profile")

    anonymizer = TextAnonymizer()

    print("\n\nTest: Using default profile")
    print_example_case(text, "Should detect HETU and registration from profile patterns")

    try:
        result = anonymizer.anonymize(text=text, profile='default')
        print(f"  Summary: {result.summary}")
        print(f"  Output: {result.anonymized_text}")
        print(f"  Details: {result.details}")

        # Check if regex patterns were applied
        has_patterns = len(result.summary) > 0
        print(f"  Status: {'✓ PASS' if has_patterns else '✗ FAIL'}")

        return 1 if has_patterns else 0
    except Exception as e:
        print(f"  ERROR: {e}")
        return 0


def test_blocklist_grantlist():
    """TEST 6: Blocklist/Grantlist with Profile"""
    print_section_header(6, "Blocklist and Grantlist with Profile", 8)

    print("\nPARAMETERS:")
    print("  Profile: 'example'")
    print("  Blocklist test: 'blockword123' should be anonymized")
    print("  Grantlist test: 'example321' should be protected")

    anonymizer = TextAnonymizer()

    # Test blocklist
    print("\n\nTest 6a: Blocklist")
    text1 = "Tunniste blockword123 on lauseessa."
    print(f"  Input:  {text1}")
    result1 = anonymizer.anonymize(text1, profile='example')
    print(f"  Output: {result1.anonymized_text}")
    print(f"  Summary: {result1.summary}")
    blocklist_passed = 'blockword123' not in result1.anonymized_text
    print(f"  Status: {'✓ PASS' if blocklist_passed else '✗ FAIL'}")

    # Test grantlist
    print("\n\nTest 6b: Grantlist (Protection)")
    text2 = "Sallittu kohde on example321 lauseessa."
    print(f"  Input:  {text2}")
    result2 = anonymizer.anonymize(text2, profile='example')
    print(f"  Output: {result2.anonymized_text}")
    grantlist_passed = 'example321' in result2.anonymized_text
    print(f"  Status: {'✓ PASS' if grantlist_passed else '✗ FAIL'}")

    return 2 if (blocklist_passed and grantlist_passed) else (1 if (blocklist_passed or grantlist_passed) else 0)


def test_config_cache_loading():
    """TEST 7: Config Cache Loading Verification"""
    print_section_header(7, "Config Cache Loading Verification", 8)

    from text_anonymizer.config_cache import ConfigCache

    print("\nChecking config loading:")

    config_cache = ConfigCache()

    # Check blocklist
    print("\n  Blocklist (example profile):")
    blocklist = config_cache.get_blocklist('example')
    print(f"    Items: {len(blocklist)}")
    print(f"    Contains 'blockword123': {'blockword123' in blocklist}")

    # Check grantlist
    print("\n  Grantlist (example profile):")
    grantlist = config_cache.get_grantlist('example')
    print(f"    Items: {len(grantlist)}")
    print(f"    Contains 'example321': {'example321' in grantlist}")

    # Check regex patterns
    print("\n  Regex Patterns (default profile):")
    patterns = config_cache.get_regex_patterns('default')
    print(f"    Patterns loaded: {len(patterns)}")
    for p in patterns[:5]:
        print(f"      - {p['entity_type']}")
    if len(patterns) > 5:
        print(f"      ... and {len(patterns) - 5} more")

    passed = len(blocklist) > 0 and len(patterns) > 0
    print(f"\n  Status: {'✓ PASS' if passed else '✗ FAIL'}")

    return 1 if passed else 0


def test_combined_controls():
    """TEST 8: Combined Controls - Full Example"""
    print_section_header(8, "Combined Controls - Full Example", 8)

    text = """
    Asiakas: Matti Meikäläinen
    HETU: 311299-999A
    Puhelin: 040-1234567
    Sähköposti: matti@example.com
    Osoite: Mannerheimintie 5 A, 00100 Helsinki
    """

    params = {
        'text': 'Full customer record',
        'labels': ['person_ner', 'email_ner', 'address_ner',
                   'fi_hetu_regex', 'fi_puhelin_regex'],
        'threshold': 0.3
    }

    print("\nPARAMETERS:")
    print(f"  Text type: {params['text']}")
    print(f"  Labels: {len(params['labels'])} labels")
    for label in params['labels']:
        print(f"    - {label}")
    print(f"  Threshold: {params['threshold']}")

    anonymizer = TextAnonymizer()

    print("\n\nTest: Anonymizing complete record with multiple controls")
    print_example_case(text.strip()[:50] + "...", "Should anonymize all PII with one call")

    result = anonymizer.anonymize(
        text=text,
        labels=params['labels'],
        gliner_threshold=params['threshold']
    )

    print(f"\n  Summary: {result.summary}")
    print(f"  Entities found: {len(result.details)}")
    print(f"  Output preview: {result.anonymized_text[:100]}...")

    # Check multiple entity types were found
    entity_types = len(result.summary.split(';'))
    print(f"  Entity types detected: {entity_types}")
    print(f"  Status: {'✓ PASS' if entity_types >= 3 else '✗ FAIL (expected >= 3 types)'}")

    return 1 if entity_types >= 3 else 0


def main():
    """Run all GLiNER controls tests."""

    print("\n" + "="*80)
    print("GLINER CONTROLS DEBUG SCRIPT")
    print("Tests: Labels, Thresholds, Label Conversion, Multi-word Labels,")
    print("       Profiles, Blocklist/Grantlist, Config Loading")
    print("="*80)

    all_passed = 0

    # Run all tests
    try:
        all_passed += test_labels_parameter()
        all_passed += test_gliner_threshold()
        all_passed += test_underscore_label_conversion()
        all_passed += test_multi_word_labels()
        all_passed += test_regex_with_profile()
        all_passed += test_blocklist_grantlist()
        all_passed += test_config_cache_loading()
        all_passed += test_combined_controls()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print(f"COMPLETED: {all_passed} tests")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

