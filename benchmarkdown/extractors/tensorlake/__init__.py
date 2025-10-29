"""
TensorLake extractor plugin.

This plugin provides document-to-markdown extraction using TensorLake's
Document Ingestion API. TensorLake provides state-of-the-art layout detection,
table recognition, and optional enrichment features like figure/table summarization.
"""

from typing import Tuple

# Always import config (no external dependencies)
from .config import (
    TensorLakeConfig,
    TENSORLAKE_BASIC_FIELDS,
    TENSORLAKE_ADVANCED_FIELDS,
    TENSORLAKE_CONDITIONAL_FIELDS,
    ChunkingStrategyEnum,
    TableOutputModeEnum,
)

# Plugin metadata
ENGINE_NAME = "tensorlake"
ENGINE_DISPLAY_NAME = "TensorLake (Cloud)"

# Conditionally import extractor only if dependencies are available
_extractor_available = False
_import_error = None

try:
    from .extractor import TensorLakeExtractor
    _extractor_available = True
except ImportError as e:
    _import_error = str(e)
    # Create a dummy class for when dependency isn't installed
    class TensorLakeExtractor:
        def __init__(self, *args, **kwargs):
            raise ImportError(f"TensorLake not available: {_import_error}")

# Standard plugin interface exports
Extractor = TensorLakeExtractor
Config = TensorLakeConfig
BASIC_FIELDS = TENSORLAKE_BASIC_FIELDS
ADVANCED_FIELDS = TENSORLAKE_ADVANCED_FIELDS
CONDITIONAL_FIELDS = TENSORLAKE_CONDITIONAL_FIELDS


def is_available() -> Tuple[bool, str]:
    """
    Check if TensorLake dependencies are installed and available.

    Returns:
        Tuple of (is_available, message)
        - is_available: True if tensorlake is installed and API key is configured
        - message: Empty string if available, error message otherwise
    """
    import os

    # Check if API key is configured
    api_key = os.environ.get("TENSORLAKE_API_KEY")
    if not api_key:
        return False, "TENSORLAKE_API_KEY environment variable not set"

    # Check if library is installed
    if not _extractor_available:
        return False, f"TensorLake not installed: {_import_error}"

    # Double-check the actual library is importable
    try:
        import tensorlake
        return True, ""
    except ImportError as e:
        return False, f"TensorLake not installed: {e}"


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
    'TensorLakeExtractor',
    'TensorLakeConfig',
    'ChunkingStrategyEnum',
    'TableOutputModeEnum',
]
