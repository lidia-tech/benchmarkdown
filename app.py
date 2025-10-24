#!/usr/bin/env python3
"""
Main application file for Benchmarkdown Gradio UI.

This script initializes the extractors and launches the Gradio interface.

CONFIGURATION GUIDE:
    To compare different configurations of the same extractor library, create
    multiple instances with different parameters and register them with unique names.

    Example:
        # Create two Docling instances with different settings
        docling_default = DoclingExtractor()
        docling_custom = DoclingExtractor(custom_param=value)

        extractors["Docling (Default)"] = {"instance": docling_default, "cost_per_page": None}
        extractors["Docling (Custom)"] = {"instance": docling_custom, "cost_per_page": None}
"""

import os
from benchmarkdown.ui import create_ui

# Import extractors based on available dependencies
extractors = {}

# Try to import Docling
try:
    from benchmarkdown.docling import DoclingExtractor

    # Register a default Docling instance
    # You can create multiple instances with different configurations here
    extractors["Docling (Default)"] = {
        "instance": DoclingExtractor(),
        "cost_per_page": None  # Free local processing
    }

    # Example: Uncomment to add another Docling instance with different config
    # from docling.datamodel.base_models import InputFormat
    # extractors["Docling (PDF Only)"] = {
    #     "instance": DoclingExtractor(allowed_formats=[InputFormat.PDF]),
    #     "cost_per_page": None
    # }

    print(f"✓ Loaded {len([k for k in extractors if k.startswith('Docling')])} Docling extractor(s)")
except ImportError as e:
    print(f"⚠️  Docling not available: {e}")
    print("   Install with: uv sync --group docling")

# Try to import AWS Textract
try:
    from benchmarkdown.textract import TextractExtractor
    from textractor.data.constants import TextractFeatures

    # Check for S3 bucket configuration
    s3_bucket = os.environ.get("TEXTRACT_S3_BUCKET", "your-bucket-name")
    s3_path = f"s3://{s3_bucket}/textract-temp/"

    if s3_bucket != "your-bucket-name":
        # Register default Textract instance with layout + tables
        extractors["Textract (Layout+Tables)"] = {
            "instance": TextractExtractor(
                s3_upload_path=s3_path,
                features=[TextractFeatures.LAYOUT, TextractFeatures.TABLES]
            ),
            "cost_per_page": 0.05  # Approximate cost per page
        }

        # Example: Uncomment to add another Textract instance with different features
        # extractors["Textract (Layout Only)"] = {
        #     "instance": TextractExtractor(
        #         s3_upload_path=s3_path,
        #         features=[TextractFeatures.LAYOUT]
        #     ),
        #     "cost_per_page": 0.03  # Cheaper without tables
        # }

        print(f"✓ Loaded {len([k for k in extractors if k.startswith('Textract')])} Textract extractor(s)")
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
