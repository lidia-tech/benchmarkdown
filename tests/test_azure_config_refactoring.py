"""
Test Azure Document Intelligence configuration refactoring.

This test verifies that the refactored Azure configuration based on
API version 2024-11-30 works correctly with all new parameters.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_azure_config_basic():
    """Test basic Azure configuration."""
    print("Test 1: Basic Azure configuration")
    print("-" * 60)

    from benchmarkdown.extractors.azure_document_intelligence import Config

    config = Config()
    print(f"  ✓ Default model: {config.model_id}")
    print(f"  ✓ Default output format: {config.output_content_format}")
    print("  ✅ Basic config created successfully")
    return True


def test_azure_config_advanced():
    """Test advanced Azure configuration with new parameters."""
    print("\nTest 2: Advanced Azure configuration")
    print("-" * 60)

    from benchmarkdown.extractors.azure_document_intelligence import Config
    from benchmarkdown.extractors.azure_document_intelligence.config import (
        DocumentAnalysisFeature,
        AnalyzeOutputOption,
        StringIndexType,
        AzureModelEnum,
        DocumentContentFormat
    )

    config = Config(
        model_id=AzureModelEnum.PREBUILT_READ,
        output_content_format=DocumentContentFormat.TEXT,
        pages='1-10',
        locale='it-IT',
        features=[DocumentAnalysisFeature.LANGUAGES, DocumentAnalysisFeature.BARCODES],
        query_fields=['Invoice', 'Date', 'Party1'],
        output=[AnalyzeOutputOption.PDF, AnalyzeOutputOption.FIGURES],
        string_index_type=StringIndexType.UTF16_CODE_UNIT
    )

    print(f"  ✓ Model ID: {config.model_id}")
    print(f"  ✓ Output format: {config.output_content_format}")
    print(f"  ✓ Pages: {config.pages}")
    print(f"  ✓ Locale: {config.locale}")
    print(f"  ✓ Features: {config.features}")
    print(f"  ✓ Query fields: {config.query_fields}")
    print(f"  ✓ Output: {config.output}")
    print(f"  ✓ String index type: {config.string_index_type}")
    print("  ✅ Advanced config created successfully")
    return True


def test_azure_config_conversion():
    """Test conversion to Azure API format."""
    print("\nTest 3: Configuration conversion to Azure API format")
    print("-" * 60)

    from benchmarkdown.extractors.azure_document_intelligence import Config
    from benchmarkdown.extractors.azure_document_intelligence.config import (
        DocumentAnalysisFeature,
        AnalyzeOutputOption,
        StringIndexType
    )

    config = Config(
        pages='1-5',
        locale='en-US',
        features=[DocumentAnalysisFeature.OCR_HIGH_RESOLUTION, DocumentAnalysisFeature.BARCODES],
        query_fields=['Party1', 'Party2'],
        output=[AnalyzeOutputOption.PDF],
        string_index_type=StringIndexType.UTF16_CODE_UNIT
    )

    endpoint, api_key, model_id, kwargs = config.to_azure_options()

    print(f"  ✓ Model ID: {model_id!r} (type: {type(model_id).__name__})")
    print(f"  ✓ Output format: {kwargs['output_content_format']!r} (type: {type(kwargs['output_content_format']).__name__})")
    print(f"  ✓ Kwargs keys: {list(kwargs.keys())}")
    print(f"  ✓ Pages: {kwargs.get('pages')}")
    print(f"  ✓ Locale: {kwargs.get('locale')}")
    print(f"  ✓ Features: {kwargs.get('features')}")
    print(f"  ✓ Query fields: {kwargs.get('query_fields')}")
    print(f"  ✓ Output: {kwargs.get('output')}")
    print(f"  ✓ String index type: {kwargs.get('string_index_type')}")

    # Verify all enum values are converted to strings
    all_strings = all([
        isinstance(model_id, str),
        isinstance(kwargs['output_content_format'], str),
        all(isinstance(f, str) for f in kwargs['features']),
        all(isinstance(o, str) for o in kwargs['output']),
        isinstance(kwargs['string_index_type'], str)
    ])

    if all_strings:
        print("  ✅ All enum values correctly converted to strings")
        return True
    else:
        print("  ❌ Some enum values are not strings")
        return False


def test_azure_extractor_integration():
    """Test extractor integration with refactored config."""
    print("\nTest 4: Extractor integration")
    print("-" * 60)

    from benchmarkdown.extractors.azure_document_intelligence import Extractor, Config
    from benchmarkdown.extractors.azure_document_intelligence.config import (
        DocumentAnalysisFeature,
        AnalyzeOutputOption,
        AzureModelEnum,
        DocumentContentFormat
    )

    # Test with default config
    config_default = Config()
    extractor = Extractor(config=config_default)
    print(f"  ✓ Default extractor endpoint: {extractor.endpoint}")
    print(f"  ✓ Default extractor model: {extractor.model_id}")
    print(f"  ✓ Default extractor kwargs: {extractor.analyze_kwargs}")

    # Test with advanced config
    config_advanced = Config(
        model_id=AzureModelEnum.PREBUILT_READ,
        output_content_format=DocumentContentFormat.TEXT,
        pages='1-10',
        locale='it-IT',
        features=[DocumentAnalysisFeature.LANGUAGES, DocumentAnalysisFeature.BARCODES],
        query_fields=['Invoice', 'Date'],
        output=[AnalyzeOutputOption.PDF]
    )
    extractor_advanced = Extractor(config=config_advanced)
    print(f"  ✓ Advanced extractor model: {extractor_advanced.model_id}")
    print(f"  ✓ Advanced extractor kwargs keys: {list(extractor_advanced.analyze_kwargs.keys())}")
    print(f"  ✓ Features: {extractor_advanced.analyze_kwargs.get('features')}")
    print(f"  ✓ Query fields: {extractor_advanced.analyze_kwargs.get('query_fields')}")
    print(f"  ✓ Output: {extractor_advanced.analyze_kwargs.get('output')}")

    print("  ✅ Extractor integration successful")
    return True


def test_azure_ui_generation():
    """Test UI component generation for Azure config."""
    print("\nTest 5: UI component generation")
    print("-" * 60)

    from benchmarkdown.extractors import ExtractorRegistry
    from benchmarkdown.config_ui import create_gradio_component_from_field

    registry = ExtractorRegistry()
    registry.discover_extractors()

    azure_metadata = registry.get_extractor('azure_document_intelligence')
    if not azure_metadata:
        print("  ⚠️  Azure Document Intelligence not in registry (expected if env vars not set)")
        return True

    config_class = azure_metadata.config_class

    print("  Testing UI component generation for all fields:")
    all_success = True
    for field_name, field_info in config_class.model_fields.items():
        try:
            field_type = field_info.annotation
            component, name = create_gradio_component_from_field(field_name, field_info, field_type)
            print(f"    ✓ {field_name}: {type(component).__name__}")
        except Exception as e:
            print(f"    ❌ {field_name}: {e}")
            all_success = False

    if all_success:
        print("  ✅ All UI components generated successfully")
        return True
    else:
        print("  ❌ Some UI components failed to generate")
        return False


def test_azure_field_groupings():
    """Test field groupings are correctly exported."""
    print("\nTest 6: Field groupings")
    print("-" * 60)

    from benchmarkdown.extractors.azure_document_intelligence import BASIC_FIELDS, ADVANCED_FIELDS

    print(f"  ✓ Basic fields: {BASIC_FIELDS}")
    print(f"  ✓ Advanced fields: {ADVANCED_FIELDS}")

    # Verify new fields are in advanced
    expected_new_fields = ['features', 'query_fields', 'output', 'string_index_type']
    all_present = all(field in ADVANCED_FIELDS for field in expected_new_fields)

    if all_present:
        print("  ✅ All new fields present in ADVANCED_FIELDS")
        return True
    else:
        missing = [f for f in expected_new_fields if f not in ADVANCED_FIELDS]
        print(f"  ❌ Missing fields in ADVANCED_FIELDS: {missing}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Azure Document Intelligence Configuration Tests")
    print("API Version: 2024-11-30")
    print("=" * 60)

    tests = [
        test_azure_config_basic,
        test_azure_config_advanced,
        test_azure_config_conversion,
        test_azure_extractor_integration,
        test_azure_ui_generation,
        test_azure_field_groupings,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n  ❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
