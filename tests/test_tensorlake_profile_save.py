"""
End-to-end test for TensorLake profile saving bug fix.

Tests that profiles can be saved and loaded with enum values correctly.
"""

import os
import sys
import json
from pathlib import Path
from benchmarkdown.extractors.tensorlake import Config
from benchmarkdown.config_ui import build_config_from_ui_values
from benchmarkdown.profile_manager import ProfileManager


def test_save_and_load_tensorlake_profile():
    """Test saving and loading a TensorLake profile with enum values."""
    print("\n" + "="*60)
    print("TEST: Save and load TensorLake profile")
    print("="*60)

    profile_name = "test_tensorlake_enum_bug"
    engine_name = "tensorlake"

    # Create profile manager instance
    pm = ProfileManager()

    # Clean up any existing test profile
    try:
        pm.delete_profile(profile_name)
    except Exception:
        pass

    # Simulate UI values (what Gradio would return)
    ui_values = {
        'api_key': 'test-api-key',
        'chunking_strategy': 'section',  # String value from dropdown
        'table_output_mode': 'markdown',
        'table_parsing_format': 'tsr',   # String value from dropdown
        'signature_detection': True,
        'remove_strikethrough_lines': False,
        'skew_detection': False,
        'disable_layout_detection': False,
        'cross_page_header_detection': False,
        'ocr_model': 'model02',  # String value from dropdown
        'figure_summarization': False,
        'figure_summarization_prompt': None,
        'table_summarization': False,
        'table_summarization_prompt': None,
        'include_full_page_image': False,
    }

    try:
        # Step 1: Build config from UI values
        print("\n1. Building config from UI values...")
        config = build_config_from_ui_values(Config, ui_values)
        print(f"   ✅ Config built successfully")
        print(f"   chunking_strategy: {config.chunking_strategy} (type: {type(config.chunking_strategy).__name__})")
        print(f"   table_parsing_format: {config.table_parsing_format} (type: {type(config.table_parsing_format).__name__})")
        print(f"   ocr_model: {config.ocr_model} (type: {type(config.ocr_model).__name__})")

        # Step 2: Save profile
        print("\n2. Saving profile...")
        pm.save_profile(engine_name, profile_name, ui_values)
        print(f"   ✅ Profile saved")

        # Step 3: Verify profile file exists and contains correct values
        print("\n3. Verifying profile file...")
        profile_path = Path("config") / f"{profile_name}.json"
        assert profile_path.exists(), f"Profile file not found at {profile_path}"

        with open(profile_path, 'r') as f:
            profile_data = json.load(f)

        print(f"   ✅ Profile file exists")
        print(f"   Engine: {profile_data.get('engine')}")
        print(f"   chunking_strategy: {profile_data['config_data'].get('chunking_strategy')}")
        print(f"   table_parsing_format: {profile_data['config_data'].get('table_parsing_format')}")
        print(f"   ocr_model: {profile_data['config_data'].get('ocr_model')}")

        # Verify values are strings, not enum representations
        assert profile_data['config_data']['chunking_strategy'] == 'section', (
            f"chunking_strategy is {profile_data['config_data']['chunking_strategy']}"
        )
        print(f"   ✅ chunking_strategy is correct string value")

        # Step 4: Load profile
        print("\n4. Loading profile...")
        loaded_profile = pm.load_profile(profile_name)
        loaded_engine = loaded_profile['engine']
        loaded_values = loaded_profile['config_data']
        print(f"   ✅ Profile loaded")
        print(f"   Engine: {loaded_engine}")
        print(f"   chunking_strategy: {loaded_values.get('chunking_strategy')}")

        # Step 5: Build config from loaded values (simulate UI reload)
        print("\n5. Building config from loaded values...")
        reloaded_config = build_config_from_ui_values(Config, loaded_values)
        print(f"   ✅ Config rebuilt from loaded values")
        print(f"   chunking_strategy: {reloaded_config.chunking_strategy}")
        print(f"   table_parsing_format: {reloaded_config.table_parsing_format}")
        print(f"   ocr_model: {reloaded_config.ocr_model}")

        # Step 6: Verify values match original
        print("\n6. Verifying values match original...")
        assert reloaded_config.chunking_strategy == config.chunking_strategy, (
            f"chunking_strategy mismatch: original {config.chunking_strategy}, "
            f"reloaded {reloaded_config.chunking_strategy}"
        )
        assert reloaded_config.table_parsing_format == config.table_parsing_format
        assert reloaded_config.ocr_model == config.ocr_model
        print(f"   ✅ All enum values match original config")
    finally:
        # Clean up
        print("\n7. Cleaning up...")
        try:
            pm.delete_profile(profile_name)
            print(f"   ✅ Test profile deleted")
        except Exception as e:
            print(f"   ⚠️  Warning: Could not delete test profile: {e}")
