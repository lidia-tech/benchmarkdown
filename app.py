#!/usr/bin/env python3
"""
Main application file for Benchmarkdown Gradio UI.

This script initializes the extractors and launches the Gradio interface.
"""

import os
from benchmarkdown.ui import create_ui

# Import extractors based on available dependencies
extractors = {}

# Try to import Docling
try:
    from benchmarkdown.docling import DoclingExtractor
    extractors["Docling (Local)"] = {
        "instance": DoclingExtractor(),
        "cost_per_page": None  # Free local processing
    }
    print("✓ Docling extractor loaded")
except ImportError as e:
    print(f"⚠️  Docling not available: {e}")
    print("   Install with: uv sync --group docling")

# Try to import AWS Textract
try:
    from benchmarkdown.textract import TextractExtractor

    # Check for S3 bucket configuration
    s3_bucket = os.environ.get("TEXTRACT_S3_BUCKET", "your-bucket-name")
    s3_path = f"s3://{s3_bucket}/textract-temp/"

    if s3_bucket != "your-bucket-name":
        extractors["AWS Textract (Cloud)"] = {
            "instance": TextractExtractor(s3_upload_path=s3_path),
            "cost_per_page": 0.05  # Approximate cost per page
        }
        print("✓ AWS Textract extractor loaded")
    else:
        print("⚠️  AWS Textract available but not configured")
        print("   Set TEXTRACT_S3_BUCKET environment variable")
except ImportError as e:
    print(f"⚠️  AWS Textract not available: {e}")
    print("   Install with: uv sync --group textract")

if not extractors:
    print("\n❌ No extractors available! Please install at least one:")
    print("   - Docling: uv sync --group docling")
    print("   - Textract: uv sync --group textract")
    exit(1)

print(f"\n🚀 Starting Benchmarkdown UI with {len(extractors)} extractor(s)...")

# Create and launch the UI
demo = create_ui(extractors)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
