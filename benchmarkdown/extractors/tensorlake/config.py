"""
Configuration models for TensorLake document extractor.

This module provides Pydantic models for configuring the TensorLake extractor
with type validation and documentation based on the official TensorLake API.

All options are directly derived from the TensorLake SDK source code.
"""

import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ChunkingStrategyEnum(str, Enum):
    """Chunking strategy for parsing."""
    FRAGMENT = "fragment"
    NONE = "none"
    PAGE = "page"
    SECTION = "section"


class TableOutputModeEnum(str, Enum):
    """Table output format mode."""
    MARKDOWN = "markdown"
    HTML = "html"


class TableParsingFormatEnum(str, Enum):
    """Table parsing format (how tables are identified and extracted)."""
    TSR = "tsr"  # Table Structure Recognition - better for clean, grid-like tables
    VLM = "vlm"  # Vision Language Model - better for complex tables


class OcrModelEnum(str, Enum):
    """OCR model provider options."""
    MODEL01 = "model01"
    MODEL02 = "model02"
    MODEL03 = "model03"


class TensorLakeConfig(BaseModel):
    """
    Configuration for TensorLake document extractor.

    TensorLake is a cloud-based document parsing service that provides
    high-quality extraction with advanced layout detection and table recognition.

    All configuration options are directly derived from ParsingOptions and
    EnrichmentOptions in the TensorLake SDK.
    """

    # ========== AUTHENTICATION ==========

    api_key: str = Field(
        default_factory=lambda: os.getenv("TENSORLAKE_API_KEY", ""),
        description="TensorLake API key (loaded from TENSORLAKE_API_KEY environment variable)"
    )

    # ========== BASIC PARSING OPTIONS ==========

    chunking_strategy: Optional[ChunkingStrategyEnum] = Field(
        default=ChunkingStrategyEnum.SECTION,
        description="How to chunk the document: fragment, none, page, or section"
    )

    table_output_mode: TableOutputModeEnum = Field(
        default=TableOutputModeEnum.MARKDOWN,
        description="Format for table output: markdown or HTML"
    )

    table_parsing_format: Optional[TableParsingFormatEnum] = Field(
        default=None,
        description="How to identify and extract tables: TSR (grid-like) or VLM (complex)"
    )

    # ========== DETECTION OPTIONS ==========

    signature_detection: bool = Field(
        default=False,
        description="Detect signatures in the document (incurs additional costs)"
    )

    remove_strikethrough_lines: bool = Field(
        default=False,
        description="Detect and remove strikethrough text (incurs additional costs)"
    )

    skew_detection: bool = Field(
        default=False,
        description="Detect and correct skewed or rotated pages (increases processing time)"
    )

    # ========== LAYOUT AND STRUCTURE OPTIONS ==========

    disable_layout_detection: bool = Field(
        default=False,
        description="Skip layout detection for documents with many tables/images"
    )

    cross_page_header_detection: bool = Field(
        default=False,
        description="Consider headers from different pages when determining hierarchy"
    )

    # ========== OCR OPTIONS ==========

    ocr_model: Optional[OcrModelEnum] = Field(
        default=None,
        description="OCR model to use (model01, model02, or model03)"
    )

    # ========== ENRICHMENT OPTIONS ==========

    figure_summarization: bool = Field(
        default=False,
        description="Generate AI summaries for figures and images"
    )

    figure_summarization_prompt: Optional[str] = Field(
        default=None,
        description="Custom prompt to guide figure summarization"
    )

    table_summarization: bool = Field(
        default=False,
        description="Generate AI summaries for tables"
    )

    table_summarization_prompt: Optional[str] = Field(
        default=None,
        description="Custom prompt to guide table summarization"
    )

    include_full_page_image: bool = Field(
        default=False,
        description="Include full page image context for summarization (may improve quality)"
    )

    class Config:
        use_enum_values = True

    def to_parsing_options(self):
        """Convert to TensorLake ParsingOptions object."""
        from tensorlake.documentai.models import ParsingOptions

        return ParsingOptions(
            chunking_strategy=self.chunking_strategy,
            table_output_mode=self.table_output_mode,
            table_parsing_format=self.table_parsing_format,
            signature_detection=self.signature_detection,
            remove_strikethrough_lines=self.remove_strikethrough_lines,
            skew_detection=self.skew_detection,
            disable_layout_detection=self.disable_layout_detection,
            cross_page_header_detection=self.cross_page_header_detection,
            ocr_model=self.ocr_model,
        )

    def to_enrichment_options(self):
        """Convert to TensorLake EnrichmentOptions object."""
        from tensorlake.documentai.models import EnrichmentOptions

        return EnrichmentOptions(
            figure_summarization=self.figure_summarization,
            figure_summarization_prompt=self.figure_summarization_prompt,
            table_summarization=self.table_summarization,
            table_summarization_prompt=self.table_summarization_prompt,
            include_full_page_image=self.include_full_page_image,
        )


# Field groupings for UI generation
# Note: api_key is intentionally excluded - it's loaded from environment variables only

TENSORLAKE_BASIC_FIELDS = [
    "chunking_strategy",
    "table_output_mode",
    "table_parsing_format",
    "signature_detection",
]

TENSORLAKE_ADVANCED_FIELDS = [
    # Enrichment
    "figure_summarization",
    "table_summarization",
    # Detection
    "remove_strikethrough_lines",
    "skew_detection",
    # Layout & Structure
    "disable_layout_detection",
    "cross_page_header_detection",
    # OCR
    "ocr_model",
]

# Conditional fields: show these only when their parent field is enabled
# Structure: {parent_field: {parent_value: [dependent_fields]}}
TENSORLAKE_CONDITIONAL_FIELDS = {
    "figure_summarization": {
        True: [
            "figure_summarization_prompt",
            "include_full_page_image",
        ]
    },
    "table_summarization": {
        True: [
            "table_summarization_prompt",
            "include_full_page_image",
        ]
    },
}

# Export names for backward compatibility
BASIC_FIELDS = TENSORLAKE_BASIC_FIELDS
ADVANCED_FIELDS = TENSORLAKE_ADVANCED_FIELDS
