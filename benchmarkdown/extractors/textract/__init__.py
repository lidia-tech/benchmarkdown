"""
AWS Textract extractor plugin.

This plugin provides document-to-markdown extraction using AWS Textract cloud service.
AWS Textract automatically extracts text, handwriting, and data from scanned documents.
"""

import os
from typing import Tuple

from .extractor import TextractExtractor
from .config import (
    TextractConfig,
    TEXTRACT_BASIC_FIELDS,
    TEXTRACT_ADVANCED_FIELDS,
)

# Standard plugin interface exports
Extractor = TextractExtractor
Config = TextractConfig
BASIC_FIELDS = TEXTRACT_BASIC_FIELDS
ADVANCED_FIELDS = TEXTRACT_ADVANCED_FIELDS

# Plugin metadata
ENGINE_NAME = "textract"
ENGINE_DISPLAY_NAME = "AWS Textract"


def is_available() -> Tuple[bool, str]:
    """
    Check if AWS Textract dependencies are installed and configured.

    Returns:
        Tuple of (is_available, message)
        - is_available: True if Textract is available
        - message: Empty string if available, error message otherwise
    """
    try:
        import textractor
        from textractor.data.constants import TextractFeatures
    except ImportError as e:
        return False, f"Textractor not installed: {e}"

    # Check if S3 workspace is configured
    s3_workspace = os.environ.get("TEXTRACT_S3_WORKSPACE")
    if not s3_workspace or not s3_workspace.startswith("s3://"):
        return False, "TEXTRACT_S3_WORKSPACE environment variable not configured (must be s3://bucket-name/path/)"

    return True, ""


__all__ = [
    'Extractor',
    'Config',
    'BASIC_FIELDS',
    'ADVANCED_FIELDS',
    'ENGINE_NAME',
    'ENGINE_DISPLAY_NAME',
    'is_available',
    # Also export the actual classes for direct imports
    'TextractExtractor',
    'TextractConfig',
]
