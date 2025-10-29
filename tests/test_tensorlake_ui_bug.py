"""
Test for TensorLake UI bug fixes.

Tests that Optional[Enum] fields correctly generate Dropdown components
and that enum values are properly extracted (not string representations).
"""

import sys
from benchmarkdown.extractors.tensorlake import Config
from benchmarkdown.config_ui import create_gradio_component_from_field, build_config_from_ui_values
import gradio as gr


def test_optional_enum_creates_dropdown():
    """Test that Optional[Enum] fields create Dropdown components."""
    print("\n" + "="*60)
    print("TEST 1: Optional[Enum] fields should create Dropdowns")
    print("="*60)

    config_class = Config
    field_name = 'chunking_strategy'
    field_info = config_class.model_fields[field_name]
    field_type = field_info.annotation

    component, comp_id = create_gradio_component_from_field(field_name, field_info, field_type)

    print(f'\nField: {field_name}')
    print(f'Field type: {field_type}')
    print(f'Component type: {type(component).__name__}')
    print(f'Expected: Dropdown')

    if isinstance(component, gr.Dropdown):
        print('✅ PASS: Optional enum creates Dropdown')
        print(f'Choices: {component.choices}')
        print(f'Default value: {component.value}')
    else:
        print(f'❌ FAIL: Got {type(component).__name__} instead of Dropdown')
        return False

    # Verify choices are enum values, not string representations
    # Gradio formats choices as tuples (label, value)
    expected_values = ['fragment', 'none', 'page', 'section']
    actual_values = [choice[1] if isinstance(choice, tuple) else choice for choice in component.choices]

    if actual_values == expected_values:
        print(f'✅ PASS: Choices are enum values: {actual_values}')
    else:
        print(f'❌ FAIL: Expected {expected_values}, got {actual_values}')
        return False

    # Verify default value is an enum value
    if component.value == 'section':
        print(f'✅ PASS: Default value is enum value: {component.value}')
    else:
        print(f'❌ FAIL: Expected "section", got {component.value}')
        return False

    return True


def test_all_optional_enums():
    """Test all optional enum fields in TensorLake config."""
    print("\n" + "="*60)
    print("TEST 2: All optional enum fields should create Dropdowns")
    print("="*60)

    config_class = Config
    optional_enum_fields = ['chunking_strategy', 'table_parsing_format', 'ocr_model']

    all_passed = True
    for field_name in optional_enum_fields:
        field_info = config_class.model_fields[field_name]
        field_type = field_info.annotation
        component, _ = create_gradio_component_from_field(field_name, field_info, field_type)

        if isinstance(component, gr.Dropdown):
            print(f'✅ {field_name}: Dropdown with choices {component.choices}')
        else:
            print(f'❌ {field_name}: {type(component).__name__} (expected Dropdown)')
            all_passed = False

    return all_passed


def test_config_build_from_ui_values():
    """Test that config can be built from UI values with proper enum values."""
    print("\n" + "="*60)
    print("TEST 3: Build config from UI values (enum value strings)")
    print("="*60)

    # Simulate UI values (what Gradio returns)
    ui_values = {
        'api_key': 'test-key',
        'chunking_strategy': 'section',  # String value, not enum
        'table_output_mode': 'markdown',
        'table_parsing_format': None,  # Optional, None is valid
        'signature_detection': False,
        'remove_strikethrough_lines': False,
        'skew_detection': False,
        'disable_layout_detection': False,
        'cross_page_header_detection': False,
        'ocr_model': None,
        'figure_summarization': False,
        'figure_summarization_prompt': None,
        'table_summarization': False,
        'table_summarization_prompt': None,
        'include_full_page_image': False,
    }

    try:
        config = build_config_from_ui_values(Config, ui_values)
        print(f'✅ PASS: Config built successfully')
        print(f'   chunking_strategy: {config.chunking_strategy}')
        print(f'   table_output_mode: {config.table_output_mode}')
        print(f'   table_parsing_format: {config.table_parsing_format}')
        return True
    except Exception as e:
        print(f'❌ FAIL: Config build failed with error:')
        print(f'   {type(e).__name__}: {e}')
        return False


def test_enum_string_representation_bug():
    """Test that we don't get string representations like 'ChunkingStrategyEnum.SECTION'."""
    print("\n" + "="*60)
    print("TEST 4: Verify no enum string representations in UI")
    print("="*60)

    config_class = Config
    field_name = 'chunking_strategy'
    field_info = config_class.model_fields[field_name]
    field_type = field_info.annotation

    component, _ = create_gradio_component_from_field(field_name, field_info, field_type)

    # Check that none of the choices are string representations
    bad_patterns = ['ChunkingStrategyEnum', 'Enum.']
    has_bad_value = any(
        any(pattern in str(choice) for pattern in bad_patterns)
        for choice in component.choices
    )

    if has_bad_value:
        print(f'❌ FAIL: Found enum string representation in choices: {component.choices}')
        return False
    else:
        print(f'✅ PASS: No enum string representations found')
        print(f'   Choices are clean values: {component.choices}')
        return True


if __name__ == '__main__':
    print("Testing TensorLake UI Bug Fixes")
    print("="*60)

    results = []
    results.append(("Optional enum creates dropdown", test_optional_enum_creates_dropdown()))
    results.append(("All optional enums", test_all_optional_enums()))
    results.append(("Config build from UI", test_config_build_from_ui_values()))
    results.append(("No enum string representations", test_enum_string_representation_bug()))

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
