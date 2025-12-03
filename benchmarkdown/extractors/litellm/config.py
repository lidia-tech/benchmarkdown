"""
Configuration models for LiteLLM multi-modal document extractor.

This module provides Pydantic models for configuring the LiteLLM extractor
that uses vision-capable LLMs to extract text from document page images.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field


class LiteLLMConfig(BaseModel):
    """
    Configuration for LiteLLM multi-modal document extractor.

    This extractor converts each PDF page to an image and uses vision-capable
    LLMs (via LiteLLM) to extract text. Supports multiple providers including
    OpenAI, Anthropic, Google, AWS Bedrock, Azure, local models, and more.
    """

    # ========== BASIC OPTIONS ==========

    model: str = Field(
        default="gpt-4o-mini",
        description="LiteLLM model identifier (e.g., 'gpt-4o-mini', 'claude-3-5-sonnet-20241022', 'bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0', 'ollama/llava')"
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



# Field groupings for UI generation
LITELLM_BASIC_FIELDS = [
    "model",
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
