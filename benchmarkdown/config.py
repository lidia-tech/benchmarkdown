"""
Backward compatibility module for extractor configurations.

This module re-exports configuration classes from their new plugin locations
to maintain backward compatibility with existing code.

New code should use:
    from benchmarkdown.extractors.docling import Config as DoclingConfig
    from benchmarkdown.extractors.textract import Config as TextractConfig

But this module allows existing imports to continue working:
    from benchmarkdown.config import DoclingConfig, TextractConfig
"""

# Re-export Docling configurations
from benchmarkdown.extractors.docling.config import (
    DoclingConfig,
    TableFormerModeEnum,
    AcceleratorDeviceEnum,
    OcrEngineEnum,
    EasyOcrConfig,
    TesseractOcrConfig,
    TesseractCliOcrConfig,
    OcrMacConfig,
    RapidOcrConfig,
)

# Re-export Textract configurations
from benchmarkdown.extractors.textract.config import (
    TextractConfig,
    TextractFeaturesEnum,
)

__all__ = [
    # Docling
    'DoclingConfig',
    'TableFormerModeEnum',
    'AcceleratorDeviceEnum',
    'OcrEngineEnum',
    'EasyOcrConfig',
    'TesseractOcrConfig',
    'TesseractCliOcrConfig',
    'OcrMacConfig',
    'RapidOcrConfig',
    # Textract
    'TextractConfig',
    'TextractFeaturesEnum',
]
