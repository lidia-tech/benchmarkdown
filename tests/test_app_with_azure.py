"""
Test that the app initializes correctly with the refactored Azure configuration.

This test verifies that the Gradio app can be created without errors when
the Azure Document Intelligence extractor is available.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_app_initialization():
    """Test that the app can be initialized without errors."""
    print("Test: App initialization with refactored Azure config")
    print("-" * 60)

    from benchmarkdown.extractors import ExtractorRegistry
    from benchmarkdown.ui.app_builder import create_app

    print("  ✓ Creating registry...")
    registry = ExtractorRegistry()
    registry.discover_extractors()

    print(f"  ✓ Found {len(registry.get_all_extractors())} extractors")
    print(f"  ✓ Available: {len(registry.get_available_extractors())} extractors")

    print("  ✓ Creating app...")
    demo = create_app(registry=registry)
    assert demo is not None
    print("  ✅ App created successfully!")
