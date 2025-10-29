"""
TensorLake extractor implementation.

This module provides the TensorLakeExtractor class that implements the
MarkdownExtractor protocol using TensorLake's Document Ingestion API.
"""

import os
import asyncio
from typing import Optional
from tensorlake.documentai import DocumentAI, ParsingOptions, EnrichmentOptions, ParseStatus

from .config import TensorLakeConfig


class TensorLakeExtractor:
    """
    Extractor that implements the MarkdownExtractor protocol for extracting
    markdown content using the TensorLake Document Ingestion API.

    TensorLake provides cloud-based document processing with state-of-the-art
    layout detection and table recognition models.

    Configuration:
        You can create multiple instances with different configurations:

        from benchmarkdown.extractors.tensorlake import Extractor, Config

        config = Config(
            chunking_strategy="section",
            table_output_mode="html",
            figure_summarization=True
        )
        extractor = Extractor(config=config)

    Example:
        # Default instance (uses TENSORLAKE_API_KEY env var)
        extractor = TensorLakeExtractor()

        # Custom instance with configuration
        config = TensorLakeConfig(
            chunking_strategy="page",
            table_output_mode="html",
            figure_summarization=True,
            table_summarization=True,
            signature_detection=True
        )
        extractor = TensorLakeExtractor(config=config)
    """

    def __init__(self, config: Optional[TensorLakeConfig] = None, **kwargs):
        """
        Initialize the TensorLake extractor.

        Args:
            config: TensorLakeConfig instance with typed configuration parameters.
                   If provided, this takes precedence over **kwargs.
            **kwargs: Raw configuration parameters.
                     Used only if config is None.
        """
        if config is not None:
            self.config = config
            self.doc_ai = DocumentAI(api_key=config.api_key)
        else:
            # Fallback to raw kwargs for backward compatibility
            api_key = kwargs.get('api_key', os.getenv("TENSORLAKE_API_KEY", ""))
            self.doc_ai = DocumentAI(api_key=api_key)
            self.config = TensorLakeConfig(**kwargs) if kwargs else TensorLakeConfig()

    async def extract_markdown(self, filename: os.PathLike) -> str:
        """
        Extract markdown content from a document using TensorLake.

        Args:
            filename: The path to the document file

        Returns:
            Extracted markdown content as a string

        Raises:
            Exception: If extraction fails
        """
        def blocking_extract_markdown(filename: os.PathLike) -> str:
            try:
                # Upload the document
                file_id = self.doc_ai.upload(str(filename))

                # Configure parsing options
                parsing_options = ParsingOptions(
                    chunking_strategy=self.config.chunking_strategy,
                    table_output_mode=self.config.table_output_mode,
                    signature_detection=self.config.signature_detection,
                )

                # Configure enrichment options
                enrichment_options = EnrichmentOptions(
                    figure_summarization=self.config.figure_summarization,
                    table_summarization=self.config.table_summarization,
                )

                # Parse and wait for completion
                result = self.doc_ai.parse_and_wait(
                    file_id,
                    parsing_options=parsing_options,
                    enrichment_options=enrichment_options,
                    timeout=self.config.max_timeout
                )

                # Check if parsing was successful
                if result.status != ParseStatus.SUCCESSFUL:
                    raise ValueError(f"Parsing failed with status: {result.status}")

                # Combine all chunks into a single markdown string
                if result.chunks:
                    return "\n\n".join(chunk.content for chunk in result.chunks)
                return ""

            except Exception as e:
                # Make error messages more user-friendly
                error_msg = str(e)

                # Check for common API errors
                if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                    raise ValueError(
                        "Authentication failed. Please check your TENSORLAKE_API_KEY environment variable."
                    ) from e
                elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    raise ValueError(
                        "API quota exceeded or rate limit reached. Please check your TensorLake account."
                    ) from e
                elif "timeout" in error_msg.lower():
                    raise ValueError(
                        f"Parsing timeout after {self.config.max_timeout} seconds. "
                        "Try increasing max_timeout or use a smaller document."
                    ) from e
                else:
                    # Re-raise with original error
                    raise

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, blocking_extract_markdown, filename)
        return result
