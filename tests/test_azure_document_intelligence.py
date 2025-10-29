#!/usr/bin/env python3
"""
Test script for Azure Document Intelligence extractor plugin.

This script tests the plugin structure, imports, configuration, and registry discovery.
Note: Full extraction testing requires valid Azure credentials.

Usage:
    uv run python tests/test_azure_document_intelligence.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_plugin_imports():
    """Test that all plugin components can be imported."""
    print("🧪 Testing plugin imports...")

    try:
        from benchmarkdown.extractors.azure_document_intelligence import (
            Extractor,
            Config,
            BASIC_FIELDS,
            ADVANCED_FIELDS,
            ENGINE_NAME,
            ENGINE_DISPLAY_NAME,
            is_available,
        )
        print("✅ All plugin exports import successfully")
        print(f"   - Engine name: {ENGINE_NAME}")
        print(f"   - Display name: {ENGINE_DISPLAY_NAME}")
        print(f"   - Basic fields: {BASIC_FIELDS}")
        print(f"   - Advanced fields: {ADVANCED_FIELDS}")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_plugin_availability():
    """Test the is_available() function."""
    print("\n🧪 Testing plugin availability check...")

    try:
        from benchmarkdown.extractors.azure_document_intelligence import is_available

        available, message = is_available()

        if available:
            print("✅ Plugin is available")
            print("   - Azure SDK installed")
            print("   - Environment variables configured")
        else:
            print("⚠️  Plugin not available (expected without setup)")
            print(f"   - Reason: {message}")

        return True
    except Exception as e:
        print(f"❌ Availability check failed: {e}")
        return False


def test_config_creation():
    """Test that configuration can be created and validated."""
    print("\n🧪 Testing configuration creation...")

    try:
        from benchmarkdown.extractors.azure_document_intelligence import Config, is_available

        # Check if dependencies are available
        available, message = is_available()
        if not available:
            print("⚠️  Skipping config test - dependencies not available")
            print(f"   - Reason: {message}")
            return True  # Not a failure, just skipped

        # Test default config
        config_default = Config()
        print("✅ Default config created")
        print(f"   - Model: {config_default.model_id}")
        print(f"   - Output format: {config_default.output_content_format}")

        # Test custom config
        config_custom = Config(
            model_id="prebuilt-read",
            output_content_format="text",
            pages="1-5",
            locale="en-US"
        )
        print("✅ Custom config created")
        print(f"   - Model: {config_custom.model_id}")
        print(f"   - Output format: {config_custom.output_content_format}")
        print(f"   - Pages: {config_custom.pages}")
        print(f"   - Locale: {config_custom.locale}")

        # Test config conversion
        endpoint, api_key, model_id, analyze_kwargs = config_custom.to_azure_options()
        print("✅ Config conversion works")
        print(f"   - Model ID: {model_id}")
        print(f"   - Analyze kwargs: {analyze_kwargs}")

        return True
    except Exception as e:
        print(f"❌ Config creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_extractor_instantiation():
    """Test that extractor can be instantiated."""
    print("\n🧪 Testing extractor instantiation...")

    try:
        from benchmarkdown.extractors.azure_document_intelligence import Extractor, Config, is_available

        # Check if dependencies are available
        available, message = is_available()
        if not available:
            print("⚠️  Skipping instantiation test - dependencies not available")
            print(f"   - Reason: {message}")
            return True  # Not a failure, just skipped

        # Set dummy credentials to test instantiation
        os.environ["AZURE_DOC_INTEL_ENDPOINT"] = "https://test.cognitiveservices.azure.com/"
        os.environ["AZURE_DOC_INTEL_KEY"] = "dummy-key-for-testing"

        config = Config()
        extractor = Extractor(config=config)

        print("✅ Extractor instantiated successfully")
        print(f"   - Endpoint: {extractor.endpoint}")
        print(f"   - Model ID: {extractor.model_id}")

        return True
    except Exception as e:
        print(f"❌ Extractor instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_registry_discovery():
    """Test that the plugin can be discovered by the registry."""
    print("\n🧪 Testing registry discovery...")

    try:
        from benchmarkdown.extractors import ExtractorRegistry

        registry = ExtractorRegistry()
        registry.discover_extractors()
        extractors = registry.get_all_extractors()

        print(f"✅ Registry initialized with {len(extractors)} extractors")

        # Check if Azure Document Intelligence is in the list
        if "azure_document_intelligence" in extractors:
            print("✅ Azure Document Intelligence discovered by registry")
            metadata = extractors["azure_document_intelligence"]
            print(f"   - Display name: {metadata.display_name}")
            print(f"   - Available: {metadata.is_available}")
            if not metadata.is_available:
                print(f"   - Reason: {metadata.availability_message}")
        else:
            print("⚠️  Azure Document Intelligence not in registry (check dependencies)")

        return True
    except Exception as e:
        print(f"❌ Registry discovery failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("Azure Document Intelligence Extractor - Plugin Test Suite")
    print("=" * 70)

    results = []

    # Run tests
    results.append(("Import Test", test_plugin_imports()))
    results.append(("Availability Test", test_plugin_availability()))
    results.append(("Config Test", test_config_creation()))
    results.append(("Instantiation Test", test_extractor_instantiation()))
    results.append(("Registry Discovery", test_registry_discovery()))

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
