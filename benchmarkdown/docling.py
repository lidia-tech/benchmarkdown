import os
import asyncio
from docling.document_converter import DocumentConverter

class DoclingExtractor:
    """A class that implements the MarkdownExtractor protocol for extracting markdown content
    using the Docling library.

    Ensure you have:
    - The `docling` library installed (`pip install docling`).

    Configuration:
        You can create multiple instances with different configurations by passing
        parameters to __init__. All parameters are forwarded to DocumentConverter.

        Common configuration options:
        - allowed_formats: List of InputFormat enums to restrict processing
        - format_options: Dict mapping InputFormat to FormatOption for format-specific settings

    Example:
        # Default instance
        extractor_default = DoclingExtractor()

        # Custom instance with specific formats
        from docling.datamodel.base_models import InputFormat
        extractor_pdf_only = DoclingExtractor(allowed_formats=[InputFormat.PDF])
    """

    def __init__(self, **kwargs):
        """Initialize the Docling extractor.

        Args:
            **kwargs: Configuration parameters passed to DocumentConverter.
                     See DocumentConverter documentation for available options.
        """
        self.converter = DocumentConverter(**kwargs)

    async def extract_markdown(self, filename: os.PathLike) -> str:
        """Extracts markdown content from the given text file.

        Args:
            filename (os.PathLike): The path to the text file.

        Returns:
            str: The extracted markdown content.
        """
        def blocking_extract_markdown(filename: os.PathLike) -> str:
            result = self.converter.convert(str(filename))
            ser_text = result.document.export_to_markdown()
            return ser_text

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, blocking_extract_markdown, filename)
        return result
