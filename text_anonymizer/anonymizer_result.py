"""
Result model for text anonymization operations.
"""
from typing import Dict, Optional, List


class AnonymizerResult:
    """
    Result object returned by anonymize operations.

    Attributes:
        anonymized_text: The anonymized version of the input text
        statistics: Dictionary with entity type counts (e.g., {'PERSON': 2, 'EMAIL': 1})
        details: Dictionary with lists of actual entities found (e.g., {'PERSON': ['John Doe', 'Jane Smith']})
    """

    def __init__(
        self,
        anonymized_text: Optional[str] = None,
        statistics: Optional[Dict[str, int]] = None,
        details: Optional[Dict[str, List[str]]] = None
    ):
        self.anonymized_text = anonymized_text
        self.statistics = statistics or {}
        self.details = details or {}

