"""
Docling extractor plugin.

This plugin provides document-to-markdown extraction using IBM's Docling library.
Docling supports local processing with OCR, table extraction, and various document formats.
"""

from typing import Tuple

from .extractor import DoclingExtractor
from .config import (
    DoclingConfig,
    DOCLING_BASIC_FIELDS,
    DOCLING_ADVANCED_FIELDS,
    # OCR configs
    EasyOcrConfig,
    TesseractOcrConfig,
    TesseractCliOcrConfig,
    OcrMacConfig,
    RapidOcrConfig,
    # OCR field groupings
    EASYOCR_BASIC_FIELDS,
    EASYOCR_ADVANCED_FIELDS,
    TESSERACT_BASIC_FIELDS,
    TESSERACT_ADVANCED_FIELDS,
    TESSERACT_CLI_BASIC_FIELDS,
    TESSERACT_CLI_ADVANCED_FIELDS,
    OCR_MAC_BASIC_FIELDS,
    OCR_MAC_ADVANCED_FIELDS,
    RAPIDOCR_BASIC_FIELDS,
    RAPIDOCR_ADVANCED_FIELDS,
)

# Standard plugin interface exports
Extractor = DoclingExtractor
Config = DoclingConfig
BASIC_FIELDS = DOCLING_BASIC_FIELDS
ADVANCED_FIELDS = DOCLING_ADVANCED_FIELDS

# Plugin metadata
ENGINE_NAME = "docling"
ENGINE_DISPLAY_NAME = "Docling (Local)"

# Nested configuration metadata (optional - for complex configs like Docling)
# Maps parent field name to child config options
NESTED_CONFIGS = {
    "ocr_engine": {
        "easyocr": {
            "config_class": EasyOcrConfig,
            "config_field": "easyocr_config",  # Field name in parent config
            "basic_fields": EASYOCR_BASIC_FIELDS,
            "advanced_fields": EASYOCR_ADVANCED_FIELDS,
            "display_name": "EasyOCR Options",
        },
        "tesseract": {
            "config_class": TesseractOcrConfig,
            "config_field": "tesseract_config",
            "basic_fields": TESSERACT_BASIC_FIELDS,
            "advanced_fields": TESSERACT_ADVANCED_FIELDS,
            "display_name": "Tesseract Options",
        },
        "tesseract_cli": {
            "config_class": TesseractCliOcrConfig,
            "config_field": "tesseract_cli_config",
            "basic_fields": TESSERACT_CLI_BASIC_FIELDS,
            "advanced_fields": TESSERACT_CLI_ADVANCED_FIELDS,
            "display_name": "Tesseract CLI Options",
        },
        "ocr_mac": {
            "config_class": OcrMacConfig,
            "config_field": "ocr_mac_config",
            "basic_fields": OCR_MAC_BASIC_FIELDS,
            "advanced_fields": OCR_MAC_ADVANCED_FIELDS,
            "display_name": "macOS OCR Options",
        },
        "rapid_ocr": {
            "config_class": RapidOcrConfig,
            "config_field": "rapidocr_config",
            "basic_fields": RAPIDOCR_BASIC_FIELDS,
            "advanced_fields": RAPIDOCR_ADVANCED_FIELDS,
            "display_name": "RapidOCR Options",
        },
    }
}


def is_available() -> Tuple[bool, str]:
    """
    Check if Docling dependencies are installed and available.

    Returns:
        Tuple of (is_available, message)
        - is_available: True if Docling is installed
        - message: Empty string if available, error message otherwise
    """
    try:
        import docling
        return True, ""
    except ImportError as e:
        return False, f"Docling not installed: {e}"


__all__ = [
    'Extractor',
    'Config',
    'BASIC_FIELDS',
    'ADVANCED_FIELDS',
    'ENGINE_NAME',
    'ENGINE_DISPLAY_NAME',
    'is_available',
    # Also export the actual classes for direct imports
    'DoclingExtractor',
    'DoclingConfig',
]
