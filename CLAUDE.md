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

# Run quick component test
uv run python test_ui.py

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

**`app.py`**: Main application with Configuration tab
- Users create named configurations through UI
- Configurations dynamically register as extractors
- No code changes needed to compare different settings

See `CONFIG_UI_README.md` for user guide and configuration patterns.

### Extractor Implementations

**`benchmarkdown/docling.py`**:
- Wraps IBM's Docling library for local document processing
- Uses `DocumentConverter` and thread executor for async operation
- Free, no external dependencies beyond the library

**`benchmarkdown/textract.py`**:
- AWS Textract cloud-based service wrapper
- Requires S3 bucket configuration via `TEXTRACT_S3_BUCKET` environment variable
- Uses `Textractor` library with Layout and Tables features
- Cost per page ~$0.05

### UI Architecture (`benchmarkdown/ui.py`)

The Gradio UI is built around the `BenchmarkUI` class with these key responsibilities:

1. **Extractor Registry**: Dynamically registers extractors with metadata (cost, name)
2. **Async Processing Pipeline**:
   - Processes multiple documents × multiple extractors in parallel
   - Uses `asyncio.gather()` for concurrent execution
   - Stores results in `self.results` dict: `{filename: {extractor_name: ExtractionResult}}`
3. **View Generation**: Creates HTML for tabbed and side-by-side comparison modes
4. **Export Functions**: ZIP bundling, HTML report generation, individual file downloads

**Progressive Disclosure Pattern**: UI controls (document selector, view toggle, download buttons) remain hidden until extraction completes, reducing cognitive load.

### Application Entry Point (`app.py`)

Auto-detects available extractors by attempting imports:
- Gracefully handles missing dependencies (prints warnings, continues)
- Checks AWS configuration (S3 bucket environment variable)
- Registers all available extractors with the UI
- Fails fast if no extractors available

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

4. **Add Configuration tab section** in `app.py` following the Docling pattern

The UI will automatically generate appropriate Gradio components based on field types.

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

AWS Textract requires environment variable:
```bash
export TEXTRACT_S3_BUCKET=your-bucket-name
```

AWS credentials via standard AWS SDK methods (`~/.aws/credentials` or environment variables).

## Testing

### Unit/Integration Testing

`test_ui.py` provides integration test:
- Finds first DOCX in `data/input/lidia-anon/`
- Processes with Docling extractor
- Validates metrics (timing, character/word counts)
- Prints first 200 chars of extracted markdown

Run after UI changes to verify extraction pipeline integrity.

### Smoke Tests and Functional Testing

Browser tools can be used for smoke tests and functional tests of the Gradio UI:
- Launch the app with `uv run python app.py`
- Use browser automation to verify UI loads, file uploads work, extraction completes, and results display correctly
- Test both tabbed and side-by-side comparison views
- Validate download functionality (ZIP and HTML report generation)

## Development Notes

- All extractors use async/await pattern via thread pool executors
- UI uses `asyncio.run()` wrapper for Gradio compatibility (Gradio is sync)
- Temp files stored in `tempfile.mkdtemp()` for downloads/reports
- Cost estimation is rough (3000 chars = 1 page) - adjust in `ui.py` if needed
- If you want to update the python libraries in the virtual environment, use `uv sync --all-extras --all-groups`.