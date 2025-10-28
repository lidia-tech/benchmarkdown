"""
Configuration models for document extraction tools.

This module provides Pydantic models for configuring extractors with type validation
and documentation. These models can be used to generate UI components automatically.
"""

import os
from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
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


class OcrEngineEnum(str, Enum):
    """OCR engine selection."""
    EASYOCR = "easyocr"
    TESSERACT = "tesseract"
    TESSERACT_CLI = "tesseract_cli"
    OCR_MAC = "ocr_mac"
    RAPID_OCR = "rapid_ocr"


# ============================================================================
# OCR Engine Configuration Models
# ============================================================================

class EasyOcrConfig(BaseModel):
    """Configuration for EasyOCR engine."""
    lang: list[str] = Field(
        default=["en"],
        description="Language codes for OCR (e.g.: en, fr, de')"
    )
    use_gpu: bool = Field(
        default=False,
        description="Enable GPU acceleration for EasyOCR"
    )
    confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for text detection"
    )
    bitmap_area_threshold: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Minimum area threshold for processing bitmaps"
    )
    force_full_page_ocr: bool = Field(
        default=False,
        description="Force OCR on entire page instead of selective regions"
    )
    model_storage_directory: Optional[str] = Field(
        default=None,
        description="Custom directory for EasyOCR models"
    )

    @field_validator("lang", mode="before")
    def split_languages(cls, v):
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [s.strip() for s in v.split(',')]
        return v


class TesseractOcrConfig(BaseModel):
    """Configuration for Tesseract OCR engine (Python API)."""
    lang: list[str] = Field(
        default=["eng"],
        description="Tesseract language codes (e.g., ['eng', 'fra', 'deu']) or ['auto'] for detection"
    )
    bitmap_area_threshold: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Minimum area threshold for processing bitmaps"
    )
    force_full_page_ocr: bool = Field(
        default=False,
        description="Force OCR on entire page instead of selective regions"
    )
    path: Optional[str] = Field(
        default=None,
        description="Path to Tesseract installation directory"
    )

    @field_validator("lang", mode="before")
    def split_languages(cls, v):
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [s.strip() for s in v.split(',')]
        return v


class TesseractCliOcrConfig(BaseModel):
    """Configuration for Tesseract OCR engine (CLI interface)."""
    lang: list[str] = Field(
        default=["eng"],
        description="Tesseract language codes (e.g., ['eng', 'fra', 'deu']) or ['auto'] for detection"
    )
    bitmap_area_threshold: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Minimum area threshold for processing bitmaps"
    )
    force_full_page_ocr: bool = Field(
        default=False,
        description="Force OCR on entire page instead of selective regions"
    )
    tesseract_cmd: Optional[str] = Field(
        default=None,
        description="Path to tesseract executable (auto-detected if None)"
    )
    path: Optional[str] = Field(
        default=None,
        description="Path to Tesseract data directory"
    )

    @field_validator("lang", mode="before")
    def split_languages(cls, v):
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [s.strip() for s in v.split(',')]
        return v

class OcrMacConfig(BaseModel):
    """Configuration for macOS native OCR engine (macOS only)."""
    lang: list[str] = Field(
        default=["en-US"],
        description="Language codes for macOS OCR (e.g., ['en-US', 'fr-FR'])"
    )
    bitmap_area_threshold: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Minimum area threshold for processing bitmaps"
    )
    force_full_page_ocr: bool = Field(
        default=False,
        description="Force OCR on entire page instead of selective regions"
    )

    @field_validator("lang", mode="before")
    def split_languages(cls, v):
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [s.strip() for s in v.split(',')]
        return v

