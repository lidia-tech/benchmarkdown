# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Benchmarkdown is a benchmark suite for comparing document-to-markdown extraction technologies. It provides a protocol-based framework for testing different extraction tools (local and cloud-based) against real-world documents, with both a programmatic API and a web-based Gradio UI.

## Essential Commands

### Environment Setup
```bash
# Install with all extractors (recommended for development)
uv sync --all-groups

# Install specific extractors only
uv sync --group docling      # Local processing with Docling
uv sync --group textract     # AWS Textract cloud service
```

### Running the Application
```bash
# Launch Gradio web UI (primary interface)
uv run python app.py

# Use in Jupyter notebooks
# Set kernel to .venv/bin/python and open notebooks/docling.ipynb or notebooks/textract.ipynb
```

### Python Execution
Always use `uv run python` or `uv run` prefix when executing Python scripts or the interpreter.

## Architecture

### Protocol-Based Design

The core architecture uses Python's `Protocol` typing for loose coupling between the UI and extraction implementations:

**`benchmarkdown/types.py`**: Defines `MarkdownExtractor` protocol with single async method:
```python
async def extract_markdown(self, filename: os.PathLike) -> str
```

All extractors implement this protocol, allowing the UI to work with any extraction tool without tight coupling.

### Configuration System

**Pydantic-based configuration** enables type-safe, UI-driven extractor configuration:

**`benchmarkdown/config.py`**: Pydantic models for extractor configuration
- `DoclingConfig`: 15 parameters (OCR, tables, enrichment, threading, etc.)
- Field metadata includes descriptions, constraints, defaults
- `to_docling_options()` converts to native Docling format
- Extensible pattern for other extractors (TextractConfig stub included)

**`benchmarkdown/config_ui.py`**: Automatic Gradio UI generation
- Maps Pydantic fields to Gradio components based on type
- Two-tier layout: Basic options + Advanced accordion
- `build_config_from_ui_values()` constructs validated configs

**`app.py`**: Main application entry point
- Auto-detects available extractors (Docling, AWS Textract)
- Calls `create_app()` from `benchmarkdown.ui` to build Gradio interface
- Gracefully handles missing dependencies and configuration issues

**Profile-based workflow**:
- Users create named configuration profiles through the UI
- Profiles are saved as JSON and can be reused across sessions
- Multiple tasks with different configurations can be queued before extraction
- No code changes needed to compare different settings

See `CONFIG_UI_README.md` for user guide and configuration patterns.

### Extractor Implementations

**`benchmarkdown/docling.py`**:
- Wraps IBM's Docling library for local document processing
- Uses `DocumentConverter` and thread executor for async operation
- Free, no external dependencies beyond the library

**`benchmarkdown/textract.py`**:
- AWS Textract cloud-based service wrapper
- S3 workspace URI automatically read from `TEXTRACT_S3_WORKSPACE` environment variable
- Uses `Textractor` library with Layout and Tables features
- Configuration managed through TextractConfig (s3_upload_path hidden from UI)

### UI Architecture (`benchmarkdown/ui/`)

The UI is now modularized into separate components for better maintainability:

**`benchmarkdown/ui/core.py`**: Core BenchmarkUI class
- **Extractor Registry**: Stores extractors with metadata `{name: {instance}}`
- **Async Processing Pipeline**:
  - Processes multiple documents × multiple extractors in parallel
  - Uses `asyncio.gather()` for concurrent execution
  - Stores results in `self.results` dict: `{filename: {extractor_name: ExtractionResult}}`
- **ExtractionResult dataclass**: Captures markdown, timing, metrics, errors

**`benchmarkdown/ui/results.py`**: Results display generation
- `generate_comparison_view_tabbed()`: Tabbed view for multiple extractors
- `generate_comparison_view_sidebyside()`: Side-by-side comparison
- HTML generation with syntax highlighting and metrics tables

