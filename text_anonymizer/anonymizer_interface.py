from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from .anonymizer_result import AnonymizerResult


class Anonymizer(ABC):
    '''
    An abstract base class for text anonymization.
    Subclasses must implement the anonymize_text method.
    '''

    def __init__(
        self,
        languages: Optional[List[str]] = None,
        recognizer_configuration: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        """
        Initialize the anonymizer with legacy interface parameters.

        Args:
            languages: List of language codes (e.g., ['fi', 'en'])
            recognizer_configuration: Configuration for recognizers (legacy parameter)
            **kwargs: Additional parameters for backward compatibility
        """
        self.languages = languages or ['en']
        self.recognizer_configuration = recognizer_configuration or []
        # Store any additional kwargs for flexibility during refactoring
        self.config = kwargs

    @abstractmethod
    def anonymize_text(self, text: str) -> str:
        """
        Anonymize the given text.

        Args:
            text: The text to anonymize

        Returns:
            The anonymized text
        """
        pass

    def anonymize(
        self,
        text: str,
        user_languages: Optional[List[str]] = None,
        user_recognizers: Optional[List[str]] = None,
        use_labels: bool = True,
        profile: Optional[str] = None
    ) -> AnonymizerResult:
        """
        Legacy interface for anonymization with detailed results.

        Args:
            text: The text to anonymize
            user_languages: Optional list of language codes to use
            user_recognizers: Optional list of recognizer names to use
            use_labels: Whether to use custom labels (legacy parameter)
            profile: Profile name for custom configurations (legacy parameter)

        Returns:
            AnonymizerResult object with anonymized text, summary, and details
        """
        if not text:
            return AnonymizerResult(anonymized_text=None, summary={}, details={})

        # Call the abstract method to get anonymized text
        anonymized_text = self.anonymize_text(text)

        # For GLiNER implementation, we'll parse the anonymized text to extract entities
        summary, details = self._extract_summary_from_anonymized_text(text, anonymized_text)

        return AnonymizerResult(
            anonymized_text=anonymized_text,
            summary=summary,
            details=details
        )

    def _extract_summary_from_anonymized_text(self, original_text: str, anonymized_text: str) -> tuple:
        """
        Extract summary and details from the anonymized text by comparing with original.

        Args:
            original_text: The original text
            anonymized_text: The anonymized text with placeholders like <PERSON>

        Returns:
            Tuple of (summary dict, details dict)
        """
        summary = {}
        details = {}

        # This is a basic implementation - subclasses can override for better extraction
        # Parse anonymized text to find entity placeholders like <PERSON>, <EMAIL>, etc.
        import re
        entity_pattern = r'<([A-Z\s]+)>'
        matches = re.finditer(entity_pattern, anonymized_text)

        # Build a mapping of positions to find original entities
        offset = 0
        for match in matches:
            entity_type = match.group(1)
            placeholder_start = match.start() - offset

            # Find corresponding position in original text
            # This is approximate - subclasses should implement better tracking

            # Update summary
            if entity_type in summary:
                summary[entity_type] += 1
            else:
                summary[entity_type] = 1
                details[entity_type] = []

            # Adjust offset for next match
            offset += len(match.group(0))

        return summary, details
