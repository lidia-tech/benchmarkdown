"""
Azure Document Intelligence extractor implementation.

This module provides the AzureDocIntelExtractor class that implements the
MarkdownExtractor protocol using Azure Document Intelligence service.
"""

import os
import asyncio
from typing import Optional

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from .config import AzureDocIntelConfig


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
        endpoint: str = None,
        api_key: str = None,
        model_id: str = None,
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
        def blocking_extract_markdown(filename):
            # Read the file
            with open(filename, "rb") as f:
                file_bytes = f.read()

            # Start the analysis using the correct API
            # Note: The API expects 'body' parameter (not 'analyze_request')
            # and uses keyword-only arguments for optional parameters
            poller = self.client.begin_analyze_document(
                model_id=self.model_id,
                body=file_bytes,
                content_type="application/octet-stream",
                **self.analyze_kwargs
            )

            # Wait for completion
            result = poller.result()

            # Return the markdown content
            return result.content if result.content else ""

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, blocking_extract_markdown, filename)
        return result
