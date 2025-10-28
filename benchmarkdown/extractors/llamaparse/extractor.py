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
    layout understanding, and optional multimodal model integration.

    Configuration:
        You can create multiple instances with different configurations:

        from benchmarkdown.extractors.llamaparse import Extractor, Config

        config = Config(
            result_type="markdown",
            language="en",
            premium_mode=True,
            aggressive_table_extraction=True
        )
        extractor = Extractor(config=config)

    Example:
        # Default instance (uses LLAMA_CLOUD_API_KEY env var)
        extractor = LlamaParseExtractor()

        # Custom instance with configuration
        config = LlamaParseConfig(
            language="es",
            parsing_instruction="Extract tables and preserve formatting",
            premium_mode=True,
            merge_tables_across_pages_in_markdown=True
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
            # Build kwargs from config - include all configured parameters
            parser_kwargs = {
                "api_key": config.api_key,
                "result_type": config.result_type.value if hasattr(config.result_type, 'value') else config.result_type,
                "language": config.language.value if hasattr(config.language, 'value') else config.language,
                "num_workers": config.num_workers,
                "verbose": config.verbose,
                "show_progress": config.show_progress,
                "ignore_errors": config.ignore_errors,
                "max_timeout": config.max_timeout,
                "split_by_page": config.split_by_page,

                # Mode & Performance
                "premium_mode": config.premium_mode,
                "fast_mode": config.fast_mode,
                "continuous_mode": config.continuous_mode,

                # Table Extraction
                "aggressive_table_extraction": config.aggressive_table_extraction,
                "adaptive_long_table": config.adaptive_long_table,
                "merge_tables_across_pages_in_markdown": config.merge_tables_across_pages_in_markdown,
                "outlined_table_extraction": config.outlined_table_extraction,
                "output_tables_as_HTML": config.output_tables_as_HTML,
                "compact_markdown_table": config.compact_markdown_table,

                # OCR & Text
                "disable_ocr": config.disable_ocr,
                "high_res_ocr": config.high_res_ocr,
                "skip_diagonal_text": config.skip_diagonal_text,
                "preserve_very_small_text": config.preserve_very_small_text,
                "do_not_unroll_columns": config.do_not_unroll_columns,

                # Layout & Structure
                "extract_layout": config.extract_layout,
                "extract_charts": config.extract_charts,
                "annotate_links": config.annotate_links,
                "preserve_layout_alignment_across_pages": config.preserve_layout_alignment_across_pages,
                "disable_image_extraction": config.disable_image_extraction,

                # Cache
                "invalidate_cache": config.invalidate_cache,
                "do_not_cache": config.do_not_cache,

                # Vendor Models
                "use_vendor_multimodal_model": config.use_vendor_multimodal_model,
            }

            # Add optional fields if set
            if config.parse_mode:
                parser_kwargs["parse_mode"] = config.parse_mode.value if hasattr(config.parse_mode, 'value') else config.parse_mode
            if config.parsing_instruction:
                parser_kwargs["parsing_instruction"] = config.parsing_instruction
            if config.target_pages:
                parser_kwargs["target_pages"] = config.target_pages
            if config.page_separator:
                parser_kwargs["page_separator"] = config.page_separator
            if config.page_prefix:
                parser_kwargs["page_prefix"] = config.page_prefix
            if config.page_suffix:
                parser_kwargs["page_suffix"] = config.page_suffix
            if config.max_pages is not None:
                parser_kwargs["max_pages"] = config.max_pages
            if config.vendor_multimodal_model_name:
                parser_kwargs["vendor_multimodal_model_name"] = config.vendor_multimodal_model_name
            if config.vendor_multimodal_api_key:
                parser_kwargs["vendor_multimodal_api_key"] = config.vendor_multimodal_api_key
            if config.model:
                parser_kwargs["model"] = config.model

            # Bounding box parameters
            if config.bbox_top is not None:
                parser_kwargs["bbox_top"] = config.bbox_top
            if config.bbox_bottom is not None:
                parser_kwargs["bbox_bottom"] = config.bbox_bottom
            if config.bbox_left is not None:
                parser_kwargs["bbox_left"] = config.bbox_left
            if config.bbox_right is not None:
                parser_kwargs["bbox_right"] = config.bbox_right

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
            try:
                # LlamaParse returns a list of Documents
                documents = self.parser.load_data(str(filename))

                # Combine all document text
                # Each document represents a page or chunk
                if documents:
                    return "\n\n".join(doc.text for doc in documents)
                return ""
            except Exception as e:
                # Make error messages more user-friendly
                error_msg = str(e)

                # Check for common API errors
                if "language" in error_msg.lower() and "input should be" in error_msg.lower():
                    raise ValueError(
                        "Invalid language code. Please select a valid language from the dropdown menu. "
                        "The language field only accepts single language codes (e.g., 'en', 'es', 'fr')."
                    ) from e
                elif "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                    raise ValueError(
                        "Authentication failed. Please check your LLAMA_CLOUD_API_KEY environment variable."
                    ) from e
                elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    raise ValueError(
                        "API quota exceeded or rate limit reached. Please check your LlamaParse account."
                    ) from e
                else:
                    # Re-raise with original error
                    raise

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, blocking_extract_markdown, filename)
        return result
