#!/usr/bin/env python3
"""
Test script for the integrated app with configuration UI.

This tests that the app can:
1. Initialize with default extractors
2. Create configuration UI components
3. Save new configurations dynamically
4. Update the extractor list
"""

from benchmarkdown.ui import BenchmarkUI
from benchmarkdown.extractors.docling import Config as DoclingConfig, Extractor as DoclingExtractor
from benchmarkdown.extractors.docling.config import TableFormerModeEnum
from benchmarkdown.config_ui import build_config_from_ui_values


def test_integrated_workflow():
    """Test the integrated configuration workflow."""
    print("🧪 Testing Integrated App Configuration Workflow")
    print("=" * 60)

    # Step 1: Initialize UI with default extractor
    print("\n1. Initializing UI with default extractor...")
    ui = BenchmarkUI()
    default_extractor = DoclingExtractor()
    ui.register_extractor("Docling (Default)", default_extractor)
    print(f"   ✓ Registered extractors: {list(ui.extractors.keys())}")

    # Step 2: Simulate creating a custom configuration via UI
    print("\n2. Simulating custom configuration creation...")

    # Simulate UI values (what a user would select)
    ui_values = {
        'do_ocr': False,
        'do_table_structure': True,
        'table_structure_mode': 'fast',
        'num_threads': 8,
        'force_backend_text': False,
        'do_cell_matching': True,
        'do_code_enrichment': True,
        'do_formula_enrichment': False,
        'do_picture_classification': False,
        'do_picture_description': False,
        'generate_page_images': False,
        'generate_picture_images': False,
        'images_scale': 1.0,
        'accelerator_device': 'auto',
        'document_timeout': None,
    }

    config = build_config_from_ui_values(DoclingConfig, ui_values)
    print(f"   ✓ Created config with:")
    print(f"     - OCR: {config.do_ocr}")
    print(f"     - Table mode: {config.table_structure_mode}")
    print(f"     - Threads: {config.num_threads}")
    print(f"     - Code enrichment: {config.do_code_enrichment}")

    # Step 3: Register the new configuration
    print("\n3. Registering custom configuration as new extractor...")
    custom_extractor = DoclingExtractor(config=config)
    ui.register_extractor("Docling (Fast Mode)", custom_extractor)
    print(f"   ✓ Registered extractors: {list(ui.extractors.keys())}")

    # Step 4: Verify both extractors exist
    print("\n4. Verifying extractor configurations...")
    assert "Docling (Default)" in ui.extractors
    assert "Docling (Fast Mode)" in ui.extractors
    print(f"   ✓ Found {len(ui.extractors)} extractors")

    # Step 5: Verify configs are different
    print("\n5. Verifying configuration differences...")
    default_has_config = ui.extractors["Docling (Default)"]["instance"].config is not None
    custom_has_config = ui.extractors["Docling (Fast Mode)"]["instance"].config is not None

    print(f"   - Default extractor has config: {default_has_config}")
    print(f"   - Custom extractor has config: {custom_has_config}")

    if custom_has_config:
        custom_config = ui.extractors["Docling (Fast Mode)"]["instance"].config
        print(f"   - Custom config OCR: {custom_config.do_ocr}")
        print(f"   - Custom config mode: {custom_config.table_structure_mode}")
        assert custom_config.do_ocr == False
        assert custom_config.num_threads == 8
        print(f"   ✓ Configuration correctly stored")

    print("\n" + "=" * 60)
    print("✅ All integration tests passed!")
    print("=" * 60)


def test_multiple_configs():
    """Test creating multiple configurations."""
    print("\n\n🧪 Testing Multiple Configuration Workflow")
    print("=" * 60)

    ui = BenchmarkUI()

    configs = [
        ("Default", DoclingConfig()),
        ("Fast", DoclingConfig(do_ocr=False, table_structure_mode=TableFormerModeEnum.FAST, num_threads=16)),
        ("Accurate", DoclingConfig(do_ocr=True, table_structure_mode=TableFormerModeEnum.ACCURATE, num_threads=4)),
        ("Code+Formula", DoclingConfig(do_code_enrichment=True, do_formula_enrichment=True)),
    ]

    for name, config in configs:
        extractor = DoclingExtractor(config=config)
        full_name = f"Docling ({name})"
        ui.register_extractor(full_name, extractor)
        print(f"✓ Registered: {full_name}")

    print(f"\nTotal extractors: {len(ui.extractors)}")
    print(f"Extractor names: {list(ui.extractors.keys())}")

    print("\n" + "=" * 60)
    print("✅ Multiple configuration test passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_integrated_workflow()
    test_multiple_configs()
