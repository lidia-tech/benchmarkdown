"""Test that app can be created with validation UI integrated."""

from benchmarkdown.extractors import ExtractorRegistry
from benchmarkdown.ui.app_builder import create_app


def test_app_creation_with_validation():
    """Test that the app can be created with validation UI."""
    print("\n" + "="*60)
    print("Test: App Creation with Validation UI")
    print("="*60)

    # Discover extractors
    print("\n1. Discovering extractors...")
    registry = ExtractorRegistry()
    registry.discover_extractors()

    available_count = len(registry.get_available_extractors())
    print(f"   ✅ Discovered {available_count} available extractor(s)")

    # Create app
    print("\n2. Creating app with validation UI...")
    try:
        app = create_app(registry)
        print("   ✅ App created successfully")
    except Exception as e:
        print(f"   ❌ Failed to create app: {e}")
        import traceback
        traceback.print_exc()
        raise

    # Verify app has components
    print("\n3. Verifying app structure...")
    assert app is not None, "App should not be None"
    print("   ✅ App structure verified")

    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_app_creation_with_validation()
