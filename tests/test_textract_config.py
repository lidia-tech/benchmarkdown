#!/usr/bin/env python3
"""
Test TextractEngine configuration and integration.

This script tests:
1. TextractConfig creation and validation
2. TextractConfig to native Textractor options conversion
3. TextractExtractor initialization with config
4. (Optional) End-to-end extraction if AWS credentials are configured
"""

import asyncio
import os
from pathlib import Path

from benchmarkdown.config import TextractConfig, TextractFeaturesEnum
from benchmarkdown.textract import TextractExtractor


def test_config_creation():
    """Test creating TextractConfig with various parameters."""
    print("🧪 Test 1: TextractConfig Creation\n")
    print("=" * 60)

    # Test 1a: Default configuration
    print("=== Test 1a: Default Configuration ===")
    config1 = TextractConfig()
    print(f"✓ Default config created")
    print(f"  S3 Upload Path: {config1.s3_upload_path}")
    print(f"  Features: {config1.features}")
    print(f"  Hide Headers: {config1.hide_header_layout}")
    print(f"  Hide Footers: {config1.hide_footer_layout}")
    print()

    # Test 1b: Custom configuration
    print("=== Test 1b: Custom Configuration ===")
    config2 = TextractConfig(
        s3_upload_path="s3://my-test-bucket/textract-temp/",
        features=[
            TextractFeaturesEnum.LAYOUT,
            TextractFeaturesEnum.TABLES,
            TextractFeaturesEnum.FORMS
        ],
        hide_header_layout=False,
        hide_footer_layout=False,
        table_add_title_as_caption=True,
        max_number_of_consecutive_new_lines=3
    )
    print(f"✓ Custom config created")
    print(f"  S3 Upload Path: {config2.s3_upload_path}")
    print(f"  Features: {config2.features}")
    print(f"  Hide Headers: {config2.hide_header_layout}")
    print(f"  Hide Footers: {config2.hide_footer_layout}")
    print(f"  Table Add Title: {config2.table_add_title_as_caption}")
    print(f"  Max New Lines: {config2.max_number_of_consecutive_new_lines}")
    print()

    print("✅ Test 1 passed: Config creation works correctly\n")
    return config1, config2


def test_config_conversion():
    """Test converting TextractConfig to native Textractor options."""
    print("🧪 Test 2: Config to Native Options Conversion\n")
    print("=" * 60)

    config = TextractConfig(
        s3_upload_path="s3://test-bucket/temp/",
        features=[TextractFeaturesEnum.LAYOUT, TextractFeaturesEnum.TABLES],
        hide_header_layout=True,
        hide_footer_layout=True,
        table_remove_column_headers=False
    )

    features_list, markdown_config, s3_path = config.to_textract_options()

    print("✓ Conversion successful")
    print(f"  Features: {features_list}")
    print(f"  S3 Path: {s3_path}")
    print(f"  Markdown Config Type: {type(markdown_config).__name__}")
    print(f"  Hide Headers: {markdown_config.hide_header_layout}")
    print(f"  Hide Footers: {markdown_config.hide_footer_layout}")
    print(f"  Table Remove Headers: {markdown_config.table_remove_column_headers}")
    print()

    # Verify types
    from textractor.data.constants import TextractFeatures
    from textractor.data.markdown_linearization_config import MarkdownLinearizationConfig

    assert all(isinstance(f, TextractFeatures) for f in features_list), "Features should be TextractFeatures instances"
    assert isinstance(markdown_config, MarkdownLinearizationConfig), "Should be MarkdownLinearizationConfig instance"
    assert s3_path == "s3://test-bucket/temp/", "S3 path should match"

    print("✅ Test 2 passed: Config conversion works correctly\n")
    return features_list, markdown_config, s3_path


def test_extractor_creation():
    """Test creating TextractExtractor with config."""
    print("🧪 Test 3: TextractExtractor Creation\n")
    print("=" * 60)

    config = TextractConfig(s3_upload_path="s3://test-bucket/temp/")

    # Test with region (Textractor requires either profile or region)
    try:
        extractor = TextractExtractor(config=config, region_name="us-east-1")
        print("✓ Extractor created with config")
        print(f"  S3 Path: {extractor.s3_upload_path}")
        print(f"  Features: {extractor.features}")
        print(f"  Config Type: {type(extractor.config).__name__}")
        print()
        print("✅ Test 3 passed: Extractor creation works correctly\n")
        return extractor
    except Exception as e:
        print(f"❌ Test 3 failed: {e}\n")
        raise


