# Tests Directory

This directory contains all functional and integration tests for Benchmarkdown.

## Test Categories

### Configuration System Tests

**test_config_ui.py** - Configuration UI Generation
- Tests Pydantic field → Gradio component mapping
- Verifies config building from UI values
- Validates field groupings (basic/advanced)
```bash
uv run python tests/test_config_ui.py
```

**test_config_extraction.py** - End-to-End Config Extraction
- Tests configuration-based extraction workflow
- Compares default vs custom configurations
- Validates performance differences
```bash
uv run python tests/test_config_extraction.py
```

**test_multiple_configs.py** - Multiple Instance Management
- Tests creating multiple extractor instances
- Verifies different configurations side-by-side
- Validates instance isolation
```bash
uv run python tests/test_multiple_configs.py
```

### Application Integration Tests

**test_ui.py** - Basic UI Components
- Tests BenchmarkUI with single Docling extractor
- Validates document processing
- Checks extraction metrics (timing, character/word counts)
```bash
uv run python tests/test_ui.py
```

**test_integrated_app.py** - Integrated App Workflow
- Tests dynamic extractor registration
- Validates configuration storage
- Tests multiple configuration scenarios
```bash
uv run python tests/test_integrated_app.py
```

**test_redesigned_workflow.py** - Redesigned UI Workflow
- Tests new workflow: select → configure → queue → extract
- Validates queue management (add/clear)
- Tests multi-configuration queue
```bash
uv run python tests/test_redesigned_workflow.py
```

### Browser/API Tests

**test_browser.py** - Browser Testing Guide
- Gradio client connectivity test
- Manual browser test checklist (13 visual checks)
- Interaction test guide (11 tests)
- Screenshot documentation guide
```bash
uv run python tests/test_browser.py
```

**test_workflow_api.py** - Automated Workflow Test
- Complete workflow automation via Gradio API
- Tests adding configurations programmatically
- Validates queue state management
- Tests document processing (if test files available)
```bash
uv run python tests/test_workflow_api.py
```
**Note:** Requires app to be running (`uv run python app.py`)

## Running All Tests

Run all tests in sequence:
```bash
# Configuration tests
uv run python tests/test_config_ui.py
uv run python tests/test_config_extraction.py
uv run python tests/test_multiple_configs.py

# Application tests
uv run python tests/test_ui.py
uv run python tests/test_integrated_app.py
uv run python tests/test_redesigned_workflow.py

# Browser/API tests (requires app running)
uv run python app.py &  # Start in background
sleep 5
uv run python tests/test_browser.py
uv run python tests/test_workflow_api.py
kill %1  # Stop background app
```

## Test Data

Tests use documents from:
- `data/input/lidia-anon/*.docx` - Anonymized Italian legal documents
- Tests gracefully skip if no test documents are found

## Expected Output

All tests should output:
- ✅ Success indicators for passing tests
- Clear descriptions of what's being tested
- Summary of results at the end

Example output:
```
🧪 Testing Configuration UI Generation
============================================================
✓ Boolean field 'do_ocr': Checkbox
✓ Enum field 'table_structure_mode': Dropdown
✓ Integer field 'num_threads': Slider
✓ Float field 'images_scale': Slider
============================================================
✅ All tests passed!
============================================================
```

## Test Coverage

| Component | Test File | Coverage |
|-----------|-----------|----------|
| Pydantic Config Models | test_config_ui.py | ✅ |
| UI Component Generation | test_config_ui.py | ✅ |
| Config → Extractor Flow | test_config_extraction.py | ✅ |
| Multiple Instances | test_multiple_configs.py | ✅ |
| Basic Extraction | test_ui.py | ✅ |
| Dynamic Registration | test_integrated_app.py | ✅ |
| Queue Management | test_redesigned_workflow.py | ✅ |
| Workflow API | test_workflow_api.py | ✅ |
| Browser UI | test_browser.py | 📋 Manual |

## Troubleshooting

**Import errors:**
```bash
# Install all dependencies
uv sync --all-groups
```

**No test documents found:**
- Tests will skip extraction and show warning
- Add .docx files to `data/input/lidia-anon/` to enable full tests

**API test fails:**
- Ensure app is running: `uv run python app.py`
- Check port 7860 is not in use: `lsof -i:7860`
- Wait a few seconds for app to fully start

**Gradio client errors:**
- Install: `uv pip install gradio-client`
- Ensure app is accessible at http://localhost:7860

## Adding New Tests

When adding new tests:
1. Name file `test_<feature>.py`
2. Include clear docstring explaining what's tested
3. Use emoji indicators (✅ ❌ ⏳ ⚠️) for output
4. Print summary at end with test count
5. Return exit code 0 for success, non-zero for failure
6. Update this README with test description

## Continuous Integration

These tests are designed to be run in CI/CD pipelines:
- All tests are self-contained
- No external dependencies beyond requirements
- Clear pass/fail indicators
- Suitable for automated testing
