#!/usr/bin/env python3
"""Test that task queue persists across app restarts."""

import os
import json
import sys

# Check if queue file exists
QUEUE_FILE = ".task_queue.json"

if not os.path.exists(QUEUE_FILE):
    print("❌ Queue file does not exist")
    sys.exit(1)

# Load and check contents
with open(QUEUE_FILE, 'r') as f:
    queue = json.load(f)

print(f"✓ Queue file exists with {len(queue)} tasks")

if len(queue) == 0:
    print("❌ Queue is empty")
    sys.exit(1)

# Check first task
task = queue[0]
print(f"✓ Task 1: {task['engine']} - {task['config_name']}")

# Verify all required fields
required_fields = ['engine', 'config_name', 'cost', 'config_dict']
for field in required_fields:
    if field not in task:
        print(f"❌ Task missing field: {field}")
        sys.exit(1)

print(f"✓ Task has all required fields")
print(f"✓ Config has {len(task['config_dict'])} parameters")

print("\n✅ All persistence tests passed!")
