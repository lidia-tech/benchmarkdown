"""
Configuration models for LiteLLM multi-modal document extractor.

This module provides Pydantic models for configuring the LiteLLM extractor
that uses vision-capable LLMs to extract text from document page images.
"""

import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class LiteLLMModelEnum(str, Enum):
    """Common vision-capable models supported by LiteLLM."""
    # OpenAI
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"

    # Anthropic Claude
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_3_5_HAIKU = "claude-3-5-haiku-20241022"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"

    # Google Gemini
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_2_0_FLASH_EXP = "gemini-2.0-flash-exp"

    # Others
    CUSTOM = "custom"


class LiteLLMConfig(BaseModel):
    """
    Configuration for LiteLLM multi-modal document extractor.

    This extractor converts each PDF page to an image and uses vision-capable
    LLMs (via LiteLLM) to extract text. Supports multiple providers including
    OpenAI, Anthropic, Google, and more.
    """

    # ========== BASIC OPTIONS ==========

    model: LiteLLMModelEnum = Field(
        default=LiteLLMModelEnum.GPT_4O_MINI,
        description="Vision-capable model to use for extraction"
    )

    custom_model: Optional[str] = Field(
        default=None,
        description="Custom model identifier (required when model='custom')"
    )

    dpi: int = Field(
        default=300,
        ge=72,
        le=600,
        description="DPI for page rendering (higher = better quality, slower)"
    )

    extraction_prompt: str = Field(
        default="Extract all text from this document page. Preserve the exact layout, formatting, and structure. Include headings, paragraphs, lists, and tables in markdown format. Be thorough and do not skip any text.",
        description="Instruction prompt for the LLM to guide text extraction"
    )

    page_separator: str = Field(
        default="\n\n---\n\n",
        description="Separator between pages in the final markdown output"
    )

    # ========== ADVANCED OPTIONS ==========

    max_tokens: int = Field(
        default=4096,
        ge=256,
        le=32000,
        description="Maximum tokens for each LLM response"
    )

    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0 = deterministic, higher = more creative)"
    )

    image_quality: str = Field(
        default="high",
        description="Image quality for vision API ('low', 'high', 'auto')"
    )

    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retries for failed API calls"
    )

    timeout: int = Field(
        default=120,
        ge=10,
        le=600,
        description="Timeout in seconds for each API call"
    )

    concurrent_pages: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Number of pages to process concurrently (be careful with rate limits)"
    )

    # API Keys (loaded from environment)
    # Note: These are intentionally not exposed in UI - users must set environment variables
    openai_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY"),
        description="OpenAI API key (from OPENAI_API_KEY env var)"
    )

    anthropic_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"),
        description="Anthropic API key (from ANTHROPIC_API_KEY env var)"
    )

    gemini_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY"),
        description="Google Gemini API key (from GEMINI_API_KEY env var)"
    )

    class Config:
        use_enum_values = True


# Field groupings for UI generation
LITELLM_BASIC_FIELDS = [
    "model",
    "custom_model",  # Conditional: shown only when model='custom'
    "dpi",
    "extraction_prompt",
    "page_separator",
]

LITELLM_ADVANCED_FIELDS = [
    "max_tokens",
    "temperature",
    "image_quality",
    "max_retries",
    "timeout",
    "concurrent_pages",
]

# Conditional fields
LITELLM_CONDITIONAL_FIELDS = {
    "model": {
        LiteLLMModelEnum.CUSTOM: ["custom_model"]
    }
}