**`benchmarkdown/ui/queue.py`**: Task queue persistence
- `load_queue_from_disk()`: Restores queue from `.task_queue.json` on app start
- `save_queue_to_disk()`: Persists queue after changes
- `generate_task_list_html()`: Renders task cards with delete buttons
- Serializes config_dict (excludes extractor instances which can't be JSON-serialized)

**`benchmarkdown/ui/app_builder.py`**: Main Gradio interface
- `create_app()`: Builds two-column layout (Task List | Task Editor → Results View)
- **Task Editor workflow**: Add Task → Select Engine → Select/Create Profile → Configure → Save & Add to Queue
- **Progressive Disclosure**: Editor and results shown/hidden based on user actions
- Event handlers for profile management, queue operations, extraction runs

**`benchmarkdown/profile_manager.py`**: Configuration profile management
- Saves profiles as JSON files in `./config/` directory
- `save_profile()`, `load_profile()`, `list_profiles()`, `delete_profile()`
- Profiles are engine-specific and reusable across sessions

### Key Workflow Changes

**Queue-based extraction**:
1. Users build a queue of extraction tasks (each task = engine + profile configuration)
2. Queue persists to `.task_queue.json` and reloads on app restart
3. Click "Launch Extraction" to move to upload/run phase
4. All queued extractors process all uploaded documents in parallel

**Profile persistence**:
- Profiles stored in `./config/` as JSON files (e.g., `./config/fast_mode.json`)
- Each profile contains: engine name, profile name, and config_dict
- Profiles can be edited, deleted, and reused across sessions

## Adding New Extractors

### Basic Implementation

1. Create class in `benchmarkdown/` implementing `MarkdownExtractor` protocol
2. Implement `async def extract_markdown(self, filename: os.PathLike) -> str`
3. Use `asyncio.run_in_executor()` if wrapping blocking library
4. Add to `app.py` extractor registry with try/except for graceful degradation
5. Add dependency group to `pyproject.toml` if new library required

Example:
```python
class MyExtractor:
    async def extract_markdown(self, filename: os.PathLike) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._blocking_extract, filename)

    def _blocking_extract(self, filename):
        # Your synchronous extraction logic
        return markdown_text
```

### Adding Configuration Support

To add UI-driven configuration (like Docling has):

1. **Create Pydantic model** in `benchmarkdown/config.py`:
   ```python
   class MyExtractorConfig(BaseModel):
       feature_x: bool = Field(default=True, description="Enable feature X")
       threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Detection threshold")
   ```

2. **Update extractor** to accept config:
   ```python
   class MyExtractor:
       def __init__(self, config: Optional[MyExtractorConfig] = None, **kwargs):
           if config:
               self.config = config
           else:
               # fallback
   ```

3. **Define field groupings** in `config_ui.py`:
   ```python
   MY_EXTRACTOR_BASIC_FIELDS = ["feature_x"]
   MY_EXTRACTOR_ADVANCED_FIELDS = ["threshold"]
   ```

4. **Add UI components** in `benchmarkdown/ui/app_builder.py` following the Docling/Textract pattern:
   - Add configuration area in the task editor
   - Handle profile save/load for the new extractor
   - Wire up event handlers for profile management

The UI will automatically generate appropriate Gradio components based on field types.

**Note on environment-only configuration**: For values that should not be editable in the UI (like API keys or S3 paths), exclude them from the field groupings and use `default_factory` to read from environment variables (see TextractConfig.s3_upload_path as example).

## Data Organization

- **`data/input/`**: Source documents (PDF, DOCX) organized by category
  - `lidia-internal/`: Italian legal documents (not anonymized)
  - `lidia-anon/`: Anonymized versions for testing
  - `biglaw-bench/`: Law firm benchmark documents
  - `mesa/`: Insurance/corporate documents
- **`data/raw_markdown/`**: Initial extraction outputs
- **`data/clean_markdown/`**: Processed/cleaned outputs
- **`data/docling_doc/`**: Docling JSON intermediate format

## Configuration

AWS Textract requires environment variable with full S3 URI:
```bash
export TEXTRACT_S3_WORKSPACE=s3://your-bucket-name/textract-workspace/
```

AWS credentials via standard AWS SDK methods (`~/.aws/credentials` or environment variables).

## Testing

All tests are located in the `tests/` directory. See `tests/README.md` for comprehensive documentation.

### Quick Test Suite

Run core tests without starting the app:
```bash
uv run python tests/test_config_ui.py           # Configuration UI generation
uv run python tests/test_config_extraction.py   # Config-based extraction
uv run python tests/test_integrated_app.py      # Dynamic registration
uv run python tests/test_redesigned_workflow.py # Queue workflow
```

### API/Browser Tests

Require running app:
```bash
uv run python app.py &
sleep 5
uv run python tests/test_workflow_api.py  # Automated workflow via API
uv run python tests/test_browser.py       # Manual checklist + connectivity
```

### Test Categories

**Configuration Tests:**
- `test_config_ui.py` - Pydantic → Gradio component mapping
- `test_config_extraction.py` - End-to-end with custom configs
- `test_multiple_configs.py` - Multiple extractor instances

**Integration Tests:**
- `test_integrated_app.py` - Dynamic extractor registration
- `test_redesigned_workflow.py` - Queue-based workflow with profiles

**Browser/API Tests:**
- `test_browser.py` - Manual test checklist, connectivity
- `test_workflow_api.py` - Automated workflow testing

### Test Data

Tests use documents from `data/input/lidia-anon/`. Tests gracefully skip if no documents found.

### Continuous Integration

All tests are CI-ready:
- Self-contained with clear pass/fail
- No external dependencies beyond requirements
- Emoji indicators for output (✅ ❌ ⏳ ⚠️)

## Development Notes

- All extractors use async/await pattern via thread pool executors
- UI uses `asyncio.run()` wrapper for Gradio compatibility (Gradio is sync)
- Temp files stored in `tempfile.mkdtemp()` for downloads/reports
- If you want to update the python libraries in the virtual environment, use `uv sync --all-extras --all-groups`.