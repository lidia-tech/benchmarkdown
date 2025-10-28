"""
Extractor plugin registry and discovery system.

This module provides automatic discovery and registration of extractor plugins.
"""

import importlib
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass
from pydantic import BaseModel

from .base import MarkdownExtractor


@dataclass
class ExtractorMetadata:
    """Metadata for a registered extractor plugin."""

    engine_name: str
    display_name: str
    extractor_class: Type[MarkdownExtractor]
    config_class: Type[BaseModel]
    basic_fields: List[str]
    advanced_fields: List[str]
    is_available: bool
    availability_message: str
    module_path: str
    nested_configs: Optional[Dict[str, Any]] = None  # Optional nested config metadata


class ExtractorRegistry:
    """
    Registry for managing extractor plugins.

    Provides automatic discovery, validation, and registration of extractors.
    """

    def __init__(self):
        self._extractors: Dict[str, ExtractorMetadata] = {}

    def discover_extractors(self) -> Dict[str, ExtractorMetadata]:
        """
        Discover and register all available extractor plugins.

        Scans the extractors package for subdirectories that contain valid
        extractor plugin modules.

        Returns:
            Dictionary mapping engine names to ExtractorMetadata
        """
        extractors_path = Path(__file__).parent

        # Scan for extractor subdirectories
        for item in extractors_path.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                module_name = item.name
                try:
                    self._load_extractor_plugin(module_name)
                except Exception as e:
                    print(f"⚠️  Failed to load extractor plugin '{module_name}': {e}")
                    continue

        return self._extractors

    def _load_extractor_plugin(self, module_name: str):
        """
        Load and validate a single extractor plugin.

        Args:
            module_name: Name of the extractor module (e.g., 'docling', 'textract')

        Raises:
            ImportError: If plugin module cannot be imported
            AttributeError: If plugin doesn't export required attributes
            ValueError: If plugin interface is invalid
        """
        # Import the plugin module
        plugin_module = importlib.import_module(f'benchmarkdown.extractors.{module_name}')

        # Validate required exports
        required_exports = [
            'Extractor', 'Config', 'BASIC_FIELDS', 'ADVANCED_FIELDS',
            'ENGINE_NAME', 'ENGINE_DISPLAY_NAME', 'is_available'
        ]

        for attr in required_exports:
            if not hasattr(plugin_module, attr):
                raise AttributeError(
                    f"Plugin '{module_name}' missing required export: {attr}"
                )

        # Extract plugin interface
        extractor_class = plugin_module.Extractor
        config_class = plugin_module.Config
        basic_fields = plugin_module.BASIC_FIELDS
        advanced_fields = plugin_module.ADVANCED_FIELDS
        engine_name = plugin_module.ENGINE_NAME
        display_name = plugin_module.ENGINE_DISPLAY_NAME
        is_available_func = plugin_module.is_available

        # Validate types
        if not issubclass(config_class, BaseModel):
            raise ValueError(
                f"Plugin '{module_name}' Config must be a Pydantic BaseModel"
            )

        if not isinstance(basic_fields, list) or not isinstance(advanced_fields, list):
            raise ValueError(
                f"Plugin '{module_name}' BASIC_FIELDS and ADVANCED_FIELDS must be lists"
            )

        if not callable(is_available_func):
            raise ValueError(
                f"Plugin '{module_name}' is_available must be callable"
            )

        # Check availability
        is_available, availability_message = is_available_func()

        # Extract nested configs if present (optional for plugins with nested config structures)
        nested_configs = getattr(plugin_module, 'NESTED_CONFIGS', None)

        # Create metadata
        metadata = ExtractorMetadata(
            engine_name=engine_name,
            display_name=display_name,
            extractor_class=extractor_class,
            config_class=config_class,
            basic_fields=basic_fields,
            advanced_fields=advanced_fields,
            is_available=is_available,
            availability_message=availability_message,
            module_path=f'benchmarkdown.extractors.{module_name}',
            nested_configs=nested_configs
        )

        # Register
        self._extractors[engine_name] = metadata

        if is_available:
            print(f"✓ {display_name} extractor available")
        else:
            print(f"⚠️  {display_name} not available: {availability_message}")

    def get_extractor(self, engine_name: str) -> Optional[ExtractorMetadata]:
        """
        Get metadata for a specific extractor.

        Args:
            engine_name: Engine identifier

        Returns:
            ExtractorMetadata if found, None otherwise
        """
        return self._extractors.get(engine_name)

    def get_available_extractors(self) -> Dict[str, ExtractorMetadata]:
        """
        Get all extractors that have their dependencies installed.

        Returns:
            Dictionary of available extractors
        """
        return {
            name: meta
            for name, meta in self._extractors.items()
            if meta.is_available
        }

    def get_all_extractors(self) -> Dict[str, ExtractorMetadata]:
        """
        Get all registered extractors, including unavailable ones.

        Returns:
            Dictionary of all extractors
        """
        return self._extractors.copy()

    def list_engine_names(self, available_only: bool = True) -> List[str]:
        """
        List all registered engine names.

        Args:
            available_only: If True, only return available engines

        Returns:
            List of engine names
        """
        if available_only:
            return list(self.get_available_extractors().keys())
        return list(self._extractors.keys())

    def create_extractor_instance(
        self,
        engine_name: str,
        config: Optional[BaseModel] = None,
        **kwargs
    ) -> MarkdownExtractor:
        """
        Create an instance of an extractor.

        Args:
            engine_name: Engine identifier
            config: Configuration object
            **kwargs: Additional arguments for the extractor constructor

        Returns:
            Instance of the extractor

        Raises:
            KeyError: If engine not found
            RuntimeError: If engine dependencies not available
        """
        metadata = self.get_extractor(engine_name)

        if metadata is None:
            raise KeyError(f"Extractor '{engine_name}' not found")

        if not metadata.is_available:
            raise RuntimeError(
                f"Extractor '{engine_name}' dependencies not available: "
                f"{metadata.availability_message}"
            )

        # Create instance
        if config is not None:
            return metadata.extractor_class(config=config, **kwargs)
        else:
            return metadata.extractor_class(**kwargs)


# Global registry instance
_global_registry = None


def get_global_registry() -> ExtractorRegistry:
    """
    Get or create the global extractor registry.

    Returns:
        Global ExtractorRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ExtractorRegistry()
        _global_registry.discover_extractors()
    return _global_registry


__all__ = [
    'ExtractorRegistry',
    'ExtractorMetadata',
    'get_global_registry',
]
