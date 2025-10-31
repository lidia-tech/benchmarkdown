#!/usr/bin/env python3
"""
Benchmarkdown - Main application entry point.

This script detects available extractors via plugin discovery and launches the Gradio interface.
"""

import os
import logging
from dotenv import load_dotenv
load_dotenv()

from benchmarkdown.ui import create_app
from benchmarkdown.extractors import get_global_registry

# Configure logging
# Get log level from environment, default to WARNING
log_level = os.getenv('BENCHMARKDOWN_LOG_LEVEL', 'WARNING').upper()
logger = logging.getLogger("benchmarkdown")

# Set level to INFO only for this logger and its descendants
logger.setLevel(log_level)

# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S'
# )

# Discover all available extractors via plugin system
logger.info("🔍 Discovering extractor plugins...")
registry = get_global_registry()

# Get available extractors
available_extractors = registry.get_available_extractors()

if not available_extractors:
    logger.error("❌ No extractors available! Install with: uv sync --group docling")
    exit(1)

logger.info(f"✅ Found {len(available_extractors)} available extractor(s)")

if __name__ == "__main__":
    logger.info("🚀 Starting Benchmarkdown UI...")
    demo = create_app(registry=registry)
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
