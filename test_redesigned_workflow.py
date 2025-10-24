#!/usr/bin/env python3
"""
Test script for the redesigned workflow.

Tests the new user journey:
1. Select extractor engine
2. Configure settings
3. Add to queue
4. Run extraction
"""

from benchmarkdown.ui import BenchmarkUI
from benchmarkdown.docling import DoclingExtractor
from benchmarkdown.config import DoclingConfig, TableFormerModeEnum
from benchmarkdown.config_ui import build_config_from_ui_values


def test_workflow():
    """Test the complete redesigned workflow."""
    print("🧪 Testing Redesigned Workflow")
    print("=" * 60)

    # Simulate the workflow
    ui = BenchmarkUI()
    queue = []

    # Step 1: User selects "Docling" engine
    print("\n1️⃣ User selects extractor engine: Docling")
    selected_engine = "Docling"
    print(f"   ✓ Selected: {selected_engine}")

    # Step 2: User configures settings
    print("\n2️⃣ User configures settings")
    config_name = "Fast Mode"
    ui_values = {
        'do_ocr': False,
        'do_table_structure': True,
        'table_structure_mode': 'fast',
        'num_threads': 16,
        'force_backend_text': False,
        'do_cell_matching': True,
        'do_code_enrichment': False,
        'do_formula_enrichment': False,
        'do_picture_classification': False,
        'do_picture_description': False,
        'generate_page_images': False,
        'generate_picture_images': False,
        'images_scale': 1.0,
        'accelerator_device': 'auto',
        'document_timeout': 0,
    }

    config = build_config_from_ui_values(DoclingConfig, ui_values)
    print(f"   ✓ Configuration created: {config_name}")
    print(f"     - OCR: {config.do_ocr}")
    print(f"     - Tables: {config.do_table_structure}")
    print(f"     - Mode: {config.table_structure_mode}")
    print(f"     - Threads: {config.num_threads}")

    # Step 3: User adds to queue
    print("\n3️⃣ User clicks 'Add to Extraction Queue'")
    extractor = DoclingExtractor(config=config)
    full_name = f"Docling ({config_name})"
    queue.append((full_name, extractor, None))
    ui.register_extractor(full_name, extractor, cost_per_page=None)
    print(f"   ✓ Added to queue: {full_name}")
    print(f"   ✓ Queue now has {len(queue)} item(s)")

    # Step 4: User adds another configuration
    print("\n4️⃣ User adds another configuration: Accurate Mode")
    config2 = DoclingConfig(
        do_ocr=True,
        table_structure_mode=TableFormerModeEnum.ACCURATE,
        num_threads=4
    )
    extractor2 = DoclingExtractor(config=config2)
    full_name2 = "Docling (Accurate Mode)"
    queue.append((full_name2, extractor2, None))
    ui.register_extractor(full_name2, extractor2, cost_per_page=None)
    print(f"   ✓ Added to queue: {full_name2}")
    print(f"   ✓ Queue now has {len(queue)} item(s)")

    # Step 5: Display queue
    print("\n5️⃣ Queue display")
    for i, (name, _, _) in enumerate(queue):
        print(f"   {i+1}. {name}")

    # Step 6: Verify UI has all extractors
    print("\n6️⃣ Verify UI has all extractors registered")
    print(f"   ✓ UI extractors: {list(ui.extractors.keys())}")
    assert len(ui.extractors) == 2
    assert "Docling (Fast Mode)" in ui.extractors
    assert "Docling (Accurate Mode)" in ui.extractors

    print("\n" + "=" * 60)
    print("✅ Redesigned workflow test passed!")
    print("=" * 60)
    print("\nUser Journey Summary:")
    print("1. ✓ Selected extractor engine")
    print("2. ✓ Configured settings")
    print("3. ✓ Added to queue")
    print("4. ✓ Added another configuration")
    print("5. ✓ Ready to upload documents and extract")


def test_queue_management():
    """Test queue management operations."""
    print("\n\n🧪 Testing Queue Management")
    print("=" * 60)

    queue = []
    ui = BenchmarkUI()

    # Add items
    print("\n1. Adding items to queue")
    for i in range(3):
        config = DoclingConfig(num_threads=4*(i+1))
        extractor = DoclingExtractor(config=config)
        name = f"Docling (Config {i+1})"
        queue.append((name, extractor, None))
        ui.register_extractor(name, extractor, cost_per_page=None)
        print(f"   ✓ Added: {name}")

    print(f"\n   Queue size: {len(queue)}")
    print(f"   UI extractors: {len(ui.extractors)}")

    # Clear queue
    print("\n2. Clearing queue")
    queue.clear()
    ui.extractors.clear()
    print(f"   ✓ Queue cleared: {len(queue)} items")
    print(f"   ✓ UI cleared: {len(ui.extractors)} extractors")

    print("\n" + "=" * 60)
    print("✅ Queue management test passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_workflow()
    test_queue_management()
