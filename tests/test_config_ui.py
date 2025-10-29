#!/usr/bin/env python3
"""
Test script for configuration UI generation.

This script tests that Gradio components can be generated from Pydantic models
and that config objects can be built from UI values.
"""

from benchmarkdown.extractors.docling import Config as DoclingConfig, BASIC_FIELDS as DOCLING_BASIC_FIELDS, ADVANCED_FIELDS as DOCLING_ADVANCED_FIELDS
from benchmarkdown.extractors.docling.config import TableFormerModeEnum
from benchmarkdown.config_ui import (
    create_gradio_component_from_field,
    build_config_from_ui_values
)
from pydantic import BaseModel
import gradio as gr


def test_field_component_creation():
    """Test creating Gradio components from Pydantic fields."""
    print("🧪 Testing Gradio component creation from Pydantic fields\n")

    # Test boolean field
    field_info = DoclingConfig.model_fields['do_ocr']
    field_type = field_info.annotation
    component, comp_id = create_gradio_component_from_field('do_ocr', field_info, field_type)
    print(f"✓ Boolean field 'do_ocr': {type(component).__name__}")
    assert isinstance(component, gr.Checkbox), "Boolean should create Checkbox"

    # Test enum field
    field_info = DoclingConfig.model_fields['table_structure_mode']
    field_type = field_info.annotation
    component, comp_id = create_gradio_component_from_field('table_structure_mode', field_info, field_type)
    print(f"✓ Enum field 'table_structure_mode': {type(component).__name__}")
    assert isinstance(component, gr.Dropdown), "Enum should create Dropdown"

    # Test integer field with constraints
    field_info = DoclingConfig.model_fields['num_threads']
    field_type = field_info.annotation
    component, comp_id = create_gradio_component_from_field('num_threads', field_info, field_type)
    print(f"✓ Integer field 'num_threads': {type(component).__name__}")
    assert isinstance(component, gr.Slider), "Integer should create Slider"

    # Test float field
    field_info = DoclingConfig.model_fields['images_scale']
    field_type = field_info.annotation
    component, comp_id = create_gradio_component_from_field('images_scale', field_info, field_type)
    print(f"✓ Float field 'images_scale': {type(component).__name__}")
    assert isinstance(component, gr.Slider), "Float should create Slider"

    print()


def test_config_building():
    """Test building config objects from UI values."""
    print("🧪 Testing config object building from UI values\n")

    # Simulate UI values
    ui_values = {
        'do_ocr': False,
        'do_table_structure': True,
        'table_structure_mode': 'fast',
        'num_threads': 8,
        'do_code_enrichment': True,
        'do_formula_enrichment': False,
        'images_scale': 1.5,
        'document_timeout': None,
    }

    config = build_config_from_ui_values(DoclingConfig, ui_values)

    print("✓ Config object created from UI values")
    print(f"  do_ocr: {config.do_ocr}")
    print(f"  table_structure_mode: {config.table_structure_mode}")
    print(f"  num_threads: {config.num_threads}")
    print(f"  do_code_enrichment: {config.do_code_enrichment}")
    print(f"  images_scale: {config.images_scale}")

    assert config.do_ocr == False
    assert config.table_structure_mode == TableFormerModeEnum.FAST or config.table_structure_mode == 'fast'
    assert config.num_threads == 8
    assert config.do_code_enrichment == True
    assert config.images_scale == 1.5

    print()


def test_field_groupings():
    """Test that field groupings are defined correctly."""
    print("🧪 Testing field groupings\n")

    all_fields = set(DoclingConfig.model_fields.keys())
    basic_fields = set(DOCLING_BASIC_FIELDS)
    advanced_fields = set(DOCLING_ADVANCED_FIELDS)

    print(f"Total fields in DoclingConfig: {len(all_fields)}")
    print(f"Basic fields: {len(basic_fields)}")
    print(f"Advanced fields: {len(advanced_fields)}")

    # Check that all basic fields exist
    missing_basic = basic_fields - all_fields
    if missing_basic:
        print(f"⚠️  Missing basic fields: {missing_basic}")
    else:
        print("✓ All basic fields exist in DoclingConfig")

    # Check that all advanced fields exist
    missing_advanced = advanced_fields - all_fields
    if missing_advanced:
        print(f"⚠️  Missing advanced fields: {missing_advanced}")
    else:
        print("✓ All advanced fields exist in DoclingConfig")

    # Check coverage
    covered_fields = basic_fields | advanced_fields
    uncovered_fields = all_fields - covered_fields
    if uncovered_fields:
        print(f"⚠️  Uncovered fields (not in basic or advanced): {uncovered_fields}")
    else:
        print("✓ All fields are covered by basic or advanced groupings")

    print()


def main():
    """Run all tests."""
    print("=" * 60)
    print("Configuration UI Generation Tests")
    print("=" * 60)
    print()

    try:
        test_field_component_creation()
        test_config_building()
        test_field_groupings()

        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
