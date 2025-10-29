"""
Simple test to verify the app can be created without errors.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Test app creation."""
    print("=" * 60)
    print("Simple App Creation Test")
    print("=" * 60)

    try:
        from benchmarkdown.extractors import ExtractorRegistry
        from benchmarkdown.ui.app_builder import create_app

        print("\n  ✓ Creating registry...")
        registry = ExtractorRegistry()
        registry.discover_extractors()

        available = registry.get_available_extractors()
        all_extractors = registry.get_all_extractors()

        print(f"  ✓ Registered: {len(all_extractors)} extractors")
        print(f"  ✓ Available: {len(available)} extractors")

        print("\n  ✓ Creating app...")
        demo = create_app(registry=registry)

        print("\n  ✅ App created successfully!")
        print("\n" + "=" * 60)
        print("✅ TEST PASSED")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
