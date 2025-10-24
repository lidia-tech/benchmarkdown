#!/usr/bin/env python3
"""Quick test to verify markdown rendering works correctly."""

import markdown

# Test markdown
test_md = """
## Test Header

This is **bold** and this is *italic*.

- Item 1
- Item 2
- Item 3

### Subheader

Some more text here.
"""

print("Original Markdown:")
print(test_md)
print("\n" + "="*60 + "\n")

# Render it
rendered = markdown.markdown(test_md, extensions=['extra', 'nl2br', 'sane_lists'])

print("Rendered HTML:")
print(rendered)
print("\n" + "="*60 + "\n")

# Check that it actually rendered
assert "<h2>" in rendered, "Headers not rendered"
assert "<strong>" in rendered, "Bold not rendered"
assert "<em>" in rendered, "Italic not rendered"
assert "<ul>" in rendered or "<li>" in rendered, "Lists not rendered"

print("✅ Markdown rendering works correctly!")
