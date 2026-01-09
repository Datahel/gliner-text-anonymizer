"""
Lightweight GLiNER-based text anonymizer with profile support.
"""
import sys
import re
from typing import Optional, List, Dict, Any, Set

try:
    from gliner import GLiNER
except ImportError:
    print("Required libraries not found. Please install them with:")
    print("pip install gliner")
    sys.exit(1)

from .anonymizer_interface import Anonymizer as AnonymizerInterface
from .anonymizer_result import AnonymizerResult
from .config_cache import ConfigCache

'''
Full List of Gliner supported PII Labels:
person, organization, phone number, address, passport number, email, credit card number, social security number, health insurance id number, date of birth, mobile phone number, bank account number, medication, cpf, driver's license number, tax identification number, medical condition, identity card number, national id number, ip address, email address, iban, credit card expiration date, username, health insurance number, registration number, student id number, insurance number, flight number, landline phone number, blood type, cvv, reservation number, digital signature, social media handle, license plate number, cnpj, postal code, passport_number, serial number, vehicle registration number, credit card brand, fax number, visa number, insurance company, identity document number, transaction number, national health insurance number, cvc, birth certificate number, train ticket number, passport expiration date, and social_security_number.
'''

class Anonymizer(AnonymizerInterface):
    """Lightweight GLiNER-based anonymizer with text file configuration support."""

    def __init__(self, languages: Optional[List[str]] = None,
            recognizer_configuration: Optional[List[Dict[str, Any]]] = None,
            model_name='urchade/gliner_multi-v2.1',
            debug_mode=False,
            **kwargs
    ):
        self.model_name = model_name
        self.debug_mode = debug_mode
        self.model = self._load_or_download_model()

        # Default GLiNER labels for common entities
        self.labels = ["person", "phone number", "email", "address", "organization"]
        self._last_entities = []
        self.config_cache = ConfigCache()

        super().__init__(languages, recognizer_configuration, **kwargs)

    def _load_or_download_model(self):
        """Load model from cache or download if not available"""
        try:
            if self.debug_mode:
                print("Loading GLiNER model from cache...")
            return GLiNER.from_pretrained(self.model_name, local_files_only=True)
        except Exception:
            if self.debug_mode:
                print("Model not found in cache. Downloading GLiNER model...")
            return GLiNER.from_pretrained(self.model_name)

    def _find_entities_with_gliner(self, text: str, threshold: float = 0.3) -> List[Dict]:
        """Use GLiNER to find entities in text."""
        return self.model.predict_entities(text, self.labels, threshold=threshold)

    def _find_entities_with_regex(self, text: str, patterns: List[Dict[str, str]]) -> List[Dict]:
        """Find entities using regex patterns from profile."""
        entities = []
        for pattern_def in patterns:
            entity_type = pattern_def['entity_type']
            pattern = pattern_def['pattern']

            try:
                for match in re.finditer(pattern, text):
                    entities.append({
                        'start': match.start(),
                        'end': match.end(),
                        'text': match.group(),
                        'label': entity_type,
                        'score': 1.0  # Regex matches have perfect score
                    })
            except re.error as e:
                if self.debug_mode:
                    print(f"Warning: Invalid regex pattern '{pattern}': {e}")

        return entities

    def _find_blocklist_entities(self, text: str, blocklist: Set[str]) -> List[Dict]:
        """Find entities from blocklist in text."""
        entities = []
        for blocked_word in blocklist:
            # Case-insensitive search for blocked words
            pattern = r'\b' + re.escape(blocked_word) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    'start': match.start(),
                    'end': match.end(),
                    'text': match.group(),
                    'label': 'MUU_TUNNISTE',  # Generic identifier
                    'score': 1.0
                })

        return entities

    def _filter_grantlist(self, entities: List[Dict], grantlist: Set[str]) -> List[Dict]:
        """Remove entities that are in the grantlist (protected words)."""
        if not grantlist:
            return entities

        filtered = []
        for entity in entities:
            # Check if entity text is in grantlist (case-insensitive)
            entity_text = entity.get('text', '')
            if entity_text.lower() not in {word.lower() for word in grantlist}:
                filtered.append(entity)
            elif self.debug_mode:
                print(f"Protecting grantlisted entity: {entity_text}")

        return filtered

    def _remove_overlapping_entities(self, entities: List[Dict]) -> List[Dict]:
        """
        Remove overlapping entities, prioritizing regex/blocklist matches over GLiNER.
        Priority order: 1) score=1.0 (regex/blocklist), 2) longest span, 3) highest score
        """
        if not entities:
            return []

        # Sort by start position, then prioritize score=1.0 (regex/blocklist), then length
        entities.sort(key=lambda x: (
            x['start'],  # Same start position
            0 if x.get('score', 0) == 1.0 else 1,  # Prioritize regex/blocklist (score=1.0)
            -(x['end'] - x['start']),  # Then longest span
            -x.get('score', 0)  # Then highest score
        ))

        non_overlapping = []
        last_end = -1

        for entity in entities:
            if entity['start'] >= last_end:
                non_overlapping.append(entity)
                last_end = entity['end']

        return non_overlapping

    def _map_entity_label(self, label: str) -> str:
        """Map GLiNER labels to consistent output labels."""
        label_map = {
            'person': 'PERSON',
            'phone number': 'PHONE_NUMBER',
            'email': 'EMAIL',
            'address': 'ADDRESS',
            'organization': 'ORGANIZATION'
        }
        return label_map.get(label.lower(), label.upper())

    def anonymize_text(self, text: str, profile: Optional[str] = None) -> str:
        """Anonymize text using GLiNER and optional profile configuration."""
        if not text:
            return text

        # Collect entities from GLiNER
        entities = self._find_entities_with_gliner(text)

        # Add profile-based entities if profile is specified
        if profile:
            blocklist = self.config_cache.get_blocklist(profile)
            grantlist = self.config_cache.get_grantlist(profile)
            regex_patterns = self.config_cache.get_regex_patterns(profile)

            # Add blocklist entities
            if blocklist:
                blocklist_entities = self._find_blocklist_entities(text, blocklist)
                entities.extend(blocklist_entities)

            # Add regex pattern entities
            if regex_patterns:
                regex_entities = self._find_entities_with_regex(text, regex_patterns)
                entities.extend(regex_entities)

            # Filter out grantlisted entities
            if grantlist:
                entities = self._filter_grantlist(entities, grantlist)

        # Remove overlapping entities
        entities = self._remove_overlapping_entities(entities)
        self._last_entities = entities

        if not entities:
            return text

        # Replace entities in reverse order to maintain positions
        result = text
        for entity in sorted(entities, key=lambda x: x['start'], reverse=True):
            start, end = entity['start'], entity['end']
            label = self._map_entity_label(entity['label'])
            result = result[:start] + f"<{label}>" + result[end:]

        return result

    def anonymize(self, text: str, user_languages: Optional[List[str]] = None,
                  user_recognizers: Optional[List[str]] = None,
                  use_labels: bool = True, profile: Optional[str] = None) -> AnonymizerResult:
        """
        Anonymize text and return detailed results.

        Args:
            text: Text to anonymize
            user_languages: Languages to use (currently unused, kept for API compatibility)
            user_recognizers: Specific recognizers to use (currently unused, kept for API compatibility)
            use_labels: Whether to use labels in output (currently unused, kept for API compatibility)
            profile: Profile name for blocklist/grantlist/regex patterns

        Returns:
            AnonymizerResult with anonymized text and statistics
        """
        if not text:
            return AnonymizerResult(anonymized_text=None, statistics={}, details={})

        anonymized_text = self.anonymize_text(text, profile=profile)
        statistics = {}
        details = {}

        for entity in self._last_entities:
            entity_type = self._map_entity_label(entity['label'])
            entity_text = entity.get('text', text[entity['start']:entity['end']])

            if entity_type in statistics:
                statistics[entity_type] += 1
                details[entity_type].append(entity_text)
            else:
                statistics[entity_type] = 1
                details[entity_type] = [entity_text]

        return AnonymizerResult(anonymized_text=anonymized_text, statistics=statistics, details=details)

