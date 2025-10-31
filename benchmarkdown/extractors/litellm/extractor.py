"""
LiteLLM multi-modal extractor implementation.

This module provides the LiteLLMExtractor class that implements the
MarkdownExtractor protocol using vision-capable LLMs via LiteLLM.
"""

import os
import io
import base64
import asyncio
import logging
import time
from typing import Optional, List
from pathlib import Path

# Import litellm
from litellm import acompletion

# Import PyMuPDF for PDF rendering
import fitz  # PyMuPDF

from .config import LiteLLMConfig, LiteLLMModelEnum

# Set up logging
logger = logging.getLogger(__name__)


class LiteLLMExtractor:
    """
    Extractor that implements the MarkdownExtractor protocol for extracting
    markdown content using vision-capable LLMs via LiteLLM.

    This extractor converts each PDF page to an image and sends it to a
    vision-capable LLM to extract text. Supports multiple providers through
    LiteLLM (OpenAI, Anthropic, Google, etc.).

    Example:
        # Default instance
        extractor = LiteLLMExtractor()

        # Custom instance with configuration
        config = LiteLLMConfig(
            model="gpt-4o",
            dpi=300,
            extraction_prompt="Extract all text preserving formatting",
            temperature=0.0
        )
        extractor = LiteLLMExtractor(config=config)
    """

    def __init__(self, config: Optional[LiteLLMConfig] = None, **kwargs):
        """
        Initialize the LiteLLM extractor.

        Args:
            config: LiteLLMConfig instance with typed configuration parameters.
            **kwargs: Raw configuration parameters (for backward compatibility).
        """
        self.config = config or LiteLLMConfig()

    async def extract_markdown(self, filename: os.PathLike) -> str:
        """
        Extract markdown content from a document using vision-capable LLMs.

        Args:
            filename: The path to the document file (PDF)

        Returns:
            Extracted markdown content as a string

        Raises:
            Exception: If extraction fails
        """
        filename = Path(filename)

        # Log extraction start
        model_name = self.config.custom_model if self.config.model == LiteLLMModelEnum.CUSTOM else self.config.model
        logger.info(
            f"[LiteLLM] Starting extraction: {filename.name} "
            f"(model={model_name}, dpi={self.config.dpi})"
        )
        start_time = time.time()

        try:
            # Check if file is PDF
            if filename.suffix.lower() != '.pdf':
                raise ValueError(f"LiteLLM extractor only supports PDF files, got: {filename.suffix}")

            # Open PDF document
            doc = fitz.open(filename)
            total_pages = len(doc)
            logger.info(f"[LiteLLM] Processing {total_pages} pages")

            # Process pages
            if self.config.concurrent_pages > 1:
                # Concurrent processing
                page_results = await self._process_pages_concurrent(doc)
            else:
                # Sequential processing
                page_results = await self._process_pages_sequential(doc)

            # Close document
            doc.close()

            # Combine results
            markdown_output = self.config.page_separator.join(page_results)

            # Log successful completion
            duration = time.time() - start_time
            logger.info(
                f"[LiteLLM] Completed extraction: {filename.name} "
                f"(duration: {duration:.2f}s, pages: {total_pages})"
            )

            return markdown_output

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[LiteLLM] Extraction failed: {filename.name} "
                f"(duration: {duration:.2f}s, error: {type(e).__name__}: {str(e)})",
                exc_info=True
            )
            raise

    async def _process_pages_sequential(self, doc: fitz.Document) -> List[str]:
        """Process pages sequentially."""
        results = []
        for page_num in range(len(doc)):
            try:
                result = await self._process_single_page(doc, page_num)
                results.append(result)
            except Exception as e:
                logger.error(f"[LiteLLM] Failed to process page {page_num + 1}: {e}")
                results.append(f"<!-- Error processing page {page_num + 1}: {str(e)} -->")
        return results

    async def _process_pages_concurrent(self, doc: fitz.Document) -> List[str]:
        """Process pages concurrently with semaphore to limit concurrency."""
        semaphore = asyncio.Semaphore(self.config.concurrent_pages)

        async def process_with_semaphore(page_num: int):
            async with semaphore:
                try:
                    return await self._process_single_page(doc, page_num)
                except Exception as e:
                    logger.error(f"[LiteLLM] Failed to process page {page_num + 1}: {e}")
                    return f"<!-- Error processing page {page_num + 1}: {str(e)} -->"

        tasks = [process_with_semaphore(i) for i in range(len(doc))]
        return await asyncio.gather(*tasks)

    async def _process_single_page(self, doc: fitz.Document, page_num: int) -> str:
        """Process a single page: render to image and extract text via LLM."""
        logger.info(f"[LiteLLM] Processing page {page_num + 1}/{len(doc)}")

        # Load page
        page = doc.load_page(page_num)

        # Render page to pixmap at specified DPI
        # DPI is converted to zoom factor: zoom = dpi / 72
        zoom = self.config.dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix)

        # Convert pixmap to PNG bytes
        png_bytes = pixmap.tobytes("png")

        # Encode to base64
        base64_image = base64.b64encode(png_bytes).decode('utf-8')

        # Prepare model name
        model_name = self.config.custom_model if self.config.model == LiteLLMModelEnum.CUSTOM else self.config.model

        # Prepare messages for vision API
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": self.config.extraction_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": self.config.image_quality
                        }
                    }
                ]
            }
        ]

        # Call LiteLLM
        response = await acompletion(
            model=model_name,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            timeout=self.config.timeout,
            num_retries=self.config.max_retries
        )

        # Extract text from response
        extracted_text = response.choices[0].message.content

        logger.info(f"[LiteLLM] Completed page {page_num + 1}/{len(doc)}")

        return extracted_text

    def _get_api_key_for_model(self, model: str) -> Optional[str]:
        """Get the appropriate API key for the model."""
        model_lower = model.lower()

        if "gpt" in model_lower or "openai" in model_lower:
            return self.config.openai_api_key
        elif "claude" in model_lower or "anthropic" in model_lower:
            return self.config.anthropic_api_key
        elif "gemini" in model_lower or "google" in model_lower:
            return self.config.gemini_api_key

        # For other models, let litellm handle it
        return None
