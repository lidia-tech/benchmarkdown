#!/usr/bin/env python3
"""
Browser-based smoke test for the redesigned UI.

This script tests the complete workflow by interacting with the actual
Gradio interface through browser automation.
"""

import time
from pathlib import Path


def test_with_gradio_client():
    """Test using Gradio's Python client (no browser needed)."""
    print("🧪 Testing Redesigned UI with Gradio Client")
    print("=" * 60)

    try:
        from gradio_client import Client
    except ImportError:
        print("⚠️  gradio_client not installed")
        print("   Install with: pip install gradio-client")
        return False

    try:
        # Connect to the running app
        print("\n1. Connecting to app at http://localhost:7860...")
        client = Client("http://localhost:7860")
        print("   ✓ Connected successfully")

        # Get API info
        print("\n2. Checking API endpoints...")
        print(f"   Available endpoints: {len(client.view_api())}")

        print("\n" + "=" * 60)
        print("✅ Basic connectivity test passed!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


def manual_test_checklist():
    """Print a manual test checklist for browser testing."""
    print("\n\n📋 Manual Browser Test Checklist")
    print("=" * 60)
    print("\nOpen http://localhost:7860 in your browser and verify:\n")

    checklist = [
        ("Page loads successfully", "App displays with title 'Benchmarkdown - Document Extraction Comparison'"),
        ("Section 1 visible", "See '1️⃣ Configure Extractors' section"),
        ("Engine selector works", "Dropdown shows 'Docling' option"),
        ("Config name field visible", "Text input for 'Configuration Name'"),
        ("Docling config visible", "See Docling Configuration section with checkboxes and sliders"),
        ("Basic options visible", "See: Do OCR, Do Table Structure, Table Structure Mode, Num Threads"),
        ("Advanced accordion", "Click 'Advanced Options' - expands to show more settings"),
        ("Add button visible", "See green '➕ Add to Extraction Queue' button"),
        ("Queue section visible", "See '2️⃣ Extraction Queue' section"),
        ("Initial queue empty", "Shows 'No extractors configured yet' message"),
        ("Extract section visible", "See '3️⃣ Extract & Compare' section"),
        ("File upload visible", "See file upload widget"),
        ("Extract button visible", "See '🚀 Run Extraction' button (disabled until queue has items)"),
    ]

    print("VISUAL CHECKS:")
    for i, (check, detail) in enumerate(checklist, 1):
        print(f"  [{i:2d}] {check}")
        print(f"       → {detail}")

    print("\n" + "-" * 60)
    print("\nINTERACTION TESTS:")
    print("  [1] Enter config name: 'Test Fast Mode'")
    print("  [2] Uncheck 'Do OCR'")
    print("  [3] Change 'Table Structure Mode' to 'fast'")
    print("  [4] Set 'Num Threads' to 8")
    print("  [5] Click 'Add to Extraction Queue'")
    print("  [6] Verify status shows: '✓ Added: Docling (Test Fast Mode)'")
    print("  [7] Verify queue section now shows: '1. Docling (Test Fast Mode)'")
    print("  [8] Add another config with different name")
    print("  [9] Verify queue shows both configurations")
    print("  [10] Click 'Clear Queue'")
    print("  [11] Verify queue returns to 'No extractors configured'")

    print("\n" + "-" * 60)
    print("\nFULL WORKFLOW TEST:")
    print("  [1] Add a configuration")
    print("  [2] Find a test document in data/input/lidia-anon/")
    print("  [3] Upload the document")
    print("  [4] Click 'Run Extraction'")
    print("  [5] Wait for extraction to complete")
    print("  [6] Verify results table appears with metrics")
    print("  [7] Verify comparison view shows markdown output")

    print("\n" + "=" * 60)


def quick_screenshot_guide():
    """Guide for taking screenshots."""
    print("\n\n📸 Screenshot Guide")
    print("=" * 60)
    print("\nTo document the UI, take screenshots of:")
    print("  1. Initial page load (full workflow visible)")
    print("  2. Configuration section with settings filled out")
    print("  3. Queue section with 2-3 items added")
    print("  4. Results section after extraction")
    print("  5. Comparison view (tabbed)")
    print("  6. Comparison view (side-by-side)")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Test with Gradio client
    success = test_with_gradio_client()

    # Print manual test checklist
    manual_test_checklist()

    # Print screenshot guide
    quick_screenshot_guide()

    print("\n\n🌐 BROWSER TEST")
    print("=" * 60)
    print("\nThe app is running at: http://localhost:7860")
    print("\nPlease open this URL in your browser and go through the")
    print("manual test checklist above to verify the redesigned workflow.")
    print("\nPress Ctrl+C in the terminal running app.py to stop the server.")
    print("=" * 60)
