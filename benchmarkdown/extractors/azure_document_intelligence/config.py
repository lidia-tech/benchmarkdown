"""
Configuration models for Azure Document Intelligence extractor.

This module provides Pydantic models for configuring the Azure Document Intelligence
extractor with type validation and documentation.
"""

import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class AzureModelEnum(str, Enum):
    """Azure Document Intelligence pre-built models."""
    PREBUILT_LAYOUT = "prebuilt-layout"
    PREBUILT_READ = "prebuilt-read"
    PREBUILT_DOCUMENT = "prebuilt-document"


class OutputFormatEnum(str, Enum):
    """Output content format options."""
    MARKDOWN = "markdown"
    TEXT = "text"


def _get_endpoint_from_env() -> str:
    """Get Azure endpoint from environment variable."""
    return os.environ.get(
        "AZURE_DOC_INTEL_ENDPOINT",
        "https://your-resource.cognitiveservices.azure.com/"
    )


def _get_api_key_from_env() -> str:
    """Get Azure API key from environment variable."""
    return os.environ.get("AZURE_DOC_INTEL_KEY", "")


# ============================================================================
# Main Azure Document Intelligence Configuration
# ============================================================================

class AzureDocIntelConfig(BaseModel):
    """
    Configuration for Azure Document Intelligence extractor.

    Azure Document Intelligence (formerly Form Recognizer) is Microsoft's
    cloud-based document processing service with native markdown output support.

    This configuration is split into basic and advanced sections for
    better user experience.

    Note: Credentials are read from environment variables:
    - AZURE_DOC_INTEL_ENDPOINT: Azure endpoint URL
    - AZURE_DOC_INTEL_KEY: Azure API key
    """

    # ========== BASIC OPTIONS ==========

    endpoint: str = Field(
        default_factory=_get_endpoint_from_env,
        description="Azure endpoint URL (read from AZURE_DOC_INTEL_ENDPOINT)"
    )

    api_key: str = Field(
        default_factory=_get_api_key_from_env,
        description="Azure API key (read from AZURE_DOC_INTEL_KEY)"
    )

    model_id: AzureModelEnum = Field(
        default=AzureModelEnum.PREBUILT_LAYOUT,
        description="Pre-built model to use: layout (full structure), read (OCR only), or document (general)"
    )

    output_content_format: OutputFormatEnum = Field(
        default=OutputFormatEnum.MARKDOWN,
        description="Output format: markdown (structured) or text (plain)"
    )

    # ========== ADVANCED OPTIONS ==========

    pages: Optional[str] = Field(
        default=None,
        description="Page range to process (e.g., '1-5', '1,3,5-7'). Leave empty for all pages."
    )

    locale: Optional[str] = Field(
        default=None,
        description="Document locale hint for better accuracy (e.g., 'en-US', 'it-IT', 'de-DE')"
    )

    class Config:
        use_enum_values = True

    def to_azure_options(self):
        """
        Convert this configuration to Azure Document Intelligence's native format.

        Returns:
            Tuple of (endpoint, api_key, model_id, analyze_request_kwargs)
        """
        # Build analyze_request kwargs
        analyze_kwargs = {
            "output_content_format": self.output_content_format,
        }

        # Add optional parameters
        if self.pages:
            analyze_kwargs["pages"] = self.pages

        if self.locale:
            analyze_kwargs["locale"] = self.locale

        return self.endpoint, self.api_key, self.model_id, analyze_kwargs


# Field groupings for UI generation
AZURE_DOC_INTEL_BASIC_FIELDS = [
    "model_id",
    "output_content_format",
]

AZURE_DOC_INTEL_ADVANCED_FIELDS = [
    "pages",
    "locale",
]
