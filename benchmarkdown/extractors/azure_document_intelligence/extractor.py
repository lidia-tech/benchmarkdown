"""
Azure Document Intelligence extractor implementation.

This module provides the AzureDocIntelExtractor class that implements the
MarkdownExtractor protocol using Azure Document Intelligence service.
"""

import os
import asyncio
import logging
import time
from typing import Optional

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from .config import AzureDocIntelConfig

# Set up logging
logger = logging.getLogger(__name__)


class AzureDocIntelExtractor:
    """
    Extractor that implements the MarkdownExtractor protocol for extracting
    markdown content using Azure Document Intelligence service.

    Azure Document Intelligence (formerly Form Recognizer) is Microsoft's
    cloud-based service for document processing with native markdown output.

    Requirements:
        - Azure subscription with Document Intelligence resource
        - The `azure-ai-documentintelligence` library installed
        - AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT environment variable (endpoint URL)
        - AZURE_DOCUMENT_INTELLIGENCE_KEY environment variable (API key)

    Configuration:
        You can create multiple instances with different configurations:

        1. Using AzureDocIntelConfig (recommended for UI integration):
            from benchmarkdown.extractors.azure_document_intelligence import Extractor, Config

            config = Config(
                model_id="prebuilt-layout",
                output_content_format="markdown",
                locale="en-US"
            )
            extractor = Extractor(config=config)

        2. Using raw kwargs (for advanced use):
            extractor = Extractor(
                endpoint="https://my-resource.cognitiveservices.azure.com/",
                api_key="my-key",
                model_id="prebuilt-layout"
            )

    Example:
        # Default instance with config
        config = AzureDocIntelConfig()
        extractor = AzureDocIntelExtractor(config=config)

        # Custom instance with modified config
        config_custom = AzureDocIntelConfig(
            model_id="prebuilt-read",
            pages="1-5"
        )
        extractor_custom = AzureDocIntelExtractor(config=config_custom)
    """

    def __init__(
        self,
        config: Optional[AzureDocIntelConfig] = None,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the AzureDocIntelExtractor with configuration.

        Args:
            config: AzureDocIntelConfig instance with typed configuration parameters.
                   If provided, this takes precedence over other parameters.
            endpoint: Azure endpoint URL. Used only if config is None.
            api_key: Azure API key. Used only if config is None.
            model_id: Model ID to use. Used only if config is None.
            **kwargs: Additional keyword arguments for analyze_request.
        """
        if config is not None:
            # Use the config object to build Azure options
            endpoint, api_key, model_id, analyze_kwargs = config.to_azure_options()
            self.endpoint = endpoint
            self.api_key = api_key
            self.model_id = model_id
            self.analyze_kwargs = analyze_kwargs
        else:
            # Fallback to raw parameters for backward compatibility
            if endpoint is None:
                endpoint = os.environ.get(
                    "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT",
                    "https://your-resource.cognitiveservices.azure.com/"
                )
            if api_key is None:
                api_key = os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_KEY", "")
            if model_id is None:
                model_id = "prebuilt-layout"

            if not api_key:
                raise ValueError(
                    "Azure API key must be provided via config, parameter, or "
                    "AZURE_DOCUMENT_INTELLIGENCE_KEY environment variable"
                )

            self.endpoint = endpoint
            self.api_key = api_key
            self.model_id = model_id
            self.analyze_kwargs = kwargs.get("analyze_kwargs", {
                "output_content_format": "markdown"
            })

        # Initialize the client
        self.client = DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key)
        )

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
        # Log extraction start with config summary
        # Extract hostname from endpoint for cleaner logs
        endpoint_host = self.endpoint.split('/')[2] if '//' in self.endpoint else self.endpoint
        features = self.analyze_kwargs.get('features', [])
        features_str = ', '.join(features) if features else 'default'
        config_summary = f"model={self.model_id}, endpoint={endpoint_host}, features=[{features_str}]"

        logger.info(f"[Azure DI] Starting extraction: {os.path.basename(filename)} ({config_summary})")
        start_time = time.time()

        def blocking_extract_markdown(filename):
            # Read the file
            with open(filename, "rb") as f:
                # Start the analysis using the correct API
                # Note: The API expects 'body' parameter (not 'analyze_request')
                # and uses keyword-only arguments for optional parameters
                poller = self.client.begin_analyze_document(
                    model_id=self.model_id,
                    body=f,
                    content_type="application/octet-stream",
                    **self.analyze_kwargs
                )

            # Log operation ID if available
            # Azure uses operation-location header which contains the operation ID
            if hasattr(poller, '_operation_location'):
                operation_id = poller._operation_location.split('/')[-1].split('?')[0]
                logger.info(f"[Azure DI] Operation ID: {operation_id} for {os.path.basename(filename)}")

            # Wait for completion
            result = poller.result()

            # Return the markdown content
            return result.content if result.content else ""

        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, blocking_extract_markdown, filename)

            # Log successful completion with duration
            duration = time.time() - start_time
            logger.info(f"[Azure DI] Completed extraction: {os.path.basename(filename)} (duration: {duration:.2f}s)")

            return result
        except Exception as e:
            # Log error with details
            duration = time.time() - start_time
            logger.error(
                f"[Azure DI] Extraction failed: {os.path.basename(filename)} "
                f"(duration: {duration:.2f}s, error: {type(e).__name__}: {str(e)})"
            )
            raise