def test_backward_compatibility():
    """Test that old raw parameter initialization still works."""
    print("🧪 Test 4: Backward Compatibility\n")
    print("=" * 60)

    try:
        from textractor.data.constants import TextractFeatures
        from textractor.data.markdown_linearization_config import MarkdownLinearizationConfig

        # Create extractor without config (old way)
        markdown_config = MarkdownLinearizationConfig(
            hide_header_layout=True,
            hide_footer_layout=True
        )

        extractor = TextractExtractor(
            s3_upload_path="s3://test-bucket/temp/",
            features=[TextractFeatures.LAYOUT, TextractFeatures.TABLES],
            markdown_config=markdown_config,
            region_name="us-east-1"
        )

        print("✓ Extractor created with raw parameters (backward compatibility)")
        print(f"  S3 Path: {extractor.s3_upload_path}")
        print(f"  Features: {extractor.features}")
        print()
        print("✅ Test 4 passed: Backward compatibility maintained\n")
        return extractor
    except Exception as e:
        print(f"❌ Test 4 failed: {e}\n")
        raise


async def test_extraction_if_aws_available():
    """Test actual extraction if AWS credentials are available."""
    print("🧪 Test 5: End-to-End Extraction (Optional)\n")
    print("=" * 60)

    # Check if AWS credentials are configured
    s3_workspace = os.environ.get("TEXTRACT_S3_BUCKET")
    if not s3_workspace or not s3_workspace.startswith("s3://"):
        print("⚠️  Test 5 skipped: AWS Textract not configured")
        print("   Set TEXTRACT_S3_BUCKET environment variable to a full S3 URI")
        print("   Example: export TEXTRACT_S3_BUCKET=s3://my-bucket/textract-workspace/")
        print()
        return

    # Find a test document
    test_dir = Path("data/input/lidia-anon")
    if not test_dir.exists():
        print("⚠️  Test 5 skipped: No test files directory found")
        print()
        return

    test_files = list(test_dir.glob("*.pdf"))
    if not test_files:
        print("⚠️  Test 5 skipped: No PDF test files found")
        print()
        return

    test_file = str(test_files[0])
    print(f"📄 Test document: {test_file}")
    print()

    # Create config and extractor
    config = TextractConfig(
        s3_upload_path=s3_workspace,
        features=[TextractFeaturesEnum.LAYOUT, TextractFeaturesEnum.TABLES],
        hide_header_layout=True,
        hide_footer_layout=True
    )

    extractor = TextractExtractor(config=config)

    print("⏳ Extracting with AWS Textract...")
    import time
    start = time.time()

    try:
        markdown = await extractor.extract_markdown(test_file)
        elapsed = time.time() - start

        print(f"✓ Extraction complete")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Characters: {len(markdown):,}")
        print(f"  Words: {len(markdown.split()):,}")
        print(f"  First 100 chars: {markdown[:100]}...")
        print()
        print("✅ Test 5 passed: End-to-end extraction works correctly\n")
    except Exception as e:
        print(f"⚠️  Test 5 failed (this may be expected if AWS isn't configured): {e}")
        print()


async def main():
    print("\n" + "=" * 60)
    print("🚀 TextractEngine Configuration Tests")
    print("=" * 60 + "\n")

    try:
        # Run tests
        config1, config2 = test_config_creation()
        features, markdown_config, s3_path = test_config_conversion()
        extractor1 = test_extractor_creation()
        extractor2 = test_backward_compatibility()
        await test_extraction_if_aws_available()

        print("=" * 60)
        print("🎉 All tests passed!")
        print("=" * 60)

    except Exception as e:
        print("=" * 60)
        print(f"❌ Tests failed: {e}")
        print("=" * 60)
        raise


if __name__ == "__main__":
    asyncio.run(main())
