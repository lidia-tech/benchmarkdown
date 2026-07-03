#!/usr/bin/env python3
"""
Test the Benchmarkdown UI extraction pipeline with a sample document.

Requires a sample .docx in data/input/lidia-anon/ (gitignored); skips otherwise.
Docling runs locally (no credentials), so this is not marked integration.
"""

from pathlib import Path

import pytest

from benchmarkdown.extractors.docling import Extractor as DoclingExtractor
from benchmarkdown.ui import BenchmarkUI


async def test_extraction():
    """Test the extraction pipeline with a sample document."""
    input_dir = Path("data/input/lidia-anon")
    sample_docs = list(input_dir.glob("*.docx"))[:1]
    if not sample_docs:
        pytest.skip("No .docx sample document in data/input/lidia-anon/")

    sample_doc = sample_docs[0]

    ui = BenchmarkUI()
    ui.register_extractor("Docling (Local)", DoclingExtractor())

    result = await ui.process_document(str(sample_doc), "Docling (Local)")

    assert result.error is None, f"Extraction failed: {result.error}"
    assert result.extractor_name == "Docling (Local)"
    assert result.character_count > 0
    assert result.word_count > 0
    assert isinstance(result.markdown, str) and len(result.markdown) > 0
