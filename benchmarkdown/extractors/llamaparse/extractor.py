"""
LlamaParse extractor implementation.

This module provides the LlamaParseExtractor class that implements the
MarkdownExtractor protocol using LlamaIndex's LlamaParse cloud service.
"""

import os
import asyncio
from typing import Optional
from llama_parse import LlamaParse

from .config import LlamaParseConfig


class LlamaParseExtractor:
    """
    Extractor that implements the MarkdownExtractor protocol for extracting
    markdown content using the LlamaParse cloud service.

    LlamaParse provides cloud-based document processing with advanced OCR,
    layout understanding, and optional GPT-4o integration for complex documents.

    Configuration:
        You can create multiple instances with different configurations:

        from benchmarkdown.extractors.llamaparse import Extractor, Config

        config = Config(
            api_key="your-api-key",
            result_type="markdown",
            language="en",
            gpt4o_mode=True
        )
        extractor = Extractor(config=config)

    Example:
        # Default instance (uses LLAMA_CLOUD_API_KEY env var)
        extractor = LlamaParseExtractor()

        # Custom instance with configuration
        config = LlamaParseConfig(
            language="es",
            parsing_instruction="Extract tables and preserve formatting",
            gpt4o_mode=True
        )
        extractor = LlamaParseExtractor(config=config)
    """

    def __init__(self, config: Optional[LlamaParseConfig] = None, **kwargs):
        """
        Initialize the LlamaParse extractor.

        Args:
            config: LlamaParseConfig instance with typed configuration parameters.
                   If provided, this takes precedence over **kwargs.
            **kwargs: Raw configuration parameters passed to LlamaParse.
                     Used only if config is None.
        """
        if config is not None:
            # Build kwargs from config
            parser_kwargs = {
                "api_key": config.api_key,
                "result_type": config.result_type.value if hasattr(config.result_type, 'value') else config.result_type,
                "language": config.language,
                "skip_diagonal_text": config.skip_diagonal_text,
                "invalidate_cache": config.invalidate_cache,
                "do_not_cache": config.do_not_cache,
                "page_separator": config.page_separator,
                "num_workers": config.num_workers,
                "verbose": config.verbose,
            }

            # Add optional fields if set
            if config.parsing_instruction:
                parser_kwargs["parsing_instruction"] = config.parsing_instruction
            if config.page_range:
                parser_kwargs["page_range"] = config.page_range
            if config.gpt4o_mode:
                parser_kwargs["gpt4o_mode"] = True
                if config.gpt4o_api_key:
                    parser_kwargs["gpt4o_api_key"] = config.gpt4o_api_key

            self.parser = LlamaParse(**parser_kwargs)
            self.config = config
        else:
            # Fallback to raw kwargs for backward compatibility
            self.parser = LlamaParse(**kwargs)
            self.config = None

    async def extract_markdown(self, filename: os.PathLike) -> str:
        """
        Extract markdown content from a document using LlamaParse.

        Args:
            filename: The path to the document file

        Returns:
            Extracted markdown content as a string

        Raises:
            Exception: If extraction fails
        """
        def blocking_extract_markdown(filename: os.PathLike) -> str:
            # LlamaParse returns a list of Documents
            documents = self.parser.load_data(str(filename))

            # Combine all document text
            # Each document represents a page or chunk
            if documents:
                return "\n\n".join(doc.text for doc in documents)
            return ""

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, blocking_extract_markdown, filename)
        return result
