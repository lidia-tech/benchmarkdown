#!/usr/bin/env python3
"""
Benchmarkdown - Main application entry point.

This script detects available extractors via plugin discovery and launches the Gradio interface.
"""

import os
from dotenv import load_dotenv
load_dotenv()

from benchmarkdown.ui import create_app
from benchmarkdown.extractors import get_global_registry

# Discover all available extractors via plugin system
print("🔍 Discovering extractor plugins...")
registry = get_global_registry()

# Get available extractors
available_extractors = registry.get_available_extractors()

if not available_extractors:
    print("\n❌ No extractors available! Install with: uv sync --group docling")
    exit(1)

print(f"\n✅ Found {len(available_extractors)} available extractor(s)")

if __name__ == "__main__":
    print("\n🚀 Starting Benchmarkdown UI...")
    demo = create_app(registry=registry)
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
