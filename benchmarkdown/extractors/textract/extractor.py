"""
AWS Textract extractor implementation.

This module provides the TextractExtractor class that implements the
MarkdownExtractor protocol using AWS Textract service.
"""

import os
import asyncio
from typing import Optional

from textractor import Textractor
from textractor.data.constants import TextractFeatures
from textractor.data.markdown_linearization_config import MarkdownLinearizationConfig

from .config import TextractConfig


class TextractExtractor:
    """
    Extractor that implements the MarkdownExtractor protocol for extracting
    markdown content using AWS Textract service.

    AWS Textract is a cloud-based service that automatically extracts text,
    handwriting, and data from scanned documents.

    Requirements:
        - AWS credentials configured (via ~/.aws/credentials or environment variables)
        - The `textractor` library installed
        - AWS_PROFILE environment variable (defaults to "default" if not set)
        - S3 workspace configured via TEXTRACT_S3_WORKSPACE environment variable

    Configuration:
        You can create multiple instances with different configurations:

        1. Using TextractConfig (recommended for UI integration):
            from benchmarkdown.extractors.textract import Extractor, Config

            config = Config(
                s3_upload_path="s3://my-bucket/temp/",
                features=["LAYOUT", "TABLES"],
                hide_header_layout=True
            )
            extractor = Extractor(config=config)

        2. Using raw kwargs (for advanced use):
            extractor = Extractor(
                s3_upload_path="s3://bucket/temp/",
                features=[TextractFeatures.LAYOUT, TextractFeatures.TABLES]
            )

    Example:
        # Default instance with config
        config = TextractConfig(s3_upload_path="s3://my-bucket/temp/")
        extractor_default = TextractExtractor(config=config)

        # Custom instance with modified config
        config_custom = TextractConfig(
            s3_upload_path="s3://my-bucket/temp/",
            hide_header_layout=False,
            hide_footer_layout=False
        )
        extractor_custom = TextractExtractor(config=config_custom)
    """

    def __init__(
        self,
        config: Optional[TextractConfig] = None,
        s3_upload_path: str = None,
        features: list = None,
        markdown_config: MarkdownLinearizationConfig = None,
        **kwargs
    ):
        """
        Initialize the TextractExtractor with configuration.

        Args:
            config: TextractConfig instance with typed configuration parameters.
                   If provided, this takes precedence over other parameters.
            s3_upload_path: The S3 path for document uploads. Used only if config is None.
            features: List of TextractFeatures to enable. Used only if config is None.
            markdown_config: Markdown output configuration. Used only if config is None.
            **kwargs: Additional keyword arguments to pass to the Textractor constructor.
        """
        # Set AWS profile from environment or use default
        if 'profile_name' not in kwargs:
            kwargs['profile_name'] = os.environ.get('AWS_PROFILE', 'default')

        if config is not None:
            # Use the config object to build Textractor options
            features_list, markdown_config, s3_path = config.to_textract_options()
            self.s3_upload_path = s3_path
            self.features = features_list
            self.config = markdown_config
            self.extractor = Textractor(**kwargs)
        else:
            # Fallback to raw parameters for backward compatibility
            if s3_upload_path is None:
                raise ValueError("Either config or s3_upload_path must be provided")

            self.s3_upload_path = s3_upload_path
            self.extractor = Textractor(**kwargs)

            # Default features if not specified
            if features is None:
                features = [TextractFeatures.LAYOUT, TextractFeatures.TABLES]
            self.features = features

            # Default markdown config if not specified
            if markdown_config is None:
                markdown_config = MarkdownLinearizationConfig(
                    hide_header_layout=True,
                    hide_footer_layout=True,
                )
            self.config = markdown_config

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
            document = self.extractor.start_document_analysis(
                str(filename),
                features=self.features,
                s3_upload_path=self.s3_upload_path,
                save_image=False,
            )
            return document.to_markdown(config=self.config)

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, blocking_extract_markdown, filename)
        return result
