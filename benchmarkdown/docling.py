import os
import asyncio
from typing import Optional
from docling.document_converter import DocumentConverter


class DoclingExtractor:
    """A class that implements the MarkdownExtractor protocol for extracting markdown content
    using the Docling library.

    Ensure you have:
    - The `docling` library installed (`pip install docling`).

    Configuration:
        You can create multiple instances with different configurations:

        1. Using DoclingConfig (recommended for UI integration):
            from benchmarkdown.config import DoclingConfig, TableFormerModeEnum

            config = DoclingConfig(
                do_ocr=False,
                table_structure_mode=TableFormerModeEnum.FAST,
                num_threads=8
            )
            extractor = DoclingExtractor(config=config)

        2. Using raw kwargs (for advanced use):
            from docling.datamodel.base_models import InputFormat

            extractor = DoclingExtractor(allowed_formats=[InputFormat.PDF])

    Example:
        # Default instance
        extractor_default = DoclingExtractor()

        # Custom instance with configuration
        from benchmarkdown.config import DoclingConfig

        config = DoclingConfig(do_ocr=False, num_threads=16)
        extractor_custom = DoclingExtractor(config=config)
    """

    def __init__(self, config: Optional['DoclingConfig'] = None, **kwargs):
        """Initialize the Docling extractor.

        Args:
            config: DoclingConfig instance with typed configuration parameters.
                   If provided, this takes precedence over **kwargs.
            **kwargs: Raw configuration parameters passed to DocumentConverter.
                     Used only if config is None.
        """
        if config is not None:
            # Use the config object to build DocumentConverter options
            format_options = config.to_docling_options()
            self.converter = DocumentConverter(format_options=format_options)
            self.config = config
        else:
            # Fallback to raw kwargs for backward compatibility
            self.converter = DocumentConverter(**kwargs)
            self.config = None

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
