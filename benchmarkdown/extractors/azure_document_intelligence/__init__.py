"""
Azure Document Intelligence extractor plugin.

This plugin provides document-to-markdown extraction using Microsoft's
Azure Document Intelligence service (formerly Form Recognizer).
"""

import os
from typing import Tuple

# Try to import the plugin components, but don't fail if dependencies are missing
# The registry will catch any ImportError and handle it gracefully
try:
    from .extractor import AzureDocIntelExtractor
    from .config import (
        AzureDocIntelConfig,
        AZURE_DOCUMENT_INTELLIGENCE_BASIC_FIELDS,
        AZURE_DOCUMENT_INTELLIGENCE_ADVANCED_FIELDS,
    )

    # Standard plugin interface exports
    Extractor = AzureDocIntelExtractor
    Config = AzureDocIntelConfig
    BASIC_FIELDS = AZURE_DOCUMENT_INTELLIGENCE_BASIC_FIELDS
    ADVANCED_FIELDS = AZURE_DOCUMENT_INTELLIGENCE_ADVANCED_FIELDS

    _import_successful = True
except ImportError as e:
    # If imports fail, create dummy exports so the plugin interface is still valid
    # The is_available() function will return False with the error message
    _import_error = str(e)
    _import_successful = False

    # Create minimal stubs for the registry to validate
    from pydantic import BaseModel

    class Config(BaseModel):
        """Stub config when dependencies are missing."""
        pass

    class Extractor:
        """Stub extractor when dependencies are missing."""
        def __init__(self, *args, **kwargs):
            raise ImportError(f"Azure Document Intelligence dependencies not installed: {_import_error}")

    BASIC_FIELDS = []
    ADVANCED_FIELDS = []

# Plugin metadata
ENGINE_NAME = "azure_document_intelligence"
ENGINE_DISPLAY_NAME = "Azure Document Intelligence"


def is_available() -> Tuple[bool, str]:
    """
    Check if Azure Document Intelligence dependencies are installed and configured.

    Returns:
        Tuple of (is_available, message)
        - is_available: True if Azure Document Intelligence is available
        - message: Empty string if available, error message otherwise
    """
    # First check if imports were successful
    if not _import_successful:
        return False, f"Azure Document Intelligence SDK not installed: {_import_error}"

    try:
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        from azure.core.credentials import AzureKeyCredential
    except ImportError as e:
        return False, f"Azure Document Intelligence SDK not installed: {e}"

    # Check if credentials are configured
    endpoint = os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    api_key = os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_KEY")

    if not endpoint:
        return False, "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT environment variable not set"

    if not api_key:
        return False, "AZURE_DOCUMENT_INTELLIGENCE_KEY environment variable not set"

    # Validate endpoint format
    if not endpoint.startswith("https://"):
        return False, "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT must start with https://"

    return True, ""


__all__ = [
    'Extractor',
    'Config',
    'BASIC_FIELDS',
    'ADVANCED_FIELDS',
    'ENGINE_NAME',
    'ENGINE_DISPLAY_NAME',
    'is_available',
]
