# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Benchmarkdown is a benchmark suite for comparing document-to-markdown extraction technologies. It features a **plugin-based architecture** where new extractors can be added by simply creating a directory—no code changes needed. The UI automatically discovers and integrates new extractors at runtime. The system provides both a programmatic API and a web-based Gradio UI that dynamically adapts to available extractors.

## Documentation Guidelines

### Implementation Notes

When implementing significant features or architectural patterns:

1. **Create implementation notes** in `docs/implementation_notes/`:
   - Use Markdown format
   - Include: overview, architecture, implementation details, examples, extensibility, testing
   - Name files descriptively (e.g., `conditional_fields.md`, `plugin_discovery.md`)

2. **Update README** in `docs/implementation_notes/README.md`:
   - Add entry for the new note
   - Include status, commits, and use case summary

3. **When to write implementation notes**:
   - New architectural patterns (e.g., conditional fields, nested configs)
   - Complex features spanning multiple files
   - Reusable patterns for extending the system
   - Significant plugin system changes
   - Features that need detailed developer documentation

4. **Structure**:
   ```markdown
   # Feature Name
   **Status:** ✅ Complete
   **Date:** YYYY-MM-DD
   **Commits:** abc123, def456

   ## Overview
   ## Architecture
   ## Implementation Details
   ## Examples
   ## Extensibility
   ## Testing
   ## Related Files
   ```

These notes serve as developer reference and onboarding documentation, distinct from user-facing docs.

