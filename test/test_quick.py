#!/usr/bin/env python
"""Quick test of the GLiNER anonymizer implementation."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from text_anonymizer import TextAnonymizer

# Test 1: Basic anonymization
print("=" * 60)
print("Test 1: Basic Anonymization (no profile)")
print("=" * 60)
anonymizer = TextAnonymizer(languages=['fi'], debug_mode=True)

text1 = "Puhelinnumeroni on 040-1234567."
result1 = anonymizer.anonymize(text1)
print(f"Input: {text1}")
print(f"Output: {result1.anonymized_text}")
print(f"Statistics: {result1.statistics}")
print()

# Test 2: With profile - blocklist
print("=" * 60)
print("Test 2: With Profile - Blocklist")
print("=" * 60)
text2 = "Tunniste blockword123 on lauseessa."
result2 = anonymizer.anonymize(text2, profile='example')
print(f"Input: {text2}")
print(f"Output: {result2.anonymized_text}")
print(f"Statistics: {result2.statistics}")
print()

# Test 3: With profile - grantlist
print("=" * 60)
print("Test 3: With Profile - Grantlist")
print("=" * 60)
text3 = "Sallittu kohde on example321 lauseessa."
result3 = anonymizer.anonymize(text3, profile='example')
print(f"Input: {text3}")
print(f"Output: {result3.anonymized_text}")
print(f"Statistics: {result3.statistics}")
print()

# Test 4: With profile - regex patterns
print("=" * 60)
print("Test 4: With Profile - Regex Patterns")
print("=" * 60)
test_words = ["VARCODE123", "PROD_VARCODE99", "VARCODEabc"]
for word in test_words:
    text4 = f"Tässä lauseessa on {word} tunniste."
    result4 = anonymizer.anonymize(text4, profile='example')
    print(f"Input: {text4}")
    print(f"Output: {result4.anonymized_text}")
    print(f"Statistics: {result4.statistics}")
    print()

# Test 5: Combined profile features
print("=" * 60)
print("Test 5: Combined Profile Features")
print("=" * 60)
text5 = "Estetty: blockword123, Sallittu: example321, Puhelin: 040-1234567"
result5 = anonymizer.anonymize(text5, profile='example')
print(f"Input: {text5}")
print(f"Output: {result5.anonymized_text}")
print(f"Statistics: {result5.statistics}")
print()

print("=" * 60)
print("All tests completed!")
print("=" * 60)

