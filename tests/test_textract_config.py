#!/usr/bin/env python3
"""
Test TextractEngine configuration and integration.

This module tests:
1. TextractConfig creation and validation (unit)
2. TextractConfig to native Textractor options conversion (unit)
3. TextractExtractor initialization with config (integration — needs AWS creds)
4. Backward-compatible raw-parameter initialization (integration — needs AWS creds)
5. End-to-end extraction if AWS credentials are configured (integration + live)

Instantiating a TextractExtractor builds a boto3/Textractor session, which
requires an AWS profile/credentials to exist; those tests are marked
``integration`` so they are deselected on a plain offline run.
"""

import os
from pathlib import Path

import pytest

from benchmarkdown.extractors.textract import Config as TextractConfig, Extractor as TextractExtractor
from benchmarkdown.extractors.textract.config import TextractFeaturesEnum


def test_config_creation():
    """Test creating TextractConfig with various parameters."""
    # Default configuration
    config1 = TextractConfig()
    assert hasattr(config1, "s3_upload_path")
    assert hasattr(config1, "features")

    # Custom configuration
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
    assert config2.s3_upload_path == "s3://my-test-bucket/textract-temp/"
    assert config2.hide_header_layout is False
    assert config2.hide_footer_layout is False
    assert config2.table_add_title_as_caption is True
    assert config2.max_number_of_consecutive_new_lines == 3


def test_config_conversion():
    """Test converting TextractConfig to native Textractor options."""
    from textractor.data.constants import TextractFeatures
    from textractor.data.markdown_linearization_config import MarkdownLinearizationConfig

    config = TextractConfig(
        s3_upload_path="s3://test-bucket/temp/",
        features=[TextractFeaturesEnum.LAYOUT, TextractFeaturesEnum.TABLES],
        hide_header_layout=True,
        hide_footer_layout=True,
        table_remove_column_headers=False
    )

    features_list, markdown_config, s3_path = config.to_textract_options()

    assert all(isinstance(f, TextractFeatures) for f in features_list), "Features should be TextractFeatures instances"
    assert isinstance(markdown_config, MarkdownLinearizationConfig), "Should be MarkdownLinearizationConfig instance"
    assert s3_path == "s3://test-bucket/temp/", "S3 path should match"
    assert markdown_config.hide_header_layout is True
    assert markdown_config.hide_footer_layout is True
    assert markdown_config.table_remove_column_headers is False


@pytest.mark.integration
def test_extractor_creation():
    """Test creating TextractExtractor with config (requires an AWS session)."""
    config = TextractConfig(s3_upload_path="s3://test-bucket/temp/")

    # Textractor requires either a profile or a region.
    extractor = TextractExtractor(config=config, region_name="us-east-1")
    assert extractor.s3_upload_path == "s3://test-bucket/temp/"
    assert extractor.features is not None
    assert extractor.config is not None


@pytest.mark.integration
def test_backward_compatibility():
    """Test that old raw parameter initialization still works (requires an AWS session)."""
    from textractor.data.constants import TextractFeatures
    from textractor.data.markdown_linearization_config import MarkdownLinearizationConfig

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

    assert extractor.s3_upload_path == "s3://test-bucket/temp/"
    assert extractor.features is not None


@pytest.mark.integration
@pytest.mark.live
async def test_extraction_if_aws_available():
    """End-to-end extraction against real AWS Textract."""
    s3_workspace = os.environ.get("TEXTRACT_S3_WORKSPACE")
    if not s3_workspace or not s3_workspace.startswith("s3://"):
        pytest.skip("TEXTRACT_S3_WORKSPACE not set to an s3:// URI")

    test_dir = Path("data/input/lidia-anon")
    if not test_dir.exists():
        pytest.skip("No test document directory (data/input/lidia-anon)")

    test_files = list(test_dir.glob("*.pdf"))
    if not test_files:
        pytest.skip("No PDF test files found")

    test_file = str(test_files[0])

    config = TextractConfig(
        s3_upload_path=s3_workspace,
        features=[TextractFeaturesEnum.LAYOUT, TextractFeaturesEnum.TABLES],
        hide_header_layout=True,
        hide_footer_layout=True
    )
    extractor = TextractExtractor(config=config)

    markdown = await extractor.extract_markdown(test_file)
    assert isinstance(markdown, str)
    assert len(markdown) > 0
