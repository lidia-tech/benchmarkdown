"""
LlamaParse extractor plugin.

This plugin provides document-to-markdown extraction using LlamaIndex's LlamaParse
cloud service. LlamaParse supports advanced OCR, layout understanding, and optional
GPT-4o integration for complex documents.
"""

from typing import Tuple, TYPE_CHECKING

# Always import config (no external dependencies)
from .config import (
    LlamaParseConfig,
    LLAMAPARSE_BASIC_FIELDS,
    LLAMAPARSE_ADVANCED_FIELDS,
)

# Plugin metadata
ENGINE_NAME = "llamaparse"
ENGINE_DISPLAY_NAME = "LlamaParse (Cloud)"

# Conditionally import extractor only if dependencies are available
_extractor_available = False
_import_error = None

try:
    from .extractor import LlamaParseExtractor
    _extractor_available = True
except ImportError as e:
    _import_error = str(e)
    # Create a dummy class for when dependency isn't installed
    class LlamaParseExtractor:
        def __init__(self, *args, **kwargs):
            raise ImportError(f"LlamaParse not available: {_import_error}")

# Standard plugin interface exports
Extractor = LlamaParseExtractor
Config = LlamaParseConfig
BASIC_FIELDS = LLAMAPARSE_BASIC_FIELDS
ADVANCED_FIELDS = LLAMAPARSE_ADVANCED_FIELDS


def is_available() -> Tuple[bool, str]:
    """
    Check if LlamaParse dependencies are installed and available.

    Returns:
        Tuple of (is_available, message)
        - is_available: True if llama_parse is installed and API key is configured
        - message: Empty string if available, error message otherwise
    """
    import os

    # Check if API key is configured
    api_key = os.environ.get("LLAMA_CLOUD_API_KEY")
    if not api_key:
        return False, "LLAMA_CLOUD_API_KEY environment variable not set"

    # Check if library is installed
    if not _extractor_available:
        return False, f"LlamaParse not installed: {_import_error}"

    # Double-check the actual library is importable
    try:
        import llama_parse
        return True, ""
    except ImportError as e:
        return False, f"LlamaParse not installed: {e}"


__all__ = [
    'Extractor',
    'Config',
    'BASIC_FIELDS',
    'ADVANCED_FIELDS',
    'ENGINE_NAME',
    'ENGINE_DISPLAY_NAME',
    'is_available',
    # Also export the actual classes for direct imports
    'LlamaParseExtractor',
    'LlamaParseConfig',
]
