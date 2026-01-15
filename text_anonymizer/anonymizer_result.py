"""
Result model for text anonymization operations.
"""
from typing import Dict, Optional, List


class AnonymizerResult:
    """
    Result object returned by anonymize operations.

    Attributes:
        anonymized_text: The anonymized version of the input text
        summary: Dictionary with entity type counts (e.g., {'PERSON': 2, 'EMAIL': 1})
        details: Dictionary with lists of actual entities found (e.g., {'PERSON': ['John Doe', 'Jane Smith']})
    """

    def __init__(
        self,
        anonymized_text: Optional[str] = None,
        summary: Optional[Dict[str, int]] = None,
        details: Optional[Dict[str, List[str]]] = None
    ):
        self.anonymized_text = anonymized_text
        self.summary = summary or {}
        self.details = details or {}

    # Provide a human-friendly string representation for debugging and logs
    def __str__(self) -> str:
        parts = []
        parts.append(f"Anonymized text: {self.anonymized_text!r}")

        if self.summary:
            stats = ", ".join(f"{k}: {v}" for k, v in self.summary.items())
            parts.append(f"Summary: {stats}")
        else:
            parts.append("Summary: {}")

        if self.details:
            # Show counts per entity type rather than printing all values (keeps it concise)
            details_summary = ", ".join(f"{k}: {len(v)}" for k, v in self.details.items())
            parts.append(f"Details (counts): {details_summary}")
        else:
            parts.append("Details: {}")

        return "\n".join(parts)

    def __repr__(self) -> str:
        # repr should be helpful; delegate to __str__ for brevity
        return self.__str__()
