from abc import ABC, abstractmethod
from typing import List, Optional

from .anonymizer_result import AnonymizerResult


class Anonymizer(ABC):
    '''
    An abstract base class for text anonymization.
    Subclasses must implement the anonymize_text method.
    '''

    def __init__(
        self,
        model_name: str = 'urchade/gliner_multi-v2.1',
        debug_mode: bool = False,
        **kwargs
    ):
        """
        Initialize the anonymizer.

        Args:
            model_name: Name of the GLiNER model to use
            debug_mode: Whether to enable debug output
            **kwargs: Additional parameters for flexibility
        """
        self.model_name = model_name
        self.debug_mode = debug_mode
        # Store any additional kwargs for flexibility during refactoring
        self.config = kwargs

    @abstractmethod
    def anonymize_text(
        self,
        text: str,
        profile: str = 'default',
        labels: Optional[List[str]] = None,
        gliner_threshold: float = 0.3
    ) -> str:
        """
        Anonymize the given text.

        Args:
            text: The text to anonymize
            profile: Profile name for configuration (defaults to 'default')
            labels: List of entity labels to detect with suffixes:
                   - '_ner' for NER/GLiNER labels (e.g., 'person_ner', 'email_ner')
                   - '_regex' for regex patterns (e.g., 'fi_hetu_regex', 'fi_puhelin_regex')
                   - 'blocklist' to enable blocklist matching
                   - Unsuffixed labels are treated as NER labels for backward compatibility
            gliner_threshold: GLiNER confidence threshold (0.0-1.0, default 0.3)

        Returns:
            The anonymized text with entities replaced by labels
        """
        pass

    @abstractmethod
    def anonymize(
        self,
        text: str,
        labels: Optional[List[str]] = None,
        profile: str = 'default',
        gliner_threshold: float = 0.6
    ) -> AnonymizerResult:
        """
        Anonymize text and return detailed results including summary statistics.

        Args:
            text: The text to anonymize
            labels: List of entity labels to detect with suffixes:
                   - '_ner' for NER/GLiNER labels (e.g., 'person_ner', 'email_ner')
                   - '_regex' for regex patterns (e.g., 'fi_hetu_regex', 'fi_puhelin_regex')
                   - 'blocklist' to enable blocklist matching
                   - Unsuffixed labels treated as NER for backward compatibility
                   Examples: ['person_ner', 'email_ner', 'fi_hetu_regex', 'blocklist']
            profile: Profile name for blocklist/grantlist/regex patterns
            gliner_threshold: GLiNER confidence threshold (0.0-1.0, default 0.6)

        Returns:
            AnonymizerResult object with anonymized text, summary, and details
        """
        pass
