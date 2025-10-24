#!/usr/bin/env python3
"""
Quick test script for the Benchmarkdown UI components.
"""

import asyncio
import os
from pathlib import Path
from benchmarkdown.docling import DoclingExtractor
from benchmarkdown.ui import BenchmarkUI

async def test_extraction():
    """Test the extraction pipeline with a sample document."""

    # Find a sample document
    input_dir = Path("data/input/lidia-anon")
    sample_docs = list(input_dir.glob("*.docx"))[:1]  # Get first docx file

    if not sample_docs:
        print("❌ No sample documents found in data/input/lidia-anon/")
        return

    sample_doc = sample_docs[0]
    print(f"📄 Testing with: {sample_doc.name}")

    # Create UI instance
    ui = BenchmarkUI()

    # Register Docling extractor
    ui.register_extractor("Docling (Local)", DoclingExtractor())
    print("✓ Registered Docling extractor")

    # Process the document
    print("⏳ Processing document...")
    result = await ui.process_document(str(sample_doc), "Docling (Local)")

    # Print results
    print("\n📊 Results:")
    print(f"  Extractor: {result.extractor_name}")
    print(f"  Filename: {result.filename}")
    print(f"  Execution time: {result.execution_time:.2f}s")
    print(f"  Characters: {result.character_count:,}")
    print(f"  Words: {result.word_count:,}")

    if result.error:
        print(f"  ❌ Error: {result.error}")
    else:
        print(f"  ✓ Success!")
        print(f"\n📝 First 200 chars of markdown:")
        print(f"  {result.markdown[:200]}...")

    return result

if __name__ == "__main__":
    print("🧪 Testing Benchmarkdown UI components\n")
    result = asyncio.run(test_extraction())

    if result and not result.error:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")
