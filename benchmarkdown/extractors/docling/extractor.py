"""
Docling extractor implementation.

This module provides the DoclingExtractor class that implements the
MarkdownExtractor protocol using IBM's Docling library.
"""

import os
import asyncio
from typing import Optional
from docling.document_converter import DocumentConverter

from .config import DoclingConfig


class DoclingExtractor:
    """
    Extractor that implements the MarkdownExtractor protocol for extracting
    markdown content using the Docling library.

    Docling provides local document processing with support for OCR, table
    extraction, and various document formats.

    Configuration:
        You can create multiple instances with different configurations:

        1. Using DoclingConfig (recommended for UI integration):
            from benchmarkdown.extractors.docling import Extractor, Config

            config = Config(
                do_ocr=False,
                table_structure_mode="fast",
                num_threads=8
            )
            extractor = Extractor(config=config)

        2. Using raw kwargs (for advanced use):
            from docling.datamodel.base_models import InputFormat

            extractor = Extractor(allowed_formats=[InputFormat.PDF])

    Example:
        # Default instance
        extractor_default = DoclingExtractor()

        # Custom instance with configuration
        config = DoclingConfig(do_ocr=False, num_threads=16)
        extractor_custom = DoclingExtractor(config=config)
    """

    def __init__(self, config: Optional[DoclingConfig] = None, **kwargs):
        """
        Initialize the Docling extractor.

        Args:
            config: DoclingConfig instance with typed configuration parameters.
                   If provided, this takes precedence over **kwargs.
            **kwargs: Raw configuration parameters passed to DocumentConverter.
                     Used only if config is None.
        """
        if config is not None:
            # Use the config object to build DocumentConverter options
            format_options = config.to_docling_options()
            self.converter = DocumentConverter(format_options=format_options)
            self.config = config
        else:
            # Fallback to raw kwargs for backward compatibility
            self.converter = DocumentConverter(**kwargs)
            self.config = None

    async def extract_markdown(self, filename: os.PathLike) -> str:
        """
        Extract markdown content from a document.

        Args:
            filename: The path to the document file

        Returns:
            Extracted markdown content as a string

        Raises:
            Exception: If extraction fails
        """
        def blocking_extract_markdown(filename: os.PathLike) -> str:
            result = self.converter.convert(str(filename))
            ser_text = result.document.export_to_markdown()
            return ser_text

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, blocking_extract_markdown, filename)
        return result
