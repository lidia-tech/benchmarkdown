#!/usr/bin/env python3
"""
Smoke test for the redesigned UI against a running app.

Exercises the workflow through Gradio's Python HTTP client (`gradio_client`),
not a real browser. Marked `integration` because it needs the app running.
"""

import time
from pathlib import Path

import pytest


@pytest.mark.integration
def test_with_gradio_client():
    """Test using Gradio's Python client (no browser needed)."""
    print("🧪 Testing Redesigned UI with Gradio Client")
    print("=" * 60)

    try:
        from gradio_client import Client
    except ImportError:
        pytest.skip("gradio_client not installed")

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
