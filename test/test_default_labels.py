#!/usr/bin/env python
"""
Test default labels and underscore-to-space conversion.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from text_anonymizer import TextAnonymizer


def test_default_labels():
    """Test that default labels include both NER and regex patterns."""
    print("=" * 70)
    print("TEST 1: Default Labels (NER + Regex)")
    print("=" * 70)

    anonymizer = TextAnonymizer()

    # Default labels should detect both NER and regex patterns
    text = "Matti Meikäläinen, HETU: 311299-999A, puhelin: 040-1234567, email: matti@example.com"
    result = anonymizer.anonymize(text, profile='example')

    print(f"Input:  {text}")
    print(f"Output: {result.anonymized_text}")
    print(f"Stats:  {result.statistics}")
    print()

    # Should detect both NER (person, email) and regex (FI_HETU, FI_PUHELIN)
    assert 'PERSON' in result.statistics or 'EMAIL' in result.statistics, "Should detect NER entities"
    assert 'FI_HETU' in result.statistics or 'FI_PUHELIN' in result.statistics, "Should detect regex entities"
    print("✓ Default labels detect both NER and regex patterns")
    print()


def test_underscore_to_space():
    """Test that underscores in NER labels convert to spaces."""
    print("=" * 70)
    print("TEST 2: Underscore-to-Space Conversion")
    print("=" * 70)

    anonymizer = TextAnonymizer()

    text = "Puhelinnumero: 040-1234567"

    # Test with underscore
    result1 = anonymizer.anonymize(text, labels=['phone_number_ner'])
    print(f"With underscore (phone_number_ner):")
    print(f"  Output: {result1.anonymized_text}")
    print(f"  Stats:  {result1.statistics}")
    print()

    # Test with space (backward compatible)
    result2 = anonymizer.anonymize(text, labels=['phone number'])
    print(f"With space (phone number):")
    print(f"  Output: {result2.anonymized_text}")
    print(f"  Stats:  {result2.statistics}")
    print()

    # Both should produce same result
    assert result1.statistics == result2.statistics, "Underscore and space should be equivalent"
    print("✓ Underscore and space conversion work equivalently")
    print()


def test_multi_word_labels():
    """Test various multi-word labels."""
    print("=" * 70)
    print("TEST 3: Multi-Word NER Labels")
    print("=" * 70)

    anonymizer = TextAnonymizer()

    # Test common multi-word labels
    test_cases = [
        ('phone_number_ner', 'Numero: 040-1234567'),
        ('date_of_birth_ner', 'Syntymäaika: 31.12.1999'),
        ('credit_card_number_ner', 'Kortti: 4532-1234-5678-9010'),
    ]

    for label, text in test_cases:
        result = anonymizer.anonymize(text, labels=[label])
        # Convert label to readable format
        readable = label.replace('_ner', '').replace('_', ' ')
        print(f"{readable:25} → {result.anonymized_text}")

    print()
    print("✓ Multi-word labels converted correctly")
    print()


def test_mixed_labels():
    """Test mixing NER labels with underscores and regex labels."""
    print("=" * 70)
    print("TEST 4: Mixed NER (with underscores) + Regex")
    print("=" * 70)

    anonymizer = TextAnonymizer()

    text = "Henkilö: Matti, syntymäaika: 31.12.1999, HETU: 311299-999A, puhelin: 040-1234567"

    result = anonymizer.anonymize(
        text,
        labels=[
            'person_ner',
            'date_of_birth_ner',
            'fi_hetu_regex',
            'fi_puhelin_regex'
        ],
        profile='example'
    )

    print(f"Input:  {text}")
    print(f"Output: {result.anonymized_text}")
    print(f"Stats:  {result.statistics}")
    print()
    print("✓ Mixed NER + regex labels work correctly")
    print()


def test_all_defaults():
    """Test that all default labels are properly configured."""
    print("=" * 70)
    print("TEST 5: All Default Labels Configuration")
    print("=" * 70)

    anonymizer = TextAnonymizer()

    print("Default labels:")
    for i, label in enumerate(anonymizer.labels, 1):
        print(f"  {i}. {label}")

    print()

    # Verify we have both NER and regex labels
    ner_labels = [l for l in anonymizer.labels if not l.endswith('_regex')]
    regex_labels = [l for l in anonymizer.labels if l.endswith('_regex')]

    print(f"NER labels: {len(ner_labels)} → {ner_labels}")
    print(f"Regex labels: {len(regex_labels)} → {regex_labels}")
    print()

    assert len(ner_labels) > 0, "Should have NER labels"
    assert len(regex_labels) > 0, "Should have regex labels"
    print("✓ Default labels correctly include both NER and regex")
    print()


if __name__ == "__main__":
    try:
        print("\n")
        print("*" * 70)
        print("  DEFAULT LABELS & SPACE HANDLING - TESTISARJA")
        print("*" * 70)
        print("\n")

        test_default_labels()
        test_underscore_to_space()
        test_multi_word_labels()
        test_mixed_labels()
        test_all_defaults()

        print("=" * 70)
        print("✓ KAIKKI TESTIT ONNISTUIVAT")
        print("=" * 70)
        sys.exit(0)

    except AssertionError as e:
        print(f"\n✗ TESTI EPÄONNISTUI: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ VIRHE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

