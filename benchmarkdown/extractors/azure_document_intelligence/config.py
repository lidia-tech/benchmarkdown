"""
Configuration models for Azure Document Intelligence extractor.

This module provides Pydantic models for configuring the Azure Document Intelligence
extractor with type validation and documentation.

Based on Azure SDK API version 2024-11-30.
"""

import os
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class AzureModelEnum(str, Enum):
    """Azure Document Intelligence pre-built models."""
    PREBUILT_LAYOUT = "prebuilt-layout"
    PREBUILT_READ = "prebuilt-read"
    PREBUILT_DOCUMENT = "prebuilt-document"
    # Add other prebuilt models as needed
    # PREBUILT_INVOICE = "prebuilt-invoice"
    # PREBUILT_RECEIPT = "prebuilt-receipt"
    # PREBUILT_ID_DOCUMENT = "prebuilt-idDocument"
    # etc.


class DocumentContentFormat(str, Enum):
    """Output content format options."""
    MARKDOWN = "markdown"
    TEXT = "text"


class DocumentAnalysisFeature(str, Enum):
    """Document analysis features that can be enabled."""
    OCR_HIGH_RESOLUTION = "ocrHighResolution"
    LANGUAGES = "languages"
    BARCODES = "barcodes"
    FORMULAS = "formulas"
    KEY_VALUE_PAIRS = "keyValuePairs"
    STYLE_FONT = "styleFont"
    QUERY_FIELDS = "queryFields"


class AnalyzeOutputOption(str, Enum):
    """Additional output options for document analysis."""
    PDF = "pdf"  # Generate searchable PDF
    FIGURES = "figures"  # Extract figures/images


class StringIndexType(str, Enum):
    """String offset encoding type."""
    TEXT_ELEMENTS = "textElements"
    UNICODE_CODE_POINT = "unicodeCodePoint"
    UTF16_CODE_UNIT = "utf16CodeUnit"


def _get_endpoint_from_env() -> str:
    """Get Azure endpoint from environment variable."""
    return os.environ.get(
        "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT",
        "https://your-resource.cognitiveservices.azure.com/"
    )


def _get_api_key_from_env() -> str:
    """Get Azure API key from environment variable."""
    return os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_KEY", "")


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
    - AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: Azure endpoint URL
    - AZURE_DOCUMENT_INTELLIGENCE_KEY: Azure API key

    Based on Azure SDK API version 2024-11-30.
    """

    # ========== BASIC OPTIONS ==========

    endpoint: str = Field(
        default_factory=_get_endpoint_from_env,
        description="Azure endpoint URL (read from AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT)"
    )

    api_key: str = Field(
        default_factory=_get_api_key_from_env,
        description="Azure API key (read from AZURE_DOCUMENT_INTELLIGENCE_KEY)"
    )

    model_id: AzureModelEnum = Field(
        default=AzureModelEnum.PREBUILT_LAYOUT,
        description="Pre-built model: layout (full structure), read (OCR only), or document (general)"
    )

    output_content_format: DocumentContentFormat = Field(
        default=DocumentContentFormat.MARKDOWN,
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

    features: Optional[List[DocumentAnalysisFeature]] = Field(
        default=None,
        description="Analysis features to enable: OCR high-resolution, languages, barcodes, formulas, key-value pairs, style/font, query fields"
    )

    query_fields: Optional[List[str]] = Field(
        default=None,
        description="Custom field labels to extract (requires 'queryFields' feature). E.g., ['Party1', 'Party2', 'PaymentTerms']"
    )

    output: Optional[List[AnalyzeOutputOption]] = Field(
        default=None,
        description="Additional outputs: PDF (searchable PDF), figures (extract images)"
    )

    string_index_type: Optional[StringIndexType] = Field(
        default=None,
        description="String offset encoding type (advanced): textElements, unicodeCodePoint, or utf16CodeUnit"
    )

    class Config:
        use_enum_values = True

    def to_azure_options(self):
        """
        Convert this configuration to Azure Document Intelligence's native format.

        Returns:
            Tuple of (endpoint, api_key, model_id, analyze_request_kwargs)

        Note: Enum values are converted to their string representations for the Azure API.
        """
        # Convert model_id enum to string value
        model_id_str = self.model_id.value if hasattr(self.model_id, 'value') else self.model_id

        # Build analyze_request kwargs with enum values converted to strings
        analyze_kwargs = {
            "output_content_format": (
                self.output_content_format.value
                if hasattr(self.output_content_format, 'value')
                else self.output_content_format
            ),
        }

        # Add optional parameters
        if self.pages:
            analyze_kwargs["pages"] = self.pages

        if self.locale:
            analyze_kwargs["locale"] = self.locale

        if self.features:
            # Convert enum list to string list
            analyze_kwargs["features"] = [
                f.value if hasattr(f, 'value') else f
                for f in self.features
            ]

        if self.query_fields:
            analyze_kwargs["query_fields"] = self.query_fields

        if self.output:
            # Convert enum list to string list
            analyze_kwargs["output"] = [
                o.value if hasattr(o, 'value') else o
                for o in self.output
            ]

        if self.string_index_type:
            analyze_kwargs["string_index_type"] = (
                self.string_index_type.value
                if hasattr(self.string_index_type, 'value')
                else self.string_index_type
            )

        return self.endpoint, self.api_key, model_id_str, analyze_kwargs


# Field groupings for UI generation
AZURE_DOCUMENT_INTELLIGENCE_BASIC_FIELDS = [
    "model_id",
    "output_content_format",
]

AZURE_DOCUMENT_INTELLIGENCE_ADVANCED_FIELDS = [
    "pages",
    "locale",
    "features",
    "query_fields",
    "output",
    "string_index_type",
]
