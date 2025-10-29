#!/usr/bin/env python3
"""
Test script for profile management functionality.

This tests the ProfileManager class with Docling configurations.
"""

import os
import sys
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarkdown.profile_manager import ProfileManager
from benchmarkdown.extractors.docling import Config as DoclingConfig
from benchmarkdown.extractors.docling.config import TableFormerModeEnum


def test_profile_manager():
    """Test all profile management operations."""
    print("=" * 60)
    print("Testing Profile Manager")
    print("=" * 60)

    # Use a temporary config directory for testing
    test_config_dir = "./test_config"
    if Path(test_config_dir).exists():
        shutil.rmtree(test_config_dir)

    pm = ProfileManager(config_dir=test_config_dir)
    print(f"\n✓ Created ProfileManager with directory: {test_config_dir}")

    # Test 1: Save a profile
    print("\n" + "-" * 60)
    print("Test 1: Save a profile")
    print("-" * 60)

    config1 = DoclingConfig(
        do_ocr=True,
        do_table_structure=True,
        table_structure_mode=TableFormerModeEnum.FAST,
        num_threads=4,
        do_code_enrichment=True
    )

    profile_name_1 = "Fast Mode"
    filepath = pm.save_profile(
        engine="Docling",
        profile_name=profile_name_1,
        config_data=config1.model_dump()
    )
    print(f"✓ Saved profile '{profile_name_1}' to: {filepath}")

    # Test 2: Save another profile
    print("\n" + "-" * 60)
    print("Test 2: Save another profile")
    print("-" * 60)

    config2 = DoclingConfig(
        do_ocr=True,
        do_table_structure=True,
        table_structure_mode=TableFormerModeEnum.ACCURATE,
        num_threads=8,
        do_formula_enrichment=True,
        do_picture_classification=True
    )

    profile_name_2 = "High Quality"
    filepath = pm.save_profile(
        engine="Docling",
        profile_name=profile_name_2,
        config_data=config2.model_dump()
    )
    print(f"✓ Saved profile '{profile_name_2}' to: {filepath}")

    # Test 3: List profiles
    print("\n" + "-" * 60)
    print("Test 3: List profiles")
    print("-" * 60)

    profiles = pm.list_profiles()
    print(f"✓ Found {len(profiles)} profiles:")
    for p in profiles:
        print(f"  - {p['profile_name']} ({p['engine']})")

    assert len(profiles) == 2, f"Expected 2 profiles, got {len(profiles)}"

    # Test 4: List profiles filtered by engine
    print("\n" + "-" * 60)
    print("Test 4: List profiles filtered by engine")
    print("-" * 60)

    docling_profiles = pm.list_profiles(engine="Docling")
    print(f"✓ Found {len(docling_profiles)} Docling profiles")
    assert len(docling_profiles) == 2, f"Expected 2 Docling profiles, got {len(docling_profiles)}"

    textract_profiles = pm.list_profiles(engine="AWS Textract")
    print(f"✓ Found {len(textract_profiles)} Textract profiles")
    assert len(textract_profiles) == 0, f"Expected 0 Textract profiles, got {len(textract_profiles)}"

    # Test 5: Load a profile
    print("\n" + "-" * 60)
    print("Test 5: Load a profile")
    print("-" * 60)

    loaded_profile = pm.load_profile(profile_name_1)
    print(f"✓ Loaded profile: {loaded_profile['profile_name']}")
    print(f"  Engine: {loaded_profile['engine']}")
    print(f"  Config keys: {list(loaded_profile['config_data'].keys())[:5]}...")

    assert loaded_profile['profile_name'] == profile_name_1
    assert loaded_profile['engine'] == "Docling"
    assert loaded_profile['config_data']['do_ocr'] == True
    assert loaded_profile['config_data']['table_structure_mode'] == "fast"
    assert loaded_profile['config_data']['num_threads'] == 4

    # Test 6: Check if profile exists
    print("\n" + "-" * 60)
    print("Test 6: Check if profile exists")
    print("-" * 60)

    exists = pm.profile_exists(profile_name_1)
    print(f"✓ Profile '{profile_name_1}' exists: {exists}")
    assert exists == True

    exists = pm.profile_exists("Non Existent Profile")
    print(f"✓ Profile 'Non Existent Profile' exists: {exists}")
    assert exists == False

    # Test 7: Delete a profile
    print("\n" + "-" * 60)
    print("Test 7: Delete a profile")
    print("-" * 60)

    success = pm.delete_profile(profile_name_1)
    print(f"✓ Deleted profile '{profile_name_1}': {success}")
    assert success == True

    profiles = pm.list_profiles()
    print(f"✓ Remaining profiles: {len(profiles)}")
    assert len(profiles) == 1

    # Test 8: Try to delete a non-existent profile
    print("\n" + "-" * 60)
    print("Test 8: Try to delete a non-existent profile")
    print("-" * 60)

    success = pm.delete_profile("Non Existent Profile")
    print(f"✓ Deleted 'Non Existent Profile': {success} (should be False)")
    assert success == False

    # Test 9: Try to load a deleted profile
    print("\n" + "-" * 60)
    print("Test 9: Try to load a deleted profile")
    print("-" * 60)

    try:
        pm.load_profile(profile_name_1)
        print("❌ Should have raised FileNotFoundError")
        assert False
    except FileNotFoundError as e:
        print(f"✓ Correctly raised FileNotFoundError: {e}")

    # Cleanup
    print("\n" + "-" * 60)
    print("Cleanup")
    print("-" * 60)
    shutil.rmtree(test_config_dir)
    print(f"✓ Removed test directory: {test_config_dir}")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_profile_manager()
