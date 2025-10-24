#!/usr/bin/env python3
"""
End-to-end test of configuration-based extraction.

This script tests the full flow: create config -> create extractor -> extract document.
"""

import asyncio
from pathlib import Path

from benchmarkdown.config import DoclingConfig, TableFormerModeEnum
from benchmarkdown.docling import DoclingExtractor


async def main():
    print("🧪 End-to-End Configuration-Based Extraction Test\n")
    print("=" * 60)

    # Find a test document
    test_dir = Path("data/input/lidia-anon")
    test_files = list(test_dir.glob("*.docx"))

    if not test_files:
        print("❌ No test files found in data/input/lidia-anon/")
        return

    test_file = str(test_files[0])
    print(f"📄 Test document: {test_file}\n")

    # Test 1: Default configuration
    print("=== Test 1: Default Configuration ===")
    config1 = DoclingConfig()
    extractor1 = DoclingExtractor(config=config1)

    print(f"Configuration:")
    print(f"  OCR: {config1.do_ocr}")
    print(f"  Tables: {config1.do_table_structure}")
    print(f"  Table Mode: {config1.table_structure_mode}")
    print(f"  Threads: {config1.num_threads}")

    print("\n⏳ Extracting...")
    import time
    start = time.time()
    markdown1 = await extractor1.extract_markdown(test_file)
    elapsed1 = time.time() - start

    print(f"✓ Extraction complete")
    print(f"  Time: {elapsed1:.2f}s")
    print(f"  Characters: {len(markdown1):,}")
    print(f"  Words: {len(markdown1.split()):,}")
    print(f"  First 100 chars: {markdown1[:100]}...")
    print()

    # Test 2: Fast mode, no OCR
    print("=== Test 2: Fast Mode Configuration ===")
    config2 = DoclingConfig(
        do_ocr=False,
        table_structure_mode=TableFormerModeEnum.FAST,
        num_threads=8
    )
    extractor2 = DoclingExtractor(config=config2)

    print(f"Configuration:")
    print(f"  OCR: {config2.do_ocr}")
    print(f"  Tables: {config2.do_table_structure}")
    print(f"  Table Mode: {config2.table_structure_mode}")
    print(f"  Threads: {config2.num_threads}")

    print("\n⏳ Extracting...")
    start = time.time()
    markdown2 = await extractor2.extract_markdown(test_file)
    elapsed2 = time.time() - start

    print(f"✓ Extraction complete")
    print(f"  Time: {elapsed2:.2f}s")
    print(f"  Characters: {len(markdown2):,}")
    print(f"  Words: {len(markdown2.split()):,}")
    print(f"  First 100 chars: {markdown2[:100]}...")
    print()

    # Comparison
    print("=" * 60)
    print("🔍 Comparison Summary")
    print("=" * 60)
    print(f"Default config time: {elapsed1:.2f}s")
    print(f"Fast mode time: {elapsed2:.2f}s")
    print(f"Speed difference: {elapsed1 - elapsed2:.2f}s ({(elapsed1-elapsed2)/elapsed1*100:.1f}% {'faster' if elapsed2 < elapsed1 else 'slower'})")
    print()
    print(f"Default config characters: {len(markdown1):,}")
    print(f"Fast mode characters: {len(markdown2):,}")
    print(f"Character difference: {abs(len(markdown1) - len(markdown2)):,}")
    print()

    print("✅ End-to-end test completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
