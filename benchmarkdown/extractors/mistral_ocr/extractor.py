"""
Mistral OCR extractor implementation.

This module provides the MistralOCRExtractor class that implements the
MarkdownExtractor protocol using Mistral's OCR endpoint (``/v1/ocr``, model
``mistral-ocr-latest``). Local documents are uploaded via the Files API, a
signed URL is obtained, and OCR runs against that URL. The per-page markdown
returned by the API is concatenated into a single markdown string.
"""

import os
import asyncio
import logging
import time
from typing import Optional

from mistralai.client import Mistral

from .config import MistralOCRConfig

logger = logging.getLogger(__name__)


class MistralOCRExtractor:
    """
    Extractor that implements the MarkdownExtractor protocol using the Mistral
    OCR API.

    Example:
        from benchmarkdown.extractors.mistral_ocr import Extractor, Config

        config = Config(table_format="html", extract_footer=False)
        extractor = Extractor(config=config)
        markdown = await extractor.extract_markdown("document.pdf")
    """

    def __init__(self, config: Optional[MistralOCRConfig] = None, **kwargs):
        """
        Initialize the Mistral OCR extractor.

        Args:
            config: MistralOCRConfig instance with typed configuration.
                    If provided, takes precedence over **kwargs.
            **kwargs: Raw configuration parameters, used only if config is None.
        """
        if config is not None:
            self.config = config
        else:
            self.config = MistralOCRConfig(**kwargs) if kwargs else MistralOCRConfig()

        self.client = Mistral(api_key=self.config.api_key)

    async def extract_markdown(self, filename: os.PathLike) -> str:
        """
        Extract markdown content from a document using Mistral OCR.

        Args:
            filename: The path to the document file

        Returns:
            Extracted markdown content as a string

        Raises:
            Exception: If extraction fails
        """
        config_summary = (
            f"model={self.config.model}, tables={self.config.table_format}, "
            f"header={self.config.extract_header}, footer={self.config.extract_footer}"
        )
        logger.info(
            f"[MistralOCR] Starting extraction: {os.path.basename(filename)} ({config_summary})"
        )
        start_time = time.time()

        def blocking_extract_markdown(filename: os.PathLike) -> str:
            uploaded_file_id = None
            try:
                # Upload the local document with the OCR purpose.
                with open(filename, "rb") as fh:
                    uploaded = self.client.files.upload(
                        file={
                            "file_name": os.path.basename(str(filename)),
                            "content": fh.read(),
                        },
                        purpose="ocr",
                    )
                uploaded_file_id = uploaded.id
                logger.info(
                    f"[MistralOCR] File uploaded: {os.path.basename(filename)} "
                    f"(file_id: {uploaded_file_id})"
                )

                # Obtain a signed URL to feed the OCR endpoint.
                signed = self.client.files.get_signed_url(
                    file_id=uploaded_file_id, expiry=1
                )

                # Run OCR against the signed document URL.
                response = self.client.ocr.process(
                    document={"type": "document_url", "document_url": signed.url},
                    **self.config.to_ocr_kwargs(),
                )

                # Concatenate per-page markdown into a single document.
                if response.pages:
                    return "\n\n".join(page.markdown for page in response.pages)
                return ""

            except Exception as e:
                error_msg = str(e)
                error_type = type(e).__name__

                if (
                    "api_key" in error_msg.lower()
                    or "authentication" in error_msg.lower()
                    or "unauthorized" in error_msg.lower()
                    or "401" in error_msg
                ):
                    raise ValueError(
                        "Authentication failed. Please check your MISTRAL_API_KEY environment variable."
                    ) from e
                elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower() or "429" in error_msg:
                    raise ValueError(
                        "API quota exceeded or rate limit reached. Please check your Mistral account."
                    ) from e
                else:
                    raise ValueError(
                        f"Mistral OCR extraction failed: {error_type}: {error_msg}"
                    ) from e

            finally:
                # Best-effort cleanup so uploaded files don't accumulate.
                if uploaded_file_id is not None:
                    try:
                        self.client.files.delete(file_id=uploaded_file_id)
                    except Exception as cleanup_error:
                        logger.warning(
                            f"[MistralOCR] Failed to delete uploaded file "
                            f"{uploaded_file_id}: {cleanup_error}"
                        )

        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, blocking_extract_markdown, filename)

            duration = time.time() - start_time
            logger.info(
                f"[MistralOCR] Completed extraction: {os.path.basename(filename)} "
                f"(duration: {duration:.2f}s)"
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[MistralOCR] Extraction failed: {os.path.basename(filename)} "
                f"(duration: {duration:.2f}s, error: {type(e).__name__}: {str(e)})",
                exc_info=True,
            )
            raise
