#!/usr/bin/env python3
"""
Test script to demonstrate multiple extractor instances with different configurations.

This script shows how to register and use multiple instances of the same extractor
library with different configuration parameters.
"""

import asyncio
import os
from pathlib import Path
from benchmarkdown.ui import BenchmarkUI
from benchmarkdown.docling import DoclingExtractor


async def main():
    print("🧪 Testing Multiple Extractor Configurations\n")

    # Find a test document
    test_dir = Path("data/input/lidia-anon")
    test_files = list(test_dir.glob("*.docx"))

    if not test_files:
        print("❌ No test files found in data/input/lidia-anon/")
        return

    test_file = str(test_files[0])
    print(f"📄 Test document: {os.path.basename(test_file)}\n")

    # Create UI instance
    ui = BenchmarkUI()

    # Register multiple Docling instances with different configurations
    # Instance 1: Default configuration
    docling_default = DoclingExtractor()
    ui.register_extractor(
        name="Docling (Default)",
        extractor=docling_default
    )
    print("✓ Registered Docling (Default)")

    # Instance 2: Custom configuration example
    # Note: This demonstrates the pattern, actual parameters depend on DocumentConverter API
    docling_custom = DoclingExtractor()  # Add custom params here when defined
    ui.register_extractor(
        name="Docling (Custom)",
        extractor=docling_custom
    )
    print("✓ Registered Docling (Custom)")

    print(f"\n📊 Total extractors registered: {len(ui.extractors)}")
    print(f"   Names: {list(ui.extractors.keys())}\n")

    # Process document with all extractors
    print("⏳ Processing document with all extractor instances...\n")

    results = {}
    for extractor_name in ui.extractors.keys():
        result = await ui.process_document(test_file, extractor_name)
        results[extractor_name] = result

        print(f"📊 {extractor_name}:")
        print(f"   Execution time: {result.execution_time:.2f}s")
        print(f"   Characters: {result.character_count:,}")
        print(f"   Words: {result.word_count:,}")
        if result.error:
            print(f"   ❌ Error: {result.error}")
        else:
            print(f"   ✓ Success")
        print()

    # Compare results
    print("🔍 Comparison Summary:")
    print("-" * 60)

    char_counts = {name: r.character_count for name, r in results.items()}
    word_counts = {name: r.word_count for name, r in results.items()}
    times = {name: r.execution_time for name, r in results.items()}

    print(f"Character count variation: {min(char_counts.values())} - {max(char_counts.values())}")
    print(f"Word count variation: {min(word_counts.values())} - {max(word_counts.values())}")
    print(f"Execution time range: {min(times.values()):.2f}s - {max(times.values()):.2f}s")

    print("\n✅ Test completed successfully!")
    print("\n💡 To add more configurations, edit app.py and follow the pattern shown there.")


if __name__ == "__main__":
    asyncio.run(main())
