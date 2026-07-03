"""
Simple test to verify the app can be created without errors.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_app_creation():
    """The Gradio app object builds from a discovered registry without launching."""
    from benchmarkdown.extractors import ExtractorRegistry
    from benchmarkdown.ui.app_builder import create_app

    registry = ExtractorRegistry()
    registry.discover_extractors()

    # Discovery should surface the plugin set (available is a subset of all).
    all_extractors = registry.get_all_extractors()
    available = registry.get_available_extractors()
    assert len(all_extractors) > 0
    assert len(available) <= len(all_extractors)

    demo = create_app(registry=registry)
    assert demo is not None
