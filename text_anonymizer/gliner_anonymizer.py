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
person, organization, phone number, address, passport number, email, credit card number, 
social security number, health insurance id number, date of birth, mobile phone number, 
bank account number, medication, cpf, driver's license number, tax identification number, 
medical condition, identity card number, national id number, ip address, email address, 
iban, credit card expiration date, username, health insurance number, registration number, 
student id number, insurance number, flight number, landline phone number, blood type, 
cvv, reservation number, digital signature, social media handle, license plate number, 
cnpj, postal code, passport_number, serial number, vehicle registration number, 
credit card brand, fax number, visa number, insurance company, identity document number, 
transaction number, national health insurance number, cvc, birth certificate number, 
train ticket number, passport expiration date, and social_security_number.
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

        # Default labels: NER labels + all implemented regex labels
        self.labels = [
            # NER labels (GLiNER)
            "person_ner",
            "phone_number_ner",
            "email_ner",
            "address_ner",
            # Regex labels (all implemented Finnish patterns)
            "fi_hetu_regex",
            "fi_puhelin_regex",
            "fi_rekisteri_regex",
            "fi_kiinteisto_regex",
            "iban_regex",
            "tiedosto_regex"
        ]
        self._last_entities = []
        self.config_cache = ConfigCache()

        # Load label mappings from config file
        self.label_mappings = self.config_cache.get_label_mappings()

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


    def _find_entities_with_gliner(self, text: str, threshold: float = 0.3,
                                   custom_labels: Optional[List[str]] = None) -> List[Dict]:
        """
        Use GLiNER to find entities in text.

        Args:
            text: Text to analyze
            threshold: Confidence threshold (0.0-1.0)
            custom_labels: Custom labels to use instead of default
        """
        labels = custom_labels if custom_labels is not None else self.labels
        return self.model.predict_entities(text, labels, threshold=threshold)

    def _find_entities_with_regex(self, text: str, patterns: List[Dict[str, str]],
                                  allowed_types: Optional[Set[str]] = None) -> List[Dict]:
        """
        Find entities using regex patterns from profile.

        Args:
            text: Text to search
            patterns: List of pattern definitions
            allowed_types: Set of allowed entity types (if None, all are allowed)
        """
        entities = []
        for pattern_def in patterns:
            entity_type = pattern_def['entity_type']

            # Skip if this entity type is not in the allowed list
            if allowed_types is not None and entity_type not in allowed_types:
                continue

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
        """
        Map entity labels to output labels using config/label_mappings.txt.

        Process:
        1. Convert label to uppercase with underscores (e.g., 'phone number' -> 'PHONE_NUMBER')
        2. Look up in label_mappings (e.g., 'PHONE_NUMBER' -> 'PUHELINNUMERO')
        3. If not found in mappings, use the uppercase version

        Args:
            label: Input label (e.g., 'person', 'phone number', 'FI_HETU')

        Returns:
            Mapped output label (e.g., 'NIMI', 'PUHELINNUMERO', 'HETU')
        """
        # Convert label to uppercase with underscores (normalize)
        normalized_label = label.upper().replace(' ', '_')

        # Look up in mappings, fallback to normalized label if not found
        return self.label_mappings.get(normalized_label, normalized_label)

    def _separate_labels(self, labels: List[str]) -> tuple[List[str], Optional[Set[str]]]:
        """
        Separate NER labels from regex entity types based on suffix.

        NER labels: end with '_ner' (e.g., 'person_ner', 'phone_number_ner')
        Regex types: end with '_regex' (e.g., 'fi_hetu_regex', 'fi_puhelin_regex')

        Args:
            labels: List of labels with suffixes

        Returns:
            Tuple of (gliner_labels, regex_entity_types_set or None)
        """
        gliner_labels = []
        regex_types = []

        for label in labels:
            if label.endswith('_ner'):
                # Remove _ner suffix and convert underscores to spaces for GLiNER
                # (e.g., 'person_ner' -> 'person', 'phone_number_ner' -> 'phone number')
                ner_label = label[:-4].replace('_', ' ')
                gliner_labels.append(ner_label)
            elif label.endswith('_regex'):
                # Remove _regex suffix and convert to uppercase entity type
                # (e.g., 'fi_hetu_regex' -> 'FI_HETU')
                entity_type = label[:-6].upper()
                regex_types.append(entity_type)
            else:
                # For backward compatibility: treat unsuffixed labels as NER labels
                # Also convert underscores to spaces (e.g., 'phone_number' -> 'phone number')
                gliner_labels.append(label.replace('_', ' '))

        # Return None for regex_types if empty (means don't use regex patterns)
        return gliner_labels, set(regex_types) if regex_types else None

    def anonymize_text(self, text: str, profile: str = 'default',
                      labels: Optional[List[str]] = None,
                      gliner_threshold: float = 0.3) -> str:
        """
        Anonymize text using GLiNER and optional profile configuration.

        Args:
            text: Text to anonymize
            profile: Profile name for configuration (defaults to 'default' if None)
            labels: List of entity labels to detect with suffixes:
                   - '_ner' for NER/GLiNER labels (e.g., 'person_ner', 'email_ner')
                   - '_regex' for regex patterns (e.g., 'fi_hetu_regex', 'fi_puhelin_regex')
                   - 'blocklist' to enable blocklist matching
                   - Unsuffixed labels are treated as NER labels for backward compatibility
                   If None, uses profile labels or defaults
            gliner_threshold: GLiNER confidence threshold (0.0-1.0, default 0.3)
        """
        if not text:
            return text

        # Use 'default' profile if none specified to ensure regex patterns are applied
        effective_profile = profile if profile else 'default'

        # Load profile configuration
        profile_labels = self.config_cache.get_gliner_labels(effective_profile)

        # Determine which labels to use (priority: parameter > profile > default)
        active_labels = labels or profile_labels or self.labels

        # Check if blocklist is requested
        enable_blocklist = 'blocklist' in active_labels if isinstance(active_labels, list) else False
        if enable_blocklist:
            active_labels = [l for l in active_labels if l != 'blocklist']

        # Separate NER labels from regex entity types
        gliner_labels, regex_entity_types = self._separate_labels(active_labels)

        # Collect entities from GLiNER (only if there are GLiNER labels)
        entities = []
        if gliner_labels:
            entities = self._find_entities_with_gliner(text, threshold=gliner_threshold,
                                                       custom_labels=gliner_labels)

        # Always load regex patterns from effective_profile (defaults to 'default')
        # Always load blocklist/grantlist when an explicit profile is provided
        regex_patterns = self.config_cache.get_regex_patterns(effective_profile)

        if profile:
            blocklist = self.config_cache.get_blocklist(profile)
            grantlist = self.config_cache.get_grantlist(profile)
        else:
            blocklist = set()
            grantlist = set()

        # Add blocklist entities
        if blocklist:
            blocklist_entities = self._find_blocklist_entities(text, blocklist)
            entities.extend(blocklist_entities)

        # Add regex pattern entities from the profile
        # If the caller requested specific regex types (via labels), only apply those.
        # Otherwise (no specific regex labels requested) apply all profile regex patterns.
        if regex_patterns:
            if regex_entity_types is None:
                # No specific regex types requested -> apply all patterns from profile
                entities.extend(self._find_entities_with_regex(text, regex_patterns))
            else:
                # Apply only requested regex entity types
                entities.extend(self._find_entities_with_regex(text, regex_patterns, allowed_types=regex_entity_types))

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

    def anonymize(self, text: str,
                  labels: Optional[List[str]] = None,
                  user_languages: Optional[List[str]] = None,
                  user_recognizers: Optional[List[str]] = None,
                  use_labels: bool = True,
                  profile: str = 'default',
                  gliner_threshold: float = 0.6) -> AnonymizerResult:
        """
        Anonymize text and return detailed results.

        Args:
            text: Text to anonymize
            labels: List of entity labels to detect with suffixes:
                   - '_ner' for NER/GLiNER labels (e.g., 'person_ner', 'email_ner')
                   - '_regex' for regex patterns (e.g., 'fi_hetu_regex', 'fi_puhelin_regex')
                   - 'blocklist' to enable blocklist matching
                   - Unsuffixed labels treated as NER for backward compatibility
                   Examples: ['person_ner', 'email_ner', 'fi_hetu_regex', 'blocklist']
            user_languages: Languages to use (deprecated, kept for compatibility)
            user_recognizers: Deprecated - use 'labels' parameter instead
            use_labels: Whether to use labels in output (deprecated)
            profile: Profile name for blocklist/grantlist/regex patterns
            gliner_threshold: GLiNER confidence threshold (0.0-1.0, default 0.3)

        Returns:
            AnonymizerResult with anonymized text and summary
        """
        if not text:
            return AnonymizerResult(anonymized_text=None, summary={}, details={})

        # Handle backward compatibility: user_recognizers -> labels
        if user_recognizers is not None and labels is None:
            labels = user_recognizers

        anonymized_text = self.anonymize_text(
            text,
            profile=profile,
            labels=labels,
            gliner_threshold=gliner_threshold
        )

        summary = {}
        details = {}

        for entity in self._last_entities:
            entity_type = self._map_entity_label(entity['label'])
            entity_text = entity.get('text', text[entity['start']:entity['end']])

            if entity_type in summary:
                summary[entity_type] += 1
                details[entity_type].append(entity_text)
            else:
                summary[entity_type] = 1
                details[entity_type] = [entity_text]

        return AnonymizerResult(anonymized_text=anonymized_text, summary=summary, details=details)
