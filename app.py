#!/usr/bin/env python3
"""
Benchmarkdown - Main application entry point.

This script detects available extractors and launches the Gradio interface.
"""

import os
from dotenv import load_dotenv
load_dotenv()

from benchmarkdown.ui import create_app

# Check available extractors
has_docling = False
has_textract = False

try:
    from benchmarkdown.docling import DoclingExtractor
    has_docling = True
    print("✓ Docling extractor available")
except ImportError as e:
    print(f"⚠️  Docling not available: {e}")

try:
    from benchmarkdown.textract import TextractExtractor
    from textractor.data.constants import TextractFeatures
    s3_workspace = os.environ.get("TEXTRACT_S3_WORKSPACE")
    if s3_workspace and s3_workspace.startswith("s3://"):
        has_textract = True
        print(f"✓ AWS Textract extractor available (workspace: {s3_workspace})")
    else:
        print("⚠️  AWS Textract not configured (set TEXTRACT_S3_WORKSPACE to s3://bucket-name/path/)")
except ImportError:
    print("⚠️  AWS Textract not available")

if not has_docling and not has_textract:
    print("\n❌ No extractors available! Install with: uv sync --group docling")
    exit(1)


if __name__ == "__main__":
    print("\n🚀 Starting Benchmarkdown UI (Redesigned)...")
    demo = create_app(has_docling=has_docling, has_textract=has_textract)
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