**For detailed information about specific implementation patterns and features**, see `docs/implementation_notes/README.md` which provides a comprehensive index of all implementation notes including:
- Plugin architecture and discovery
- Conditional fields (progressive disclosure UI pattern)
- Nested configurations (e.g., Docling's OCR engines)
- Dynamic UI generation
- Profile management
- And more...

## Essential Commands

### Environment Setup
```bash
# Install with all extractors (recommended for development)
uv sync --all-groups

# Install specific extractors only
uv sync --group docling                      # Local processing with Docling
uv sync --group textract                     # AWS Textract cloud service
uv sync --group llamaparse                   # LlamaParse cloud service
uv sync --group tensorlake                   # TensorLake cloud service
uv sync --group azure-document-intelligence  # Azure Document Intelligence
```

**Environment Variables**: Each extractor has specific environment variable requirements documented in its own README:
- `benchmarkdown/extractors/docling/README.md`
- `benchmarkdown/extractors/textract/README.md`
- `benchmarkdown/extractors/llamaparse/README.md`
- `benchmarkdown/extractors/tensorlake/README.md`
- `benchmarkdown/extractors/azure_document_intelligence/README.md`

See also: `docs/ENVIRONMENT_VARIABLES.md` for a consolidated reference.

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

### Plugin Architecture

**Complete plugin-based system** with automatic discovery and zero-code integration:

**`benchmarkdown/extractors/__init__.py`**: ExtractorRegistry
- Automatic plugin discovery on app startup
- Validates plugin interface (Extractor, Config, fields, metadata, is_available())
- Checks dependencies and gracefully skips unavailable extractors
- Dynamic instantiation through `create_extractor_instance()`

**Plugin structure** (`benchmarkdown/extractors/{name}/`):
- `__init__.py` - Standard exports: Extractor, Config, BASIC_FIELDS, ADVANCED_FIELDS, ENGINE_NAME, ENGINE_DISPLAY_NAME, is_available(), optional NESTED_CONFIGS
- `config.py` - Pydantic config model(s) with field groupings
- `extractor.py` - Class implementing MarkdownExtractor protocol

**`benchmarkdown/ui/dynamic_config.py`**: Dynamic UI generation
- Generates Gradio UI from plugin metadata at runtime
- Handles nested configurations (e.g., Docling's 5 OCR engines)
- Profile save/load works for any extractor automatically
- Event handlers are generic, not extractor-specific

**Adding new extractors**: Simply create `extractors/{name}/` directory with the 3 files above. UI discovers and integrates automatically—no code changes needed in app.py or UI!

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

**`benchmarkdown/extractors/docling/`**: Docling plugin
- `extractor.py`: Wraps IBM's Docling library for local document processing
- `config.py`: DoclingConfig with nested OCR configs (EasyOCR, Tesseract, TesseractCLI, OcrMac, RapidOCR)
- Uses `DocumentConverter` and thread executor for async operation
- Free, no external dependencies beyond the library
- **Backward compatibility**: `benchmarkdown/docling.py` re-exports from plugin

**`benchmarkdown/extractors/textract/`**: AWS Textract plugin
- `extractor.py`: AWS Textract cloud-based service wrapper
- `config.py`: TextractConfig with markdown formatting options
- S3 workspace URI automatically read from `TEXTRACT_S3_WORKSPACE` environment variable
- Uses `Textractor` library with Layout and Tables features
- **Backward compatibility**: `benchmarkdown/textract.py` re-exports from plugin

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

**`benchmarkdown/ui/dynamic_config.py`**: Dynamic UI generation (NEW!)
- `DynamicConfigUI`: Generates Gradio components from plugin metadata at runtime
- Handles nested configurations (e.g., Docling's OCR engine options)
- Generic event handlers work for ANY extractor
- Profile save/load automatically supports all extractors
- **Zero UI code changes needed when adding new extractors!**

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

**The plugin architecture makes adding extractors incredibly simple - just create a directory!**

### Plugin-Based Implementation (Recommended)

**Step 1**: Create plugin directory: `benchmarkdown/extractors/{name}/`

**Step 2**: Create three files:

**`config.py`** - Pydantic configuration model:
```python
from pydantic import BaseModel, Field
from typing import List

class MyExtractorConfig(BaseModel):
    """Configuration for MyExtractor."""
    feature_x: bool = Field(default=True, description="Enable feature X")
    threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Detection threshold")
    api_key: str = Field(default_factory=lambda: os.getenv("MY_API_KEY", ""), description="API key")

# Field groupings for UI generation
BASIC_FIELDS = ["feature_x", "threshold"]
ADVANCED_FIELDS = ["api_key"]
```

**`extractor.py`** - Extractor implementation:
```python
import asyncio
from typing import Optional
from benchmarkdown.extractors.base import MarkdownExtractor
from .config import MyExtractorConfig

class MyExtractor:
    """MyExtractor implementation."""

    def __init__(self, config: Optional[MyExtractorConfig] = None, **kwargs):
        self.config = config or MyExtractorConfig()

    async def extract_markdown(self, filename: os.PathLike) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._blocking_extract, filename)

    def _blocking_extract(self, filename):
        # Your extraction logic here
        return markdown_text
```

**`__init__.py`** - Standard plugin interface:
```python
from typing import Tuple
from .extractor import MyExtractor
from .config import MyExtractorConfig, BASIC_FIELDS, ADVANCED_FIELDS

# Standard exports (required by registry)
Extractor = MyExtractor
Config = MyExtractorConfig
BASIC_FIELDS = BASIC_FIELDS
ADVANCED_FIELDS = ADVANCED_FIELDS

# Plugin metadata (required)
ENGINE_NAME = "myextractor"
ENGINE_DISPLAY_NAME = "My Extractor"

def is_available() -> Tuple[bool, str]:
    """Check if dependencies are installed."""
    try:
        import myextractor_library
        return True, ""
    except ImportError as e:
        return False, f"MyExtractor not installed: {e}"

__all__ = ['Extractor', 'Config', 'BASIC_FIELDS', 'ADVANCED_FIELDS',
           'ENGINE_NAME', 'ENGINE_DISPLAY_NAME', 'is_available']
```

**Step 3**: (Optional) Add dependency group to `pyproject.toml`:
```toml
[project.optional-dependencies]
myextractor = ["myextractor-library>=1.0.0"]
```

**Step 4**: Done! Launch app and the UI will automatically:
- Discover your extractor
- Generate configuration UI from your Pydantic model
- Handle profile save/load
- Support task queueing

**No changes needed to app.py, UI code, or any other files!**

### Nested Configurations (Optional)

For complex nested configs (like Docling's OCR engines), add to `__init__.py`:

```python
NESTED_CONFIGS = {
    "parent_field": {  # e.g., "ocr_engine"
        "option1": {
            "config_class": Option1Config,
            "config_field": "option1_config",
            "basic_fields": ["field1", "field2"],
            "advanced_fields": ["field3"],
            "display_name": "Option 1 Settings"
        },
        # More options...
    }
}
```

The UI will automatically generate nested sections that show/hide based on the parent field value.

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