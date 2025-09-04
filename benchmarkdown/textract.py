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
    """

    def __init__(self, s3_upload_path: str, **kwargs):
        """Initializes the TextractMarkdownExtractor with optional parameters.

        Args:
            s3_upload_path (str): The S3 path where documents will be temporarily uploaded for processing.
            **kwargs: Additional keyword arguments to pass to the Textractor constructor.
        """
        self.s3_upload_path = s3_upload_path
        self.extractor = Textractor(**kwargs)
        self.config = MarkdownLinearizationConfig(
            hide_header_layout=True,
            hide_footer_layout=True,
        )


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
                features=[
                    TextractFeatures.LAYOUT,
                    TextractFeatures.TABLES,
                ],
                s3_upload_path=self.s3_upload_path,
                save_image=False,
            )
            return document.to_markdown(config=self.config)

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, blocking_extract_markdown, filename)
        return result

