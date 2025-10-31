"""
LiteLLM multi-modal extractor plugin.

This plugin provides document-to-markdown extraction using vision-capable
LLMs via the LiteLLM framework. Supports multiple providers including
OpenAI, Anthropic, Google, and more.
"""

from typing import Tuple, TYPE_CHECKING

# Always import config (no external dependencies)
from .config import (
    LiteLLMConfig,
    LITELLM_BASIC_FIELDS,
    LITELLM_ADVANCED_FIELDS,
    LITELLM_CONDITIONAL_FIELDS,
    LiteLLMModelEnum,
)

# Plugin metadata
ENGINE_NAME = "litellm"
ENGINE_DISPLAY_NAME = "LiteLLM Vision (Multi-Provider)"

# Conditionally import extractor only if dependencies are available
_extractor_available = False
_import_error = None

try:
    from .extractor import LiteLLMExtractor
    _extractor_available = True
except ImportError as e:
    _import_error = str(e)
    # Create a dummy class for when dependency isn't installed
    class LiteLLMExtractor:
        def __init__(self, *args, **kwargs):
            raise ImportError(f"LiteLLM not available: {_import_error}")

# Standard plugin interface exports
Extractor = LiteLLMExtractor
Config = LiteLLMConfig
BASIC_FIELDS = LITELLM_BASIC_FIELDS
ADVANCED_FIELDS = LITELLM_ADVANCED_FIELDS
CONDITIONAL_FIELDS = LITELLM_CONDITIONAL_FIELDS


def is_available() -> Tuple[bool, str]:
    """
    Check if LiteLLM dependencies are installed and available.

    Returns:
        Tuple of (is_available, message)
        - is_available: True if litellm and dependencies are installed
        - message: Empty string if available, error message otherwise
    """
    import os

    # Check if library is installed
    if not _extractor_available:
        return False, f"LiteLLM not installed: {_import_error}"

    # Double-check the actual library is importable
    try:
        import litellm
        import fitz  # PyMuPDF
    except ImportError as e:
        return False, f"Required dependency not installed: {e}"

    # Check if at least one API key is configured
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
    has_gemini = bool(os.environ.get("GEMINI_API_KEY"))

    if not (has_openai or has_anthropic or has_gemini):
        return False, "No API keys configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY environment variable"

    return True, ""


__all__ = [
    'Extractor',
    'Config',
    'BASIC_FIELDS',
    'ADVANCED_FIELDS',
    'CONDITIONAL_FIELDS',
    'ENGINE_NAME',
    'ENGINE_DISPLAY_NAME',
    'is_available',
    # Also export the actual classes for direct imports
    'LiteLLMExtractor',
    'LiteLLMConfig',
    'LiteLLMModelEnum',
]
