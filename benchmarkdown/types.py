from typing import Protocol
import os


class MarkdownExtractor(Protocol):

    async def extract_markdown(self, filename: os.PathLike) -> str:
        """Extracts markdown content from the given text."""
        raise NotImplementedError("This method should be overridden by subclasses.")
