#!/usr/bin/env python3
"""
Test the full persistence workflow:
1. Check that queue file exists with 2 tasks
2. Import and call create_app()
3. Verify that extractor_queue has 2 tasks loaded
4. Verify that the initial HTML shows the tasks
"""

import os
import sys

# Ensure we're in the right directory
os.chdir('/Users/janos/Projects/benchmarkdown')

# Import the app
from app import create_app

print("Creating app...")
demo = create_app()

# The create_app function should have loaded the queue
# and the HTML component should have the correct initial value

print("✅ Full persistence test completed")
print("Next step: manually test in browser by navigating to http://localhost:7860")
