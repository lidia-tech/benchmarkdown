"""
Configuration models for document extraction tools.

This module provides Pydantic models for configuring extractors with type validation
and documentation. These models can be used to generate UI components automatically.
"""

from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel, Field
import multiprocessing


# ============================================================================
# Docling Configuration
# ============================================================================

class TableFormerModeEnum(str, Enum):
    """Table extraction accuracy mode."""
    FAST = "fast"
    ACCURATE = "accurate"


class AcceleratorDeviceEnum(str, Enum):
    """Hardware acceleration device."""
    AUTO = "auto"
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"


class DoclingConfig(BaseModel):
    """
    Configuration for Docling document extractor.

    This configuration is split into basic and advanced sections for
    better user experience.
    """

    # ========== BASIC OPTIONS ==========

    do_ocr: bool = Field(
        default=True,
        description="Enable optical character recognition for scanned documents"
    )

    do_table_structure: bool = Field(
        default=True,
        description="Enable table structure recognition and extraction"
    )

    table_structure_mode: TableFormerModeEnum = Field(
        default=TableFormerModeEnum.ACCURATE,
        description="Table extraction mode: FAST (faster, less accurate) or ACCURATE (slower, better quality)"
    )

    num_threads: int = Field(
        default=multiprocessing.cpu_count(),
        ge=1,
        le=32,
        description="Number of CPU threads to use for processing"
    )

    # ========== ADVANCED OPTIONS ==========

    force_backend_text: bool = Field(
        default=False,
        description="Force re-extraction of text instead of using native PDF text (advanced)"
    )

    do_cell_matching: bool = Field(
        default=True,
        description="Match detected table cells with text content (advanced)"
    )

    do_code_enrichment: bool = Field(
        default=False,
        description="Enable code block identification and enrichment (advanced)"
    )

    do_formula_enrichment: bool = Field(
        default=False,
        description="Enable mathematical formula understanding (advanced)"
    )

    do_picture_classification: bool = Field(
        default=False,
        description="Classify detected images by type (requires AI model, advanced)"
    )

    do_picture_description: bool = Field(
        default=False,
        description="Generate descriptions for detected images (requires AI model, advanced)"
    )

    generate_page_images: bool = Field(
        default=False,
        description="Generate rendered images of each page (increases memory usage, advanced)"
    )

    generate_picture_images: bool = Field(
        default=False,
        description="Extract and save detected images (advanced)"
    )

    images_scale: float = Field(
        default=1.0,
        ge=0.1,
        le=2.0,
        description="Scale factor for generated images (1.0 = original size, advanced)"
    )

    accelerator_device: AcceleratorDeviceEnum = Field(
        default=AcceleratorDeviceEnum.AUTO,
        description="Hardware acceleration device (advanced)"
    )

    document_timeout: Optional[float] = Field(
        default=None,
        ge=1.0,
        description="Maximum processing time per document in seconds (advanced)"
    )

    class Config:
        use_enum_values = True

    def to_docling_options(self):
        """
        Convert this configuration to Docling's PdfPipelineOptions.

        Returns:
            Tuple of (format_options dict, accelerator_options) ready for DocumentConverter
        """
        from docling.datamodel.pipeline_options import (
            PdfPipelineOptions,
            AcceleratorOptions,
            TableStructureOptions,
            TableFormerMode
        )
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import PdfFormatOption
        from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

        # Map our enum to Docling's enum
        table_mode_map = {
            TableFormerModeEnum.FAST: TableFormerMode.FAST,
            TableFormerModeEnum.ACCURATE: TableFormerMode.ACCURATE
        }

        # Create accelerator options
        accelerator_options = AcceleratorOptions(
            num_threads=self.num_threads,
            device=self.accelerator_device.value if isinstance(self.accelerator_device, Enum) else self.accelerator_device
        )

        # Create table structure options
        table_structure_options = TableStructureOptions(
            do_cell_matching=self.do_cell_matching,
            mode=table_mode_map[self.table_structure_mode] if isinstance(self.table_structure_mode, TableFormerModeEnum) else table_mode_map[TableFormerModeEnum(self.table_structure_mode)]
        )

        # Create PDF pipeline options
        pdf_options = PdfPipelineOptions(
            do_ocr=self.do_ocr,
            do_table_structure=self.do_table_structure,
            do_code_enrichment=self.do_code_enrichment,
            do_formula_enrichment=self.do_formula_enrichment,
            do_picture_classification=self.do_picture_classification,
            do_picture_description=self.do_picture_description,
            generate_page_images=self.generate_page_images,
            generate_picture_images=self.generate_picture_images,
            images_scale=self.images_scale,
            force_backend_text=self.force_backend_text,
            accelerator_options=accelerator_options,
            table_structure_options=table_structure_options,
            document_timeout=self.document_timeout,
        )

        # Create format options dict
        format_options = {
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pdf_options,
                backend=PyPdfiumDocumentBackend
            )
        }

        return format_options


# ============================================================================
# Textract Configuration
# ============================================================================

class TextractFeaturesEnum(str, Enum):
    """AWS Textract feature flags."""
    LAYOUT = "LAYOUT"
    TABLES = "TABLES"
    FORMS = "FORMS"
    QUERIES = "QUERIES"
    SIGNATURES = "SIGNATURES"


class TextractConfig(BaseModel):
    """
    Configuration for AWS Textract document extractor.

    This configuration is split into basic and advanced sections for
    better user experience.
    """

    # ========== BASIC OPTIONS ==========

    s3_upload_path: str = Field(
        default="s3://your-bucket-name/textract-temp/",
        description="S3 path for temporary document uploads (required for Textract)"
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
