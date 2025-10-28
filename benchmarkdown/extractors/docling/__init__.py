"""
Docling extractor plugin.

This plugin provides document-to-markdown extraction using IBM's Docling library.
Docling supports local processing with OCR, table extraction, and various document formats.
"""

from typing import Tuple

from .extractor import DoclingExtractor
from .config import (
    DoclingConfig,
    DOCLING_BASIC_FIELDS,
    DOCLING_ADVANCED_FIELDS,
)

# Standard plugin interface exports
Extractor = DoclingExtractor
Config = DoclingConfig
BASIC_FIELDS = DOCLING_BASIC_FIELDS
ADVANCED_FIELDS = DOCLING_ADVANCED_FIELDS

# Plugin metadata
ENGINE_NAME = "docling"
ENGINE_DISPLAY_NAME = "Docling (Local)"


def is_available() -> Tuple[bool, str]:
    """
    Check if Docling dependencies are installed and available.

    Returns:
        Tuple of (is_available, message)
        - is_available: True if Docling is installed
        - message: Empty string if available, error message otherwise
    """
    try:
        import docling
        return True, ""
    except ImportError as e:
        return False, f"Docling not installed: {e}"


__all__ = [
    'Extractor',
    'Config',
    'BASIC_FIELDS',
    'ADVANCED_FIELDS',
    'ENGINE_NAME',
    'ENGINE_DISPLAY_NAME',
    'is_available',
    # Also export the actual classes for direct imports
    'DoclingExtractor',
    'DoclingConfig',
]
