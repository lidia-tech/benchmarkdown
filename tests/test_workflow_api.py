#!/usr/bin/env python3
"""
Test the redesigned UI workflow using Gradio's API client.

This simulates user interactions with the browser interface.
"""

from gradio_client import Client
from pathlib import Path

import pytest


@pytest.mark.integration
def test_complete_workflow():
    """Test the complete workflow through the API."""
    print("🧪 Testing Complete Workflow via Gradio API")
    print("=" * 60)

    # Connect to app
    print("\n1. Connecting to app...")
    client = Client("http://localhost:7860")
    print("   ✓ Connected")

    # Step 1: Add first configuration
    print("\n2. Adding configuration: 'Fast Mode'")
    result = client.predict(
        engine="Docling",
        config_name="Fast Mode",
        param_2=False,  # do_ocr
        param_3=True,   # do_table_structure
        param_4="fast", # table_structure_mode
        param_5=16,     # num_threads
        param_6=False,  # force_backend_text
        param_7=True,   # do_cell_matching
        param_8=False,  # do_code_enrichment
        param_9=False,  # do_formula_enrichment
        param_10=False, # do_picture_classification
        param_11=False, # do_picture_description
        param_12=False, # generate_page_images
        param_13=False, # generate_picture_images
        param_14=1.0,   # images_scale
        param_15="auto",# accelerator_device
        param_16=0.0,   # document_timeout
        api_name="/add_to_queue"
    )
    status, queue_html = result
    print(f"   Status: {status}")
    assert "Added: Docling (Fast Mode)" in status, f"Unexpected status: {status}"
    assert len(queue_html) > 100, "Queue HTML did not update after adding a task"

    # Step 2: Add second configuration
    print("\n3. Adding configuration: 'Accurate Mode'")
    result = client.predict(
        engine="Docling",
        config_name="Accurate Mode",
        param_2=True,      # do_ocr
        param_3=True,      # do_table_structure
        param_4="accurate",# table_structure_mode
        param_5=4,         # num_threads
        param_6=False,
        param_7=True,
        param_8=False,
        param_9=False,
        param_10=False,
        param_11=False,
        param_12=False,
        param_13=False,
        param_14=1.0,
        param_15="auto",
        param_16=0.0,
        api_name="/add_to_queue"
    )
    status, queue_html = result
    print(f"   Status: {status}")
    assert "Added: Docling (Accurate Mode)" in status, f"Unexpected status: {status}"

    # Verify queue has both items
    assert "Docling (Fast Mode)" in queue_html and "Docling (Accurate Mode)" in queue_html, \
        "Queue does not show both configurations"

    # Step 3: Test document extraction (if test file exists)
    test_files = list(Path("data/input/lidia-anon").glob("*.docx"))
    if test_files:
        test_file = test_files[0]
        print(f"\n4. Testing extraction with: {test_file.name}")
        print("   ⏳ Running extraction... (this may take a minute)")

        result = client.predict(
            files=[str(test_file)],
            api_name="/sync_process_documents"
        )
        results_html, comparison_html = result

        assert "✓ OK" in results_html or "Success" in results_html, \
            f"Extraction did not succeed: {results_html[:200]}"
        # Both configurations should have processed the document
        assert "Fast Mode" in results_html and "Accurate Mode" in results_html, \
            "Not both configurations processed the document"
    else:
        print("\n4. No test documents found in data/input/lidia-anon/")
        print("   ⏭️  Skipping extraction test")

    # Step 4: Clear queue
    print("\n5. Testing queue clear...")
    result = client.predict(api_name="/clear_queue")
    queue_html, status = result
    assert "No extractors configured" in queue_html, \
        f"Queue not empty after clear: {queue_html[:100]}"

    print("\n" + "=" * 60)
    print("✅ Workflow test completed!")
    print("=" * 60)

    print("\n📊 Test Summary:")
    print("  ✓ Connected to app")
    print("  ✓ Added configuration 1 (Fast Mode)")
    print("  ✓ Added configuration 2 (Accurate Mode)")
    print("  ✓ Queue management works")
    if test_files:
        print("  ✓ Document extraction works")
    else:
        print("  ⏭  Document extraction skipped (no test files)")
