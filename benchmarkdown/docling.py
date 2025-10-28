"""
Backward compatibility module for Docling extractor.

This module re-exports the Docling extractor from its new plugin location
to maintain backward compatibility with existing code.

New code should use:
    from benchmarkdown.extractors.docling import Extractor, Config

But this module allows existing imports to continue working:
    from benchmarkdown.docling import DoclingExtractor
"""

from benchmarkdown.extractors.docling import (
    DoclingExtractor,
    DoclingConfig,
    Extractor,
    Config,
)

__all__ = ['DoclingExtractor', 'DoclingConfig', 'Extractor', 'Config']
