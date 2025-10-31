"""
TensorLake extractor implementation.

This module provides the TensorLakeExtractor class that implements the
MarkdownExtractor protocol using TensorLake's Document Ingestion API.
"""

import os
import asyncio
import logging
import time
from typing import Optional
from tensorlake.documentai import DocumentAI, ParseStatus

from .config import TensorLakeConfig

# Set up logging
logger = logging.getLogger(__name__)


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
        # Log extraction start with config summary
        config_summary = "default config"
        if self.config:
            chunking = self.config.chunking_strategy
            table_mode = self.config.table_output_mode
            features = []
            if self.config.figure_summarization:
                features.append("figures")
            if self.config.table_summarization:
                features.append("tables")
            if self.config.signature_detection:
                features.append("signatures")
            features_str = "+".join(features) if features else "none"
            config_summary = f"chunking={chunking}, tables={table_mode}, features=[{features_str}]"

        logger.info(f"[TensorLake] Starting extraction: {os.path.basename(filename)} ({config_summary})")
        start_time = time.time()

        def blocking_extract_markdown(filename: os.PathLike) -> str:
            try:
                # Upload the document
                file_id = self.doc_ai.upload(path=str(filename))
                logger.info(f"[TensorLake] File uploaded: {os.path.basename(filename)} (file_id: {file_id})")

                # Convert config to TensorLake options objects
                parsing_options = self.config.to_parsing_options()
                enrichment_options = self.config.to_enrichment_options()

                # Submit parse operation (using known-working API pattern)
                parse_id = self.doc_ai.read(
                    file_id=file_id,
                    parsing_options=parsing_options,
                    enrichment_options=enrichment_options
                )
                logger.info(f"[TensorLake] Parse job submitted: {os.path.basename(filename)} (parse_id: {parse_id})")

                # Wait for parsing to complete
                result = self.doc_ai.wait_for_completion(parse_id)

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
                error_type = type(e).__name__

                # Check for common API errors with more specific matching
                if "api_key" in error_msg.lower() or "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
                    user_msg = "Authentication failed. Please check your TENSORLAKE_API_KEY environment variable."
                    raise ValueError(user_msg) from e
                elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    user_msg = "API quota exceeded or rate limit reached. Please check your TensorLake account."
                    raise ValueError(user_msg) from e
                elif error_type == "TimeoutError" or "timed out" in error_msg.lower():
                    # Only catch actual timeout errors, not parameter validation errors
                    user_msg = "Parsing timeout. Try using a smaller document or contact TensorLake support."
                    raise ValueError(user_msg) from e
                else:
                    # Re-raise with original error for better debugging
                    # Include the error type and message
                    user_msg = f"TensorLake extraction failed: {error_type}: {error_msg}"
                    raise ValueError(user_msg) from e

        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, blocking_extract_markdown, filename)

            # Log successful completion with duration
            duration = time.time() - start_time
            logger.info(f"[TensorLake] Completed extraction: {os.path.basename(filename)} (duration: {duration:.2f}s)")

            return result
        except Exception as e:
            # Log error with duration
            duration = time.time() - start_time
            logger.error(
                f"[TensorLake] Extraction failed: {os.path.basename(filename)} "
                f"(duration: {duration:.2f}s, error: {type(e).__name__}: {str(e)})",
                exc_info=True
            )
            raise
