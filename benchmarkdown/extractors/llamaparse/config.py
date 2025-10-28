"""
Configuration models for LlamaParse document extractor.

This module provides Pydantic models for configuring the LlamaParse extractor
with type validation and documentation based on the official LlamaParse API.
"""

import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ResultTypeEnum(str, Enum):
    """Output format type."""
    MARKDOWN = "markdown"
    TEXT = "text"


class LlamaParseConfig(BaseModel):
    """
    Configuration for LlamaParse document extractor.

    LlamaParse is a cloud-based document parsing service from LlamaIndex
    that provides high-quality extraction with advanced OCR and layout understanding.

    Based on: https://github.com/run-llama/llama_cloud_services
    """

    # ========== BASIC OPTIONS ==========

    api_key: str = Field(
        default_factory=lambda: os.getenv("LLAMA_CLOUD_API_KEY", ""),
        description="LlamaCloud API key (loaded from LLAMA_CLOUD_API_KEY environment variable)"
    )

    result_type: ResultTypeEnum = Field(
        default=ResultTypeEnum.MARKDOWN,
        description="Output format: markdown or text"
    )

    language: str = Field(
        default="en",
        description="Document language for OCR (e.g., 'en', 'es', 'fr', 'de', 'auto')"
    )

    parsing_instruction: Optional[str] = Field(
        default=None,
        description="Custom instruction to guide the parsing (e.g., 'Extract tables and preserve formatting')"
    )

    target_pages: Optional[str] = Field(
        default=None,
        description="Specific pages to parse (e.g., '1-5', '1,3,5-7'). If not set, all pages are parsed."
    )

    premium_mode: bool = Field(
        default=False,
        description="Use the best parser mode (higher accuracy, higher cost)"
    )

    # ========== ADVANCED OPTIONS ==========

    # === Mode & Performance ===
    fast_mode: bool = Field(
        default=False,
        description="Use faster mode (skips OCR of images and table reconstruction). Not compatible with premium_mode."
    )

    continuous_mode: bool = Field(
        default=False,
        description="Parse documents continuously for better results on tables spanning multiple pages"
    )

    # === Table Extraction ===
    aggressive_table_extraction: bool = Field(
        default=False,
        description="Extract tables aggressively (may lead to false positives)"
    )

    adaptive_long_table: bool = Field(
        default=False,
        description="Detect and adapt output for long tables"
    )

    merge_tables_across_pages_in_markdown: bool = Field(
        default=False,
        description="Merge tables that span across multiple pages in markdown output"
    )

    outlined_table_extraction: bool = Field(
        default=False,
        description="Use dedicated approach for tables with outlined cells (spreadsheet-style)"
    )

    output_tables_as_HTML: bool = Field(
        default=False,
        description="Output tables as HTML in the markdown"
    )

    compact_markdown_table: bool = Field(
        default=False,
        description="Output compact markdown tables (without trailing spaces in cells)"
    )

    # === OCR & Text Extraction ===
    disable_ocr: bool = Field(
        default=False,
        description="Disable OCR, only extract copyable text from the document"
    )

    high_res_ocr: bool = Field(
        default=False,
        description="Use high resolution OCR for better accuracy (slower)"
    )

    skip_diagonal_text: bool = Field(
        default=False,
        description="Skip extraction of diagonal/rotated text"
    )

    preserve_very_small_text: bool = Field(
        default=False,
        description="Try to preserve very small text lines (useful for CAD drawings)"
    )

    do_not_unroll_columns: bool = Field(
        default=False,
        description="Keep column layout according to document structure (may reduce accuracy)"
    )

    # === Layout & Structure ===
    extract_layout: bool = Field(
        default=False,
        description="Extract layout information from the document (costs 1 credit per page)"
    )

    extract_charts: bool = Field(
        default=False,
        description="Extract/tag charts from the document"
    )

    annotate_links: bool = Field(
        default=False,
        description="Annotate links found in the document to extract their URLs"
    )

    preserve_layout_alignment_across_pages: bool = Field(
        default=False,
        description="Preserve grid alignment across pages in text mode"
    )

    disable_image_extraction: bool = Field(
        default=False,
        description="Do not extract images from the document (faster parsing)"
    )

    # === Page Formatting ===
    page_separator: Optional[str] = Field(
        default=None,
        description="Page separator (default: '\\n---\\n'). Can include {page_number} template variable."
    )

    page_prefix: Optional[str] = Field(
        default=None,
        description="Prefix to add to each page. Can include {page_number} template variable."
    )

    page_suffix: Optional[str] = Field(
        default=None,
        description="Suffix to add to each page. Can include {page_number} template variable."
    )

    split_by_page: bool = Field(
        default=True,
        description="Whether to split output by page using the page separator"
    )

    # === Cache & Optimization ===
    invalidate_cache: bool = Field(
        default=False,
        description="Force re-parsing by invalidating cached results (documents cached for 48 hours)"
    )

    do_not_cache: bool = Field(
        default=False,
        description="Do not cache parsing results (you will be re-charged for reprocessing)"
    )

    max_pages: Optional[int] = Field(
        default=None,
        description="Maximum number of pages to extract. If 0 or None, all pages are extracted."
    )

    # === Vendor Multimodal Models ===
    use_vendor_multimodal_model: bool = Field(
        default=False,
        description="Use a vendor multimodal model (e.g., Claude, Gemini) for parsing"
    )

    vendor_multimodal_model_name: Optional[str] = Field(
        default=None,
        description="Name of the vendor multimodal model to use"
    )

    vendor_multimodal_api_key: Optional[str] = Field(
        default=None,
        description="API key for the vendor multimodal model"
    )

    # === Bounding Box ===
    bbox_top: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Top margin of bounding box (0-1 as percentage of page height)"
    )

    bbox_bottom: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Bottom margin of bounding box (0-1 as percentage of page height)"
    )

    bbox_left: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Left margin of bounding box (0-1 as percentage of page width)"
    )

    bbox_right: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Right margin of bounding box (0-1 as percentage of page width)"
    )

    # === System Options ===
    num_workers: int = Field(
        default=4,
        ge=1,
        lt=20,
        description="Number of workers for parallel page processing"
    )

    verbose: bool = Field(
        default=False,
        description="Enable verbose logging"
    )

    show_progress: bool = Field(
        default=True,
        description="Show progress when parsing multiple files"
    )

    ignore_errors: bool = Field(
        default=True,
        description="Whether to ignore and skip errors raised during parsing"
    )

    max_timeout: int = Field(
        default=2000,
        description="Maximum timeout in seconds to wait for parsing to finish"
    )

    class Config:
        use_enum_values = True

    @field_validator("premium_mode", mode="after")
    def validate_premium_mode(cls, v, info):
        # Premium mode and fast mode are incompatible
        # Note: This validator runs after premium_mode is set, so we check data
        if v and info.data.get("fast_mode"):
            raise ValueError("premium_mode and fast_mode are not compatible")
        return v

    @field_validator("fast_mode", mode="after")
    def validate_fast_mode(cls, v, info):
        # Fast mode and premium mode are incompatible
        if v and info.data.get("premium_mode"):
            raise ValueError("fast_mode and premium_mode are not compatible")
        return v


