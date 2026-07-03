#!/usr/bin/env python3
"""
Test registering and running multiple instances of the same extractor library
with different configurations.

Requires a sample .docx in data/input/lidia-anon/ (gitignored); skips otherwise.
Docling runs locally (no credentials), so this is not marked integration.
"""

import os
from pathlib import Path

import pytest

from benchmarkdown.ui import BenchmarkUI
from benchmarkdown.extractors.docling import Extractor as DoclingExtractor


async def test_multiple_extractor_configs():
    # Find a test document
    test_dir = Path("data/input/lidia-anon")
    test_files = list(test_dir.glob("*.docx"))
    if not test_files:
        pytest.skip("No .docx test document in data/input/lidia-anon/")

    test_file = str(test_files[0])

    # Register two Docling instances under different names
    ui = BenchmarkUI()
    ui.register_extractor(name="Docling (Default)", extractor=DoclingExtractor())
    ui.register_extractor(name="Docling (Custom)", extractor=DoclingExtractor())
    assert len(ui.extractors) == 2

    # Process the document with each registered instance
    results = {}
    for extractor_name in ui.extractors.keys():
        result = await ui.process_document(test_file, extractor_name)
        results[extractor_name] = result
        assert result.error is None, f"{extractor_name} failed: {result.error}"

    assert set(results.keys()) == {"Docling (Default)", "Docling (Custom)"}
    for result in results.values():
        assert result.character_count > 0
        assert result.word_count > 0
