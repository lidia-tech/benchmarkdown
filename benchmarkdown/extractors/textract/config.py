"""
Configuration models for AWS Textract document extractor.

This module provides Pydantic models for configuring the AWS Textract extractor
with type validation and documentation.
"""

import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class TextractFeaturesEnum(str, Enum):
    """AWS Textract feature flags."""
    LAYOUT = "LAYOUT"
    TABLES = "TABLES"
    FORMS = "FORMS"
    QUERIES = "QUERIES"
    SIGNATURES = "SIGNATURES"


def _get_s3_workspace_from_env() -> str:
    """Get S3 workspace from environment variable."""
    return os.environ.get("TEXTRACT_S3_WORKSPACE", "s3://your-bucket-name/textract-workspace/")


# ============================================================================
# Main Textract Configuration
# ============================================================================

class TextractConfig(BaseModel):
    """
    Configuration for AWS Textract document extractor.

    This configuration is split into basic and advanced sections for
    better user experience.

    Note: s3_upload_path is automatically read from TEXTRACT_S3_WORKSPACE environment variable.
    """

    # ========== BASIC OPTIONS ==========

    s3_upload_path: str = Field(
        default_factory=_get_s3_workspace_from_env,
        description="Full S3 URI path for Textract workspace (read from TEXTRACT_S3_WORKSPACE environment variable)"
    )

    features: list[TextractFeaturesEnum] = Field(
        default=[TextractFeaturesEnum.LAYOUT, TextractFeaturesEnum.TABLES],
        description="Textract features to enable (LAYOUT, TABLES, FORMS, QUERIES, SIGNATURES)"
    )

    hide_header_layout: bool = Field(
        default=True,
        description="Hide headers in markdown output"
    )

    hide_footer_layout: bool = Field(
        default=True,
        description="Hide footers in markdown output"
    )

    # ========== ADVANCED OPTIONS ==========

    hide_figure_layout: bool = Field(
        default=False,
        description="Hide figures/images in markdown output (advanced)"
    )

    hide_table_layout: bool = Field(
        default=False,
        description="Hide entire tables in markdown output (advanced)"
    )

    hide_key_value_layout: bool = Field(
        default=False,
        description="Hide key-value pairs in markdown output (advanced)"
    )

    hide_page_num_layout: bool = Field(
        default=False,
        description="Hide page numbers in markdown output (advanced)"
    )

    table_remove_column_headers: bool = Field(
        default=True,
        description="Remove column headers from tables (advanced)"
    )

    table_add_title_as_caption: bool = Field(
        default=False,
        description="Add table titles as captions (advanced)"
    )

    table_add_footer_as_paragraph: bool = Field(
        default=False,
        description="Add table footers as paragraphs (advanced)"
    )

    max_number_of_consecutive_new_lines: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Maximum consecutive newlines in output (advanced)"
    )

    title_prefix: str = Field(
        default="# ",
        description="Prefix for document titles (advanced)"
    )

    section_header_prefix: str = Field(
        default="## ",
        description="Prefix for section headers (advanced)"
    )

    class Config:
        use_enum_values = True

    def to_textract_options(self):
        """
        Convert this configuration to Textract's native format.

        Returns:
            Tuple of (features_list, markdown_config, s3_upload_path)
        """
        from textractor.data.constants import TextractFeatures
        from textractor.data.markdown_linearization_config import MarkdownLinearizationConfig

        # Map our enum to Textract's enum
        feature_map = {
            "LAYOUT": TextractFeatures.LAYOUT,
            "TABLES": TextractFeatures.TABLES,
            "FORMS": TextractFeatures.FORMS,
            "QUERIES": TextractFeatures.QUERIES,
            "SIGNATURES": TextractFeatures.SIGNATURES,
        }

        # Convert feature list
        features_list = [feature_map[f] if isinstance(f, str) else feature_map[f.value] for f in self.features]

        # Create markdown linearization config
        markdown_config = MarkdownLinearizationConfig(
            hide_header_layout=self.hide_header_layout,
            hide_footer_layout=self.hide_footer_layout,
            hide_figure_layout=self.hide_figure_layout,
            hide_table_layout=self.hide_table_layout,
            hide_key_value_layout=self.hide_key_value_layout,
            hide_page_num_layout=self.hide_page_num_layout,
            table_remove_column_headers=self.table_remove_column_headers,
            table_add_title_as_caption=self.table_add_title_as_caption,
            table_add_footer_as_paragraph=self.table_add_footer_as_paragraph,
            max_number_of_consecutive_new_lines=self.max_number_of_consecutive_new_lines,
            title_prefix=self.title_prefix,
            section_header_prefix=self.section_header_prefix,
        )

        return features_list, markdown_config, self.s3_upload_path


# Field groupings for UI generation
TEXTRACT_BASIC_FIELDS = [
    # Note: s3_upload_path is read from TEXTRACT_S3_WORKSPACE environment variable
    "features",
    "hide_header_layout",
    "hide_footer_layout",
]

TEXTRACT_ADVANCED_FIELDS = [
    "hide_figure_layout",
    "hide_table_layout",
    "hide_key_value_layout",
    "hide_page_num_layout",
    "table_remove_column_headers",
    "table_add_title_as_caption",
    "table_add_footer_as_paragraph",
    "max_number_of_consecutive_new_lines",
    "title_prefix",
    "section_header_prefix",
]
