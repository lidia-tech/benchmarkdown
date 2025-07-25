import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

from textractor import Textractor

class TextractMarkdownExtractor:
    """
    A class that implements the MarkdownExtractor protocol for extracting markdown content.
    """

    def __init__(self, s3_upload_path: str, **kwargs):
        """
        Initializes the TextractMarkdownExtractor with optional parameters.
        """
        self.s3_upload_path = s3_upload_path
        self.extractor = Textractor(**kwargs)
        self._executor = ThreadPoolExecutor()


    async def extract_markdown(self, filename: os.PathLike) -> str:
        """
        Extracts markdown content from the given text file.

        Args:
            filename (os.PathLike): The path to the text file.

        Returns:
            str: The extracted markdown content.
        """
        def blocking_get_text(filename):
            """
            Blocking function to get text from the document.
            """
            document = self.extractor.start_document_text_detection(
                str(filename),
                s3_upload_path=self.s3_upload_path,
                save_image=False,
            )
            return document.get_text()

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, blocking_get_text, filename)
        return result

