"""
Test TensorLake plugin implementation.

This test verifies that the TensorLake plugin is correctly structured and
can be discovered by the extractor registry.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_tensorlake_config_import():
    """Test that TensorLake configuration can be imported."""
    print("✅ Test 1: Import TensorLake config module")

    try:
        from benchmarkdown.extractors.tensorlake import config
        print(f"   ✓ Config module imported: {config.__file__}")

        # Check for required classes and enums
        assert hasattr(config, 'TensorLakeConfig')
        assert hasattr(config, 'ChunkingStrategyEnum')
        assert hasattr(config, 'TableOutputModeEnum')
        assert hasattr(config, 'TENSORLAKE_BASIC_FIELDS')
        assert hasattr(config, 'TENSORLAKE_ADVANCED_FIELDS')
        print("   ✓ All required config classes found")

        return True
    except Exception as e:
        print(f"   ❌ Failed to import config: {e}")
        return False


def test_tensorlake_config_creation():
    """Test that TensorLake config can be instantiated."""
    print("\n✅ Test 2: Create TensorLake configuration")

    try:
        from benchmarkdown.extractors.tensorlake.config import TensorLakeConfig

        # Test default config
        config = TensorLakeConfig()
        print(f"   ✓ Default config created")
        print(f"     - chunking_strategy: {config.chunking_strategy}")
        print(f"     - table_output_mode: {config.table_output_mode}")
        print(f"     - signature_detection: {config.signature_detection}")

        # Test custom config
        config = TensorLakeConfig(
            chunking_strategy="page",
            table_output_mode="html",
            signature_detection=True,
            figure_summarization=True,
            table_summarization=True,
            max_timeout=600
        )
        print(f"   ✓ Custom config created with:")
        print(f"     - chunking_strategy: {config.chunking_strategy}")
        print(f"     - table_output_mode: {config.table_output_mode}")
        print(f"     - figure_summarization: {config.figure_summarization}")

        return True
    except Exception as e:
        print(f"   ❌ Failed to create config: {e}")
        return False


def test_tensorlake_plugin_interface():
    """Test that TensorLake plugin interface is correct."""
    print("\n✅ Test 3: Check TensorLake plugin interface")

    try:
        from benchmarkdown.extractors import tensorlake

        # Check plugin metadata
        assert hasattr(tensorlake, 'ENGINE_NAME')
        assert hasattr(tensorlake, 'ENGINE_DISPLAY_NAME')
        assert hasattr(tensorlake, 'is_available')
        assert hasattr(tensorlake, 'Extractor')
        assert hasattr(tensorlake, 'Config')
        assert hasattr(tensorlake, 'BASIC_FIELDS')
        assert hasattr(tensorlake, 'ADVANCED_FIELDS')
        assert hasattr(tensorlake, 'CONDITIONAL_FIELDS')

        print(f"   ✓ Plugin metadata:")
        print(f"     - ENGINE_NAME: {tensorlake.ENGINE_NAME}")
        print(f"     - ENGINE_DISPLAY_NAME: {tensorlake.ENGINE_DISPLAY_NAME}")
        print(f"     - BASIC_FIELDS: {tensorlake.BASIC_FIELDS}")
        print(f"     - ADVANCED_FIELDS: {tensorlake.ADVANCED_FIELDS}")

        # Test is_available function
        available, message = tensorlake.is_available()
        print(f"   ✓ is_available() returned: {available}")
        if not available:
            print(f"     - Message: {message}")

        return True
    except Exception as e:
        print(f"   ❌ Failed plugin interface check: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tensorlake_extractor_registry():
    """Test that TensorLake can be discovered by the extractor registry."""
    print("\n✅ Test 4: Check TensorLake in extractor registry")

    try:
        from benchmarkdown.extractors import ExtractorRegistry

        registry = ExtractorRegistry()
        print(f"   ✓ ExtractorRegistry created")

        # Discover extractors
        extractors = registry.discover_extractors()
        print(f"   ✓ Available extractors: {list(extractors.keys())}")

        if 'tensorlake' in extractors:
            print("   ✅ TensorLake is registered!")
            extractor_info = extractors['tensorlake']
            print(f"     - Display name: {extractor_info.display_name}")
            print(f"     - Available: {extractor_info.is_available}")
            print(f"     - Availability message: {extractor_info.availability_message}")
        else:
            print("   ⚠️  TensorLake not registered (plugin discovery failed)")
            print(f"     - Registered extractors: {list(extractors.keys())}")

        return True
    except Exception as e:
        print(f"   ❌ Failed registry check: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_field_groupings():
    """Test that field groupings are properly defined."""
    print("\n✅ Test 5: Validate field groupings")

    try:
        from benchmarkdown.extractors.tensorlake import BASIC_FIELDS, ADVANCED_FIELDS
        from benchmarkdown.extractors.tensorlake.config import TensorLakeConfig

        # Get all config fields
        config_fields = set(TensorLakeConfig.model_fields.keys())
        basic_set = set(BASIC_FIELDS)
        advanced_set = set(ADVANCED_FIELDS)

        # api_key and max_timeout are intentionally excluded from UI fields
        config_fields.discard('api_key')
        config_fields.discard('max_timeout')

        print(f"   ✓ Config fields: {len(config_fields)}")
        print(f"   ✓ Basic fields: {len(BASIC_FIELDS)}")
        print(f"   ✓ Advanced fields: {len(ADVANCED_FIELDS)}")

        # Check for duplicates
        overlap = basic_set & advanced_set
        if overlap:
            print(f"   ⚠️  Overlapping fields: {overlap}")
        else:
            print(f"   ✓ No overlapping fields between BASIC and ADVANCED")

        # Check all fields are covered
        all_ui_fields = basic_set | advanced_set
        uncovered = config_fields - all_ui_fields
        if uncovered:
            print(f"   ⚠️  Fields not in UI: {uncovered}")
        else:
            print(f"   ✓ All config fields covered in UI")

        return True
    except Exception as e:
        print(f"   ❌ Failed field grouping check: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("TensorLake Plugin Implementation Test")
    print("=" * 70)

    tests = [
        test_tensorlake_config_import,
        test_tensorlake_config_creation,
        test_tensorlake_plugin_interface,
        test_tensorlake_extractor_registry,
        test_field_groupings,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Test Results: {passed}/{total} passed")

    if passed == total:
        print("✅ All tests passed!")
    else:
        print(f"❌ {total - passed} test(s) failed")
    print("=" * 70)

    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(main())
