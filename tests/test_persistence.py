#!/usr/bin/env python3
"""Test that the task queue is persisted to disk in the expected schema.

This test is self-contained: it points the queue module at a temporary file,
saves a synthetic task list, and verifies the persisted JSON. It does not
depend on a running app or a pre-existing ``.task_queue.json`` artifact.
"""

import json
import tempfile
from pathlib import Path

import benchmarkdown.ui.queue as queue_mod
from benchmarkdown.ui.queue import save_queue_to_disk

# Fields that save_queue_to_disk persists for each task. Extractor objects are
# intentionally dropped on save and rebuilt from config_dict on load.
REQUIRED_FIELDS = ["engine", "config_name", "config_dict"]


def test_queue_persistence():
    """Save a synthetic queue and verify the persisted schema."""
    print("=" * 60)
    print("Test: Task Queue Persistence")
    print("=" * 60)

    tasks = [
        {
            "engine": "Docling",
            "config_name": "default",
            "extractor": object(),  # stand-in; must be dropped on save
            "config_dict": {"num_threads": 4, "do_ocr": True},
        },
        {
            "engine": "AWS Textract",
            "config_name": "high-quality",
            "extractor": object(),
            "config_dict": {"region": "us-east-1"},
        },
    ]

    # Point the queue module at a temporary file so we don't clobber a real
    # .task_queue.json in the working directory.
    original_queue_file = queue_mod.QUEUE_FILE
    with tempfile.TemporaryDirectory() as tmp:
        queue_mod.QUEUE_FILE = str(Path(tmp) / "test_queue.json")
        try:
            save_queue_to_disk(tasks)

            assert Path(queue_mod.QUEUE_FILE).exists(), "Queue file should be created"

            with open(queue_mod.QUEUE_FILE, "r") as f:
                saved = json.load(f)
        finally:
            queue_mod.QUEUE_FILE = original_queue_file

    print(f"✓ Queue file written with {len(saved)} tasks")
    assert len(saved) == len(tasks), f"Expected {len(tasks)} tasks, got {len(saved)}"

    for i, saved_task in enumerate(saved):
        print(f"✓ Task {i + 1}: {saved_task['engine']} - {saved_task['config_name']}")

        for field in REQUIRED_FIELDS:
            assert field in saved_task, f"Task missing field: {field}"

        # The live extractor object must not be serialized.
        assert "extractor" not in saved_task, "Extractor object should not be persisted"

    # Values round-trip correctly.
    assert saved[0]["engine"] == "Docling"
    assert saved[0]["config_dict"] == {"num_threads": 4, "do_ocr": True}
    assert saved[1]["config_name"] == "high-quality"

    print("✓ All tasks have the expected fields and values")
    print("\n✅ All persistence tests passed!")


if __name__ == "__main__":
    test_queue_persistence()
