"""
API request and response models for the anonymizer service.
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class AnonymizerApiRequest(BaseModel):
    """Request model for anonymization API."""

    text: str = Field(..., description="Text to anonymize")
    labels: Optional[List[str]] = Field(
        default=None,
        description="List of entity labels to detect with suffixes. "
                   "Use '_ner' suffix for NER/GLiNER labels (e.g., 'person_ner', 'email_ner'). "
                   "Use '_regex' suffix for regex patterns (e.g., 'fi_hetu_regex', 'fi_puhelin_regex'). "
                   "Use 'blocklist' to enable blocklist matching. "
                   "Unsuffixed labels treated as NER labels. "
                   "Examples: ['person_ner', 'email_ner', 'fi_hetu_regex', 'fi_puhelin_regex', 'blocklist']"
    )
    profile: Optional[str] = Field(default='default', description="Profile name for custom configuration (blocklist/grantlist)")
    gliner_threshold: Optional[float] = Field(default=0.6, ge=0.0, le=1.0, description="GLiNER confidence threshold (0.0-1.0)")


class AnonymizerApiResponse(BaseModel):
    """Response model for anonymization API."""

    anonymized_txt: Optional[str] = Field(default=None, description="Anonymized text")
    summary: Dict[str, int] = Field(default_factory=dict, description="Statistics of entities found and anonymized")
