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
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
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
from benchmarkdown.extractors.mistral_ocr import extractor as extractor_module


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
    assert config.max_retries == 3


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

    # max_retries is a robustness setting, not a benchmark knob: kept out of the UI.
    assert "max_retries" not in BASIC_FIELDS
    assert "max_retries" not in ADVANCED_FIELDS


def _fake_page(markdown):
    return SimpleNamespace(markdown=markdown)


def _make_extractor_with_fake_client(process_side_effect, max_retries=3):
    """Build an extractor whose client is a fake with the given ocr.process behavior."""
    extractor = MistralOCRExtractor(config=MistralOCRConfig(max_retries=max_retries))

    client = MagicMock()
    client.files.upload.return_value = SimpleNamespace(id="file-123")
    client.files.get_signed_url.return_value = SimpleNamespace(url="https://signed.example/doc")
    client.files.delete.return_value = None
    client.ocr.process.side_effect = process_side_effect

    extractor.client = client
    return extractor, client


def _make_doc(tmp_path):
    doc = tmp_path / "doc.pdf"
    doc.write_bytes(b"%PDF-1.4 fake test bytes")
    return str(doc)


async def test_retry_then_succeeds(monkeypatch, tmp_path):
    """A transient error is retried and the subsequent success is returned."""
    monkeypatch.setattr(extractor_module.time, "sleep", lambda _s: None)

    success = SimpleNamespace(pages=[_fake_page("hello"), _fake_page("world")])
    extractor, client = _make_extractor_with_fake_client(
        process_side_effect=[
            httpx.RemoteProtocolError("Server disconnected without sending a response."),
            success,
        ],
        max_retries=3,
    )

    result = await extractor.extract_markdown(_make_doc(tmp_path))

    assert result == "hello\n\nworld"
    assert client.ocr.process.call_count == 2
    # Each attempt re-uploads, so upload is called once per attempt.
    assert client.files.upload.call_count == 2
    # The uploaded file is cleaned up on every attempt.
    assert client.files.delete.call_count == 2


async def test_fail_fast_on_auth_error(monkeypatch, tmp_path):
    """A 401 is permanent: no retries, mapped to the auth-friendly message."""
    sleep_calls = []
    monkeypatch.setattr(extractor_module.time, "sleep", lambda s: sleep_calls.append(s))

    extractor, client = _make_extractor_with_fake_client(
        process_side_effect=Exception("API error occurred: Status 401. Body: unauthorized"),
        max_retries=3,
    )

    with pytest.raises(ValueError, match="Authentication failed"):
        await extractor.extract_markdown(_make_doc(tmp_path))

    assert client.ocr.process.call_count == 1  # no retries on a permanent error
    assert sleep_calls == []  # never backed off


async def test_retries_exhausted(monkeypatch, tmp_path):
    """A persistently transient error raises after exactly 1 + max_retries attempts."""
    monkeypatch.setattr(extractor_module.time, "sleep", lambda _s: None)

    extractor, client = _make_extractor_with_fake_client(
        process_side_effect=httpx.RemoteProtocolError("Server disconnected."),
        max_retries=2,
    )

    with pytest.raises(ValueError, match="Mistral OCR extraction failed"):
        await extractor.extract_markdown(_make_doc(tmp_path))

    assert client.ocr.process.call_count == 3  # 1 initial + 2 retries


async def test_transient_classification():
    """_is_transient retries races/5xx/connection errors and fails fast on auth/bad-request."""
    is_transient = extractor_module._is_transient

    assert is_transient(httpx.RemoteProtocolError("disconnected")) is True
    assert is_transient(Exception("Status 404. Body: No file matches the given query.")) is True
    assert is_transient(Exception("Status 500. Body: internal error")) is True
    assert is_transient(Exception("Status 429. Body: rate limited")) is True

    assert is_transient(Exception("Status 401. Body: unauthorized")) is False
    assert is_transient(Exception("Status 400. Body: bad request")) is False
    assert is_transient(Exception("something unclassifiable")) is False


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
