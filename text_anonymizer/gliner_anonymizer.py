"""
Lightweight GLiNER-based text anonymizer with profile support.
"""
import sys
import re
import time
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
    """Lightweight GLiNER-based anonymizer with text file configuration support.

    Thread Safety:
        This class is thread-safe. All shared state is immutable after initialization,
        and entity detection results are returned directly rather than stored in instance state.
    """

    def __init__(self,
            model_name: str = 'urchade/gliner_multi-v2.1',
            debug_mode: bool = False,
            address_score_boost: float = 0.15,
            **kwargs
    ):
        """
        Initialize the GLiNER-based anonymizer.

        Args:
            model_name: GLiNER model to use
            debug_mode: Enable debug output
            address_score_boost: Score boost for address entities when they overlap with
                               person entities. Finnish streets often contain person names
                               (e.g., "Antti Mäen kuja"), this boost helps addresses win
                               the overlap resolution. Set to 0 to disable. Default: 0.15
        """
        super().__init__(model_name=model_name, debug_mode=debug_mode, **kwargs)
        self.model = self._load_or_download_model()

        # Score boost for addresses competing with person names
        # See docs/ADDRESS_DETECTION_FIX.md for rationale
        self.address_score_boost = address_score_boost

        # Default labels: NER labels + all implemented regex labels
        self.labels = [
            # NER labels (GLiNER)
            "address_ner",
            "phone_number_ner",
            "email_ner",
            "person_ner",
            # Regex labels (all implemented Finnish patterns)
            "fi_hetu_regex",
            "fi_puhelin_regex",
            "fi_rekisteri_regex",
            "fi_kiinteisto_regex",
            "iban_regex",
            "tiedosto_regex"
        ]
        self.config_cache = ConfigCache()

        # Load label mappings from config file
        self.label_mappings = self.config_cache.get_label_mappings()


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

    # GLiNER has a token limit of 384, we use conservative char limit
    # Average ~4 chars per token, so 350 tokens * 4 = 1400 chars with safety margin
    GLINER_MAX_CHARS = 1200
    GLINER_OVERLAP_CHARS = 100  # Overlap to avoid splitting entities at boundaries

    def _split_text_into_chunks(self, text: str) -> List[tuple]:
        """
        Split text into chunks that fit within GLiNER's token limit.

        Uses sentence boundaries when possible to avoid splitting entities.
        Returns list of (chunk_text, start_offset) tuples.
        """
        if len(text) <= self.GLINER_MAX_CHARS:
            return [(text, 0)]

        chunks = []
        current_pos = 0

        while current_pos < len(text):
            # Calculate end position for this chunk
            end_pos = min(current_pos + self.GLINER_MAX_CHARS, len(text))

            # If not at the end, try to find a good break point
            if end_pos < len(text):
                # Look for sentence boundaries (. ! ? followed by space or newline)
                chunk_text = text[current_pos:end_pos]

                # Search backwards for a sentence boundary
                best_break = -1
                for i in range(len(chunk_text) - 1, max(0, len(chunk_text) - 300), -1):
                    if chunk_text[i] in '.!?\n' and (i + 1 >= len(chunk_text) or chunk_text[i + 1] in ' \n\t'):
                        best_break = i + 1
                        break

                # If no sentence boundary found, try to break at whitespace
                if best_break == -1:
                    for i in range(len(chunk_text) - 1, max(0, len(chunk_text) - 100), -1):
                        if chunk_text[i] in ' \n\t':
                            best_break = i + 1
                            break

                # If still no good break point, just use the max position
                if best_break > 0:
                    end_pos = current_pos + best_break

            chunk_text = text[current_pos:end_pos]
            chunks.append((chunk_text, current_pos))

            # Move to next chunk with overlap (but not past the current end)
            next_pos = end_pos - self.GLINER_OVERLAP_CHARS
            if next_pos <= current_pos:
                next_pos = end_pos  # Avoid infinite loop
            current_pos = next_pos

            # If we've passed the end, stop
            if current_pos >= len(text):
                break

        if self.debug_mode:
            print(f"[CHUNKING] Split text ({len(text)} chars) into {len(chunks)} chunks")

        return chunks

    def _find_entities_with_gliner(self, text: str, threshold: float = 0.3,
                                   custom_labels: Optional[List[str]] = None) -> List[Dict]:
        """
        Use GLiNER to find entities in text.

        Automatically chunks long texts to avoid GLiNER's 384 token limit.
        Entities from overlapping regions are deduplicated.

        Uses two-pass detection for addresses to avoid label interference:
        - Pass 1: Detect addresses separately (with lower threshold)
        - Pass 2: Detect other entities together

        Note: GLiNER uses positional encoding for labels, so label order affects
        detection confidence scores (see: https://github.com/urchade/GLiNER/issues/192).
        Running address detection separately avoids this interference.

        Args:
            text: Text to analyze
            threshold: Confidence threshold (0.0-1.0)
            custom_labels: Custom labels to use instead of default
        """
        labels = custom_labels if custom_labels is not None else self.labels

        # Split text into chunks if needed
        chunks = self._split_text_into_chunks(text)

        # Check if we need two-pass detection (address + other labels)
        has_address = 'address' in [l.lower() for l in labels]
        other_labels = [l for l in labels if l.lower() != 'address']

        # Two-pass detection to avoid GLiNER label interference
        # GLiNER uses positional encoding, so label order affects scores.
        # Address detection is more reliable when run separately.
        # See: https://github.com/urchade/GLiNER/issues/192
        if has_address and other_labels:
            if self.debug_mode:
                print(f"[GLINER] Using two-pass detection: address + {other_labels}")

            # Pass 1: Address detection with slightly lower threshold
            address_threshold = max(0.3, threshold - 0.1)  # Lower threshold for addresses
            address_entities = self._gliner_predict_chunks(text, chunks, ['address'], address_threshold)

            # Pass 2: Other entities with normal threshold
            # Put 'person' first as it's typically highest priority for detection
            other_entities = self._gliner_predict_chunks(text, chunks, other_labels, threshold)

            # Combine results
            all_entities = address_entities + other_entities

            if self.debug_mode:
                print(f"[GLINER] Two-pass results: {len(address_entities)} addresses, {len(other_entities)} others")

            return all_entities

        # Single-pass detection (either only address or no address label)
        return self._gliner_predict_chunks(text, chunks, labels, threshold)

    def _gliner_predict_chunks(self, text: str, chunks: List[tuple],
                                labels: List[str], threshold: float) -> List[Dict]:
        """
        Run GLiNER prediction across text chunks with deduplication.

        Args:
            text: Original full text
            chunks: List of (chunk_text, offset) tuples
            labels: Labels to detect
            threshold: Confidence threshold

        Returns:
            List of detected entities with adjusted positions
        """
        if len(chunks) == 1:
            # No chunking needed, process directly
            return self.model.predict_entities(text, labels, threshold=threshold)

        # Process each chunk and collect entities with adjusted positions
        all_entities = []
        seen_spans = set()  # Track (start, end, label) to deduplicate overlaps

        for chunk_text, offset in chunks:
            chunk_entities = self.model.predict_entities(chunk_text, labels, threshold=threshold)

            for entity in chunk_entities:
                # Adjust positions to original text coordinates
                adjusted_start = entity['start'] + offset
                adjusted_end = entity['end'] + offset

                # Create a unique key for deduplication
                span_key = (adjusted_start, adjusted_end, entity['label'])

                if span_key not in seen_spans:
                    seen_spans.add(span_key)
                    all_entities.append({
                        'start': adjusted_start,
                        'end': adjusted_end,
                        'text': entity.get('text', text[adjusted_start:adjusted_end]),
                        'label': entity['label'],
                        'score': entity.get('score', 0.5)
                    })

        if self.debug_mode:
            print(f"[CHUNKING] Found {len(all_entities)} entities across {len(chunks)} chunks")

        return all_entities

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

        Special handling: Address entities get a score boost when competing with person
        entities, since street names often contain person names (e.g., "Antti Mäen kuja").
        """
        if not entities:
            return []

        # Apply score boost for address entities that overlap with person entities
        # This helps addresses win when street names contain person names
        # (e.g., "Antti Mäen kuja" - GLiNER might detect "Antti Mäen" as person)

        boosted_entities = []
        for entity in entities:
            boosted_entity = entity.copy()

            # Check if this is an address entity and boost is enabled
            if self.address_score_boost > 0 and entity.get('label', '').lower() == 'address':
                # Check if there's an overlapping person entity
                has_overlapping_person = any(
                    other.get('label', '').lower() == 'person' and
                    not (other['end'] <= entity['start'] or other['start'] >= entity['end'])
                    for other in entities if other is not entity
                )

                if has_overlapping_person:
                    # Boost the address score
                    original_score = entity.get('score', 0.5)
                    boosted_entity['score'] = min(1.0, original_score + self.address_score_boost)
                    if self.debug_mode:
                        print(f"[BOOST] Address '{entity.get('text')}' score: {original_score:.3f} -> {boosted_entity['score']:.3f} (boost: +{self.address_score_boost})")

            boosted_entities.append(boosted_entity)

        # Sort by start position, then prioritize score=1.0 (regex/blocklist), then length
        boosted_entities.sort(key=lambda x: (
            x['start'],  # Same start position
            0 if x.get('score', 0) == 1.0 else 1,  # Prioritize regex/blocklist (score=1.0)
            -(x['end'] - x['start']),  # Then longest span
            -x.get('score', 0)  # Then highest score
        ))

        non_overlapping = []
        last_end = -1

        for entity in boosted_entities:
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

    def _anonymize_core(self, text: str, profile: str = 'default',
                        labels: Optional[List[str]] = None,
                        gliner_threshold: float = 0.3) -> tuple[str, List[Dict]]:
        """
        Core anonymization logic returning both anonymized text and detected entities.

        This is an internal method that performs the actual anonymization work.
        Use anonymize() or anonymize_text() for public API.

        Args:
            text: Text to anonymize
            profile: Profile name for configuration (defaults to 'default')
            labels: List of entity labels to detect with suffixes
            gliner_threshold: GLiNER confidence threshold (0.0-1.0)

        Returns:
            Tuple of (anonymized_text, entities_list)
        """
        total_start = time.perf_counter() if self.debug_mode else None

        if not text:
            return text, []

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
            t0 = time.perf_counter() if self.debug_mode else None
            entities = self._find_entities_with_gliner(text, threshold=gliner_threshold,
                                                       custom_labels=gliner_labels)
            if self.debug_mode:
                elapsed = time.perf_counter() - t0
                print(f"[TIMING] GLiNER prediction: {elapsed:.3f}s")
                if elapsed > 0.5:
                    print(f"[TIMING] WARNING: GLiNER prediction slow (>{0.5}s)")

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
            t0 = time.perf_counter() if self.debug_mode else None
            blocklist_entities = self._find_blocklist_entities(text, blocklist)
            entities.extend(blocklist_entities)
            if self.debug_mode:
                elapsed = time.perf_counter() - t0
                print(f"[TIMING] Blocklist matching: {elapsed:.3f}s")

        # Add regex pattern entities from the profile
        # If the caller requested specific regex types (via labels), only apply those.
        # Otherwise (no specific regex labels requested) apply all profile regex patterns.
        if regex_patterns:
            t0 = time.perf_counter() if self.debug_mode else None
            if regex_entity_types is None:
                # No specific regex types requested -> apply all patterns from profile
                entities.extend(self._find_entities_with_regex(text, regex_patterns))
            else:
                # Apply only requested regex entity types
                entities.extend(self._find_entities_with_regex(text, regex_patterns, allowed_types=regex_entity_types))
            if self.debug_mode:
                elapsed = time.perf_counter() - t0
                print(f"[TIMING] Regex patterns: {elapsed:.3f}s")

        # Filter out grantlisted entities
        if grantlist:
            entities = self._filter_grantlist(entities, grantlist)

        # Remove overlapping entities
        entities = self._remove_overlapping_entities(entities)

        if not entities:
            if self.debug_mode:
                total_elapsed = time.perf_counter() - total_start
                print(f"[TIMING] Total _anonymize_core: {total_elapsed:.3f}s (no entities found)")
            return text, []

        # Replace entities in reverse order to maintain positions
        t0 = time.perf_counter() if self.debug_mode else None
        result = text
        for entity in sorted(entities, key=lambda x: x['start'], reverse=True):
            start, end = entity['start'], entity['end']
            label = self._map_entity_label(entity['label'])
            result = result[:start] + f"<{label}>" + result[end:]
        if self.debug_mode:
            elapsed = time.perf_counter() - t0
            print(f"[TIMING] Entity replacement: {elapsed:.3f}s")

        if self.debug_mode:
            total_elapsed = time.perf_counter() - total_start
            print(f"[TIMING] Total _anonymize_core: {total_elapsed:.3f}s ({len(entities)} entities)")
            if total_elapsed > 1.0:
                print(f"[TIMING] WARNING: Total processing slow (>1.0s)")

        return result, entities

    def anonymize_text(self, text: str, profile: str = 'default',
                      labels: Optional[List[str]] = None,
                      gliner_threshold: float = 0.5) -> str:
        """
        Anonymize text and return only the anonymized string.

        Args:
            text: Text to anonymize
            profile: Profile name for configuration (defaults to 'default')
            labels: List of entity labels to detect with suffixes:
                   - '_ner' for NER/GLiNER labels (e.g., 'person_ner', 'email_ner')
                   - '_regex' for regex patterns (e.g., 'fi_hetu_regex', 'fi_puhelin_regex')
                   - 'blocklist' to enable blocklist matching
                   - Unsuffixed labels are treated as NER labels for backward compatibility
                   If None, uses profile labels or defaults
            gliner_threshold: GLiNER confidence threshold (0.0-1.0, default 0.3)

        Returns:
            Anonymized text with entities replaced by labels
        """
        anonymized_text, _ = self._anonymize_core(text, profile, labels, gliner_threshold)
        return anonymized_text

    def anonymize(self, text: str,
                  labels: Optional[List[str]] = None,
                  profile: str = 'default',
                  gliner_threshold: float = 0.6) -> AnonymizerResult:
        """
        Anonymize text and return detailed results including summary statistics.

        Args:
            text: Text to anonymize
            labels: List of entity labels to detect with suffixes:
                   - '_ner' for NER/GLiNER labels (e.g., 'person_ner', 'email_ner')
                   - '_regex' for regex patterns (e.g., 'fi_hetu_regex', 'fi_puhelin_regex')
                   - 'blocklist' to enable blocklist matching
                   - Unsuffixed labels treated as NER for backward compatibility
                   Examples: ['person_ner', 'email_ner', 'fi_hetu_regex', 'blocklist']
            profile: Profile name for blocklist/grantlist/regex patterns
            gliner_threshold: GLiNER confidence threshold (0.0-1.0, default 0.6)

        Returns:
            AnonymizerResult with anonymized text, summary counts, and entity details
        """
        if not text:
            return AnonymizerResult(anonymized_text=None, summary={}, details={})

        anonymized_text, entities = self._anonymize_core(
            text,
            profile=profile,
            labels=labels,
            gliner_threshold=gliner_threshold
        )

        summary = {}
        details = {}

        for entity in entities:
            entity_type = self._map_entity_label(entity['label'])
            entity_text = entity.get('text', text[entity['start']:entity['end']])

            if entity_type in summary:
                summary[entity_type] += 1
                details[entity_type].append(entity_text)
            else:
                summary[entity_type] = 1
                details[entity_type] = [entity_text]

        return AnonymizerResult(anonymized_text=anonymized_text, summary=summary, details=details)

    def combine_statistics(self, statistics_list: List[Dict[str, int]]) -> Dict[str, int]:
        """
        Combine multiple statistics dictionaries into a single aggregated summary.

        Args:
            statistics_list: List of summary dicts from multiple anonymize() calls

        Returns:
            Combined dictionary with aggregated counts
        """
        combined = {}
        for stats in statistics_list:
            if stats:
                for entity_type, count in stats.items():
                    combined[entity_type] = combined.get(entity_type, 0) + count
        return combined

    def combine_details(self, details_list: List[Dict[str, List[str]]]) -> Dict[str, List[str]]:
        """
        Combine multiple details dictionaries into a single aggregated collection.

        Args:
            details_list: List of details dicts from multiple anonymize() calls

        Returns:
            Combined dictionary with aggregated entity text lists
        """
        combined = {}
        for details in details_list:
            if details:
                for entity_type, entities in details.items():
                    if entity_type not in combined:
                        combined[entity_type] = []
                    combined[entity_type].extend(entities)
        return combined

