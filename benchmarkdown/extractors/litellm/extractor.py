"""
LiteLLM multi-modal extractor implementation.

This module provides the LiteLLMExtractor class that implements the
MarkdownExtractor protocol using vision-capable LLMs via LiteLLM.
"""

import os
import io
import re
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

from .config import LiteLLMConfig

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
        logger.info(
            f"[LiteLLM] Starting extraction: {filename.name} "
            f"(model={self.config.model}, dpi={self.config.dpi}, batch_size={self.config.batch_size})"
        )
        logger.debug(
            f"[LiteLLM] Config: temperature={self.config.temperature}, "
            f"max_tokens={self.config.max_tokens}, concurrent_pages={self.config.concurrent_pages}, "
            f"image_quality={self.config.image_quality}"
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
        """Process pages sequentially, in batches if batch_size > 1."""
        results = []
        total_pages = len(doc)

        # Process in batches
        for batch_start in range(0, total_pages, self.config.batch_size):
            batch_end = min(batch_start + self.config.batch_size, total_pages)
            page_numbers = list(range(batch_start, batch_end))

            try:
                if len(page_numbers) == 1:
                    # Single page - use existing single-page method
                    result = await self._process_single_page(doc, page_numbers[0])
                    results.append(result)
                else:
                    # Multiple pages - use batch method
                    batch_results = await self._process_batch(doc, page_numbers)
                    results.extend(batch_results)
            except Exception as e:
                logger.error(f"[LiteLLM] Failed to process batch {page_numbers}: {e}")
                # Add error markers for each page in the failed batch
                for page_num in page_numbers:
                    results.append(f"<!-- Error processing page {page_num + 1}: {str(e)} -->")

        return results

    async def _process_pages_concurrent(self, doc: fitz.Document) -> List[str]:
        """Process pages concurrently in batches, with semaphore to limit concurrency."""
        semaphore = asyncio.Semaphore(self.config.concurrent_pages)
        total_pages = len(doc)

        # Create batches
        batches = []
        for batch_start in range(0, total_pages, self.config.batch_size):
            batch_end = min(batch_start + self.config.batch_size, total_pages)
            batches.append(list(range(batch_start, batch_end)))

        async def process_batch_with_semaphore(page_numbers: List[int]):
            async with semaphore:
                try:
                    if len(page_numbers) == 1:
                        # Single page
                        result = await self._process_single_page(doc, page_numbers[0])
                        return [result]
                    else:
                        # Multiple pages
                        return await self._process_batch(doc, page_numbers)
                except Exception as e:
                    logger.error(f"[LiteLLM] Failed to process batch {page_numbers}: {e}")
                    # Return error markers for each page in the failed batch
                    return [f"<!-- Error processing page {pn + 1}: {str(e)} -->" for pn in page_numbers]

        # Process all batches concurrently
        tasks = [process_batch_with_semaphore(batch) for batch in batches]
        batch_results = await asyncio.gather(*tasks)

        # Flatten results (list of lists -> single list)
        results = []
        for batch_result in batch_results:
            results.extend(batch_result)

        return results

    async def _process_batch(self, doc: fitz.Document, page_numbers: List[int]) -> List[str]:
        """
        Process multiple pages in a single API call.

        Args:
            doc: PyMuPDF document
            page_numbers: List of page indices to process in this batch

        Returns:
            List of extracted markdown strings, one per page
        """
        batch_size = len(page_numbers)
        logger.info(f"[LiteLLM] Processing batch: pages {page_numbers[0] + 1}-{page_numbers[-1] + 1}/{len(doc)} ({batch_size} pages)")

        # Render all pages to images
        images = []
        total_image_bytes = 0
        for page_num in page_numbers:
            page = doc.load_page(page_num)
            zoom = self.config.dpi / 72.0
            matrix = fitz.Matrix(zoom, zoom)
            pixmap = page.get_pixmap(matrix=matrix)
            png_bytes = pixmap.tobytes("png")

            # Log image size
            image_size_bytes = len(png_bytes)
            total_image_bytes += image_size_bytes
            logger.debug(
                f"[LiteLLM] Rendered page {page_num + 1}: "
                f"{pixmap.width}x{pixmap.height} pixels, "
                f"{image_size_bytes:,} bytes ({image_size_bytes / 1024:.1f} KB)"
            )

            base64_image = base64.b64encode(png_bytes).decode('utf-8')
            images.append(base64_image)

        # Log total batch size
        logger.debug(
            f"[LiteLLM] Batch total image size: {total_image_bytes:,} bytes "
            f"({total_image_bytes / 1024:.1f} KB, {total_image_bytes / (1024 * 1024):.2f} MB)"
        )

        # Build content with text prompt and all images
        batch_prompt_text = self._build_batch_prompt(page_numbers)
        logger.debug(
            f"[LiteLLM] Batch prompt length: {len(batch_prompt_text)} chars, "
            f"first 200 chars: {batch_prompt_text[:200]}..."
        )

        content = [
            {
                "type": "text",
                "text": batch_prompt_text
            }
        ]

        # Add all images
        for idx, base64_image in enumerate(images):
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}",
                    "detail": self.config.image_quality
                }
            })

        # Prepare messages
        messages = [{"role": "user", "content": content}]

        logger.debug(
            f"[LiteLLM] API call parameters: model={self.config.model}, "
            f"max_tokens={self.config.max_tokens}, temperature={self.config.temperature}, "
            f"timeout={self.config.timeout}, num_images={len(images)}"
        )

        # Call LiteLLM
        api_start = time.time()
        response = await acompletion(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            timeout=self.config.timeout,
            num_retries=self.config.max_retries
        )
        api_duration = time.time() - api_start

        # Extract and parse response
        full_response = response.choices[0].message.content

        # Log API response metadata
        logger.debug(
            f"[LiteLLM] API call completed in {api_duration:.2f}s, "
            f"response length: {len(full_response)} chars"
        )

        # Try to extract token usage if available
        if hasattr(response, 'usage') and response.usage:
            logger.debug(
                f"[LiteLLM] Token usage: "
                f"prompt={getattr(response.usage, 'prompt_tokens', 'N/A')}, "
                f"completion={getattr(response.usage, 'completion_tokens', 'N/A')}, "
                f"total={getattr(response.usage, 'total_tokens', 'N/A')}"
            )

        # Parse response into individual page results
        page_results = self._parse_batch_response(full_response, page_numbers)

        logger.info(
            f"[LiteLLM] Completed batch: pages {page_numbers[0] + 1}-{page_numbers[-1] + 1}/{len(doc)} "
            f"(api_time={api_duration:.2f}s)"
        )

        return page_results

    def _build_batch_prompt(self, page_numbers: List[int]) -> str:
        """
        Build a prompt for batch processing that instructs the LLM to separate pages.

        Args:
            page_numbers: List of page indices being processed

        Returns:
            Modified extraction prompt with page separation instructions
        """
        page_labels = ", ".join([f"Page {pn + 1}" for pn in page_numbers])

        batch_prompt = f"""{self.config.extraction_prompt}

IMPORTANT: You are processing {len(page_numbers)} pages in this batch ({page_labels}).

For each page, start your output with a clear marker:
- Start with "=== PAGE {page_numbers[0] + 1} ===" for the first image
- Start with "=== PAGE {page_numbers[1] + 1} ===" for the second image
{f'- Start with "=== PAGE {page_numbers[2] + 1} ===" for the third image' if len(page_numbers) > 2 else ''}
{f'- And so on for the remaining {len(page_numbers) - 3} pages' if len(page_numbers) > 3 else ''}

Extract the text from each page separately, maintaining the order of the images provided."""

        return batch_prompt

    def _parse_batch_response(self, response: str, page_numbers: List[int]) -> List[str]:
        """
        Parse a batched response into individual page results.

        Args:
            response: Full response from LLM containing multiple pages
            page_numbers: List of page indices that were processed

        Returns:
            List of extracted text for each page
        """
        results = []

        # Look for page markers like "=== PAGE N ==="

        # Create a pattern that matches any of our page markers
        page_markers = [f"=== PAGE {pn + 1} ===" for pn in page_numbers]

        # Split by page markers
        parts = re.split(r'=== PAGE \d+ ===', response)

        # First part is usually empty or contains preamble - skip it
        page_contents = [part.strip() for part in parts[1:] if part.strip()]

        # If we got the expected number of results, use them
        if len(page_contents) == len(page_numbers):
            results = page_contents
            logger.debug(
                f"[LiteLLM] Successfully parsed {len(results)} pages from batch response"
            )
        else:
            # Fallback: LLM didn't follow instructions perfectly
            logger.warning(
                f"[LiteLLM] Expected {len(page_numbers)} page sections, got {len(page_contents)}. "
                f"Using fallback parsing."
            )

            if len(page_contents) == 0:
                # No markers found - treat entire response as single page or split equally
                if len(page_numbers) == 1:
                    results = [response.strip()]
                else:
                    # Try to split response equally (rough heuristic)
                    # Just return the full response for each page with a warning
                    for pn in page_numbers:
                        results.append(f"<!-- Warning: Could not parse separate pages -->\n{response}")
            elif len(page_contents) < len(page_numbers):
                # Got some markers but not all - use what we have and pad
                results = page_contents
                for i in range(len(page_contents), len(page_numbers)):
                    results.append(f"<!-- Warning: Missing content for page {page_numbers[i] + 1} -->")
            else:
                # Got more markers than expected - take first N
                results = page_contents[:len(page_numbers)]

        return results

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

        # Log image details
        image_size_bytes = len(png_bytes)
        logger.debug(
            f"[LiteLLM] Rendered page {page_num + 1}: "
            f"{pixmap.width}x{pixmap.height} pixels, "
            f"{image_size_bytes:,} bytes ({image_size_bytes / 1024:.1f} KB)"
        )

        # Encode to base64
        base64_image = base64.b64encode(png_bytes).decode('utf-8')

        # Prepare messages for vision API
        logger.debug(
            f"[LiteLLM] Prompt for page {page_num + 1}: "
            f"{len(self.config.extraction_prompt)} chars, "
            f"preview: {self.config.extraction_prompt[:150]}..."
        )

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

        logger.debug(
            f"[LiteLLM] API call for page {page_num + 1}: "
            f"model={self.config.model}, max_tokens={self.config.max_tokens}, "
            f"temperature={self.config.temperature}"
        )

        # Call LiteLLM
        api_start = time.time()
        response = await acompletion(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            timeout=self.config.timeout,
            num_retries=self.config.max_retries
        )
        api_duration = time.time() - api_start

        # Extract text from response
        extracted_text = response.choices[0].message.content

        # Log response metadata
        logger.debug(
            f"[LiteLLM] API response for page {page_num + 1}: "
            f"time={api_duration:.2f}s, response_length={len(extracted_text)} chars"
        )

        # Try to extract token usage if available
        if hasattr(response, 'usage') and response.usage:
            logger.debug(
                f"[LiteLLM] Token usage for page {page_num + 1}: "
                f"prompt={getattr(response.usage, 'prompt_tokens', 'N/A')}, "
                f"completion={getattr(response.usage, 'completion_tokens', 'N/A')}, "
                f"total={getattr(response.usage, 'total_tokens', 'N/A')}"
            )

        logger.info(
            f"[LiteLLM] Completed page {page_num + 1}/{len(doc)} "
            f"(api_time={api_duration:.2f}s)"
        )

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
