import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

from textractor import Textractor
from textractor.data.constants import TextractFeatures
from textractor.data.markdown_linearization_config import MarkdownLinearizationConfig

class TextractExtractor:
    """A class that implements the MarkdownExtractor protocol for extracting markdown content
    using AWS Textract service.

    Ensure you have:
    - AWS credentials configured in your environment.
    - The `textractor` library installed (`pip install textractor`).

    Configuration:
        You can create multiple instances with different configurations to compare
        different Textract settings.

        Key configuration options:
        - s3_upload_path: S3 path for temporary document uploads (required)
        - features: List of TextractFeatures (LAYOUT, TABLES, FORMS, etc.)
        - markdown_config: MarkdownLinearizationConfig for output formatting
        - **kwargs: Additional parameters passed to Textractor constructor

    Example:
        # Instance with layout only
        extractor_layout = TextractExtractor(
            s3_upload_path="s3://bucket/temp/",
            features=[TextractFeatures.LAYOUT]
        )

        # Instance with tables and forms
        extractor_full = TextractExtractor(
            s3_upload_path="s3://bucket/temp/",
            features=[TextractFeatures.LAYOUT, TextractFeatures.TABLES, TextractFeatures.FORMS]
        )

        # Instance with custom markdown config
        custom_config = MarkdownLinearizationConfig(
            hide_header_layout=False,
            hide_footer_layout=False
        )
        extractor_custom = TextractExtractor(
            s3_upload_path="s3://bucket/temp/",
            markdown_config=custom_config
        )
    """

    def __init__(
        self,
        s3_upload_path: str,
        features: list = None,
        markdown_config: MarkdownLinearizationConfig = None,
        **kwargs
    ):
        """Initializes the TextractExtractor with configuration.

        Args:
            s3_upload_path (str): The S3 path where documents will be temporarily uploaded for processing.
            features (list, optional): List of TextractFeatures to enable. Defaults to [LAYOUT, TABLES].
            markdown_config (MarkdownLinearizationConfig, optional): Configuration for markdown output.
                Defaults to hiding headers and footers.
            **kwargs: Additional keyword arguments to pass to the Textractor constructor.
        """
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
        """Extracts markdown content from the given text file.

        Args:
            filename (os.PathLike): The path to the text file.

        Returns:
            str: The extracted markdown content.
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