# Field groupings for UI generation
# Note: api_key is intentionally excluded - it's loaded from environment variables only
LLAMAPARSE_BASIC_FIELDS = [
    "result_type",
    "language",
    "parsing_instruction",
    "target_pages",
    "premium_mode",
]

LLAMAPARSE_ADVANCED_FIELDS = [
    # Mode & Performance
    "fast_mode",
    "continuous_mode",

    # Table Extraction
    "aggressive_table_extraction",
    "adaptive_long_table",
    "merge_tables_across_pages_in_markdown",
    "outlined_table_extraction",
    "output_tables_as_HTML",
    "compact_markdown_table",

    # OCR & Text
    "disable_ocr",
    "high_res_ocr",
    "skip_diagonal_text",
    "preserve_very_small_text",
    "do_not_unroll_columns",

    # Layout & Structure
    "extract_layout",
    "extract_charts",
    "annotate_links",
    "preserve_layout_alignment_across_pages",
    "disable_image_extraction",

    # Page Formatting
    "page_separator",
    "page_prefix",
    "page_suffix",
    "split_by_page",

    # Cache & Optimization
    "invalidate_cache",
    "do_not_cache",
    "max_pages",

    # Vendor Models
    "use_vendor_multimodal_model",
    "vendor_multimodal_model_name",
    "vendor_multimodal_api_key",

    # Bounding Box
    "bbox_top",
    "bbox_bottom",
    "bbox_left",
    "bbox_right",

    # System
    "num_workers",
    "verbose",
    "show_progress",
    "ignore_errors",
    "max_timeout",
]
