"""
Configuration models for TensorLake document extractor.

This module provides Pydantic models for configuring the TensorLake extractor
with type validation and documentation based on the official TensorLake API.
"""

import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ChunkingStrategyEnum(str, Enum):
    """Chunking strategy for parsing."""
    SECTION = "section"
    PAGE = "page"


class TableOutputModeEnum(str, Enum):
    """Table output format mode."""
    MARKDOWN = "markdown"
    HTML = "html"


class TensorLakeConfig(BaseModel):
    """
    Configuration for TensorLake document extractor.

    TensorLake is a cloud-based document parsing service that provides
    high-quality extraction with advanced layout detection and table recognition.

    Based on: https://docs.tensorlake.ai/document-ingestion/parsing/read
    """

    # ========== BASIC OPTIONS ==========

    api_key: str = Field(
        default_factory=lambda: os.getenv("TENSORLAKE_API_KEY", ""),
        description="TensorLake API key (loaded from TENSORLAKE_API_KEY environment variable)"
    )

    chunking_strategy: ChunkingStrategyEnum = Field(
        default=ChunkingStrategyEnum.SECTION,
        description="How to chunk the document: by section or by page"
    )

    table_output_mode: TableOutputModeEnum = Field(
        default=TableOutputModeEnum.MARKDOWN,
        description="Format for table output: markdown or HTML"
    )

    signature_detection: bool = Field(
        default=False,
        description="Detect signatures in the document"
    )

    # ========== ADVANCED OPTIONS ==========

    # Enrichment options
    figure_summarization: bool = Field(
        default=False,
        description="Generate summaries for figures and images"
    )

    table_summarization: bool = Field(
        default=False,
        description="Generate summaries for tables"
    )

    # Additional parsing options
    strike_through_detection: bool = Field(
        default=False,
        description="Detect strike-through text in the document"
    )

    # System options
    max_timeout: int = Field(
        default=300,
        ge=30,
        le=600,
        description="Maximum timeout in seconds to wait for parsing to finish (30-600 seconds)"
    )

    class Config:
        use_enum_values = True


# Field groupings for UI generation
# Note: api_key is intentionally excluded - it's loaded from environment variables only
TENSORLAKE_BASIC_FIELDS = [
    "chunking_strategy",
    "table_output_mode",
    "signature_detection",
]

TENSORLAKE_ADVANCED_FIELDS = [
    "figure_summarization",
    "table_summarization",
    "strike_through_detection",
    # Note: max_timeout is a system setting and not exposed in UI (uses default 300s)
]

# No conditional fields for TensorLake (simple configuration)
TENSORLAKE_CONDITIONAL_FIELDS = {}
