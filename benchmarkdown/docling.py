import os
import asyncio
from docling.document_converter import DocumentConverter

class DoclingExtractor:

    def __init__(self):
        self.converter = DocumentConverter()

    async def extract_markdown(self, filename: os.PathLike) -> str:
        def blocking_extract_markdown(filename: os.PathLike) -> str:
            """
            Blocking function to get text from the document.
            """
            result = self.converter.convert(str(filename))
            ser_text = result.document.export_to_markdown()
            return ser_text

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, blocking_extract_markdown, filename)
        return result
