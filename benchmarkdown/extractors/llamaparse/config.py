"""
Configuration models for LlamaParse document extractor.

This module provides Pydantic models for configuring the LlamaParse extractor
with type validation and documentation.
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
    """

    # ========== BASIC OPTIONS ==========

    api_key: str = Field(
        default_factory=lambda: os.getenv("LLAMA_CLOUD_API_KEY", ""),
        description="LlamaCloud API key (set via LLAMA_CLOUD_API_KEY environment variable)"
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

    # ========== ADVANCED OPTIONS ==========

    gpt4o_mode: bool = Field(
        default=False,
        description="Enable GPT-4o mode for complex document understanding (higher cost, better quality)"
    )

    gpt4o_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", None),
        description="OpenAI API key for GPT-4o mode (set via OPENAI_API_KEY environment variable)"
    )

    skip_diagonal_text: bool = Field(
        default=False,
        description="Skip extraction of diagonal/rotated text"
    )

    invalidate_cache: bool = Field(
        default=False,
        description="Force re-parsing by invalidating cached results"
    )

    do_not_cache: bool = Field(
        default=False,
        description="Do not cache parsing results for future use"
    )

    page_separator: str = Field(
        default="\n\n---\n\n",
        description="Separator string between pages in output"
    )

    page_range: Optional[str] = Field(
        default=None,
        description="Page range to parse (e.g., '1-5', '1,3,5-7')"
    )

    num_workers: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Number of workers for parallel page processing"
    )

    verbose: bool = Field(
        default=False,
        description="Enable verbose logging"
    )

    class Config:
        use_enum_values = True

    @field_validator("api_key")
    def validate_api_key(cls, v):
        if not v:
            raise ValueError(
                "LlamaCloud API key is required. "
                "Set LLAMA_CLOUD_API_KEY environment variable or provide it in configuration."
            )
        return v

    @field_validator("gpt4o_api_key")
    def validate_gpt4o_key(cls, v, values):
        # Only validate if gpt4o_mode is enabled
        if values.data.get("gpt4o_mode") and not v:
            raise ValueError(
                "OpenAI API key is required for GPT-4o mode. "
                "Set OPENAI_API_KEY environment variable or provide it in configuration."
            )
        return v


# Field groupings for UI generation
LLAMAPARSE_BASIC_FIELDS = [
    "api_key",
    "result_type",
    "language",
    "parsing_instruction",
]

LLAMAPARSE_ADVANCED_FIELDS = [
    "gpt4o_mode",
    "gpt4o_api_key",
    "skip_diagonal_text",
    "invalidate_cache",
    "do_not_cache",
    "page_separator",
    "page_range",
    "num_workers",
    "verbose",
]
