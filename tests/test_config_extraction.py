#!/usr/bin/env python3
"""
End-to-end test of configuration-based extraction.

Tests the full flow: create config -> create extractor -> extract document.
Requires a sample .docx in data/input/lidia-anon/ (gitignored); skips otherwise.
Docling runs locally (no credentials), so this is not marked integration.
"""

from pathlib import Path

import pytest

from benchmarkdown.extractors.docling import Config as DoclingConfig, Extractor as DoclingExtractor
from benchmarkdown.extractors.docling.config import TableFormerModeEnum


async def test_config_based_extraction():
    # Find a test document
    test_dir = Path("data/input/lidia-anon")
    test_files = list(test_dir.glob("*.docx"))
    if not test_files:
        pytest.skip("No .docx test document in data/input/lidia-anon/")

    test_file = str(test_files[0])

    # Test 1: Default configuration
    config1 = DoclingConfig()
    extractor1 = DoclingExtractor(config=config1)
    markdown1 = await extractor1.extract_markdown(test_file)
    assert isinstance(markdown1, str) and len(markdown1) > 0

    # Test 2: Fast mode, no OCR
    config2 = DoclingConfig(
        do_ocr=False,
        table_structure_mode=TableFormerModeEnum.FAST,
        num_threads=8,
    )
    assert config2.do_ocr is False
    assert config2.table_structure_mode == TableFormerModeEnum.FAST
    extractor2 = DoclingExtractor(config=config2)
    markdown2 = await extractor2.extract_markdown(test_file)
    assert isinstance(markdown2, str) and len(markdown2) > 0
