#!/usr/bin/env python3
"""
Test script to verify logging is working correctly.
"""
import os
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

async def test_docling_logging():
    """Test logging for Docling extractor."""
    print("\n" + "="*80)
    print("Testing Docling Extractor Logging")
    print("="*80 + "\n")

    try:
        from benchmarkdown.extractors.docling import Extractor, Config

        # Create a simple config
        config = Config(
            do_ocr=False,
            table_structure_mode="fast",
            num_threads=2
        )

        # Create extractor
        extractor = Extractor(config=config)

        # Find a test file
        test_file = Path("data/input/lidia-anon/Atto di citazione Fazio vs. RAI - Anonimizzato.docx")

        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return

        print(f"📄 Testing with: {test_file.name}\n")

        # Run extraction
        result = await extractor.extract_markdown(test_file)

        print(f"\n✅ Extraction successful! Result length: {len(result)} chars")

    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_azure_logging():
    """Test logging for Azure Document Intelligence extractor."""
    print("\n" + "="*80)
    print("Testing Azure Document Intelligence Extractor Logging")
    print("="*80 + "\n")

    try:
        from benchmarkdown.extractors.azure_document_intelligence import Extractor, Config

        # Check if credentials are available
        endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

        if not endpoint or not api_key:
            print("⏭️  Skipping Azure test - credentials not configured")
            return

        # Create a simple config
        config = Config(model_id="prebuilt-layout")

        # Create extractor
        extractor = Extractor(config=config)

        # Find a test file
        test_file = Path("data/input/lidia-anon/Atto di citazione Fazio vs. RAI - Anonimizzato.docx")

        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return

        print(f"📄 Testing with: {test_file.name}\n")

        # Run extraction
        result = await extractor.extract_markdown(test_file)

        print(f"\n✅ Extraction successful! Result length: {len(result)} chars")

    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)}")

async def main():
    """Run all logging tests."""
    print("\n" + "="*80)
    print("LOGGING TEST SUITE")
    print("="*80)

    # Test Docling (local, always available)
    await test_docling_logging()

    # Test Azure (cloud, requires credentials)
    await test_azure_logging()

    print("\n" + "="*80)
    print("TESTS COMPLETED")
    print("="*80 + "\n")
    print("Expected log entries:")
    print("  - [Extractor] Starting extraction: filename (config summary)")
    print("  - [Extractor] Completed extraction: filename (duration: X.XXs)")
    print("  OR")
    print("  - [Extractor] Extraction failed: filename (duration: X.XXs, error: ...)")
    print()

if __name__ == "__main__":
    asyncio.run(main())
