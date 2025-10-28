"""
Backward compatibility module for AWS Textract extractor.

This module re-exports the Textract extractor from its new plugin location
to maintain backward compatibility with existing code.

New code should use:
    from benchmarkdown.extractors.textract import Extractor, Config

But this module allows existing imports to continue working:
    from benchmarkdown.textract import TextractExtractor
"""

from benchmarkdown.extractors.textract import (
    TextractExtractor,
    TextractConfig,
    Extractor,
    Config,
)

__all__ = ['TextractExtractor', 'TextractConfig', 'Extractor', 'Config']
