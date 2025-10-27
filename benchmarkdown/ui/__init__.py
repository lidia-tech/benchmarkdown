"""
Benchmarkdown UI - Modular user interface components.

This module provides a refactored, modular architecture for the Benchmarkdown UI:
- core: BenchmarkUI class and ExtractionResult dataclass
- queue: Task queue management and persistence
- results: Results viewing and comparison HTML generation
- app_builder: Main Gradio app creation function
"""

from .core import BenchmarkUI, ExtractionResult
from .app_builder import create_app

__all__ = ['BenchmarkUI', 'ExtractionResult', 'create_app']
