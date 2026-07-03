"""
Mistral OCR extractor implementation.

This module provides the MistralOCRExtractor class that implements the
MarkdownExtractor protocol using Mistral's OCR endpoint (``/v1/ocr``, model
``mistral-ocr-latest``). Local documents are uploaded via the Files API, a
signed URL is obtained, and OCR runs against that URL. The per-page markdown
returned by the API is concatenated into a single markdown string.

The upload/OCR sequence is retried on transient failures (a post-upload 404
eventual-consistency race, HTTP 5xx/429, and connection/protocol errors), which
live testing showed occur intermittently and recover on a re-run.
"""

import os
import re
import asyncio
import logging
import time
from typing import Optional

import httpx
from mistralai.client import Mistral

from .config import MistralOCRConfig

logger = logging.getLogger(__name__)

# The SDK's error message always embeds the HTTP status as "Status <code>".
_STATUS_RE = re.compile(r"Status (\d{3})")

# Base for exponential backoff between retries (seconds): 0.5, 1.0, 2.0, ...
_RETRY_BACKOFF_BASE = 0.5


def _is_transient(exc: Exception) -> bool:
    """
    Decide whether an exception from the upload/OCR sequence is worth retrying.

    Transient (retry): transport-level errors (connection/protocol/timeout,
    including RemoteProtocolError), HTTP 408/409/425/429, any 5xx, and 404 (the
    post-upload eventual-consistency race, "No file matches the given query").

    Permanent (fail fast): 401/403 (auth), 400/422 (bad request), any other 4xx,
    and any exception whose shape we can't classify.
    """
    # Transport-layer failures: connection reset, disconnect, timeout, etc.
    if isinstance(exc, httpx.RequestError):
        return True

    match = _STATUS_RE.search(str(exc))
    if match:
        code = int(match.group(1))
        if code in (404, 408, 409, 425, 429) or code >= 500:
            return True
        return False

    return False


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

    def _run_ocr_once(self, filename: os.PathLike) -> str:
        """
        Run a single upload -> signed URL -> OCR -> join attempt.

        Raises the raw SDK/transport exception on failure so the caller's retry
        loop can classify it. The uploaded file is deleted in a ``finally`` block
        so a retried attempt never leaks the previous upload.
        """
        uploaded_file_id = None
        try:
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

            signed = self.client.files.get_signed_url(
                file_id=uploaded_file_id, expiry=1
            )

            response = self.client.ocr.process(
                document={"type": "document_url", "document_url": signed.url},
                **self.config.to_ocr_kwargs(),
            )

            if response.pages:
                return "\n\n".join(page.markdown for page in response.pages)
            return ""
        finally:
            if uploaded_file_id is not None:
                try:
                    self.client.files.delete(file_id=uploaded_file_id)
                except Exception as cleanup_error:
                    logger.warning(
                        f"[MistralOCR] Failed to delete uploaded file "
                        f"{uploaded_file_id}: {cleanup_error}"
                    )

    async def extract_markdown(self, filename: os.PathLike) -> str:
        """
        Extract markdown content from a document using Mistral OCR.

        Args:
            filename: The path to the document file

        Returns:
            Extracted markdown content as a string

        Raises:
            Exception: If extraction fails after exhausting retries
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
            basename = os.path.basename(str(filename))
            max_attempts = self.config.max_retries + 1

            for attempt in range(max_attempts):
                try:
                    return self._run_ocr_once(filename)
                except Exception as e:
                    is_last = attempt == max_attempts - 1
                    if not is_last and _is_transient(e):
                        delay = _RETRY_BACKOFF_BASE * (2 ** attempt)
                        logger.warning(
                            f"[MistralOCR] Transient error on {basename} "
                            f"(attempt {attempt + 1}/{max_attempts}), retrying in "
                            f"{delay:.1f}s: {type(e).__name__}: {str(e)[:120]}"
                        )
                        time.sleep(delay)
                        continue

                    # Permanent error, or transient error with no retries left:
                    # map to a friendly message.
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

            # Unreachable: the loop either returns or raises.
            raise RuntimeError("Mistral OCR retry loop exited without a result")

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
