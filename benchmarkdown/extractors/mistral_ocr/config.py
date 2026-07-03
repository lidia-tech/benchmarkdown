"""
Configuration models for the Mistral OCR document extractor.

This module provides a Pydantic model for configuring the Mistral OCR extractor
with type validation and documentation. All options map directly to parameters
of the Mistral ``/v1/ocr`` endpoint (``client.ocr.process``) as exposed by the
``mistralai`` SDK.
"""

import os
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TableFormatEnum(str, Enum):
    """Format used to render tables in the extracted markdown."""
    MARKDOWN = "markdown"
    HTML = "html"


class MistralOCRConfig(BaseModel):
    """
    Configuration for the Mistral OCR document extractor.

    Mistral OCR is a dedicated OCR endpoint (model ``mistral-ocr-latest``) that
    returns markdown directly, one entry per page. Every field here corresponds
    to a real ``ocr.process`` parameter.
    """

    # ========== AUTHENTICATION ==========

    api_key: str = Field(
        default_factory=lambda: os.getenv("MISTRAL_API_KEY", ""),
        description="Mistral API key (loaded from MISTRAL_API_KEY environment variable)"
    )

    # ========== BASIC OPTIONS ==========

    model: str = Field(
        default="mistral-ocr-latest",
        description="Mistral OCR model to use"
    )

    pages: Optional[str] = Field(
        default=None,
        description=(
            "Specific pages to process as comma-separated numbers and ranges, "
            "0-based (e.g. '0,1,2' or '0-5' or '0,2-4'). Leave empty for all pages."
        )
    )

    table_format: TableFormatEnum = Field(
        default=TableFormatEnum.MARKDOWN,
        description="Format for tables in the output: markdown or HTML"
    )

    extract_header: bool = Field(
        default=True,
        description="Extract page headers into the markdown output"
    )

    extract_footer: bool = Field(
        default=True,
        description="Extract page footers into the markdown output"
    )

    # ========== ADVANCED OPTIONS ==========

    include_image_base64: bool = Field(
        default=False,
        description="Include base64-encoded images of extracted figures in the response"
    )

    image_limit: Optional[int] = Field(
        default=None,
        ge=0,
        description="Maximum number of images to extract (leave empty for no limit)"
    )

    image_min_size: Optional[int] = Field(
        default=None,
        ge=0,
        description="Minimum height and width (px) for an image to be extracted (leave empty for no minimum)"
    )

    # ========== ROBUSTNESS ==========

    max_retries: int = Field(
        default=3,
        ge=0,
        description=(
            "Number of times to retry the upload/OCR sequence on transient API "
            "failures (post-upload 404 race, 5xx, 429, connection errors)"
        )
    )

    class Config:
        use_enum_values = True

    def to_ocr_kwargs(self) -> dict:
        """
        Build the keyword arguments for ``client.ocr.process``.

        The ``document`` and ``model`` arguments that identify what to process
        are supplied by the extractor; this method contributes the configurable
        parameters. Options left at "no value" (empty ``pages``, ``None`` image
        controls) are omitted so the API applies its own defaults.
        """
        table_format = self.table_format
        # With use_enum_values=True this is already the plain string, but guard
        # against a raw enum in case the model is constructed differently.
        if isinstance(table_format, TableFormatEnum):
            table_format = table_format.value

        kwargs: dict = {
            "model": self.model,
            "table_format": table_format,
            "extract_header": self.extract_header,
            "extract_footer": self.extract_footer,
            "include_image_base64": self.include_image_base64,
        }

        if self.pages and self.pages.strip():
            # The API natively parses comma-separated numbers and ranges.
            kwargs["pages"] = self.pages.strip()

        if self.image_limit is not None:
            kwargs["image_limit"] = self.image_limit

        if self.image_min_size is not None:
            kwargs["image_min_size"] = self.image_min_size

        return kwargs


# Field groupings for UI generation
# Note: api_key is intentionally excluded - it's loaded from environment variables only

MISTRAL_OCR_BASIC_FIELDS = [
    "model",
    "pages",
    "table_format",
    "extract_header",
    "extract_footer",
]

MISTRAL_OCR_ADVANCED_FIELDS = [
    "include_image_base64",
    "image_limit",
    "image_min_size",
]

# Export names for consistency with the plugin interface
BASIC_FIELDS = MISTRAL_OCR_BASIC_FIELDS
ADVANCED_FIELDS = MISTRAL_OCR_ADVANCED_FIELDS
