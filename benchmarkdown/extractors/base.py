"""
Base classes and interfaces for extractor plugins.

This module defines the standard interface that all extractor plugins must implement.
"""

from typing import Protocol, Tuple, Type, List
from pydantic import BaseModel
import os


class MarkdownExtractor(Protocol):
    """
    Protocol for markdown extractors.

    All extractor implementations must provide an async extract_markdown method.
    """

    async def extract_markdown(self, filename: os.PathLike) -> str:
        """
        Extract markdown content from a document.

        Args:
            filename: Path to the document file

        Returns:
            Extracted markdown content as a string

        Raises:
            Exception: If extraction fails
        """
        ...


class ExtractorPlugin(Protocol):
    """
    Protocol defining the required interface for extractor plugins.

    Each extractor plugin module must export:
    - Extractor: A class implementing MarkdownExtractor protocol
    - Config: A Pydantic BaseModel for configuration
    - BASIC_FIELDS: List of field names for basic configuration
    - ADVANCED_FIELDS: List of field names for advanced configuration
    - ENGINE_NAME: Unique identifier for the engine
    - ENGINE_DISPLAY_NAME: Human-readable name for UI display
    - is_available: Function to check if dependencies are installed
    """

    Extractor: Type[MarkdownExtractor]
    Config: Type[BaseModel]
    BASIC_FIELDS: List[str]
    ADVANCED_FIELDS: List[str]
    ENGINE_NAME: str
    ENGINE_DISPLAY_NAME: str

    @staticmethod
    def is_available() -> Tuple[bool, str]:
        """
        Check if the extractor is available (dependencies installed).

        Returns:
            Tuple of (is_available, message)
            - is_available: True if all dependencies are installed
            - message: Empty string if available, error message otherwise
        """
        ...


class BaseExtractor:
    """
    Optional base class for extractors.

    Extractors don't need to inherit from this, but it provides
    common functionality and type hints.
    """

    def __init__(self, config: BaseModel = None, **kwargs):
        """
        Initialize the extractor.

        Args:
            config: Optional Pydantic config model
            **kwargs: Additional keyword arguments for backward compatibility
        """
        self.config = config

    async def extract_markdown(self, filename: os.PathLike) -> str:
        """
        Extract markdown content from a document.

        This method must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement extract_markdown")
