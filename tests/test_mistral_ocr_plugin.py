"""
Test the Mistral OCR plugin implementation.

The unit tests verify the plugin is correctly structured, its config maps to the
real Mistral OCR API parameters, and it is discoverable by the extractor
registry. They need no API key or network access.

The end-to-end extraction test is marked ``integration`` + ``live`` and skips
gracefully unless ``MISTRAL_API_KEY`` and a test document are available.
"""

import os
from pathlib import Path

import pytest

from benchmarkdown.extractors.mistral_ocr import (
    Config as MistralOCRConfig,
    Extractor as MistralOCRExtractor,
    BASIC_FIELDS,
    ADVANCED_FIELDS,
    ENGINE_NAME,
    ENGINE_DISPLAY_NAME,
    is_available,
)
from benchmarkdown.extractors.mistral_ocr.config import TableFormatEnum


def test_config_defaults():
    """Default config carries the expected model and toggles."""
    config = MistralOCRConfig()
    assert config.model == "mistral-ocr-latest"
    assert config.table_format == TableFormatEnum.MARKDOWN.value
    assert config.extract_header is True
    assert config.extract_footer is True
    assert config.include_image_base64 is False
    assert config.pages is None
    assert config.image_limit is None
    assert config.image_min_size is None


def test_config_custom_values():
    """Custom values are stored and enum is normalized to its string value."""
    config = MistralOCRConfig(
        pages="0,2-4",
        table_format="html",
        extract_header=False,
        extract_footer=False,
        include_image_base64=True,
        image_limit=5,
        image_min_size=100,
    )
    assert config.pages == "0,2-4"
    assert config.table_format == "html"
    assert config.extract_header is False
    assert config.extract_footer is False
    assert config.include_image_base64 is True
    assert config.image_limit == 5
    assert config.image_min_size == 100


def test_to_ocr_kwargs_defaults():
    """to_ocr_kwargs always sends the core params and omits unset optionals."""
    kwargs = MistralOCRConfig().to_ocr_kwargs()

    assert kwargs["model"] == "mistral-ocr-latest"
    assert kwargs["table_format"] == "markdown"
    assert kwargs["extract_header"] is True
    assert kwargs["extract_footer"] is True
    assert kwargs["include_image_base64"] is False

    # Unset optionals must be omitted so the API applies its own defaults.
    assert "pages" not in kwargs
    assert "image_limit" not in kwargs
    assert "image_min_size" not in kwargs


def test_to_ocr_kwargs_custom():
    """Set optionals are included; pages passes through as a string."""
    kwargs = MistralOCRConfig(
        pages="0,2-4",
        table_format="html",
        image_limit=5,
        image_min_size=100,
    ).to_ocr_kwargs()

    assert kwargs["pages"] == "0,2-4"
    assert kwargs["table_format"] == "html"
    assert kwargs["image_limit"] == 5
    assert kwargs["image_min_size"] == 100


def test_to_ocr_kwargs_blank_pages_omitted():
    """A whitespace-only pages value is treated as 'all pages' (omitted)."""
    kwargs = MistralOCRConfig(pages="   ").to_ocr_kwargs()
    assert "pages" not in kwargs


def test_is_available_without_key(monkeypatch):
    """is_available() reports False and a helpful message when no key is set."""
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    available, message = is_available()
    assert available is False
    assert "MISTRAL_API_KEY" in message


def test_plugin_interface():
    """The plugin exports the standard symbols and metadata."""
    assert ENGINE_NAME == "mistral_ocr"
    assert ENGINE_DISPLAY_NAME == "Mistral OCR (Cloud)"
    assert BASIC_FIELDS == ["model", "pages", "table_format", "extract_header", "extract_footer"]
    assert ADVANCED_FIELDS == ["include_image_base64", "image_limit", "image_min_size"]

    # Every UI field must exist on the config model.
    config_fields = set(MistralOCRConfig.model_fields.keys())
    for field in BASIC_FIELDS + ADVANCED_FIELDS:
        assert field in config_fields, f"UI field {field} missing from config model"


def test_extractor_registry_discovery(monkeypatch):
    """The registry discovers the plugin and marks it available with a key."""
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")

    from benchmarkdown.extractors import ExtractorRegistry

    registry = ExtractorRegistry()
    extractors = registry.discover_extractors()

    assert "mistral_ocr" in extractors, (
        f"Mistral OCR not registered. Registered: {list(extractors.keys())}"
    )
    meta = extractors["mistral_ocr"]
    assert meta.display_name == "Mistral OCR (Cloud)"
    assert meta.is_available is True


@pytest.mark.integration
@pytest.mark.live
async def test_extraction_if_mistral_available():
    """End-to-end extraction against the real Mistral OCR API."""
    if not os.environ.get("MISTRAL_API_KEY"):
        pytest.skip("MISTRAL_API_KEY not set")

    test_dir = Path("data/input/lidia-anon")
    if not test_dir.exists():
        pytest.skip("No test document directory (data/input/lidia-anon)")

    test_files = list(test_dir.glob("*.pdf"))
    if not test_files:
        pytest.skip("No PDF test files found")

    extractor = MistralOCRExtractor(config=MistralOCRConfig())
    markdown = await extractor.extract_markdown(str(test_files[0]))

    assert isinstance(markdown, str)
    assert len(markdown) > 0
