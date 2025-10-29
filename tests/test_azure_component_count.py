"""
Test Azure component count to debug the save_profile_handler mismatch.

This test verifies that the correct number of UI components is generated
for the Azure Document Intelligence extractor.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_azure_component_count():
    """Test that Azure generates the expected number of components."""
    print("Test: Azure UI Component Count")
    print("-" * 60)

    from benchmarkdown.extractors import ExtractorRegistry
    from benchmarkdown.ui.dynamic_config import DynamicConfigUI
    import gradio as gr

    registry = ExtractorRegistry()
    registry.discover_extractors()

    # Get Azure metadata
    azure_metadata = registry.get_extractor('azure_document_intelligence')
    if not azure_metadata:
        print("  ⚠️  Azure not available (expected if env vars not set)")
        print("  Creating mock metadata for testing...")
        # Import directly to test component generation
        from benchmarkdown.extractors.azure_document_intelligence import (
            Config, BASIC_FIELDS, ADVANCED_FIELDS, ENGINE_NAME, ENGINE_DISPLAY_NAME
        )
        from benchmarkdown.extractors import ExtractorMetadata

        azure_metadata = ExtractorMetadata(
            engine_name=ENGINE_NAME,
            display_name=ENGINE_DISPLAY_NAME,
            extractor_class=None,  # Not needed for UI generation
            config_class=Config,
            basic_fields=BASIC_FIELDS,
            advanced_fields=ADVANCED_FIELDS,
            is_available=False,
            availability_message="Test mode",
            module_path="benchmarkdown.extractors.azure_document_intelligence"
        )

    print(f"  ✓ Azure config class: {azure_metadata.config_class.__name__}")
    print(f"  ✓ Basic fields: {azure_metadata.basic_fields}")
    print(f"  ✓ Advanced fields: {azure_metadata.advanced_fields}")
    print(f"  ✓ Total fields: {len(azure_metadata.basic_fields) + len(azure_metadata.advanced_fields)}")

    # Count fields in config class
    all_fields = list(azure_metadata.config_class.model_fields.keys())
    print(f"  ✓ Fields in config class: {all_fields}")
    print(f"  ✓ Field count from model: {len(all_fields)}")

    # Now generate UI and count components
    with gr.Blocks():
        dynamic_config = DynamicConfigUI(registry)

        # Manually generate UI for Azure
        (config_area, components, field_names, nested_groups, parent_components,
         conditional_groups, conditional_parent_components) = dynamic_config.generate_config_ui_for_extractor(azure_metadata)

        print(f"\n  UI Generation Results:")
        print(f"  ✓ Components generated: {len(components)}")
        print(f"  ✓ Field names tracked: {len(field_names)}")
        print(f"  ✓ Field names: {field_names}")

        # Check for discrepancies
        expected_field_count = len(azure_metadata.basic_fields) + len(azure_metadata.advanced_fields)
        if len(components) == expected_field_count:
            print(f"\n  ✅ Component count matches expected: {len(components)} == {expected_field_count}")
            return True
        else:
            print(f"\n  ❌ Component count mismatch!")
            print(f"     Expected: {expected_field_count}")
            print(f"     Got: {len(components)}")
            print(f"     Difference: {expected_field_count - len(components)}")

            # Find missing fields
            basic_and_advanced = azure_metadata.basic_fields + azure_metadata.advanced_fields
            missing = [f for f in basic_and_advanced if f not in field_names]
            extra = [f for f in field_names if f not in basic_and_advanced]

            if missing:
                print(f"     Missing from UI: {missing}")
            if extra:
                print(f"     Extra in UI: {extra}")

            return False


def test_all_extractors_component_count():
    """Test component counts for all extractors."""
    print("\n" + "=" * 60)
    print("Test: All Extractors Component Count")
    print("=" * 60)

    from benchmarkdown.extractors import ExtractorRegistry
    from benchmarkdown.ui.dynamic_config import DynamicConfigUI
    import gradio as gr

    registry = ExtractorRegistry()
    registry.discover_extractors()

    all_extractors = registry.get_all_extractors()
    print(f"\nTotal extractors: {len(all_extractors)}")

    with gr.Blocks():
        dynamic_config = DynamicConfigUI(registry)

        total_components = 0
        for engine_name, metadata in all_extractors.items():
            (config_area, components, field_names, nested_groups, parent_components,
             conditional_groups, conditional_parent_components) = dynamic_config.generate_config_ui_for_extractor(metadata)

            expected = len(metadata.basic_fields) + len(metadata.advanced_fields)

            # Count nested config components
            nested_count = 0
            if metadata.nested_configs:
                for parent_field, options in metadata.nested_configs.items():
                    for option_value, option_meta in options.items():
                        nested_basic = len(option_meta.get("basic_fields", []))
                        nested_advanced = len(option_meta.get("advanced_fields", []))
                        nested_count += nested_basic + nested_advanced + 1  # +1 for label
                        if nested_advanced > 0:
                            nested_count += 1  # +1 for accordion

            expected_with_nested = expected + nested_count

            status = "✅" if len(components) == expected_with_nested else "❌"
            print(f"\n  {status} {metadata.display_name}:")
            print(f"     Basic fields: {len(metadata.basic_fields)}")
            print(f"     Advanced fields: {len(metadata.advanced_fields)}")
            print(f"     Nested components: {nested_count}")
            print(f"     Expected components: {expected_with_nested}")
            print(f"     Actual components: {len(components)}")

            total_components += len(components)

        print(f"\n  Total components across all extractors: {total_components}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Azure Component Count Debug Tests")
    print("=" * 60)
    print()

    result1 = test_azure_component_count()
    test_all_extractors_component_count()

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    if result1:
        print("✅ Azure component count test passed!")
        return 0
    else:
        print("❌ Azure component count test failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
