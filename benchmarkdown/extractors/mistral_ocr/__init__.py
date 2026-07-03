"""
Mistral OCR extractor plugin.

This plugin provides document-to-markdown extraction using Mistral's OCR
endpoint (``/v1/ocr``, model ``mistral-ocr-latest``). Mistral OCR returns
markdown directly, one entry per page, which the extractor concatenates into a
single markdown document.
"""

from typing import Tuple

# Always import config (no external dependencies)
from .config import (
    MistralOCRConfig,
    TableFormatEnum,
    MISTRAL_OCR_BASIC_FIELDS,
    MISTRAL_OCR_ADVANCED_FIELDS,
)

# Plugin metadata
ENGINE_NAME = "mistral_ocr"
ENGINE_DISPLAY_NAME = "Mistral OCR (Cloud)"

# Conditionally import extractor only if dependencies are available
_extractor_available = False
_import_error = None

try:
    from .extractor import MistralOCRExtractor
    _extractor_available = True
except ImportError as e:
    _import_error = str(e)

    class MistralOCRExtractor:
        def __init__(self, *args, **kwargs):
            raise ImportError(f"Mistral OCR not available: {_import_error}")

# Standard plugin interface exports
Extractor = MistralOCRExtractor
Config = MistralOCRConfig
BASIC_FIELDS = MISTRAL_OCR_BASIC_FIELDS
ADVANCED_FIELDS = MISTRAL_OCR_ADVANCED_FIELDS


def is_available() -> Tuple[bool, str]:
    """
    Check if Mistral OCR dependencies are installed and configured.

    Returns:
        Tuple of (is_available, message)
        - is_available: True if the mistralai SDK is installed and MISTRAL_API_KEY is set
        - message: Empty string if available, error message otherwise
    """
    import os

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        return False, "MISTRAL_API_KEY environment variable not set"

    if not _extractor_available:
        return False, f"Mistral OCR not installed: {_import_error}"

    try:
        from mistralai.client import Mistral  # noqa: F401
        return True, ""
    except ImportError as e:
        return False, f"Mistral OCR not installed: {e}"


__all__ = [
    'Extractor',
    'Config',
    'BASIC_FIELDS',
    'ADVANCED_FIELDS',
    'ENGINE_NAME',
    'ENGINE_DISPLAY_NAME',
    'is_available',
    # Also export the actual classes for direct imports
    'MistralOCRExtractor',
    'MistralOCRConfig',
    'TableFormatEnum',
]