class RapidOcrConfig(BaseModel):
    """Configuration for RapidOCR engine."""
    lang: list[str] = Field(
        default=["en"],
        description="Language codes for RapidOCR"
    )
    use_det: bool = Field(
        default=True,
        description="Enable text detection module"
    )
    use_rec: bool = Field(
        default=True,
        description="Enable text recognition module"
    )
    use_cls: bool = Field(
        default=False,
        description="Enable text classification/orientation detection"
    )
    text_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum text detection confidence score"
    )
    bitmap_area_threshold: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Minimum area threshold for processing bitmaps"
    )
    force_full_page_ocr: bool = Field(
        default=False,
        description="Force OCR on entire page instead of selective regions"
    )
    print_verbose: bool = Field(
        default=False,
        description="Enable verbose debug output"
    )

    @field_validator("lang", mode="before")
    def split_languages(cls, v):
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [s.strip() for s in v.split(',')]
        return v


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

    ocr_engine: OcrEngineEnum = Field(
        default=OcrEngineEnum.EASYOCR,
        description="OCR engine to use (EasyOCR, Tesseract, TesseractCLI, OcrMac, RapidOCR)"
    )

    # OCR Engine Configurations (only the selected engine config is used)
    easyocr_config: Optional[EasyOcrConfig] = Field(
        default_factory=EasyOcrConfig,
        description="Configuration for EasyOCR engine"
    )
    tesseract_config: Optional[TesseractOcrConfig] = Field(
        default_factory=TesseractOcrConfig,
        description="Configuration for Tesseract OCR engine (Python API)"
    )
    tesseract_cli_config: Optional[TesseractCliOcrConfig] = Field(
        default_factory=TesseractCliOcrConfig,
        description="Configuration for Tesseract CLI OCR engine"
    )
    ocr_mac_config: Optional[OcrMacConfig] = Field(
        default_factory=OcrMacConfig,
        description="Configuration for macOS native OCR (macOS only)"
    )
    rapidocr_config: Optional[RapidOcrConfig] = Field(
        default_factory=RapidOcrConfig,
        description="Configuration for RapidOCR engine"
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
            TableFormerMode,
            EasyOcrOptions,
            TesseractOcrOptions,
            TesseractCliOcrOptions,
            RapidOcrOptions,
        )
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import PdfFormatOption
        from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
        import platform

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

        # Create OCR options based on selected engine
        # Always provide a default OCR options instance, even if OCR is disabled
        ocr_options = EasyOcrOptions()  # Default fallback

        if self.do_ocr:
            ocr_engine = self.ocr_engine.value if isinstance(self.ocr_engine, OcrEngineEnum) else self.ocr_engine

            if ocr_engine == "easyocr" and self.easyocr_config:
                ocr_options = EasyOcrOptions(
                    lang=self.easyocr_config.lang,
                    use_gpu=self.easyocr_config.use_gpu,
                    confidence_threshold=self.easyocr_config.confidence_threshold,
                    bitmap_area_threshold=self.easyocr_config.bitmap_area_threshold,
                    force_full_page_ocr=self.easyocr_config.force_full_page_ocr,
                    model_storage_directory=self.easyocr_config.model_storage_directory,
                )
            elif ocr_engine == "tesseract" and self.tesseract_config:
                kwargs = {
                    "lang": self.tesseract_config.lang,
                    "bitmap_area_threshold": self.tesseract_config.bitmap_area_threshold,
                    "force_full_page_ocr": self.tesseract_config.force_full_page_ocr,
                }
                if self.tesseract_config.path:
                    kwargs["path"] = self.tesseract_config.path
                ocr_options = TesseractOcrOptions(**kwargs)
            elif ocr_engine == "tesseract_cli" and self.tesseract_cli_config:
                kwargs = {
                    "lang": self.tesseract_cli_config.lang,
                    "bitmap_area_threshold": self.tesseract_cli_config.bitmap_area_threshold,
                    "force_full_page_ocr": self.tesseract_cli_config.force_full_page_ocr,
                }
                if self.tesseract_cli_config.tesseract_cmd:
                    kwargs["tesseract_cmd"] = self.tesseract_cli_config.tesseract_cmd
                if self.tesseract_cli_config.path:
                    kwargs["path"] = self.tesseract_cli_config.path
                ocr_options = TesseractCliOcrOptions(**kwargs)
            elif ocr_engine == "ocr_mac" and self.ocr_mac_config:
                # Only create OcrMacOptions on macOS
                if platform.system() == "Darwin":
                    from docling.datamodel.pipeline_options import OcrMacOptions
                    ocr_options = OcrMacOptions(
                        lang=self.ocr_mac_config.lang,
                        bitmap_area_threshold=self.ocr_mac_config.bitmap_area_threshold,
                        force_full_page_ocr=self.ocr_mac_config.force_full_page_ocr,
                    )
                else:
                    # Fallback to EasyOCR if OcrMac is selected on non-Mac systems
                    ocr_options = EasyOcrOptions(force_full_page_ocr=True)
            elif ocr_engine == "rapid_ocr" and self.rapidocr_config:
                kwargs = {
                    "lang": self.rapidocr_config.lang,
                    "use_det": self.rapidocr_config.use_det,
                    "use_rec": self.rapidocr_config.use_rec,
                    "use_cls": self.rapidocr_config.use_cls,
                    "text_score": self.rapidocr_config.text_score,
                    "bitmap_area_threshold": self.rapidocr_config.bitmap_area_threshold,
                    "force_full_page_ocr": self.rapidocr_config.force_full_page_ocr,
                    "print_verbose": self.rapidocr_config.print_verbose,
                }
                ocr_options = RapidOcrOptions(**kwargs)

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
            ocr_options=ocr_options,
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


def _get_s3_workspace_from_env() -> str:
    """Get S3 workspace from environment variable."""
    return os.environ.get("TEXTRACT_S3_WORKSPACE", "s3://your-bucket-name/textract-workspace/")


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
