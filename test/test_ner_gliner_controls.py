#!/usr/bin/env python
"""
Consolidated test for GLiNER controls, configuration, and label mappings.

This test combines:
- test_gliner_controls.py → Custom labels, thresholds, regex/blocklist controls
- test_default_labels.py → Default labels, underscore-to-space conversion, multi-word labels
- test_label_mappings.py → Label mapping configuration from label_mappings.txt

Tests the core configuration and control mechanisms of the GLiNER-based anonymizer.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import unittest
from text_anonymizer import TextAnonymizer


# ============================================================================
# DEFAULT LABELS AND CONFIGURATION TESTS
# ============================================================================

class TestDefaultLabelsAndConfig(unittest.TestCase):
    """Test default labels, underscore-to-space conversion, and multi-word labels."""

    def test_default_labels_ner_and_regex(self):
        """Test that default labels include both NER and regex patterns."""
        anonymizer = TextAnonymizer()

        # Default labels should detect both NER and regex patterns
        text = "Matti Meikäläinen, HETU: 311299-999A, puhelin: 040-1234567, email: matti@example.com"
        result = anonymizer.anonymize(text, profile='example')

        # Should detect both NER (person, email) and regex (FI_HETU, FI_PUHELIN)
        self.assertTrue(
            'PERSON' in result.statistics or 'EMAIL' in result.statistics,
            "Should detect NER entities"
        )
        self.assertTrue(
            'FI_HETU' in result.statistics or 'FI_PUHELIN' in result.statistics,
            "Should detect regex entities"
        )

    def test_underscore_to_space_conversion(self):
        """Test that underscores in NER labels convert to spaces."""
        anonymizer = TextAnonymizer()

        text = "Puhelinnumero: 040-1234567"

        # Test with underscore
        result1 = anonymizer.anonymize(text, labels=['phone_number_ner'])

        # Test with space (backward compatible)
        result2 = anonymizer.anonymize(text, labels=['phone number'])

        # Both should produce same result
        self.assertEqual(
            result1.statistics,
            result2.statistics,
            "Underscore and space should be equivalent"
        )

    def test_multi_word_labels(self):
        """Test various multi-word NER labels."""
        anonymizer = TextAnonymizer()

        # Test common multi-word labels
        test_cases = [
            ('phone_number_ner', 'Numero: 040-1234567'),
            ('date_of_birth_ner', 'Syntymäaika: 31.12.1999'),
            ('credit_card_number_ner', 'Kortti: 4532-1234-5678-9010'),
        ]

        for label, text in test_cases:
            result = anonymizer.anonymize(text, labels=[label])
            self.assertIsNotNone(result.anonymized_text)


# ============================================================================
# LABEL MAPPING TESTS
# ============================================================================

class TestLabelMappings(unittest.TestCase):
    """Test label mapping functionality from config/label_mappings.txt."""

    def test_label_mappings_loaded(self):
        """Test that label mappings are loaded from config file."""
        anonymizer = TextAnonymizer()

        # Check that mappings were loaded
        self.assertGreater(
            len(anonymizer.label_mappings),
            0,
            "Should load mappings from file"
        )

    def test_person_ner_maps_to_nimi(self):
        """Test that person_ner maps to NIMI in output."""
        anonymizer = TextAnonymizer()

        result = anonymizer.anonymize(
            "Matti Meikäläinen asuu Helsingissä",
            labels=['person_ner']
        )

        # Should use NIMI instead of PERSON
        self.assertIn('NIMI', result.statistics, "Should map PERSON to NIMI")
        self.assertNotIn('PERSON', result.statistics, "Should NOT use PERSON label")
        self.assertIn('<NIMI>', result.anonymized_text, "Should show <NIMI> in text")

    def test_phone_number_ner_maps_to_puhelinnumero(self):
        """Test that phone_number_ner maps to PUHELINNUMERO."""
        anonymizer = TextAnonymizer()

        result = anonymizer.anonymize(
            "Soita numeroon 040-1234567",
            labels=['phone_number_ner']
        )

        # Should use PUHELINNUMERO instead of PHONE_NUMBER
        self.assertIn(
            'PUHELINNUMERO',
            result.statistics,
            "Should map PHONE_NUMBER to PUHELINNUMERO"
        )
        self.assertNotIn(
            'PHONE_NUMBER',
            result.statistics,
            "Should NOT use PHONE_NUMBER label"
        )

    def test_fi_hetu_regex_maps_to_hetu(self):
        """Test that fi_hetu_regex maps to HETU."""
        anonymizer = TextAnonymizer()

        result = anonymizer.anonymize(
            "Henkilötunnus: 311299-999A",
            labels=['fi_hetu_regex'],
            profile='example'
        )

        # Should use HETU
        self.assertIn('HETU', result.statistics, "Should map fi_hetu_regex to HETU")


# ============================================================================
# GLINER CONTROLS AND CONFIGURATION TESTS
# ============================================================================

class TestGLiNERControls(unittest.TestCase):
    """Test GLiNER label controls, thresholds, and regex/blocklist management."""

    def test_custom_labels(self):
        """Test using custom GLiNER labels."""
        anonymizer = TextAnonymizer(languages=['fi'])

        text = "Matti Meikäläinen asuu Helsingissä. Email: matti@example.com, puhelin: 040-1234567"

        # Custom labels (only person and email, no phone number)
        result_custom = anonymizer.anonymize(text, custom_labels=["person", "email"])

        # Phone number should remain when using custom labels without "phone number"
        self.assertIn(
            "040-1234567",
            result_custom.anonymized_text,
            "Phone number should remain without 'phone number' label"
        )

    def test_gliner_threshold_control(self):
        """Test GLiNER threshold control affects detection sensitivity."""
        anonymizer = TextAnonymizer(languages=['fi'])

        text = "Matti Meikäläinen asuu Helsingissä. Yhteyshenkilö Liisa Virtanen."

        # Low threshold (more detections)
        result_low = anonymizer.anonymize(text, gliner_threshold=0.2)

        # High threshold (fewer detections)
        result_high = anonymizer.anonymize(text, gliner_threshold=0.7)

        # Both should produce valid results
        self.assertIsNotNone(result_low.anonymized_text)
        self.assertIsNotNone(result_high.anonymized_text)

    def test_enable_disable_regex(self):
        """Test enabling/disabling regex patterns."""
        anonymizer = TextAnonymizer(languages=['fi'])

        text = "Henkilötunnus 311299-999A ja VARCODE123 tunniste."

        # With regex enabled (default)
        result_with_regex = anonymizer.anonymize(text, profile='example', enable_regex=True)

        # With regex disabled
        result_no_regex = anonymizer.anonymize(text, profile='example', enable_regex=False)

        # VARCODE123 should remain when regex is disabled
        self.assertIn(
            "VARCODE123",
            result_no_regex.anonymized_text,
            "VARCODE should remain without regex patterns"
        )

    def test_enable_disable_blocklist(self):
        """Test enabling/disabling blocklist protection."""
        anonymizer = TextAnonymizer(languages=['fi'])

        text = "Tunniste blockword123 on lauseessa."

        # With blocklist enabled (default)
        result_with_blocklist = anonymizer.anonymize(
            text,
            profile='example',
            enable_blocklist=True
        )

        # With blocklist disabled
        result_no_blocklist = anonymizer.anonymize(
            text,
            profile='example',
            enable_blocklist=False
        )

        # blockword123 should remain when blocklist is disabled
        self.assertIn(
            "blockword123",
            result_no_blocklist.anonymized_text,
            "Blocklist word should remain without blocklist"
        )


if __name__ == '__main__':
    unittest.main()

