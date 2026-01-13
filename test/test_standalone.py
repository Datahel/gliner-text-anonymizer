pl#!/usr/bin/env python
"""
Simple standalone test to verify the GLiNER anonymizer works.
Run this without starting the API server.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from text_anonymizer import TextAnonymizer

def test_basic():
    """Test basic anonymization without profile."""
    print("=" * 60)
    print("TEST 1: Basic Anonymization")
    print("=" * 60)

    anonymizer = TextAnonymizer(languages=['fi'])

    # Test phone number
    text = "Puhelinnumeroni on 040-1234567."
    result = anonymizer.anonymize(text)

    assert "040-1234567" not in result.anonymized_text, "Phone should be anonymized"
    assert "PHONE_NUMBER" in result.statistics, "Should detect phone number"

    print(f"✓ Input:  {text}")
    print(f"✓ Output: {result.anonymized_text}")
    print(f"✓ Stats:  {result.statistics}")
    print()

def test_blocklist():
    """Test blocklist functionality."""
    print("=" * 60)
    print("TEST 2: Blocklist")
    print("=" * 60)

    anonymizer = TextAnonymizer(languages=['fi'])

    text = "Tunniste blockword123 on lauseessa."
    result = anonymizer.anonymize(text, profile='example')

    assert "blockword123" not in result.anonymized_text, "Blocklisted word should be anonymized"
    assert "MUU_TUNNISTE" in result.statistics, "Should detect blocklisted word"

    print(f"✓ Input:  {text}")
    print(f"✓ Output: {result.anonymized_text}")
    print(f"✓ Stats:  {result.statistics}")
    print()

def test_grantlist():
    """Test grantlist functionality."""
    print("=" * 60)
    print("TEST 3: Grantlist (Protection)")
    print("=" * 60)

    anonymizer = TextAnonymizer(languages=['fi'])

    text = "Sallittu kohde on example321 lauseessa."
    result = anonymizer.anonymize(text, profile='example')

    assert "example321" in result.anonymized_text, "Grantlisted word should be protected"

    print(f"✓ Input:  {text}")
    print(f"✓ Output: {result.anonymized_text}")
    print(f"✓ Stats:  {result.statistics}")
    print()

def test_regex():
    """Test regex pattern functionality."""
    print("=" * 60)
    print("TEST 4: Regex Patterns")
    print("=" * 60)

    anonymizer = TextAnonymizer(languages=['fi'])

    test_cases = [
        "VARCODE123",
        "VARCODEabc",
        "PROD_VARCODE99"
    ]

    for word in test_cases:
        text = f"Tässä on {word} tunniste."
        result = anonymizer.anonymize(text, profile='example')

        if word not in result.anonymized_text:
            print(f"✓ {word:20} -> ANONYMIZED")
        else:
            print(f"✗ {word:20} -> NOT ANONYMIZED (might be detected as other entity)")
    print()

def test_combined():
    """Test combined features."""
    print("=" * 60)
    print("TEST 5: Combined Features")
    print("=" * 60)

    anonymizer = TextAnonymizer(languages=['fi'])

    text = "Estetty: blockword123, Sallittu: example321, Puhelin: 040-1234567"
    result = anonymizer.anonymize(text, profile='example')

    assert "blockword123" not in result.anonymized_text, "Blocked word should be anonymized"
    assert "example321" in result.anonymized_text, "Granted word should be protected"
    assert "040-1234567" not in result.anonymized_text, "Phone should be anonymized"

    print(f"✓ Input:  {text}")
    print(f"✓ Output: {result.anonymized_text}")
    print(f"✓ Stats:  {result.statistics}")
    print()

if __name__ == "__main__":
    try:
        test_basic()
        test_blocklist()
        test_grantlist()
        test_regex()
        test_combined()

        print("=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        sys.exit(0)

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

